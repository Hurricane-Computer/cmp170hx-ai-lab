/* Exact declarations extracted from pinned NVIDIA MIT interface header. */
#ifndef CMP_RM_ABI_H
#define CMP_RM_ABI_H
#include "nv_uvm_types.h"
typedef struct
{
    struct pci_dev *pci_dev;

    // DMA addressable range of the device, mirrors fields in nv_state_t.
    NvU64 dma_addressable_start;
    NvU64 dma_addressable_limit;
} UvmGpuPlatformInfo;
NV_STATUS nvUvmInterfaceRegisterGpu(const NvProcessorUuid *gpuUuid, UvmGpuPlatformInfo *gpuInfo);
void nvUvmInterfaceUnregisterGpu(const NvProcessorUuid *gpuUuid);
NV_STATUS nvUvmInterfaceSessionCreate(uvmGpuSessionHandle *session,
                                      UvmPlatformInfo *platformInfo);
NV_STATUS nvUvmInterfaceSessionDestroy(uvmGpuSessionHandle session);
NV_STATUS nvUvmInterfaceGetGpuInfo(const NvProcessorUuid *gpuUuid,
                                   const UvmGpuClientInfo *pGpuClientInfo,
                                   UvmGpuInfo *pGpuInfo);
NV_STATUS nvUvmInterfaceDeviceCreate(uvmGpuSessionHandle session,
                                     const UvmGpuInfo *pGpuInfo,
                                     const NvProcessorUuid *gpuUuid,
                                     uvmGpuDeviceHandle *device,
                                     NvBool bCreateSmcPartition);
void nvUvmInterfaceDeviceDestroy(uvmGpuDeviceHandle device);
NV_STATUS nvUvmInterfaceAddressSpaceCreate(uvmGpuDeviceHandle device,
                                           unsigned long long vaBase,
                                           unsigned long long vaSize,
                                           NvBool enableAts,
                                           uvmGpuAddressSpaceHandle *vaSpace,
                                           UvmGpuAddressSpaceInfo *vaSpaceInfo);
void nvUvmInterfaceAddressSpaceDestroy(uvmGpuAddressSpaceHandle vaSpace);
NV_STATUS nvUvmInterfaceMemoryAllocFB(uvmGpuAddressSpaceHandle vaSpace,
                                      NvLength length,
                                      UvmGpuPointer * gpuPointer,
                                      UvmGpuAllocInfo * allocInfo);
void nvUvmInterfaceMemoryFree(uvmGpuAddressSpaceHandle vaSpace,
                              UvmGpuPointer gpuPointer);
NV_STATUS nvUvmInterfaceMemoryCpuMap(uvmGpuAddressSpaceHandle vaSpace,
                                     UvmGpuPointer gpuPointer,
                                     NvLength length, void **cpuPtr,
                                     NvU64 pageSize);
void nvUvmInterfaceMemoryCpuUnMap(uvmGpuAddressSpaceHandle vaSpace,
                                  void *cpuPtr);
#endif
