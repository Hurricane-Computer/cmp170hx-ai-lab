// SPDX-License-Identifier: MIT
// Bounded kernel-owned CE test; no global CUDA peer-capability changes.
// Method sequences adapted from NVIDIA's MIT UVM Turing/Ampere CE/host HAL,
// copyright NVIDIA Corporation, pinned commit 61dcc93722ecb418bb5f2e00923f05b4b8051dd1.
#include <linux/module.h>
#include <linux/io.h>
#include <linux/pci.h>
#include <linux/slab.h>
#include <linux/sizes.h>
#include <linux/uuid.h>
#include <linux/delay.h>
#include <linux/jiffies.h>
#include "cmp_ce_abi.h"
#include "nvmisc.h"
#include "class/clc46f.h"
#include "class/clc56f.h"
#include "class/clc6b5.h"
#include "class/cla06fsubch.h"

static char owner_uuid[37], accessor_uuid[37];
static unsigned int owner_gib;
static unsigned long nonce;
module_param_string(owner_uuid, owner_uuid, sizeof(owner_uuid), 0);
module_param_string(accessor_uuid, accessor_uuid, sizeof(accessor_uuid), 0);
module_param(owner_gib, uint, 0);
module_param(nonce, ulong, 0);

#define ACQUIRE_MAPPING ((UvmGpuMappingType)0x43575033U)
#define RELEASE_MAPPING ((UvmGpuMappingType)0x43575034U)
#define PROTOCOL_MAGIC 0x435750524f424532ULL
#define SEM_OFFSET SZ_4K
#define SENTINEL 0xa753c91eU
#define F(d,r,f,c) DRF_DEF(d,_##r,_##f,_##c)
#define V(d,r,f,v) DRF_NUM(d,_##r,_##f,v)

struct allocation {
    UvmGpuPointer va;
    UvmGpuAllocInfo info;
    void *cpu;
    u32 bytes;
    unsigned int slot;
    bool allocated;
};
struct ce_context {
    uvmGpuSessionHandle session;
    uvmGpuDeviceHandle device[2];
    uvmGpuAddressSpaceHandle space[2];
    NvProcessorUuid uuid[2];
    bool registered[2];
    struct allocation owner, local, dest, push;
    uvmGpuTsgHandle tsg;
    uvmGpuChannelHandle channel;
    UvmGpuChannelInfo channel_info;
    u32 put;
    bool in_flight, lease;
};
static struct ce_context ctx;
static bool retained;

static u32 pattern(u32 i, u32 tag)
{
    u32 x = (u32)nonce ^ tag ^ (i * 0x9e3779b9U);
    x ^= x >> 16; x *= 0x7feb352dU;
    x ^= x >> 15; x *= 0x846ca68bU;
    return x ^ (x >> 16);
}

static void fill(struct allocation *a, bool tagged, u32 tag)
{
    u32 i;
    for (i = 0; i < a->bytes / 4; ++i)
        writel(tagged ? pattern(i, tag) : SENTINEL, (u8 __iomem *)a->cpu + 4 * i);
    wmb();
    (void)readl((u8 __iomem *)a->cpu + a->bytes - 4);
}

static u32 check(struct allocation *a, u32 tagged_bytes, u32 tag, const char *label)
{
    u32 i, bad = 0, first = U32_MAX, actual = 0, expected = 0;
    mb();
    for (i = 0; i < a->bytes / 4; ++i) {
        u32 value = readl((u8 __iomem *)a->cpu + 4 * i);
        u32 want = i < tagged_bytes / 4 ? pattern(i, tag) : SENTINEL;
        if (value != want) {
            if (!bad) { first = i; actual = value; expected = want; }
            ++bad;
        }
    }
    pr_info("cmp_ce132 nonce=%lu check label=%s words=%u bad=%u first=%u actual=%u expected=%u\n",
            nonce, label, a->bytes / 4, bad, first, actual, expected);
    return bad;
}

