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

The initial control above did not pass explicit bounds. The follow-up below now qualifies ordinary fixed and range placements and their owned mappings. No expanded profile was loaded. The [earlier upper-window alias result](cache-alias.md) and the [foreign positive capacity reports](capacity-evidence.md) retain their existing scope.

## Follow-up: normal fixed and range requests

Later controls used a normal user-space RM client, `NV01_MEMORY_LOCAL_USER` and `NV_MEMORY_ALLOCATION_PARAMS`. No helper kernel module or driver change was needed. The native C ABI was compiled against the matching headers: allocation/control 32 bytes each, memory parameters 128 bytes, map parameters 48 bytes, the Linux map-with-FD wrapper 56 bytes, and unmap parameters 32 bytes.

An early caller error left the ordinary owner tag at zero. The constructor refused it with `NV_ERR_INVALID_OWNER` before any test memory was allocated. The correction used a nonzero application tag outside the reserved RM scratch interval; internal flags stayed zero. The [normal validation](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/src/kernel/mem_mgr/standard_mem.c#L49-L82) and [reserved bounds](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/generated/g_heap_nvoc.h#L158-L165) remained intact.

| Normal request | Variants tested | Requested physical windows | Observation |
|---|---|---|---|
| Fixed address | CMP40 and CMP64 | 64 KiB at 1 and 2 GiB | Exact requested offsets returned; five complete CPU comparisons per card, zero wrong words |
| Narrow physical range | CMP40 | 64 KiB at 1 and 2 GiB | Exact requested offsets returned; five complete CPU comparisons, zero wrong words |
| Fixed upper address | CMP40 / CMP64 | 64 KiB at 40.5 / 64.5 GiB | Constructor refused with `0x40`, `NV_ERR_INVALID_STATE`; no upper mapping or data access |
| Narrow upper range | CMP40 / CMP64 | 64 KiB at 40.5 / 64.5 GiB | Constructor refused with `0x51`, `NV_ERR_NO_MEMORY`; no upper mapping or data access |

Each upper request had a separate lower 64-KiB object at 0.5 GiB. The lower object and its CPU mapping were accepted, but the program did not fill either buffer before both allocations and mappings existed. Consequently all four upper-refusal cases wrote **zero test bytes**. These are constructor results, not failed comparisons of physical upper HBM. [Curated records and timestamps](../data/native-pa-placement.json).

The successful controls used at most 128 KiB of owned memory each. Their CPU access and five comparisons had the same bounded footprint as the initial method. Here cleanup supplied checked return values: both OS unmaps, both RM unmaps, both framebuffer frees and the subdevice/device/client frees all returned zero. The separate OS mapping was removed before the RM mapping, which was released using its RM-returned token.

The [Linux map-memory escape](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/arch/nvalloc/unix/src/escape.c#L587-L643) validates the object and creates a mapping context on the specified device FD. The [mmap consumer](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/kernel-open/nvidia/nv-mmap.c#L541-L557) requires that validated context and file offset zero. The helper additionally checked that the RM token lay within the current framebuffer BAR1. It did not map a guessed register window.

The fixed/range difference has a concrete source discriminator. [The allocator selector](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/src/kernel/mem_mgr/video_mem.c#L682-L695) applies `heapIsPmaManaged` specifically to fixed-address requests; the following non-PMA scrub guard can return `INVALID_STATE`. The selected native journal query did not identify the runtime predicate or exact return site, so that explanation remains a source hypothesis. The normal range request instead supplies bounds to the PMA consumer. For these aligned one-page requests the caller used `rangeLo=P`, `rangeHi=P+65536`, matching that consumer's aligned-end-minus-one conversion. PMA range and ownership checks were retained.

At the last 12-second follow-up, 18 October 21:14:30 UTC, both cards still reported 40/64 GiB, zero used MiB and zero clients at 1215/1728 MHz. The selected native error query had no matches. No driver reload, firmware change or clock change occurred. No CUDA kernel or transfer was executed.

**Additional usable GiB remain zero.** The native allocator did not supply the requested upper pages through either tested route. This does not establish the installed HBM density, a physical capacity ceiling or the cause of the earlier expanded-profile alias. Further upper-memory work needs a new backing/geometry experiment using the now-qualified small PA-aware method; these unchanged G requests and the previous large H allocation should not be replayed as new evidence.

## Simultaneous sparse address-separation matrix at 100 W

On 19 October 2026, a new finite test held six ordinary owned 64-KiB windows on CMP40 and nine on CMP64 simultaneously. Native `USE_BEGIN_END` requests returned the exact requested GPU physical offsets; ownership, bounds and checked cleanup remained intact. The distinction from the earlier two-buffer control is the simultaneous multi-address set and a complete partner sweep after every isolated rewrite.

| Variant | Tested GPU physical offsets (GiB) | Simultaneous owned memory | Full 64-KiB comparisons | Wrong words |
|---|---|---:|---:|---:|
| CMP40 | 0.5, 8.5, 16.5, 24.5, 32.5, 39 | 384 KiB | 42 | 0 |
| CMP64 | 0.5, 8.5, 16.5, 24.5, 32.5, 40.5, 48.5, 56.5, 63 | 576 KiB | 90 | 0 |

All objects and CPU BAR1 mappings existed before the first test write. Each slot received a distinct nonce-dependent word pattern. After the initial full comparison, each window was rewritten once while every held window was compared in full. The test wrote 1.875 MiB and compared 8.25 MiB across both cards. CPU-only controls correctly detected one changed word and 16,384 wrong words when the entire wrong-window pattern was substituted. These controls did not inject errors into either GPU.

Both cards retained 100 W power limits and unchanged HBM clocks, 1215/1728 MHz. No driver/module, geometry, register, firmware, clock, service or VM change was made for the matrix. All 51 reported OS/RM cleanup calls succeeded; afterwards both cards had zero reported used MiB and zero clients, and the selected current test-window kernel error query was empty. This is a timestamped finite observation, not long-duration qualification. [Curated measurements](../data/owned-address-matrix.json).

The samples are entirely inside already reported 40/64 GiB. In particular, 48.5/56.5/63 GiB on CMP64 are ordinary baseline addresses, not an expansion. Only 64 KiB at each offset was tested, and these particular native objects were accessed through CPU BAR1 mappings rather than CUDA kernels. No whole-range integrity, partition identity, distinct installed HBM-cell population, additional usable capacity, throughput or sound-level claim follows. The old rejected upper allocations and expanded-profile alias test were not replayed. A new actual physical initialization/backing mechanism is still needed for a meaningful expansion attempt.
