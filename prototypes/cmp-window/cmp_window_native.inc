/* SPDX-License-Identifier: MIT
 * Compile-only adapter for nv_gpu_ops.c, pinned 615.71.09 plus retained G.
 * Not called by the driver yet. Pair admission, PTE publication, reference
 * ownership and fatal client teardown must be integrated before installation.
 */
#include "cmp_window_lease.h"

typedef struct CmpNativeWindow
{
    CmpWindowLease lease;
    OBJGPU *owner;
    OBJGPU *accessor;
    MEMORY_DESCRIPTOR *allocation;
    MEMORY_DESCRIPTOR *window;
    MemoryArea area;
    MemoryRange range;
    NvHandle client;
    NvHandle accessorSubdevice;
    NvHandle duplicate;
    NvU32 iovaspaceId;
    struct CmpNativeWindow *next;
} CmpNativeWindow;

/* The all-GPU lock protects both the owner-global budget and all sessions. */
static CmpWindowBudget cmpWindowBudgets[NV_MAX_DEVICES];
static OBJGPU *cmpWindowBudgetOwners[NV_MAX_DEVICES];
static CmpNativeWindow *cmpWindowList;

static NvBool cmpWindowIsPair(OBJGPU *accessor, OBJGPU *owner)
{
    NvU32 a, b;
    if (accessor == NULL || owner == NULL || accessor == owner)
        return NV_FALSE;
    a = accessor->idInfo.PCIDeviceID >> 16;
    b = owner->idInfo.PCIDeviceID >> 16;
    return (a == 0x2082 && b == 0x20c2) || (a == 0x20c2 && b == 0x2082);
}

static NV_STATUS cmpWindowMapOwner(CmpWindowLease *lease)
{
    CmpNativeWindow *map = lease->backend;
    NV_STATUS status;
    NvU64 physicalBase;

    map->area.numRanges = 1;
    map->area.pRanges = &map->range;
    status = kbusMapFbAperture_HAL(map->owner, GPU_GET_KERNEL_BUS(map->owner),
                                  map->allocation, mrangeMake(0, lease->size),
                                  &map->area,
                                  BUS_MAP_FB_FLAGS_MAP_UNICAST |
                                  BUS_MAP_FB_FLAGS_UNMANAGED_MEM_AREA, NULL);
    if (status != NV_OK)
        return status;
    lease->ownerMapped = NV_TRUE;
    lease->apertureOffset = map->range.start;
    lease->apertureLength = map->range.size;
    if (map->area.numRanges != 1)
        return NV_ERR_INVALID_STATE;

    physicalBase = gpumgrGetGpuPhysFbAddr(map->owner);
    if (lease->apertureOffset > NV_U64_MAX - physicalBase)
        return NV_ERR_INVALID_LIMIT;
    lease->cpuPhysicalBase = physicalBase + lease->apertureOffset;
    return NV_OK;
}

static NV_STATUS cmpWindowMapDma(CmpWindowLease *lease)
{
    CmpNativeWindow *map = lease->backend;
    NV_STATUS status;

    status = memdescCreate(&map->window, map->owner, lease->size, 0,
                           NV_MEMORY_CONTIGUOUS, ADDR_SYSMEM,
                           NV_MEMORY_UNCACHED, MEMDESC_FLAGS_NONE);
    if (status != NV_OK)
        return status;
    lease->dmaDescriptor = NV_TRUE;
    memdescDescribe(map->window, ADDR_SYSMEM, lease->cpuPhysicalBase, lease->size);
    status = memdescMapIommu(map->window, map->iovaspaceId);
    if (status != NV_OK)
        return status;
    lease->dmaMapped = NV_TRUE;
    memdescGetPtePhysAddrsForGpu(map->window, map->accessor, AT_GPU, 0, 0, 1,
                                &lease->dmaBase);
    return NV_OK;
}

static NV_STATUS cmpWindowUnmapDma(CmpWindowLease *lease)
{
    CmpNativeWindow *map = lease->backend;
    if (lease->dmaMapped)
    {
        memdescUnmapIommu(map->window, map->iovaspaceId);
        lease->dmaMapped = NV_FALSE;
    }
    if (lease->dmaDescriptor)
    {
        memdescDestroy(map->window);
        map->window = NULL;
        lease->dmaDescriptor = NV_FALSE;
    }
    /* The existing DMA unmap API is void, not independent hardware ACK. */
    return NV_OK;
}

static NV_STATUS cmpWindowUnmapOwner(CmpWindowLease *lease)
{
    CmpNativeWindow *map = lease->backend;
    NV_STATUS status;
    status = kbusUnmapFbAperture_HAL(map->owner, GPU_GET_KERNEL_BUS(map->owner),
                                    map->allocation, map->area,
                                    BUS_MAP_FB_FLAGS_MAP_UNICAST |
                                    BUS_MAP_FB_FLAGS_UNMANAGED_MEM_AREA);
    if (status == NV_OK)
        lease->ownerMapped = NV_FALSE;
    return status;
}

