# Mixed-CMP driver candidates: three bounded negative trials

**All three candidates built successfully, but none made the CMPs ready for CUDA.** Blackwell remained visible. The result is an initialization failure, not an extra-memory or P2P success. The test guest is retained in that research state with its GPU workloads stopped.

## What was built and changed

Full NVIDIA open-kernel sources for 615.71.09 were built for the actual 6.8.0-147-generic guest kernel, using the pinned fork's mixed profile. Four compiler jobs were used. The distribution's existing DKMS source contains the kernel-facing layer and a prebuilt resource-manager object, so it was insufficient for these source changes.

The build-only step did not install or load modules. In the separate approved trial, stock package modules and the previous initrd were preserved, the candidate went into its own module directory, and the guest's next boot was configured to use it. GPU service/container autostarts were stopped for the experiment. There was no host restart, IOMMU/ACS change, flash or OTP programming.

| Candidate | Difference | Observed result |
|---|---|---|
| A | Pinned mixed 40/64-GiB profile, without P2P or memory-clock opt-ins | Both CMPs failed probe-time initialization; Blackwell visible |
| B | Restored original NVIDIA PRAMIN window placement; promoted one existing diagnostic from INFO to ERROR | Both CMPs failed at the same BAR2 test; Blackwell visible |
| C | Requested an uncached CPU BAR2 mapping on CMP IDs only; retained all tests and B placement | Same BAR2 failure on both CMPs; direct BAR0 prechecks logged as passed |

Candidate A used one exclusive CMP64 reset. Candidate B used one exclusive reset of each previously failed CMP before the new mapping trial. Reset protection was restored and other running guests retained their process IDs. These were different prepared candidates, not retries of the same failed module.

## The actual failure

Initialization logged 64/40-GiB framebuffer declarations before failing `kbusVerifyBar2_GM107` with `NV_ERR_MEMORY_ERROR` and `RmInitAdapter` tuple `0x24:0x72:1298`. The test writes a pattern through BAR2 and reads back through the BAR0 window; the read at offset `0x70e000` returned zero.

Candidate B's diagnostic confirmed the changed placement: the saved window was near 64/40 GiB, and the test targeted framebuffer offsets `0xff48de000` / `0x9f4ade000`. Aperture 0 came from the actual memory descriptor. Both CMP BAR1 resources still ended at 64 MiB despite the fork's promotion attempt.

This closes the narrow hypothesis that removing that initial PRAMIN placement clamp alone fixes this boot. It does not establish absent HBM, a universal BAR failure or unusable hardware under every driver. The planned 8-MiB copy checks were not reached, and P2P patches/transfers were not run. Do not turn the internal 64/40-GiB declarations into a working-memory result.

## Marker-method correction

The Stage42 marker scan examined a Zstandard-compressed module as bytes. That was insufficient to infer marker absence from executable content. A subsequent scan actually decompressed both installed modules, checked the ELF header and found the same markers absent. The negative outcome stayed the same; the corrected method and distinct compressed/ELF hashes are recorded in the data.

The two newly built variants also shared a kernel `srcversion`, despite different module hashes and resource-manager code. That field alone does not uniquely identify this rebuilt core. Keep file hashes, controlled boot provenance and the diagnostic behavior together.

## Candidate C: isolate the CPU aperture request

The source control flow narrowed the earlier failure: before writing through virtual BAR2, the same function writes and reads the first four bytes directly through BAR0, evicts L2, then reads those four bytes again. Both mismatch paths exit before the previously observed error. This is a four-byte observation, not a whole-memory or anti-alias test.

Candidate C requested `NV_MEMORY_UNCACHED` instead of `NV_MEMORY_WRITECOMBINED` for the CPU BAR2 aperture on the two CMP IDs only. Other GPU types retained the original request. All original self-tests remained active. The mapping call returned success, and new diagnostics explicitly confirmed the BAR0 prechecks passed on both CMPs. The subsequent BAR2 write/readback still returned zero and initialization failed.

The CPU mapping request covered 16 MiB at the start of the correct 32-MiB PCI BAR2 resource; the test used relative offset zero and a 16-byte descriptor. Actual CPU PAT encoding was not independently read. This rules out that mapping-request change alone as a fix in this test; it does not close every possible ordering or mapping defect.

One additional VM restart and one exclusive reset per CMP were used for C. Reset protection was restored, other running guests retained their process IDs, and only Blackwell remained NVML-visible. Small CUDA copies and P2P were still not reached. The retained driver is C; previous stock and A/B recovery artifacts remain available.

## Next useful work

The ordinary BAR2 page-table join is now a concrete diagnostic lead. CPU-RM passes its top-level entry through `UPDATE_BAR_PDE` so GSP-RM can merge it into the root bound in hardware. In this source version the RPC macro assigns a status, but the helper ends with `NV_OK` and its caller does not consume the return. That is a source-level visibility gap; no failed RPC has been observed. Next record the CPU/GSP root descriptors, copied entry, level shift and actual RPC return. Do not repeat A/B/C, suppress the self-test, or run more identical resets. The separately prepared P2P builder remains unexecuted and needs a usable baseline.

Historical CMP40 clock and capacity observations remain historical. After these candidate boots the CMPs are not NVML-ready, so no current capacity or operating clock is asserted. Stock packages and recovery artifacts remain available; services were not automatically restored after each trial.

[Candidate hashes, diagnostics and explicit limits](../data/driver-candidates.json). Sources: [NVIDIA 615.71.09](https://github.com/NVIDIA/open-gpu-kernel-modules/tree/615.71.09), [pinned fork](https://github.com/admunch888/cmpunlocker/tree/7d86a7f8f4ac3abbd0f48fa6d6cd09aa6b953f03). No proprietary firmware or raw host logs are published here.
