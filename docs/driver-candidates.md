# Mixed-CMP driver candidates: a working baseline after BAR1 isolation

**Candidate F now initializes both CMPs and Blackwell, and all three passed an 8-MiB checked CUDA copy.** Removing the fork's BAR1 forcing bundle recovered the historical 40/64-GiB configuration in this passthrough guest. Earlier A–E failures remain documented. This is a working driver baseline, not extra VRAM or P2P success.

## What was built and changed

Full NVIDIA open-kernel sources for 615.71.09 were built for the actual 6.8.0-147-generic guest kernel, using the pinned fork's mixed profile. Four compiler jobs were used. The distribution's existing DKMS source contains the kernel-facing layer and a prebuilt resource-manager object, so it was insufficient for these source changes.

The build-only step did not install or load modules. In the separate approved trial, stock package modules and the previous initrd were preserved, the candidate went into its own module directory, and the guest's next boot was configured to use it. GPU service/container autostarts were stopped for the experiment. There was no host restart, IOMMU/ACS change, flash or OTP programming.

| Candidate | Difference | Observed result |
|---|---|---|
| A | Pinned mixed 40/64-GiB profile, without P2P or memory-clock opt-ins | Both CMPs failed probe-time initialization; Blackwell visible |
| B | Restored original NVIDIA PRAMIN window placement; promoted one existing diagnostic from INFO to ERROR | Both CMPs failed at the same BAR2 test; Blackwell visible |
| C | Requested an uncached CPU BAR2 mapping on CMP IDs only; retained all tests and B placement | Same BAR2 failure on both CMPs; direct BAR0 prechecks logged as passed |
| D | Log actual root entries and existing RPC status | Both RPCs returned zero with nonzero entries; BAR2 still failed |
| E | Independently read CPU/GSP root entries through existing BAR0 helper and restore window | Both 8-byte entries matched; BAR2 still failed |
| F | Remove two fork BAR1 force writes and global ResizableBar override | Both CMPs ready; 8-MiB checked copies passed on all three GPUs |

Candidate A used one exclusive CMP64 reset. Candidate B used one exclusive reset of each previously failed CMP before the new mapping trial. Reset protection was restored and other running guests retained their process IDs. These were different prepared candidates, not retries of the same failed module.

## The actual failure

Initialization logged 64/40-GiB framebuffer declarations before failing `kbusVerifyBar2_GM107` with `NV_ERR_MEMORY_ERROR` and `RmInitAdapter` tuple `0x24:0x72:1298`. The test writes a pattern through BAR2 and reads back through the BAR0 window; the read at offset `0x70e000` returned zero.

Candidate B's diagnostic confirmed the changed placement: the saved window was near 64/40 GiB, and the test targeted framebuffer offsets `0xff48de000` / `0x9f4ade000`. Aperture 0 came from the actual memory descriptor. Both CMP BAR1 resources still ended at 64 MiB despite the fork's promotion attempt.

This closes the narrow hypothesis that removing that initial PRAMIN placement clamp alone fixes this boot. It does not establish absent HBM, a universal BAR failure or unusable hardware under every driver. The planned 8-MiB copy checks were not reached, and P2P patches/transfers were not run. Do not turn the internal 64/40-GiB declarations into a working-memory result.

## Marker-method correction

The Stage42 marker scan examined a Zstandard-compressed module as bytes. That was insufficient to infer marker absence from executable content. A subsequent scan actually decompressed both installed modules, checked the ELF header and found the same markers absent. The negative outcome stayed the same; the corrected method and distinct compressed/ELF hashes are recorded in the data.

Candidates A and B also shared a kernel `srcversion`, despite different module hashes and resource-manager code. That field alone does not uniquely identify this rebuilt core. Keep file hashes, controlled boot provenance and the diagnostic behavior together.

## Candidate C: isolate the CPU aperture request

The source control flow narrowed the earlier failure: before writing through virtual BAR2, the same function writes and reads the first four bytes directly through BAR0, evicts L2, then reads those four bytes again. Both mismatch paths exit before the previously observed error. This is a four-byte observation, not a whole-memory or anti-alias test.

Candidate C requested `NV_MEMORY_UNCACHED` instead of `NV_MEMORY_WRITECOMBINED` for the CPU BAR2 aperture on the two CMP IDs only. Other GPU types retained the original request. All original self-tests remained active. The mapping call returned success, and new diagnostics explicitly confirmed the BAR0 prechecks passed on both CMPs. The subsequent BAR2 write/readback still returned zero and initialization failed.

