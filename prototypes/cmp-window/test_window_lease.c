/* SPDX-License-Identifier: MIT
 * CPU-only fault injection. Independent resource flags/events are the oracle;
 * this neither maps a BAR nor simulates a successful hardware transfer.
 */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef uint64_t NvU64;
typedef uint32_t NvU32;
typedef int NvBool;
typedef int NV_STATUS;
#define NV_TRUE 1
#define NV_FALSE 0
#define NV_OK 0
#define NV_ERR_INVALID_STATE 1
#define NV_ERR_INVALID_LIMIT 2
#define NV_ERR_INSUFFICIENT_RESOURCES 3
#define NV_U64_MAX UINT64_MAX
#include "cmp_window_lease.h"

typedef struct
{
    int fail;
    int ownerLive, descriptorLive, dmaLive;
    int maps;
    int events[24];
    int count;
    NvU64 dma, offset, length, physical;
} Backend;
enum { FAIL_OWNER=11, FAIL_DESC=12, FAIL_DMA=13,
       FAIL_DMA_PARTIAL=14, FAIL_DMA_UNMAP=15, FAIL_OWNER_UNMAP=16 };
static void event(Backend *b, int code)
{
    assert(b->count < (int)(sizeof(b->events)/sizeof(b->events[0])));
    b->events[b->count++] = code;
}
static NV_STATUS mapOwner(CmpWindowLease *l)
{
    Backend *b = l->backend;
    event(b, 1); b->maps++;
    if (b->fail == FAIL_OWNER) return b->fail;
    assert(!b->ownerLive);
    b->ownerLive = 1; l->ownerMapped = 1;
    l->apertureOffset = b->offset; l->apertureLength = b->length;
    l->cpuPhysicalBase = b->physical;
    return NV_OK;
}
static NV_STATUS mapDma(CmpWindowLease *l)
{
    Backend *b = l->backend;
    event(b, 2);
    assert(b->ownerLive);
    if (b->fail == FAIL_DESC) return b->fail;
    assert(!b->descriptorLive); b->descriptorLive = 1; l->dmaDescriptor = 1;
    if (b->fail == FAIL_DMA) return b->fail;
    b->dmaLive = 1; l->dmaMapped = 1; l->dmaBase = b->dma;
    if (b->fail == FAIL_DMA_PARTIAL) return b->fail;
    return NV_OK;
}
static NV_STATUS unmapDma(CmpWindowLease *l)
{
    Backend *b = l->backend;
    event(b, 3);
    if (b->fail == FAIL_DMA_UNMAP) return b->fail;
    assert(b->ownerLive);
    b->dmaLive = 0; b->descriptorLive = 0;
    l->dmaMapped = 0; l->dmaDescriptor = 0;
    return NV_OK;
}
static NV_STATUS unmapOwner(CmpWindowLease *l)
{
    Backend *b = l->backend;
    event(b, 4);
    assert(!b->dmaLive && !b->descriptorLive);
    if (b->fail == FAIL_OWNER_UNMAP) return b->fail;
    assert(b->ownerLive); b->ownerLive = 0; l->ownerMapped = 0;
    return NV_OK;
}
static const CmpWindowOps ops = {mapOwner,mapDma,unmapDma,unmapOwner};
static CmpWindowBudget budget(void)
{
    CmpWindowBudget b = {64ULL<<20, CMP_WINDOW_RESERVE_BYTES, 0, 0};
    return b;
}
static void init(CmpWindowLease *l, Backend *b)
{
    memset(l, 0, sizeof(*l)); memset(b, 0, sizeof(*b));
    l->size = 2ULL<<20; l->backend = b;
    b->length = l->size; b->physical = 0x100000000ULL;
}
static void empty(CmpWindowLease *l, CmpWindowBudget *q, Backend *b)
{
    assert(!b->ownerLive && !b->descriptorLive && !b->dmaLive);
    assert(!l->charged && !l->ownerMapped && !l->dmaMapped && !l->quarantined);
    assert(!q->charged && !q->quarantined);
}
int main(void)
{
    CmpWindowLease l, other;
    CmpWindowBudget q;
    Backend b, b2;
    NvU64 address;
    unsigned cases = 0;
    int failure;

    q=budget(); init(&l,&b); b.dma=0;
    assert(cmpWindowAcquire(&l,&q,&ops)==NV_OK);
    assert(cmpWindowAddress(&l,l.size-1,1,&address)==NV_OK && address==l.size-1);
    assert(cmpWindowAddress(&l,l.size-1,2,&address)==NV_ERR_INVALID_LIMIT);
    assert(cmpWindowAddress(&l,NV_U64_MAX,2,&address)==NV_ERR_INVALID_LIMIT);
    assert(cmpWindowAddress(&l,0,0,&address)==NV_ERR_INVALID_LIMIT);
    assert(cmpWindowAcquire(&l,&q,&ops)==NV_ERR_INVALID_STATE && b.maps==1);
    l.published=1;
    assert(cmpWindowRelease(&l,&q,&ops,0)==NV_ERR_INVALID_STATE);
    assert(b.ownerLive && b.dmaLive && q.charged==l.size && b.count==2);
    assert(cmpWindowRelease(&l,&q,&ops,1)==NV_OK);
    assert(b.events[2]==3 && b.events[3]==4); empty(&l,&q,&b); cases++;

    for (failure=FAIL_OWNER; failure<=FAIL_DMA_PARTIAL; failure++)
    {
        q=budget(); init(&l,&b); b.fail=failure;
        assert(cmpWindowAcquire(&l,&q,&ops)==failure);
        assert(l.cleanupStatus==NV_OK); empty(&l,&q,&b); cases++;
    }
    for (failure=FAIL_DMA_UNMAP; failure<=FAIL_OWNER_UNMAP; failure++)
    {
        q=budget(); init(&l,&b); assert(cmpWindowAcquire(&l,&q,&ops)==NV_OK);
        l.published=1; b.fail=failure;
        assert(cmpWindowRelease(&l,&q,&ops,1)==failure);
        assert(l.quarantined && q.quarantined==1 && q.charged==l.size && b.ownerLive);
        if (failure==FAIL_DMA_UNMAP) assert(b.dmaLive && b.events[b.count-1]==3);
        assert(cmpWindowAddress(&l,0,1,&address)==NV_ERR_INVALID_LIMIT);
        init(&other,&b2);
        assert(cmpWindowAcquire(&other,&q,&ops)==NV_ERR_INSUFFICIENT_RESOURCES);
        assert(b2.maps==0);
        assert(cmpWindowRelease(&l,&q,&ops,1)==failure && q.quarantined==1);
        b.fail=0; assert(cmpWindowRelease(&l,&q,&ops,1)==NV_OK);
        empty(&l,&q,&b); cases++;
    }

    /* A failed create whose rollback also fails retains a charged quarantine. */
    q=budget(); init(&l,&b); b.length=l.size+1; b.fail=FAIL_OWNER_UNMAP;
    assert(cmpWindowAcquire(&l,&q,&ops)==NV_ERR_INVALID_LIMIT);
    assert(l.cleanupStatus==FAIL_OWNER_UNMAP && l.quarantined && b.ownerLive);
    assert(q.charged==l.size && q.quarantined==1);
    b.fail=0; assert(cmpWindowRelease(&l,&q,&ops,1)==NV_OK); empty(&l,&q,&b); cases++;

    /* Two sessions consume the same owner quota; reserve cannot be borrowed. */
    q=budget(); init(&l,&b); init(&other,&b2);
    q.charged=(26ULL<<20);
    assert(cmpWindowAcquire(&l,&q,&ops)==NV_OK && q.charged==(28ULL<<20));
    assert(cmpWindowAcquire(&other,&q,&ops)==NV_ERR_INSUFFICIENT_RESOURCES && b2.maps==0);
    assert(cmpWindowRelease(&l,&q,&ops,1)==NV_OK && q.charged==(26ULL<<20)); cases++;

    q=budget(); q.reserve=q.capacity+1; assert(!cmpWindowBudgetFits(&q,1));
    q=budget(); q.charged=NV_U64_MAX; assert(!cmpWindowBudgetFits(&q,1));
    q=budget(); q.capacity=NV_U64_MAX; q.charged=NV_U64_MAX-q.reserve;
    assert(!cmpWindowBudgetFits(&q,1));
    q=budget(); assert(!cmpWindowBudgetFits(&q,0));
    assert(!cmpWindowBudgetFits(&q,CMP_WINDOW_MAX_BYTES+1)); cases++;

    /* Source/window/DMA address domains, size and overflow are independent. */
    for (failure=0; failure<5; failure++)
    {
        q=budget(); init(&l,&b);
        if(failure==0) b.offset=NV_U64_MAX;
        if(failure==1) b.offset=q.capacity-l.size+1;
        if(failure==2) b.physical=NV_U64_MAX-l.size+2;
        if(failure==3) b.length=l.size-1;
        if(failure==4) b.dma=NV_U64_MAX-l.size+2;
        assert(cmpWindowAcquire(&l,&q,&ops)==NV_ERR_INVALID_LIMIT);
        empty(&l,&q,&b); cases++;
    }
    /* Exhaust boundary values without allocating physical memory. */
    for (unsigned i=0; i<10000; i++)
    {
        NvU64 n=(((NvU64)i*0x9e3779b97f4a7c15ULL) ^ ((NvU64)i<<31));
        q=budget(); init(&l,&b); b.dma=n;
        NV_STATUS status=cmpWindowAcquire(&l,&q,&ops);
        if(status==NV_OK)
        {
            NvU64 offset=i%(2U<<20), bytes=1+(i%4096);
            NV_STATUS expected=bytes<=l.size-offset ? NV_OK : NV_ERR_INVALID_LIMIT;
            assert(cmpWindowAddress(&l,offset,bytes,&address)==expected);
            if(expected==NV_OK) assert(address==n+offset);
            assert(cmpWindowRelease(&l,&q,&ops,1)==NV_OK);
        }
        else assert(status==NV_ERR_INVALID_LIMIT);
        empty(&l,&q,&b);
    }
    printf("{\"scenario_groups\":%u,\"address_boundary_cases\":10000,"
           "\"result\":\"PASS_CPU_RESOURCE_CONTRACT_ONLY\",\"GPU_calls\":0}\n",cases);
    return 0;
}