static const CmpWindowOps cmpNativeWindowOps =
{
    cmpWindowMapOwner, cmpWindowMapDma,
    cmpWindowUnmapDma, cmpWindowUnmapOwner
};

/* Call only after the RM duplicate has been validated. Never infer support. */
static NV_STATUS __attribute__((used, unused))
cmpWindowNativeAcquire(OBJGPU *accessor, OBJGPU *owner,
                        MEMORY_DESCRIPTOR *allocation, NvHandle client,
                        NvHandle accessorSubdevice, NvHandle duplicate,
                        CmpNativeWindow **result)
{
    CmpNativeWindow *map;
    CmpWindowBudget *budget;
    NvU32 index;
    NV_STATUS status;

    *result = NULL;
    if (!cmpWindowIsPair(accessor, owner) || allocation == NULL ||
        allocation->pGpu != owner || memdescGetAddressSpace(allocation) != ADDR_FBMEM ||
        IS_MIG_IN_USE(owner) || IS_MIG_IN_USE(accessor) ||
        IsSLIEnabled(owner) || IsSLIEnabled(accessor))
        return NV_ERR_NOT_SUPPORTED;
    if (!rmGpuLockIsOwner() ||
        !rmDeviceGpuLockIsOwner(gpuGetInstance(owner)) ||
        !rmDeviceGpuLockIsOwner(gpuGetInstance(accessor)))
        return NV_ERR_INVALID_LOCK_STATE;
    index = gpuGetInstance(owner);
    if (index >= NV_MAX_DEVICES)
        return NV_ERR_INVALID_ARGUMENT;
    budget = &cmpWindowBudgets[index];
    if (cmpWindowBudgetOwners[index] != owner &&
        (budget->charged != 0 || budget->quarantined != 0))
        return NV_ERR_INVALID_STATE;

    for (map = cmpWindowList; map != NULL; map = map->next)
    {
        if (map->client == client && map->accessorSubdevice == accessorSubdevice &&
            map->duplicate == duplicate)
        {
            if (map->allocation != allocation || map->owner != owner ||
                map->accessor != accessor || map->lease.quarantined)
                return NV_ERR_INVALID_STATE;
            *result = map;
            return NV_OK;
        }
    }
    cmpWindowBudgetOwners[index] = owner;
    budget->capacity = kbusGetPciBarSize(GPU_GET_KERNEL_BUS(owner), 1);
    budget->reserve = CMP_WINDOW_RESERVE_BYTES;
    if (!cmpWindowBudgetFits(budget, memdescGetSize(allocation)))
        return NV_ERR_INSUFFICIENT_RESOURCES;

    map = portMemAllocNonPaged(sizeof(*map));
    if (map == NULL)
        return NV_ERR_NO_MEMORY;
    portMemSet(map, 0, sizeof(*map));
    map->owner = owner;
    map->accessor = accessor;
    map->allocation = allocation;
    map->client = client;
    map->accessorSubdevice = accessorSubdevice;
    map->duplicate = duplicate;
    map->iovaspaceId = accessor->busInfo.iovaspaceId;
    map->lease.size = memdescGetSize(allocation);
    map->lease.backend = map;
    status = cmpWindowAcquire(&map->lease, budget, &cmpNativeWindowOps);
    if (status == NV_OK || map->lease.quarantined)
    {
        map->next = cmpWindowList;
        cmpWindowList = map;
        *result = map; /* Failure + non-NULL means quarantine, not success. */
    }
    else
    {
        portMemFree(map);
    }
    return status;
}

/* Caller must preserve the duplicate/owner ref on every release failure. */
static NV_STATUS __attribute__((used, unused))
cmpWindowNativeRelease(CmpNativeWindow *map, NvBool readersRetired)
{
    CmpNativeWindow **link;
    NV_STATUS status;
    if (!rmGpuLockIsOwner() ||
        !rmDeviceGpuLockIsOwner(gpuGetInstance(map->owner)) ||
        !rmDeviceGpuLockIsOwner(gpuGetInstance(map->accessor)))
        return NV_ERR_INVALID_LOCK_STATE;
    for (link = &cmpWindowList; *link != NULL; link = &(*link)->next)
        if (*link == map)
            break;
    if (*link == NULL)
        return NV_ERR_INVALID_ARGUMENT;
    status = cmpWindowRelease(&map->lease,
                              &cmpWindowBudgets[gpuGetInstance(map->owner)],
                              &cmpNativeWindowOps, readersRetired);
    if (status != NV_OK)
        return status;
    *link = map->next;
    portMemFree(map);
    return NV_OK;
}