static NV_STATUS allocate(struct allocation *a, unsigned int slot, u32 bytes, bool sys)
{
    NV_STATUS status;
    a->slot = slot; a->bytes = bytes;
    a->info.gpuPhysOffset = U64_MAX;
    a->info.pageSize = sys ? SZ_4K : SZ_64K;
    a->info.alignment = SZ_64K;
    a->info.bContiguousPhysAlloc = !sys;
    status = sys ? nvUvmInterfaceMemoryAllocSys(ctx.space[slot], bytes, &a->va, &a->info) :
                   nvUvmInterfaceMemoryAllocFB(ctx.space[slot], bytes, &a->va, &a->info);
    pr_info("cmp_ce132 nonce=%lu call=allocate slot=%u bytes=%u sys=%u rc=%u\n", nonce, slot, bytes, sys, status);
    if (status != NV_OK)
        return status;
    a->allocated = true;
    if (!a->va || !a->info.hPhysHandle ||
        (!sys && (!IS_ALIGNED(a->info.gpuPhysOffset, SZ_64K) ||
                  a->info.gpuPhysOffset > (40ULL << 30) - bytes)))
        return NV_ERR_INVALID_ARGUMENT;
    status = nvUvmInterfaceMemoryCpuMap(ctx.space[slot], a->va, bytes, &a->cpu, a->info.pageSize);
    pr_info("cmp_ce132 nonce=%lu call=cpu_map slot=%u bytes=%u rc=%u\n", nonce, slot, bytes, status);
    return status != NV_OK ? status : a->cpu ? NV_OK : NV_ERR_INVALID_ARGUMENT;
}

static u32 method(u32 subchannel, u32 address, u32 count)
{
    return F(C46F, DMA, SEC_OP, INC_METHOD) | V(C46F, DMA, INCR_ADDRESS, address >> 2) |
           V(C46F, DMA, INCR_SUBCHANNEL, subchannel) | V(C46F, DMA, INCR_COUNT, count);
}

