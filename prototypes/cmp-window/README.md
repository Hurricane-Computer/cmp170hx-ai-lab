# Bounded external-window allocator prototype

Status, 17 October 2026: **CPU resource tests passed; native adapter compiled; no runtime integration or GPU trial.** This is an implementation component, not a working P2P driver or a capacity unlock.

`cmp_window_lease.h` implements the resource transaction independently of hardware. `cmp_window_native.inc` adapts it to NVIDIA615.71.09's real owner-aperture and accessor-DMA APIs. The initial adapter accepts only the CMP2082/20c2 pair and at most2MiB per allocation. Its budget is global per owner across client sessions, retains a36MiB reserve and still requires the native allocator to find an exact contiguous range. A64MiB aperture minus36MiB is a nominal bound, not measured free space.

The allocation offset, returned BAR1 aperture range, CPU physical address and accessor DMA address remain distinct. Acquisition flags establish ownership; an IOVA of zero is valid. Bounds use subtraction to avoid overflow. DMA resources release before the owner window; aperture charge releases last. A published lease rejects release until its caller confirms reader PTE/tracker retirement. A reported cleanup failure preserves resources/charge, blocks new owner windows and permits an explicit cleanup retry.

## What was checked

The CPU-only harness exercises15 scenario groups and10,000 address-boundary cases under GCC address/undefined-behaviour sanitizers, with `-Wall -Wextra -Werror`. An independent backend records live resources and operation order. Cases include zero IOVA, exhausted/shared owner quota, reserve/overflow bounds, partial acquisition, reverse cleanup, early release rejection, cleanup quarantine and retry. No GPU or BAR is accessed.

To reproduce these CPU tests on a Linux development system:

```sh
gcc -std=c11 -O1 -g -Wall -Wextra -Werror \
  -fsanitize=address,undefined -fno-omit-frame-pointer \
  test_window_lease.c -o test_window_lease
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 \
UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 ./test_window_lease
```

The adapter was included in `src/nvidia/src/kernel/rmapi/nv_gpu_ops.c` immediately before `nvGpuOpsGetExternalAllocAperture` and compiled in a separate copy of the retained615.71.09 research tree. The actual `nv_gpu_ops.o` contains both `cmpWindowNativeAcquire` and `cmpWindowNativeRelease`. Five kernel modules linked. The final linker removes the unreachable adapter entries, as expected; there is no runtime caller, capability change or installed module change. Six build warnings concern compiler-version/other source diagnostics, not an adapter compiler failure.

The initial collector used an incorrect intermediate path, then incorrectly expected unreachable entries in the final module. Inspecting the actual build rule/object resolved both checks without another compilation or CPU-test run. A shell argument-length failure during transfer was fixed by transferring only the new files and applying a checked three-line include edit to the existing source. No restart or hardware recovery followed these harness errors.

## Required before a hardware candidate

- Implement resource-backed **external-only** pair admission and explicitly reject or implement internal managed/physical/virtual-copy consumers. Existing global-DMA metadata must not describe a nonexistent whole-framebuffer mapping.
- Connect the real external PTE builder, keeping GA100's selected page/kind/cache/read-only/no-atomics format. Addresses must come from an acquired, allocation-relative window.
- Connect final duplicated-handle release after native UVM PTE/tracker teardown; retain references through split maps. Implement independent owner-reference retention and fatal client/subdevice teardown. The current adapter requires its caller to hold the validated allocation reference; it does not supply that integration.
- Preserve cleanup uncertainty: the native DMA-unmap API returns void, and the unmanaged owner-unmap path contains a void allocator free. A CPU quarantine test is not hardware completion acknowledgement or proof of fatal cleanup safety.
- Review/build the integrated candidate before a bounded2MiB allocation/1MiB data trial, with actual remote kernel read and later copy verdicts separated.

The current component must not be installed as a working P2P implementation. It changes no topology, capability result, I/O overlap guard, generated HAL default, host IOMMU/ACS setting, clock or firmware. It establishes no additional usable memory or SM, and no physical40GiB limit.

## Provenance

Our three prototype source files use the MIT license. They are original adaptation/test code, not redistributed proprietary firmware or a copy of the external author's driver patch. Native API contracts come from pinned [NVIDIA615.71.09](https://github.com/NVIDIA/open-gpu-kernel-modules/tree/61dcc93722ecb418bb5f2e00923f05b4b8051dd1), particularly [nv_gpu_ops.c](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/src/kernel/rmapi/nv_gpu_ops.c), [dynamic aperture map/free](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/src/kernel/gpu/bus/arch/maxwell/kern_bus_gm107.c) and the [native36MiB reserve](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/generated/g_third_party_p2p_nvoc.h#L79). The allocation-window architecture was prompted by the attributed [Duanyll48-GB4090 experiment](https://github.com/Duanyll/open-gpu-kernel-modules/tree/025090f64d7f79b3b6de118c3e9c50bc32988235); its broad patch was not imported. See [structured build/test scope](../../data/window-prototype.json) and the separate [UVM route](../../docs/vmm-peer-mapping.md).