The CPU mapping request covered 16 MiB at the start of the correct 32-MiB PCI BAR2 resource; the test used relative offset zero and a 16-byte descriptor. Actual CPU PAT encoding was not independently read. This rules out that mapping-request change alone as a fix in this test; it does not close every possible ordering or mapping defect.

One additional VM restart and one exclusive reset per CMP were used for C. Reset protection was restored, other running guests retained their process IDs, and only Blackwell remained NVML-visible. Small CUDA copies and P2P were still not reached. C was retained at the end of that trial; later trials below supersede that state. Previous stock and A/B recovery artifacts remain available.

## D/E: the root-entry handoff was actually checked

D recorded success from both existing RPCs and nonzero forwarded entries. CPU PDB descriptors matched their stored base addresses. E then used the existing BAR0 memory-access helper to read eight bytes from the original CPU root and eight from the firmware root. All read and explicit window-restore statuses were zero, and both values matched the forwarded entry on each CMP. The helper deliberately leaves its window changed during bootstrap, so E explicitly restored the saved window.

This establishes the top-level eight-byte copy, not the entire hardware walk, lower page tables or physical capacity. The earlier source-level error-status visibility gap was not an actual failed RPC in these runs. [Curated comparisons](../data/bar2-root-observations.json) preserve that distinction.

## F: remove the BAR1 forcing bundle

The pinned fork applies its BAR1 promotion path even without the P2P build option. In this guest it changed XVE capability/configuration values and forced `EnableResizableBar=1`, while the final CMP BAR1 resource stayed 64 MiB. Before each E promotion both cold-reset cards showed the original values.

F removed the two forcing writes and the global parameter override. Passive snapshots and native NVIDIA policy remained. Both cards retained CYA `0x26`, CFG `0x80000000`, CAP `0x400` before and after the passive helper; the global parameter was zero and BAR1 remained 64 MiB. **Both CMP initializations then passed.** CMP40 reported 40 GiB at 1215 MHz, CMP64 reported 64 GiB at 1728 MHz, and Blackwell remained visible.

Each GPU passed H2D, D2D and D2H on two owned 8-MiB buffers, with a full returned-buffer SHA256 match. All buffers and owned primary-context references were released. This verifies a small working CUDA path. It does not qualify every byte of the reported 40/64 GiB or add capacity beyond those historical variants.

F differs from failing E in that forcing bundle; the individual roles of the two writes versus the global override have not been isolated. F also retains C's uncached CPU BAR2 request and the later diagnostics, whose necessity and performance cost are not established. Preserve the tested configuration rather than calling it a proven minimal patch. The [exact final E-to-F delta](bar1-forcing-delta.md) includes source fingerprints and attribution.

Three distinct VM restart cycles were used for D/E/F, with one exclusive reset per CMP in each. Other running guests retained their process IDs. No host restart, IOMMU/ACS change, flash, OTP, SM/ECC requalification or intensive memory test occurred. TTS units remain disabled; no manual model restoration was issued. External container recreation remains possible.

## Next useful work

Keep the working F module and recovery artifacts. The fresh [directed peer query](peer-memory.md) still reports zero for all six routes, so P2P is not demonstrated. Prepare an opt-in candidate from F in a separate build directory, preserve native BAR1 policy and the normal platform/topology verdict, and do not reuse the obsolete A-based builder. Any future peer test must distinguish capability, activation, transferred bytes and kernel access.

Extra-capacity and ordinary SM research continue from their own source leads. There is no reason to repeat the completed D/E handoff checks or the failing A–E modules. CMP40's earlier 1350 MHz remains a historical tested point; its current F boot is at 1215 MHz.

[Candidate hashes, diagnostics and explicit limits](../data/driver-candidates.json). Sources: [NVIDIA 615.71.09](https://github.com/NVIDIA/open-gpu-kernel-modules/tree/615.71.09), [pinned fork](https://github.com/admunch888/cmpunlocker/tree/7d86a7f8f4ac3abbd0f48fa6d6cd09aa6b953f03). No proprietary firmware or raw host logs are published here.

## Candidate G: mailbox report isolated from native discovery

G derives from F in a separate tree and keeps the working non-forced BAR1 policy. Both CMPs and Blackwell passed their small checked copies. Overriding only CMP's per-device PCIe report was insufficient: ordinary guest chipset initialization remained unavailable, and all six peer capabilities were zero. No peer enable/copy/kernel ran. See the [source boundary, contradictory prior report and mainboard lead](mailbox-p2p.md) and [curated G record](../data/mailbox-candidate.json). F remains preserved; G adds no memory or SMs.
