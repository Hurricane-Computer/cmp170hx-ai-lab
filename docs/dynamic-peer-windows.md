# Owned memory windows: CPU reads work, GPU registration rejects

On 17 October 2026, each CMP successfully exported and CPU-mapped an owned **1-MiB** device allocation. Every byte matched, with the original device data checked before and after. Registering those windows for the other CMP subsequently returned `CUDA_ERROR_INVALID_VALUE` in both directions. No remote GPU kernel ran. These are separate outcomes, recorded in the [structured measurements](../data/dynamic-peer-windows.json).

## Observed, unchanged driver G

| Test | CMP40 | CMP64 |
|---|---|---|
| Stage78: DMA-BUF export, explicit PCIe flag1 | Error801, not supported | Error801, not supported |
| Stage79: default export flag0 and CPU mmap | 1MiB, zero wrong bytes | 1MiB, zero wrong bytes |
| Stage80: same CPU window, then other GPU's I/O registration | CPU data correct; registration error1 | CPU data correct; registration error1 |

The module-free backend follows the API contract in [NVIDIA GDRCopy](https://github.com/NVIDIA/gdrcopy/tree/fcec3ce0bb40a97a6cc45dd4afeec4bccb509712). The installed CUDA driver API reports13.4, above that backend's13.3 minimum. Each window uses an owned1MiB+64KiB backing allocation; only the aligned1MiB range is exported. The general DMA-BUF capability flag does not guarantee every export mode succeeds.

Stage80 uses the documented [`cuMemHostRegister` IOMEMORY and DEVICEMAP flags](https://docs.nvidia.com/cuda/cuda-driver-api/cuda_driver_api/group__CUDA__MEM.html), combined as6. Both registrations reject before obtaining a GPU pointer or launching the prepared verifier. All CPU comparisons, owner before/after checks and resource cleanup pass. Stages78–80 require no VM restart, GPU reset, driver change or forced peer capability.

Stage77 was a preparation error: its idle check ran after its own CUDA initialization and mistook reserved memory for an external workload. No test allocation or export ran. Its recovery unnecessarily restarted the guest once and removed the previous diagnostic pair option; no GPU reset occurred. The corrected preflight checks workloads before initialization. Later tests retain native G with empty registry options.

## Source lead: real windows instead of capability overrides

A [Duanyll original report](https://github.com/Duanyll/duanyll.com-hexo/blob/7892cfa0c01be796bbba740cde1c2823ed5e0419/source/_posts/tech/2026-7-13-4090-48G-P2P.md) describes allocation-specific BAR1 mappings for48-GB4090 P2P. Its [implementation](https://github.com/Duanyll/open-gpu-kernel-modules/tree/025090f64d7f79b3b6de118c3e9c50bc32988235) is a useful mechanism lead, not our CMP result. Selected changes were compared against the author's595.71.05 base, separately from our615.71.09 version differences. No author patch was installed.

The author's64MiB reservation would admit no allocation at our previously observed64MiB BAR1 aperture. NVIDIA's [native third-party mapping reserve](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/generated/g_third_party_p2p_nvoc.h#L79) is36MiB. A nominal28MiB remainder assumes zero prior use; it is not measured free or contiguous aperture space. Reservations and topology checks were retained.

The pinned [Linux I/O lookup](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/kernel-open/nvidia/os-mlock.c#L114) requires a suitable single VMA and contiguous page-frame sequence. Stage80 recorded I/O/PFN-map flags, but did not measure page-frame continuity or identify the exact rejecting internal call. Those source conditions are not a proven explanation for error1. Next, resolve the actual registration/mapping contract before any new GPU trial; do not blindly vary flags or transplant broad HAL overrides.

CPU mapping is a useful additional observation path. It establishes neither working GPU P2P, a larger usable framebuffer, nor a physical40-GiB ceiling. The separate positive75/76- and77.5/72-GiB reports remain open;48GiB remains an initial capacity target. Earlier [peer-data failures](peer-option-trials.md) retain their original scope.
