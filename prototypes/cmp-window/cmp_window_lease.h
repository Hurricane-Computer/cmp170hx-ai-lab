/* SPDX-License-Identifier: MIT
 * Bounded CMP external-window transaction. No hardware API is called here.
 * Caller serializes one owner's budget and retains the allocation reference.
 */
#ifndef CMP_WINDOW_LEASE_H
#define CMP_WINDOW_LEASE_H

#define CMP_WINDOW_MAX_BYTES (2ULL << 20)
#define CMP_WINDOW_RESERVE_BYTES (36ULL << 20)

typedef struct
{
    NvU64 capacity;
    NvU64 reserve;
    NvU64 charged;
    NvU32 quarantined;
} CmpWindowBudget;

typedef struct CmpWindowLease
{
    NvU64 size;
    NvU64 apertureOffset;
    NvU64 apertureLength;
    NvU64 cpuPhysicalBase;
    NvU64 dmaBase;
    NvBool charged;
    NvBool ownerMapped;
    NvBool dmaDescriptor;
    NvBool dmaMapped;
    NvBool published;
    NvBool quarantined;
    NV_STATUS cleanupStatus;
    void *backend;
} CmpWindowLease;

typedef struct
{
    NV_STATUS (*mapOwner)(CmpWindowLease *);
    NV_STATUS (*mapDma)(CmpWindowLease *);
    NV_STATUS (*unmapDma)(CmpWindowLease *);
    NV_STATUS (*unmapOwner)(CmpWindowLease *);
} CmpWindowOps;

static inline NvBool
cmpWindowBudgetFits(const CmpWindowBudget *budget, NvU64 size)
{
    return size != 0 && size <= CMP_WINDOW_MAX_BYTES &&
           budget->quarantined == 0 && budget->reserve <= budget->capacity &&
           budget->charged <= budget->capacity - budget->reserve &&
           size <= budget->capacity - budget->reserve - budget->charged;
}

static inline NV_STATUS
cmpWindowQuarantine(CmpWindowLease *lease, CmpWindowBudget *budget,
                    NV_STATUS status)
{
    if (!lease->quarantined)
    {
        lease->quarantined = NV_TRUE;
        budget->quarantined++;
    }
    lease->cleanupStatus = status;
    return status;
}

/* readersRetired is a caller proof, not a request to clear/invalidate PTEs. */
static inline NV_STATUS
cmpWindowRelease(CmpWindowLease *lease, CmpWindowBudget *budget,
                 const CmpWindowOps *ops, NvBool readersRetired)
{
    NV_STATUS status;

    if (lease->published && !readersRetired)
        return NV_ERR_INVALID_STATE;

    if (lease->dmaMapped || lease->dmaDescriptor)
    {
        status = ops->unmapDma(lease);
        if (status != NV_OK)
            return cmpWindowQuarantine(lease, budget, status);
        if (lease->dmaMapped || lease->dmaDescriptor)
            return cmpWindowQuarantine(lease, budget, NV_ERR_INVALID_STATE);
    }

    if (lease->ownerMapped)
    {
        status = ops->unmapOwner(lease);
        if (status != NV_OK)
            return cmpWindowQuarantine(lease, budget, status);
        if (lease->ownerMapped)
            return cmpWindowQuarantine(lease, budget, NV_ERR_INVALID_STATE);
    }

    if (lease->charged)
    {
        if (budget->charged < lease->size)
            return cmpWindowQuarantine(lease, budget, NV_ERR_INVALID_STATE);
        budget->charged -= lease->size;
        lease->charged = NV_FALSE;
    }
    if (lease->quarantined)
    {
        if (budget->quarantined == 0)
            return NV_ERR_INVALID_STATE;
        budget->quarantined--;
        lease->quarantined = NV_FALSE;
    }
    lease->published = NV_FALSE;
    lease->cleanupStatus = NV_OK;
    return NV_OK;
}

static inline NV_STATUS
cmpWindowAcquire(CmpWindowLease *lease, CmpWindowBudget *budget,
                 const CmpWindowOps *ops)
{
    NV_STATUS status;

    if (lease->charged || lease->ownerMapped || lease->dmaDescriptor ||
        lease->dmaMapped || lease->published || lease->quarantined)
        return NV_ERR_INVALID_STATE;
    if (!cmpWindowBudgetFits(budget, lease->size))
        return NV_ERR_INSUFFICIENT_RESOURCES;

    budget->charged += lease->size;
    lease->charged = NV_TRUE;
    status = ops->mapOwner(lease);
    if (status != NV_OK)
        goto rollback;
    /* This first adapter supports an exact single range, never discontiguous. */
    if (!lease->ownerMapped || lease->apertureLength != lease->size ||
        lease->apertureOffset > budget->capacity ||
        lease->size > budget->capacity - lease->apertureOffset ||
        lease->size - 1 > NV_U64_MAX - lease->cpuPhysicalBase)
    {
        status = NV_ERR_INVALID_LIMIT;
        goto rollback;
    }

    status = ops->mapDma(lease);
    if (status != NV_OK)
        goto rollback;
    /* IOVA zero is valid. Successful resource acquisition is the evidence. */
    if (!lease->dmaDescriptor || !lease->dmaMapped ||
        lease->size - 1 > NV_U64_MAX - lease->dmaBase)
    {
        status = NV_ERR_INVALID_LIMIT;
        goto rollback;
    }
    return NV_OK;

rollback:
    /* Preserve the primary failure and the independent cleanup failure. */
    lease->cleanupStatus = cmpWindowRelease(lease, budget, ops, NV_TRUE);
    return status;
}

static inline NV_STATUS
cmpWindowAddress(const CmpWindowLease *lease, NvU64 offset, NvU64 bytes,
                 NvU64 *address)
{
    if (!lease->ownerMapped || !lease->dmaMapped || lease->quarantined ||
        !lease->charged || bytes == 0 || offset > lease->size ||
        bytes > lease->size - offset || offset > NV_U64_MAX - lease->dmaBase ||
        bytes - 1 > NV_U64_MAX - (lease->dmaBase + offset))
        return NV_ERR_INVALID_LIMIT;
    *address = lease->dmaBase + offset;
    return NV_OK;
}

#endif