static int copy(u64 source, bool sys, u32 bytes, u32 payload, bool initialize)
{
    UvmGpuChannelInfo *c = &ctx.channel_info;
    u32 commands[40], n = 0, i, next, token, semaphore, error;
    u64 entry, end;
    unsigned long deadline;
    const u32 sub = NVA06F_SUBCHANNEL_COPY_ENGINE;
    const u32 flush = F(C6B5, LAUNCH_DMA, FLUSH_ENABLE, TRUE) | F(C6B5, LAUNCH_DMA, FLUSH_TYPE, SYS);
    void __iomem *sem = (u8 __iomem *)ctx.push.cpu + SEM_OFFSET;

    if (ctx.in_flight || !payload || !bytes || bytes > SZ_1M ||
        source > (1ULL << 49) - bytes || ctx.dest.va > (1ULL << 49) - bytes ||
        ctx.push.va >= (1ULL << 40) - SZ_64K || !IS_ALIGNED(ctx.push.va, 4) ||
        readl((void __iomem *)c->gpPut) != ctx.put ||
        readl((void __iomem *)c->gpGet) != ctx.put)
        return -EINVAL;
    if (initialize) {
        commands[n++] = method(0, NVC46F_SET_OBJECT, 1);
        commands[n++] = AMPERE_DMA_COPY_A;
    }
    commands[n++] = method(sub, NVC6B5_SET_SRC_PHYS_MODE, 1);
    commands[n++] = sys ? F(C6B5, SET_SRC_PHYS_MODE, TARGET, COHERENT_SYSMEM) :
                         F(C6B5, SET_SRC_PHYS_MODE, TARGET, LOCAL_FB);
    commands[n++] = method(sub, NVC6B5_OFFSET_IN_UPPER, 4);
    commands[n++] = upper_32_bits(source);
    commands[n++] = lower_32_bits(source);
    commands[n++] = upper_32_bits(ctx.dest.va);
    commands[n++] = lower_32_bits(ctx.dest.va);
    commands[n++] = method(sub, NVC6B5_LINE_LENGTH_IN, 1);
    commands[n++] = bytes;
    commands[n++] = method(sub, NVC6B5_LAUNCH_DMA, 1);
    commands[n++] = F(C6B5, LAUNCH_DMA, SRC_TYPE, PHYSICAL) | F(C6B5, LAUNCH_DMA, DST_TYPE, VIRTUAL) |
                    F(C6B5, LAUNCH_DMA, SRC_MEMORY_LAYOUT, PITCH) | F(C6B5, LAUNCH_DMA, DST_MEMORY_LAYOUT, PITCH) |
                    F(C6B5, LAUNCH_DMA, MULTI_LINE_ENABLE, FALSE) | F(C6B5, LAUNCH_DMA, REMAP_ENABLE, FALSE) |
                    F(C6B5, LAUNCH_DMA, DATA_TRANSFER_TYPE, NON_PIPELINED) | flush;
    commands[n++] = method(sub, NVC6B5_SET_SEMAPHORE_A, 3);
    commands[n++] = V(C6B5, SET_SEMAPHORE_A, UPPER, upper_32_bits(ctx.push.va + SEM_OFFSET));
    commands[n++] = V(C6B5, SET_SEMAPHORE_B, LOWER, lower_32_bits(ctx.push.va + SEM_OFFSET));
    commands[n++] = payload;
    commands[n++] = method(sub, NVC6B5_LAUNCH_DMA, 1);
    commands[n++] = F(C6B5, LAUNCH_DMA, DATA_TRANSFER_TYPE, NONE) |
                    F(C6B5, LAUNCH_DMA, SEMAPHORE_TYPE, RELEASE_ONE_WORD_SEMAPHORE) | flush;
    if (WARN_ON(n > ARRAY_SIZE(commands) || n * 4 >= SEM_OFFSET))
        return -E2BIG;
    writel(~payload, sem);
    for (i = 0; i < n; ++i)
        writel(commands[i], (u8 __iomem *)ctx.push.cpu + 4 * i);
    entry = V(C46F, GP_ENTRY0, GET, lower_32_bits(ctx.push.va) >> 2);
    entry |= (u64)(V(C46F, GP_ENTRY1, GET_HI, upper_32_bits(ctx.push.va)) |
                   V(C46F, GP_ENTRY1, LENGTH, n) | F(C46F, GP_ENTRY1, SYNC, PROCEED)) << 32;
    WRITE_ONCE(c->gpFifoEntries[ctx.put], entry);
    wmb();
    if (c->dummyBar1Mapping)
        (void)readl((void __iomem *)c->dummyBar1Mapping);
    next = (ctx.put + 1) % c->numGpFifoEntries;
    ctx.in_flight = true;
    writel(next, (void __iomem *)c->gpPut);
    wmb();
    token = c->pWorkSubmissionToken ? READ_ONCE(*c->pWorkSubmissionToken) : c->workSubmissionToken;
    writel(token, (void __iomem *)c->workSubmissionOffset);
    ctx.put = next;
    end = jiffies;
    deadline = jiffies + msecs_to_jiffies(3000);
    do {
        semaphore = readl(sem);
        error = READ_ONCE(c->errorNotifier->status);
        if (semaphore == payload) {
            // The release is the final command and uses a SYS flush.
            ctx.in_flight = false;
            break;
        }
        if (error)
            break;
        usleep_range(500, 1000);
    } while (time_before(jiffies, deadline));
    mb();
    pr_info("cmp_ce132 nonce=%lu completion sys=%u bytes=%u done=%u error=%u payload=%u observed=%u microseconds=%llu get=%u put=%u commands=%u\n",
            nonce, sys, bytes, !ctx.in_flight, error, payload, semaphore,
            (u64)jiffies_to_usecs(jiffies - end), readl((void __iomem *)c->gpGet), ctx.put, n);
    return ctx.in_flight ? -ETIMEDOUT : error ? -EIO : 0;
}

