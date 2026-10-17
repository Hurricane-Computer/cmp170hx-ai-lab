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

## Address and lifetime follow-up, 17 October 2026

This follow-up is static analysis with source-file reads only. Nine of ten examined files match pinned NVIDIA source. The remaining file contains the retained CMP BAR2 cache-policy and diagnostic changes; its three relevant BAR1 map/unmap function bodies still match. [Structured source results and unbuilt contract](../data/bar1-lifecycle.json) retain that distinction.

| Value | Meaning | Correct use |
|---|---|---|
| Allocation offset | Position within the owner's actual allocation | Select the source subrange |
| BAR1 VAS address | Returned aperture window address | Save unchanged for matching aperture unmap |
| CPU BAR physical address | Owner BAR base plus aperture address | Describe the owner's BAR resource |
| Accessor DMA address | Result of mapping that resource for the reading GPU | Encode reader PTEs with allocation-relative offsets |

The [Single wrappers](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/src/kernel/gpu/bus/kern_bus.c#L1078) add the unmanaged-area flag. The [dynamic unmap](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/src/kernel/gpu/bus/arch/maxwell/kern_bus_gm107.c#L3211) passes that saved range to the BAR1 VAS allocator; these functions do not subtract a physical BAR base. The newer GH100 helper's normal free reads its CPU-physical descriptor address, whereas its error cleanup uses the saved aperture value. That difference blocks copying it unchanged into a dynamic CMP allocator. No actual GH100 free failure or leak has been demonstrated.

The existing [OS peer-DMA path](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/arch/nvalloc/unix/src/os.c#L3817) identifies the memory owner's BAR and maps it for the accessor. The descriptor must retain the owner as its root GPU. An accessor-specific PTE lookup can fall back to the physical array when no IOVA mapping exists, so a plausible address alone is insufficient: successful mapping and its matching release must be tracked explicitly.

Native peer unmap [rejects partial unmaps](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/src/kernel/mem_mgr/virtual_mem.c#L1724) and calls its BAR1-free hook before `dmaFreeMap`. A dynamic port needs reviewed reader-PTE retirement and error cleanup before its aperture window becomes reusable. The source order does not establish a runtime race. The tracking-list free function alone releases no new window resources.

The candidate remains unbuilt. Pair admission and the actual user-library/UVM consumer, full error-path ordering, aperture accounting/locks and GA100 PTE-kind selection remain open. Existing guards and the native aperture reserve stay intact. No new GPU trial, capacity claim or limit follows from this source work.

## UVM external allocations use a separate producer

The next source follow-up identifies a distinct route: [UVM external mapping](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/kernel-open/nvidia-uvm/uvm_map_external.c#L187) obtains PTEs through `nvUvmInterfaceGetExternalAllocPtes`; the corresponding [RM builder](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/src/kernel/rmapi/nv_gpu_ops.c#L4652) builds external-allocation PTEs without calling the core GH100 BAR1 allocator discussed above. Nine newly followed UVM/interface files in retained G match pinned NVIDIA615.71.09. [Selected source evidence](../data/uvm-external-route.json) records the route and its limits.

Before requesting PTEs, UVM's `set_ext_gpu_map_location` rejects remote framebuffer allocations unless the owner is registered and peer access is enabled in that VA space. Admitted BAR1 pairs are enabled automatically during GPU registration; the manual PCIe-enable path accepts the ordinary PCIe link type. RM checks the real peer capability again before building. These are source-bound admission points, not proof identifying which one produced our earlier CUDA101.

The UVM external route has its own lifetime contract. Splitting a map increments the shared duplicated-handle reference. On normal teardown UVM waits for mapping work, clears PTEs/TLB and releases page-table ranges before dropping that reference; only the final reference calls `FreeDupedHandle`. A window lease tied there can survive partial unmaps. The earlier full-unmap-only constraint applies to the alternative core `virtual_mem.c` route, and must not be generalized to UVM. Fatal-error behavior still needs review.

One per-allocation window does not provide a global BAR1 DMA range. UVM's physical peer-copy address builder requires a nonzero global DMA size; virtual peer copy can construct a peer-wide identity map. A scoped external-window port must explicitly reject or implement those consumers. No such gate or candidate was installed, and no capability was forced positive. The actual closed user-library request path remains untraced.
