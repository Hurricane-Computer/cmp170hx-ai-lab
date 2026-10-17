# Mixed-CMP driver candidates: two bounded negative trials

**Both candidates built successfully, but neither made the CMPs ready for CUDA.** Blackwell remained visible. The result is an initialization failure, not an extra-memory or P2P success. The test guest is retained in that research state with its GPU workloads stopped.

## What was built and changed

Full NVIDIA open-kernel sources for 615.71.09 were built for the actual 6.8.0-147-generic guest kernel, using the pinned fork's mixed profile. Four compiler jobs were used. The distribution's existing DKMS source contains the kernel-facing layer and a prebuilt resource-manager object, so it was insufficient for these source changes.

The build-only step did not install or load modules. In the separate approved trial, stock package modules and the previous initrd were preserved, the candidate went into its own module directory, and the guest's next boot was configured to use it. GPU service/container autostarts were stopped for the experiment. There was no host restart, IOMMU/ACS change, flash or OTP programming.

| Candidate | Difference | Observed result |
|---|---|---|
| A | Pinned mixed 40/64-GiB profile, without P2P or memory-clock opt-ins | Both CMPs failed probe-time initialization; Blackwell visible |
| B | Restored original NVIDIA PRAMIN window placement; promoted one existing diagnostic from INFO to ERROR | Both CMPs failed at the same BAR2 test; Blackwell visible |

Candidate A used one exclusive CMP64 reset. Candidate B used one exclusive reset of each previously failed CMP before the new mapping trial. Reset protection was restored and other running guests retained their process IDs. These were different prepared candidates, not retries of the same failed module.

## The actual failure

Initialization logged 64/40-GiB framebuffer declarations before failing `kbusVerifyBar2_GM107` with `NV_ERR_MEMORY_ERROR` and `RmInitAdapter` tuple `0x24:0x72:1298`. The test writes a pattern through BAR2 and reads back through the BAR0 window; the read at offset `0x70e000` returned zero.

Candidate B's diagnostic confirmed the changed placement: the saved window was near 64/40 GiB, and the test targeted framebuffer offsets `0xff48de000` / `0x9f4ade000`. Aperture 0 came from the actual memory descriptor. Both CMP BAR1 resources still ended at 64 MiB despite the fork's promotion attempt.

This closes the narrow hypothesis that removing that initial PRAMIN placement clamp alone fixes this boot. It does not establish absent HBM, a universal BAR failure or unusable hardware under every driver. The planned 8-MiB copy checks were not reached, and P2P patches/transfers were not run. Do not turn the internal 64/40-GiB declarations into a working-memory result.

## Marker-method correction

The Stage42 marker scan examined a Zstandard-compressed module as bytes. That was insufficient to infer marker absence from executable content. A subsequent scan actually decompressed both installed modules, checked the ELF header and found the same markers absent. The negative outcome stayed the same; the corrected method and distinct compressed/ELF hashes are recorded in the data.

The two newly built variants also shared a kernel `srcversion`, despite different module hashes and resource-manager code. That field alone does not uniquely identify this rebuilt core. Keep file hashes, controlled boot provenance and the diagnostic behavior together.

## Next useful work

Trace the BAR2 write target, PTE/mapping setup and subsequent BAR0 read to find a distinguishing mechanism. A root cause is not yet established. Do not repeat these two modules or more identical resets. The separately prepared P2P builder has not been dispatched; peer work needs a usable baseline and must preserve the normal platform-topology verdict.

Historical CMP40 clock and capacity observations remain historical. After these candidate boots the CMPs are not NVML-ready, so no current capacity or operating clock is asserted. Stock packages and recovery artifacts remain available; services were not automatically restored after each trial.

[Candidate hashes, diagnostics and explicit limits](../data/driver-candidates.json). Sources: [NVIDIA 615.71.09](https://github.com/NVIDIA/open-gpu-kernel-modules/tree/615.71.09), [pinned fork](https://github.com/admunch888/cmpunlocker/tree/7d86a7f8f4ac3abbd0f48fa6d6cd09aa6b953f03). No proprietary firmware or raw host logs are published here.