static NV_STATUS lease(bool release, u64 *dma)
{
    UvmGpuExternalPhysAddrInfo info = {0};
    NvU64 record[10];
    NV_STATUS status;
    unsigned int i;
    bool protocol;
    for (i = 0; i < ARRAY_SIZE(record); ++i)
        record[i] = (~(u64)nonce) ^ ((u64)i << 32);
    info.mappingType = release ? RELEASE_MAPPING : ACQUIRE_MAPPING;
    info.mappingPageSize = SZ_64K;
    info.physAddrBufferSize = sizeof(record);
    info.physAddrBuffer = record;
    // Conservatively retain backing if a successful acquisition cannot be decoded.
    if (!release)
        ctx.lease = true;
    status = nvUvmInterfaceGetExternalAllocPhysAddrs(ctx.space[1], ctx.owner.info.hPhysHandle, 0, SZ_1M, &info);
    protocol = info.numWrittenPhysAddrs == ARRAY_SIZE(record) && record[0] == PROTOCOL_MAGIC && record[1] == SZ_1M;
    if (protocol)
        ctx.lease = record[9] != 0;
    pr_info("cmp_ce132 nonce=%lu lease release=%u rc=%u protocol=%u acquire=%llu cleanup=%llu retained=%u flags=%llu offset=%llu length=%llu dma=%llu\n",
            nonce, release, status, protocol, record[2], record[8], ctx.lease, record[7], record[3], record[4], record[6]);
    if (!protocol || status != NV_OK || record[2] || record[8])
        return status != NV_OK ? status : NV_ERR_INVALID_STATE;
    if (!release) {
        if (record[7] != 23 || record[9] != 1 || record[4] != SZ_1M ||
            record[3] > SZ_64M - SZ_1M || !IS_ALIGNED(record[3], SZ_64K) ||
            !IS_ALIGNED(record[6], SZ_64K) || record[6] > (1ULL << 49) - SZ_1M)
            return NV_ERR_INVALID_ARGUMENT;
        *dma = record[6];
    }
    return NV_OK;
}

