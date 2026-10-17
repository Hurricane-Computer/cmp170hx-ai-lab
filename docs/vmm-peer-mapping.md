# VMM allocation works locally; peer admission rejects

The next bounded test uses ordinary CUDA virtual memory management rather than the earlier [I/O-window registration](dynamic-peer-windows.md). On 17 October 2026, both CMPs successfully create and map their own device allocation, but both requests for the other CMP's read access return **101, CUDA_ERROR_INVALID_DEVICE**. No remote-read kernel runs. [Selected measurements](../data/vmm-peer-trials.json) preserve the distinction.

## Observed on native G

| Memory owner | Reader | VMM support, owner/reader | Local allocation | Checked source | Foreign access |
|---|---|---|---|---|---|
| CMP40 | CMP64 | 1 / 1 | 2MiB | 1MiB before/after matches | Error101 |
| CMP64 | CMP40 | 1 / 1 | 2MiB | 1MiB before/after matches | Error101 |

The measured minimum allocation granularity is2MiB on both cards. Returned allocation properties identify device memory on the requested owner. Creation, VA reservation, mapping and owner read/write permission succeed. Source checks use fresh host sentinels and matching full-data hashes. The real directed legacy peer capabilities are both zero.

The reader requests read-only access using `cuMemSetAccess`; rejection occurs before obtaining a successful remote-read verdict. All contexts, mappings, physical handles and VA reservations are released with success. No driver/registry setting, I/O guard, topology field, host IOMMU/ACS configuration or clock is changed. The trial needs no restart or reset.

[NVIDIA's VMM explanation](https://developer.nvidia.com/blog/introducing-low-level-gpu-virtual-memory-management/) describes allocation-specific device access without global peer enable. The [driver API](https://docs.nvidia.com/cuda/cuda-driver-api/cuda_driver_api/group__CUDA__VA.html) supplies the allocation/map/access lifecycle. Neither description establishes compatibility of an arbitrary GPU pair. This experiment makes no global peer-enable or IOMEMORY registration call.

## Native allocator constraints, separate static analysis

Four actual G files match pinned NVIDIA615.71.09 source. Its [virtual-memory mapping consumer](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/src/kernel/mem_mgr/virtual_mem.c#L1214) contains a real BAR1 allocation branch. The [generated allocator selection](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/generated/g_virt_mem_allocator_nvoc.c#L333) chooses it for GH100/newer families; GA100 uses a not-supported default. This is not a trace identifying the exact internal producer of CUDA error101.

The [GH100 allocator](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/src/kernel/gpu/mem_mgr/arch/hopper/virt_mem_allocator_gh100.c#L45) maps an owner subrange and supplies a memory descriptor for the resulting BAR1 window. Its [pair prerequisite](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/src/kernel/gpu/bus/arch/hopper/kern_bus_gh100.c#L1442) includes static BAR1 on both cards and excludes an existing mailbox connection. Switching a support value alone supplies neither those resources nor a working GA100 allocator.

A possible CMP port remains unbuilt. It needs actual owner-window/DMA mapping, bounded aperture admission and paired allocation/free handling, including address-domain and partial-failure cleanup checks. No native check is removed or forced to return success. The original capacity/FWSEC investigation and positive large-memory reports remain open; this small allocation test establishes no additional HBM or physical40-GiB limit.
