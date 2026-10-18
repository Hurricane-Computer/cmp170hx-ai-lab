# Physical-offset diagnostic control

On 18 October 2026, a small control on both CMP variants obtained the GPU physical offsets of normal, owned framebuffer allocations. This is a new diagnostic method, **not additional usable memory**. The unchanged G test driver still reported 40/64 GiB.

## Observed control

A separate helper allocated two physically contiguous 64-KiB buffers per card through `nvUvmInterfaceMemoryAllocFB`, mapped its own buffers for CPU access, and used fresh nonce-dependent word patterns. It checked the first buffer, checked both after filling the second, then checked both after changing the first again: five complete 16384-word comparisons per card, all with zero mismatches. At most 128 KiB was owned per card; 192 KiB was written and 320 KiB compared, with three additional 32-bit readbacks to flush posted writes. No CUDA kernel or transfer ran.

| Variant | First returned GPU physical offset | Second returned GPU physical offset | Second request |
|---|---:|---:|---|
| CMP40 | `0x0a110000` | `0x0a130000` | `bMemGrowsDown=true` |
| CMP64 | `0x10090000` | `0x100b0000` | `bMemGrowsDown=true` |

Both second offsets are still low in their respective reported memory ranges. **The grows-down request did not select an upper-memory window in these runs.** Reusing this request as evidence of access above 40 or 64 GiB would be incorrect. The two offsets on each card differ by 128 KiB, although the requested buffers are 64 KiB each; no physical routing interpretation is inferred from that gap.

The helper issued both CPU unmaps and both frees, destroyed its VA/device objects and received a successful session-destroy status. The unmap/free/device/VA APIs return void, so they do not provide independent zero-status cleanup evidence. Module removal was checked separately. A 12-second follow-up found zero reported framebuffer use and zero clients, the unchanged 40/64-GiB reports, and no matching native Xid, initialization-failure or kernel BUG/Oops record. The driver was not reloaded; no firmware or clock setting changed. These are timestamped observations, not a sustained-health qualification. [Structured extract](../data/physical-offset-control.json).

## Normal entry requirements

Two earlier prototype entries stopped at `GetGpuInfo` with status `0x1b` before allocating any test memory. The first also omitted the required GPU registration. Adding registration alone did not resolve the refusal. The same corrected module then worked after the launcher opened the matching ordinary GPU device and inherited that file descriptor into the calling process.

This is the normal OS access contract, not a removed permission check: the pinned [status definition](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/kernel-open/common/inc/nvstatuscodes.h) names `0x1b` as `NV_ERR_INSUFFICIENT_PERMISSIONS`; [the access check](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/kernel-open/nvidia/nv.c#L6063-L6092) looks for the matching NVIDIA device in the current process's open files. [GPU registration](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/kernel-open/common/inc/nv_uvm_interface.h#L63-L93) is a separate reference that must also be paired with unregister after resource cleanup. No gate was forced to succeed.

## Source analysis and next step

The pinned 615.71.09 [RM allocation producer](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/src/kernel/rmapi/nv_gpu_ops.c#L4979-L5090) returns `NV_MEMORY_ALLOCATION_PARAMS.offset` as `gpuPhysOffset` for a contiguous allocation. GPU virtual addresses are allocated separately. This avoids silently treating a CUDA virtual offset as its physical backing location. A returned GPU physical offset still does not establish distinct HBM cells, installed density or whole-range integrity.

The same producer translates `bMemGrowsDown` to `NVOS32_ALLOC_FLAGS_FORCE_MEM_GROWS_DOWN`; it does not forward explicit physical bounds. The pinned [PMA consumer](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/src/kernel/mem_mgr/video_mem.c#L229-L255) handles the separate `FORCE_REVERSE_ALLOC`, `FIXED_ADDRESS_ALLOCATE` and `USE_BEGIN_END` inputs. Fixed/range requests become PMA address constraints. The [allocator implementation](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/src/kernel/gpu/mem_mgr/phys_mem_allocator/phys_mem_allocator.c#L707-L715) checks the beginning and `physEnd + 1` alignment; a header's half-open-range wording must not substitute for this consumer contract.

The next proposed control is a small allocation with an explicit physical placement constraint through the ordinary RM allocation ABI, first within the existing baseline. That exact-range user path, its CPU mapping and its cleanup have **not** been demonstrated here. No expanded profile was loaded for this control. The [earlier upper-window alias result](cache-alias.md) and the [foreign positive capacity reports](capacity-evidence.md) retain their existing scope.
