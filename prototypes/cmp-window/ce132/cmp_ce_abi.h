/* SPDX-License-Identifier: MIT
 * Exact declarations from the pinned NVIDIA MIT nv_uvm_interface.h.
 */
#include "cmp_rm_abi.h"
NV_STATUS nvUvmInterfaceMemoryAllocSys(uvmGpuAddressSpaceHandle vaSpace,
    NvLength length, UvmGpuPointer *gpuPointer, UvmGpuAllocInfo *allocInfo);
NV_STATUS nvUvmInterfaceQueryCopyEnginesCaps(uvmGpuDeviceHandle device,
    UvmGpuCopyEnginesCaps *caps);
NV_STATUS nvUvmInterfaceTsgAllocate(uvmGpuAddressSpaceHandle vaSpace,
    const UvmGpuTsgAllocParams *allocParams, uvmGpuTsgHandle *tsg);
void nvUvmInterfaceTsgDestroy(uvmGpuTsgHandle tsg);
NV_STATUS nvUvmInterfaceChannelAllocate(const uvmGpuTsgHandle tsg,
    const UvmGpuChannelAllocParams *allocParams, uvmGpuChannelHandle *channel,
    UvmGpuChannelInfo *channelInfo);
void nvUvmInterfaceChannelDestroy(uvmGpuChannelHandle channel);
NV_STATUS nvUvmInterfaceGetExternalAllocPhysAddrs(uvmGpuAddressSpaceHandle space,
    NvHandle memory, NvU64 offset, NvU64 size, UvmGpuExternalPhysAddrInfo *info);
