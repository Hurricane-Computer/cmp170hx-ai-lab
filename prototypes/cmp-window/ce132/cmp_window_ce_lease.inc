/* SPDX-License-Identifier: MIT
 * Kernel-owned, explicitly bounded diagnostic leases. The caller retains the
 * registered owner/accessor and source allocation through CE channel retirement.
 * No CUDA/UVM peer capability is advertised. These are not userspace opcodes.
 */
#define CMP_WINDOW_PROBE_MAPPING ((UvmGpuMappingType)0x43575032U)
#define CMP_WINDOW_ACQUIRE_MAPPING ((UvmGpuMappingType)0x43575033U)
#define CMP_WINDOW_RELEASE_MAPPING ((UvmGpuMappingType)0x43575034U)
#define CMP_WINDOW_PROBE_MAGIC 0x435750524f424532ULL

static NvBool cmpWindowIsDiagnostic(UvmGpuMappingType type)
{
    return type == CMP_WINDOW_PROBE_MAPPING || type == CMP_WINDOW_ACQUIRE_MAPPING ||
           type == CMP_WINDOW_RELEASE_MAPPING;
}

static NV_STATUS cmpWindowProbe(struct gpuAddressSpace *space, NvHandle memory,
                               OBJGPU *accessor, MEMORY_DESCRIPTOR *allocation,
                               NvU64 offset, NvU64 size,
                               gpuExternalPhysAddrInfo *info)
{
    CmpNativeWindow *map = NULL;
    NV_STATUS status = NV_OK, cleanup = NV_OK;
    NvU64 record[10] = {CMP_WINDOW_PROBE_MAGIC, 0, 0, 0, 0, 0, 0, 0, 0, 0};
    NvBool retained = NV_FALSE;
    const NvBool release = info->mappingType == CMP_WINDOW_RELEASE_MAPPING;
    const NvBool persistent = info->mappingType == CMP_WINDOW_ACQUIRE_MAPPING;

    if (!rmGpuLockIsOwner() || !cmpWindowIsDiagnostic(info->mappingType) ||
        info->physAddrBuffer == NULL || info->physAddrBufferSize < sizeof(record) ||
        offset != 0 || allocation == NULL || size != memdescGetSize(allocation) ||
        size == 0 || size > CMP_WINDOW_MAX_BYTES ||
        memdescGetAddressSpace(allocation) != ADDR_FBMEM ||
        !cmpWindowIsPair(accessor, allocation->pGpu))
        return NV_ERR_INVALID_ARGUMENT;

    record[1] = size;
    if (release)
    {
        for (map = cmpWindowList; map != NULL; map = map->next)
            if (map->client == space->device->session->handle &&
                map->accessorSubdevice == space->device->subhandle &&
                map->duplicate == memory && map->allocation == allocation &&
                map->owner == allocation->pGpu && map->accessor == accessor)
                break;
        if (map == NULL)
            status = NV_ERR_OBJECT_NOT_FOUND;
    }
    else
    {
        status = cmpWindowNativeAcquire(accessor, allocation->pGpu, allocation,
                                        space->device->session->handle,
                                        space->device->subhandle, memory, &map);
    }
    record[2] = status;
    if (map != NULL)
    {
        if (persistent && status == NV_OK)
            map->lease.published = NV_TRUE; // Address handed to this kernel-only consumer.
        record[3] = map->lease.apertureOffset;
        record[4] = map->lease.apertureLength;
        record[5] = map->lease.cpuPhysicalBase;
        record[6] = map->lease.dmaBase;
        record[7] = (map->lease.ownerMapped ? 1ULL : 0ULL) |
                    (map->lease.dmaDescriptor ? 2ULL : 0ULL) |
                    (map->lease.dmaMapped ? 4ULL : 0ULL) |
                    (map->lease.quarantined ? 8ULL : 0ULL) |
                    (map->lease.published ? 16ULL : 0ULL);
        if (persistent && status == NV_OK)
            retained = NV_TRUE;
        else
        {
            // Release is permitted only after the kernel caller retires its CE channel.
            // Failed acquisition never published an address to a reader.
            cleanup = cmpWindowNativeRelease(map, NV_TRUE);
            retained = cleanup != NV_OK;
        }
    }
    record[8] = cleanup;
    record[9] = retained;
    portMemCopy(info->physAddrBuffer, info->physAddrBufferSize, record, sizeof(record));
    info->numWrittenPhysAddrs = NV_ARRAY_ELEMENTS(record);
    info->numRemainingPhysAddrs = 0;
    NV_PRINTF(LEVEL_ERROR,
              "CMP_WINDOW_LEASE mode=%u acquire=%u cleanup=%u retained=%u flags=%llu size=%llu\n",
              info->mappingType, status, cleanup, retained, record[7], size);
    return status != NV_OK ? status : cleanup;
}