static int __init cmp_ce132_init(void)
{
    UvmPlatformInfo platform = {0};
    UvmGpuClientInfo client = {0};
    UvmGpuAddressSpaceInfo space_info = {0};
    UvmGpuPlatformInfo gpu_platform = {0};
    UvmGpuTsgAllocParams tsg_params = {0};
    UvmGpuChannelAllocParams channel_params = {0};
    UvmGpuCopyEnginesCaps *caps;
    UvmGpuInfo *gpu_info;
    uuid_t parsed;
    const char *ids[2] = {owner_uuid, accessor_uuid};
    NV_STATUS status = NV_OK, session_status = NV_OK;
    u64 dma = 0;
    u32 i, bad = 0, local_done = 0, peer_attempted = 0, peer_done = 0;
    int rc = -EINVAL, engine = -1;

    if (!nonce || nonce > U32_MAX || (owner_gib != 40 && owner_gib != 64))
        return -EINVAL;
    for (i = 0; i < 2; ++i) {
        if (uuid_parse(ids[i], &parsed))
            return -EINVAL;
        memcpy(ctx.uuid[i].uuid, parsed.b, sizeof(parsed.b));
    }
    if (!memcmp(ctx.uuid[0].uuid, ctx.uuid[1].uuid, sizeof(parsed.b)))
        return -EINVAL;
    gpu_info = kzalloc(sizeof(*gpu_info), GFP_KERNEL);
    caps = kzalloc(sizeof(*caps), GFP_KERNEL);
    if (!gpu_info || !caps) { kfree(gpu_info); kfree(caps); return -ENOMEM; }
    pr_info("cmp_ce132 nonce=%lu begin owner_gib=%u peer_bytes=%u\n", nonce, owner_gib, SZ_1M);
    for (i = 0; i < 2; ++i) {
        u16 device = (i == 0) == (owner_gib == 40) ? 0x2082 : 0x20c2;
        status = nvUvmInterfaceRegisterGpu(&ctx.uuid[i], &gpu_platform);
        pr_info("cmp_ce132 nonce=%lu call=register slot=%u rc=%u\n", nonce, i, status);
        if (status != NV_OK) goto done;
        ctx.registered[i] = true;
        if (!gpu_platform.pci_dev || gpu_platform.pci_dev->vendor != 0x10de || gpu_platform.pci_dev->device != device) goto done;
    }
    status = nvUvmInterfaceSessionCreate(&ctx.session, &platform);
    pr_info("cmp_ce132 nonce=%lu call=session rc=%u\n", nonce, status);
    if (status != NV_OK) goto done;
    for (i = 0; i < 2; ++i) {
        memset(gpu_info, 0, sizeof(*gpu_info));
        status = nvUvmInterfaceGetGpuInfo(&ctx.uuid[i], &client, gpu_info);
        pr_info("cmp_ce132 nonce=%lu call=gpu_info slot=%u rc=%u host=%u ce=%u virt=%u\n",
                nonce, i, status, gpu_info->hostClass, gpu_info->ceClass, gpu_info->virtMode);
        if (status != NV_OK || gpu_info->smcEnabled || gpu_info->isSimulated ||
            gpu_info->hostClass != AMPERE_CHANNEL_GPFIFO_A || gpu_info->ceClass != AMPERE_DMA_COPY_A ||
            // Native enum NONE includes ordinary PCI passthrough (not SR-IOV).
            gpu_info->virtMode != UVM_VIRT_MODE_NONE) goto done;
        status = nvUvmInterfaceDeviceCreate(ctx.session, gpu_info, &ctx.uuid[i], &ctx.device[i], NV_FALSE);
        if (status != NV_OK) goto done;
        status = nvUvmInterfaceAddressSpaceCreate(ctx.device[i], 0, 0, NV_FALSE, &ctx.space[i], &space_info);
        if (status != NV_OK) goto done;
    }
    status = allocate(&ctx.owner, 0, SZ_1M, false); if (status != NV_OK) goto done;
    status = allocate(&ctx.local, 1, SZ_64K, false); if (status != NV_OK) goto done;
    status = allocate(&ctx.dest, 1, SZ_1M, false); if (status != NV_OK) goto done;
    status = allocate(&ctx.push, 1, SZ_64K, true); if (status != NV_OK) goto done;
    fill(&ctx.owner, true, 0x4f574e52U);
    fill(&ctx.local, true, 0x4c4f434cU);
    fill(&ctx.dest, false, 0);
    bad += check(&ctx.owner, SZ_1M, 0x4f574e52U, "owner_before");
    bad += check(&ctx.local, SZ_64K, 0x4c4f434cU, "local_before");
    bad += check(&ctx.dest, 0, 0, "sentinel_before");
    if (bad) goto done;
    status = nvUvmInterfaceQueryCopyEnginesCaps(ctx.device[1], caps);
    pr_info("cmp_ce132 nonce=%lu call=ce_caps rc=%u\n", nonce, status);
    if (status != NV_OK) goto done;
    for (i = 0; i < UVM_COPY_ENGINE_COUNT_MAX; ++i) {
        UvmGpuCopyEngineCaps *ce = &caps->copyEngineCaps[i];
        if (!ce->supported) continue;
        pr_info("cmp_ce132 nonce=%lu engine index=%u grce=%u sysmem=%u read=%u p2p=%u shared=%u mask=%u\n",
                nonce, i, ce->grce, ce->sysmem, ce->sysmemRead, ce->p2p, ce->shared, ce->cePceMask);
        // sysmemRead is only an enhanced-performance hint, not permission.
        if (!ce->grce && ce->sysmem && (engine < 0 ||
            (ce->sysmemRead && !caps->copyEngineCaps[engine].sysmemRead) ||
            (ce->p2p && !caps->copyEngineCaps[engine].p2p))) engine = i;
    }
    if (engine < 0) goto done;
    tsg_params.engineType = UVM_GPU_CHANNEL_ENGINE_TYPE_CE;
    tsg_params.engineIndex = engine;
    status = nvUvmInterfaceTsgAllocate(ctx.space[1], &tsg_params, &ctx.tsg);
    pr_info("cmp_ce132 nonce=%lu call=tsg engine=%d rc=%u\n", nonce, engine, status);
    if (status != NV_OK) goto done;
    channel_params.numGpFifoEntries = 1024;
    channel_params.gpFifoLoc = channel_params.gpPutLoc = UVM_BUFFER_LOCATION_SYS;
    status = nvUvmInterfaceChannelAllocate(ctx.tsg, &channel_params, &ctx.channel, &ctx.channel_info);
    pr_info("cmp_ce132 nonce=%lu call=channel rc=%u class=%u entries=%u\n",
            nonce, status, ctx.channel_info.channelClassNum, ctx.channel_info.numGpFifoEntries);
    if (status != NV_OK) goto done;
    if (!ctx.channel_info.gpGet || !ctx.channel_info.gpPut || !ctx.channel_info.gpFifoEntries ||
        !ctx.channel_info.workSubmissionOffset || !ctx.channel_info.errorNotifier ||
        ctx.channel_info.numGpFifoEntries != 1024 || ctx.channel_info.channelClassNum != AMPERE_CHANNEL_GPFIFO_A) goto done;
    ctx.put = readl((void __iomem *)ctx.channel_info.gpPut);
    if (ctx.put >= ctx.channel_info.numGpFifoEntries) goto done;
    rc = copy(ctx.local.info.gpuPhysOffset, false, SZ_64K, (u32)nonce, true);
    if (rc) goto done;
    bad += check(&ctx.dest, SZ_64K, 0x4c4f434cU, "local_destination");
    bad += check(&ctx.local, SZ_64K, 0x4c4f434cU, "local_after");
    if (bad) goto done;
    local_done = 1;
    fill(&ctx.dest, false, 0);
    status = lease(false, &dma);
    if (status != NV_OK) goto done;
    peer_attempted = 1;
    rc = copy(dma, true, SZ_1M, ((u32)nonce ^ 0x6ac39157U) ?: 1U, false);
    if (rc) goto done;
    peer_done = 1;
    bad += check(&ctx.dest, SZ_1M, 0x4f574e52U, "peer_destination");
    bad += check(&ctx.owner, SZ_1M, 0x4f574e52U, "owner_after");
done:
    if (ctx.in_flight) retained = true;
    if (!retained) {
        if (ctx.channel) nvUvmInterfaceChannelDestroy(ctx.channel);
        if (ctx.tsg) nvUvmInterfaceTsgDestroy(ctx.tsg);
        if (ctx.lease) {
            NV_STATUS cleanup = lease(true, &dma);
            if (cleanup != NV_OK || ctx.lease) retained = true;
        }
    }
    if (!retained) {
        struct allocation *allocations[] = {&ctx.push, &ctx.dest, &ctx.local, &ctx.owner};
        for (i = 0; i < ARRAY_SIZE(allocations); ++i) {
            struct allocation *a = allocations[i];
            if (a->cpu) nvUvmInterfaceMemoryCpuUnMap(ctx.space[a->slot], a->cpu);
            if (a->allocated) nvUvmInterfaceMemoryFree(ctx.space[a->slot], a->va);
        }
        for (i = 2; i > 0; --i) {
            if (ctx.space[i - 1]) nvUvmInterfaceAddressSpaceDestroy(ctx.space[i - 1]);
            if (ctx.device[i - 1]) nvUvmInterfaceDeviceDestroy(ctx.device[i - 1]);
        }
        if (ctx.session) session_status = nvUvmInterfaceSessionDestroy(ctx.session);
        for (i = 2; i > 0; --i)
            if (ctx.registered[i - 1]) nvUvmInterfaceUnregisterGpu(&ctx.uuid[i - 1]);
    }
    else {
        // Block rmmod. Parent must recover the test VM, never free live backing.
        __module_get(THIS_MODULE);
    }
    kfree(gpu_info); kfree(caps);
    pr_info("cmp_ce132 nonce=%lu finish local_done=%u peer_attempted=%u peer_done=%u bad=%u rc=%d rm_rc=%u retained=%u session_destroy_rc=%u\n",
            nonce, local_done, peer_attempted, peer_done, bad, rc, status, retained, session_status);
    return 0;
}
static void __exit cmp_ce132_exit(void) { WARN_ON(retained); }
module_init(cmp_ce132_init);
module_exit(cmp_ce132_exit);
MODULE_LICENSE("MIT");
MODULE_DESCRIPTION("CMP bounded explicit copy-engine BAR1-window data experiment");
