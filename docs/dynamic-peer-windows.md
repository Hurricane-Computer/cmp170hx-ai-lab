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

The pinned [Linux I/O lookup](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/kernel-open/nvidia/os-mlock.c#L114) requires a suitable single VMA and contiguous page-frame sequence. At Stage80, only I/O/PFN-map flags had been observed; page-frame continuity and the internal rejection were unresolved. The follow-up below identifies an exercised rejecting condition without repeating the trial.

## Stage81: the GPU-aperture rejection is observed

Two recorded kernel diagnostics at20:20:47.775517 and20:20:48.474485UTC fall within Stage80's two registration attempts. Both identify overlap with GPU framebuffer or BAR2. Three actual G source files match the pinned upstream hashes, including the [overlap check](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/arch/nvalloc/unix/src/osmemdesc.c#L376). This follow-up made no CUDA/NVML call or configuration change.

The [I/O constructor](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/arch/nvalloc/unix/src/osmemdesc.c#L474) applies that range check after declaration and permission checks, before IOMMU mapping. Its documented rationale is an architectural full-duplex BAR1 deadlock. Passing the separate administrator/peer-permission gate does not remove the overlap check. We retain it.

This identifies a real rejection beyond the earlier general page-contiguity hypothesis. The exact user-library conversion to CUDA error1 and individual log-to-direction assignment were not traced. Smaller windows inside the same GPU aperture do not address this condition. Any next mapping experiment needs an ordinary allocation-aware GPU route and its constraints; no forced-success return, removed guard or unchanged registration retry.

CPU mapping is a useful additional observation path. It establishes neither working GPU P2P, a larger usable framebuffer, nor a physical40-GiB ceiling. The separate positive75/76- and77.5/72-GiB reports remain open;48GiB remains an initial capacity target. Earlier [peer-data failures](peer-option-trials.md) retain their original scope.

The subsequent [ordinary VMM trial](vmm-peer-mapping.md) creates real owner allocations successfully, but rejects both foreign-device access requests. It uses a separate documented mapping mechanism and preserves the I/O guard.

## External implementation and checker scope

The pinned author's full changed-path listing contains77 files relative to its595.71.05 base, extending the earlier seven-file selection. Its only UVM-module change is a Blackwell-specific coherence-policy case in `uvm_gpu.h`; that condition does not cover the Ampere CMP pair. This path listing is not a complete correctness audit or a615.71.09 port.

The author's [review follow-up](https://github.com/Duanyll/open-gpu-kernel-modules/blob/025090f64d7f79b3b6de118c3e9c50bc32988235/docs/48g-4090-p2p/method3-review-followups.md) explicitly limits the prototype to external communication buffers and excludes managed peer migration, virtual peer-copy paths and mixed static/dynamic pairs. The [cuMem-versus-legacy report](https://github.com/Duanyll/open-gpu-kernel-modules/blob/025090f64d7f79b3b6de118c3e9c50bc32988235/docs/48g-4090-p2p/method3-usable-vram-cumem-vs-legacy.md) describes small P2P communication coexisting with38GiB resident data on modified48-GB RTX4090s; legacy whole-device peer access remains roughly BAR-sized. These are attributed results on different hardware, not a CMP capacity measurement or a general requirement for identical cards.

Two checked sources narrow the claims. [`dist_p2p_bigmem.py`](https://github.com/Duanyll/open-gpu-kernel-modules/blob/025090f64d7f79b3b6de118c3e9c50bc32988235/docs/48g-4090-p2p/dist_p2p_bigmem.py) fills a large resident tensor with a uniform value and checks the collective buffer; it does not perform final dense, address-distinct readback of the resident tensor. [`p2pbig.cu`](https://github.com/Duanyll/open-gpu-kernel-modules/blob/025090f64d7f79b3b6de118c3e9c50bc32988235/docs/48g-4090-p2p/p2pbig.cu) uses legacy peer access and a position-dependent tail check. Its allocation can back off below the claimed boundary, print a warning and still finish with `PASS`. An offset within a CUDA allocation also does not establish its physical framebuffer address; the lower region is not rechecked after the tail write.

No historical false pass is inferred and neither checker was run here. These are separate from the still-open CMP75/76 and77.5/72GiB reports. [Hashes and source scope](../data/uvm-external-route.json) preserve the distinction. The useful CMP direction remains a bounded, allocation-specific window with real pair admission and full lease cleanup.

## First allocator implementation component

The [bounded CMP window prototype](../prototypes/cmp-window/README.md) now implements owner-global accounting, separate aperture/CPU/DMA domains, explicit resource states and quarantine on reported cleanup failure. Its CPU fault-injection suite passes15 scenario groups and10,000 boundary cases under address/undefined-behaviour sanitizers. The native adapter compiles in the actual615.71.09 translation unit; five modules link, while the final linker removes its still-unreachable entries. Neither new code nor modules were installed.

This closes the first implementation/type-check step, not runtime integration. Resource-backed external-only admission, PTE publication, final duplicate-handle hooks and fatal owner-reference cleanup remain required. Native void cleanup APIs also limit observable failure acknowledgement. [Structured results](../data/window-prototype.json) distinguish the tested CPU contract from untested hardware behaviour; no P2P, HBM or SM success is claimed.
