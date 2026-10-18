# Upper-window alias after an ordinary cache flush

**An 80-GiB report and a clean upper-window self-check did not mean independent extra storage on this CMP40.** In the completed trial at **2026-10-17T17:31:24.922178+00:00**, the lower window returned 512 KiB of data belonging to the upper window after an ordinary cache flush. Both windows had passed the preceding phase without an explicit flush. This is an observed alias in this configuration, not a physical 40-GiB ceiling or a verdict on other cards.

## Configuration accepted, capacity still unqualified

A separate candidate H copied the working G driver and changed exactly three CMP40 profile constants: CFG `0x02669000` to `0x02779000`, LMR `0x28a` to `0x28b`, and the framebuffer-size input from 40 to 80 GiB. Other initialization, clock, BAR and P2P policies stayed as in G. Native initialization completed; the module fingerprint and loaded source version matched. Readback accepted `0x02779000` at `0x9a0204` and `0x28b` at `0x100ce0`. CMP40 reported 81920 MiB at 1215 MHz; CMP64 retained 65536 MiB at 1728 MHz.

This trial therefore used the paired 28B/80-GiB profile, rather than the earlier inconsistent 28A/80 configuration. Accepted inputs and a successful allocation remain configuration observations. They do not prove physical memory density or new usable capacity.

## Small writes, independent CPU comparisons

One 41-GiB allocation contained a2-MiB lower canary at offset 512 MiB and a512-KiB upper window at 40.5 GiB. The SM fill kernel wrote the lower window first and the upper window second, then synchronized. Each of two finite phases used a fresh random seed and separate window tags. The CPU generated expected 64-bit words independently, checked every D2H return, compared every word and saved hashes. Only 2.5 MiB of distinct locations were written, 5 MiB across both phases; this was not a dense41-GiB test.

The second phase inserted the [documented ordinary cache operation](ltc-cache-commands.md): `FB_FLUSH_GPU_CACHE` (`0x2080130e`), flags `0x38`, returned success while the CUDA context remained alive. There were no direct test MMIO writes or forced cache-command residues. The earlier 40/64-GiB integration baseline was not repeated.

| Phase | Lower 262144 words | Upper 65536 words | Ordinary flush |
|---|---|---|---|
| Without explicit flush | 0 wrong | 0 wrong | not requested |
| With write-back/invalidate | **65536 wrong** | 0 wrong | success |

All 65536 wrong lower words decode exactly as words from the separately tagged upper payload. The source-minus-destination offsets divide evenly into four groups of 16384 words:40 GiB minus `0x900`, minus `0x700`, plus `0x700`, and plus `0x900`. These deltas and saved samples are consistent with an XOR `0x900` swizzle. A complete per-word XOR mapping was not saved or verified, so it is not claimed as a general address formula.

The unflushed/flushed contrast is consistent with cache masking a small aliasing working set. Cache residency was not traced, the phase order was fixed and patterns changed between phases; the experiment does not isolate every possible cause. It does demonstrate that the advertised size and the upper window's successful self-check were insufficient to establish independent backing. The underlying physical-versus-driver/mapping cause remains unresolved.

## Later failure and recovery are separate results

The synchronous data result and all owned-resource cleanup returned success. Roughly six seconds later, a GSP control timeout appeared, followed by a load-access fault and recovery request (Xid119, 1, 154); CMP40's clock query subsequently became unavailable. The exact trigger of this later failure was not established. Successful cleanup must not be presented as continued GPU health.

The retained G modules and saved boot image were restored for a controlled recovery. At **2026-10-17T17:39:59.178273+00:00**, native initialization again reported 40/64 GiB at 1215/1728 MHz. One necessary 8-KiB CMP40 copy returned the expected hash, cleanup succeeded, and the subsequent observation showed no new Xid. Model services were not automatically restored. No H retry or upper-window replay was performed.

## Scope and next step

No additional usable GiB or working SM was demonstrated. This alias result closes this particular H/profile/cache trial; repeating its constants or the old small verifier controls is not a new approach. A further hardware experiment needs a sourced difference in actual address mapping or takeover, not another advertised-size change. The foreign positive 75/76-GiB and77.5/72-GiB reports remain open.48 GiB is a first target, not a proven CMP40 limit.

The [structured extract](../data/cache-alias-trial.json) contains deliberately selected phase counts, hashes, configuration readbacks, source fingerprints, late-failure classification and recovery evidence. Private logs, access material and firmware are not distributed.


The source follow-up separates a [register-address translator and Nouveau sizing routes](addressing-vs-size.md) from actual HBM data mapping. Neither supplies an independent backing proof or a new hardware experiment.


A later [configured amount map](controller-amounts.md) reads the active controllers under G: uniform2/4GiB per FBPA and40/64GiB sums. Masked units and H were not tested again.

## Direct SM read follow-up: small control passes, expanded verdict pending

The actual original Open-GSP H program and later stock CPU-RM H program both launch the SM fill kernel, then obtain their word verdict through checked `cuMemcpyDtoH_v2` and a CPU comparison. Their embedded verifier/publisher definitions are not execution evidence: neither data program launches those kernels. This is a finding about those two executed programs, not every historical test. The API call does not identify a particular physical copy engine.

A new bounded discriminator compares the two patterns with SM global loads **before any large D2H**, then publishes per-thread records directly to mapped host memory. It uses no GPU-local error counter or host atomic. Poisoned records, a fresh nonce, exact per-thread coverage, a complement and a final completion value guard the result after successful CUDA synchronization.

At **2026-10-18T02:21:50.361025+00:00**, one new small G control on CMP40 allocated64 KiB and checked two8-KiB windows. A real injected one-bit error produced exactly one wrong lower word in thread0; all upper words and all other threads were clean. All128 records, checked CUDA returns and cleanup passed. No large D2H was performed. This qualifies that bounded result path, not extra capacity.

The expanded H comparison was prepared for the same41-GiB allocation and2.5-MiB total payload used previously, with an ordinary flush before SM reads and no new geometry values. It **did not execute**. Native warm module insertion stalled; one necessary cold-start attempt then timed out before GPU readiness or the data callback, and normal management became unavailable. Recovery was not verified at this cutoff. This startup failure is not an upper-memory data failure, a diagnosed physical fault or a capacity verdict. CMP64 received no new capacity trial.

The data question therefore remains open. Valid SM mismatches before D2H would rule out an explanation confined to that omitted large D2H operation. An SM pass alone would prove neither additional GiB nor a D2H defect; only then would a same-payload D2H comparison be meaningful, with its sequential cache-state limitation retained. Restore supported access and a known driver state first. The structured follow-up records observed, static and unexecuted parts separately; zero extra usable GiB is claimed.

## Later H startup failure and partial recovery

At a later read-only log observation on **2026-10-18T09:44:16.348207+00:00**, a subsequent guest boot while the preserved H modules were installed had failed native CMP40 initialization. The current-boot record contained RmInitAdapter status`0x62:0x65:2130`, GSP timeout/error classes Xid119 and140, and DRAM ECC error messages. A native status call did not complete. These are initialization/error observations; they establish neither physical memory damage nor a physical capacity ceiling. No new CUDA allocation, copy or upper-window SM comparison executed, and CMP64 received no new capacity trial.

The five owned G module backups matched their recorded hashes and the fixed G core pin. G modules and the saved boot image were restored, target hashes checked, and Depmod/Sync completed before another native status query. The boot-image/config copies retain their earlier copy provenance, without independently recorded historical hash pins. This verifies the boot-file recovery, not the running driver. A necessary guest stop completed; the following G start remained unconfirmed when management command channels stopped answering. No additional manual PCI reset or host reboot was commanded in this recovery. The existing job must be inspected before any further writer or GPU test. Zero additional usable GiB is claimed.


## Later G runtime return and a separate Blackwell reset timeout

At **2026-10-18T10:19:22.490126+00:00**, a fresh guest boot with all saved G boot-file hashes rechecked completed native initialization. The earlier G start command had timed out after 90 seconds; a later host boot was observed, and its cause is unknown. No host reboot was commanded by this work. The old incomplete runtime cutoff above is preserved as history, not the latest state.

Both CMPs passed one necessary 8192-byte random H2D/D2H recovery copy with complete CPU comparison, checked API returns and successful resource cleanup. At **2026-10-18T10:21:15.239179+00:00**, after a 12-second delay, CMP40 still reported 40960 MiB at 1215 MHz / 37 C and CMP64 reported 65536 MiB at 1728 MHz / 30 C, with no clients or new Xid/RmInitAdapter entries in the selected current-boot log. This establishes the bounded G return, not full-capacity qualification, sustained health or extra usable memory. The complete inline wrapper was not retained; the published source fingerprint refers to the common small-copy reference.

A separate previous-boot kernel extract contains repeated FLR not-ready waits ending at a logged 65535 ms and giving up. Fresh PCI identity binds that function to **RTX PRO6000 Blackwell 10de:2bb4**, rather than either CMP. Its current reset_method lists flr then bus. The [Linux PCI sysfs ABI](https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-bus-pci) describes that readback as supported/enabled reset methods in their ordering; it does not demonstrate a successful reset. No reset policy or manual PCI reset was applied.

This supplies a concrete reset-path lead, without establishing the outage/reboot cause or explaining away H's separate CMP40 native initialization errors. A CMP-only next-start configuration is prepared but unexecuted, for a later independently justified start. Releasing the currently assigned Blackwell may itself trigger a reset, so next-start removal is not a proven workaround. It does not justify an immediate restart or unchanged H replay. Preserve the recovered G runtime and require a new initialization/address-backing mechanism before another capacity trial. **Zero additional usable GiB** is demonstrated; foreign positive reports remain open.

## Read-only outage follow-up: repeated reset waits and a fatal processor record

At **2026-10-18T12:06:43.388947+00:00**, preserved logs from both affected host boots had been read without another restart, GPU query or experiment. In the original incident, RTX PRO6000 Blackwell FLR not-ready waits began immediately after the guest stop and before its next start request. The later G stop/start recovery contains the same reset-path symptom. Both host sessions ended without a recorded clean shutdown. BIOS remained at 1801 and BMC at 1.34.0; no firmware update was performed by this work.

The next boot also reported one retained **fatal IA32/X64 processor error** through ACPI BERT. Its selected fields agree between the saved 348-byte record and the native Linux CPER interpretation: uncorrected error, processor context corrupt, MCA bank 5, status `0xbea0000001000108`, IPID `0x000500b000000000`. The generic CPER structure calls it a cache error. The AMD-specific `(HWID 0xb0, MCATYPE 5)` [Linux mapping](https://github.com/torvalds/linux/blob/master/arch/x86/kernel/cpu/mce/amd.c) identifies the Execution Unit; extended error code 0 maps to **Watchdog Timeout error** in the [AMD decoder table](https://code.googlesource.com/linux/torvalds/linux/+/b8910630c967ffee582289451ddb5f9f19c26872/drivers/edac/mce_amd.c). This is a source-derived interpretation of a captured error, not a newly induced fault.

The record has no valid occurrence timestamp. Its next-boot reporting time must not be assigned to the original failure. A fatal processor record and two temporally associated reset hangs strengthen the platform-stall lead, but do not establish which caused which, a defective CPU/GPU, or the cause of the separate management-network interruption. The BMC's old critical-stop entries have unusable 2012 dates and do not settle that chain. No power action or reset workaround was tested. The H native-start errors and the missing expanded-memory verdict retain their previous scope; **zero additional usable GiB** is demonstrated.


## CMP-only follow-up: the SM observes the mismatch before large D2H

The owner requested removal of RTX PRO6000 Blackwell from the guest before continuing the tests. Only that assignment was removed. One graceful shutdown/start returned to G with both CMPs, and each passed a small 8-KiB copy. The first successful transition does not establish that the earlier outage was cured. The now irrelevant RTX-only fan helper was disabled; CMP cooling was unchanged.

The previously unexecuted upper SM discriminator then ran **once**, with Blackwell absent. It reused the preserved H profile and the control-tested PTX, without repeating the small control or introducing new geometry values. A graceful shutdown, one verified exclusive bus reset per CMP and a normal start completed. All seven saved G boot files were restored and hash-checked **before** the first native H status query; live H remained loaded.

There is an identity correction worth preserving: G and H have **identical `srcversion` strings**, so matching that string alone cannot distinguish them. Their ELF GNU build IDs differ. The loaded kernel note matched preserved H during this trial, and preserved G after recovery; file hashes and selected build IDs are in the structured extract. A whole loaded-binary hash was not independently measured.

At **2026-10-18T12:46:52.609326+00:00**, H reported 80/64 GiB and the direct SM comparison used one 41-GiB allocation. It wrote 2 MiB at 512 MiB and 512 KiB at 40.5 GiB, then applied the same ordinary successful flush. Only 2.5 MiB of distinct GPU data was written. Before any large D2H, 128 SM threads compared global loads against independently generated expected words and published 8192 bytes directly to mapped host memory.

| SM comparison | Lower window | Upper window |
|---|---:|---:|
| Words checked | 262144 | 65536 |
| Wrong words | **65536** | **0** |
| Words checked per thread | 2048 | 512 |
| Wrong words per thread | **512** | **0** |

Every record passed the fresh nonce, thread identity, exact coverage, complement and completion checks. A separate offline parser rechecked the saved 8192 bytes and their hash. All checked CUDA and owned-resource cleanup returns were 0, with the result saved at **2026-10-18T12:46:53.431083+00:00**. **No large D2H was performed.** A cause confined to that omitted operation is therefore insufficient. The equal mismatch count agrees with the earlier CPU/D2H result, but this new verifier saved counts, not the actual wrong payload words; it does not establish a complete XOR mapping or identify the faulty physical/mapping layer.

The later status probe encountered an unavailable clock; its wrapper incorrectly assumed an integer and raised on `N/A`. One subsequent raw diagnostic confirmed CMP40 GSP timeouts, Xid 119/154 and a reset-required state. The first selected Xid 119 was **2026-10-18T12:47:06.789937+00:00**, about 13.36 seconds after the completed data result and cleanup, while a native status query was active. That temporal observation does not prove the query caused the fault. This H failure occurred **without Blackwell**, independently of the earlier Blackwell reset-path lead.

One necessary CMP-only G recovery followed: a graceful shutdown/start with one exclusive bus reset per CMP. Both cards passed an 8192-byte random recovery copy with complete comparison and cleanup. At **2026-10-18T12:51:58.588476+00:00**, after a 12-second delay, CMP40 reported 40 GiB at 1215 MHz and CMP64 reported 64 GiB at 1728 MHz; both were idle, with no selected new Xid/RmInitAdapter entries. Host boot and other guest processes were unchanged. The existing CMP64 1836-MHz startup helper had failed its readiness guard, and the final observed clock was 1728 MHz; its policy and guard were not modified. No firmware update, host reboot, IOMMU/ACS change or automatic model restart was performed.

**Zero additional usable GiB** is demonstrated. The bounded SM result closes the missing D2H-only discriminator for this configuration; it does not establish a physical 40-GiB ceiling, full 41-GiB independence or sustained G health. Foreign positive reports stay open. Continue with original FWSEC initialization/address backing and the complete positive-run startup contract; do not repeat this unchanged H/flush/SM trial.

## Separate foreign alias decoder: logical offsets are established

An offline check on 18 October pinned Icyoung's [alias report](https://github.com/Icyoung/cmpunlocker/blob/bb2ae3fe2d8f5e7d6574e2a15311f2589dda33bc/docs/WALL_ALIAS_DECODE.md), [published verifier](https://github.com/Icyoung/cmpunlocker/blob/bb2ae3fe2d8f5e7d6574e2a15311f2589dda33bc/tools/wall_reconfirm.c) and [decoder](https://github.com/Icyoung/cmpunlocker/blob/bb2ae3fe2d8f5e7d6574e2a15311f2589dda33bc/tools/decode_wall_samples.py). This is a separate foreign experiment, not the original 77.5/72-GiB checker or a new test on our cards. The retrieved source is not hash-bound to the historical executable.

Independent integer reconstruction confirmed all five explicitly printed [cross48 examples](https://github.com/Icyoung/cmpunlocker/blob/bb2ae3fe2d8f5e7d6574e2a15311f2589dda33bc/docs/EXPERIMENT_32G_WALL_RESULTS.md): each expected word matches the generator, and each returned word matches a qword-aligned logical source exactly 35 GiB plus `0x900` above the damaged location, inside the reported high write range. These are five scalar consistency checks, not a replay of the claimed complete experiment.

The published verifier checks each synchronous data copy before CPU comparison; its verdict does not depend on a copied GPU error counter. Cleanup returns are outside its PASS decision, and final cross48 PASS does not itself require a zero low-before-high count. The report separately states that this baseline passed. OR-ing bit 63 is not a globally unique high/low mode tag; the five selected words still match the high pattern and its written range.

The pattern encodes **logical byte offsets within one allocation**. Its allocation query prints a virtual range. It supplies no physical page/bank/die map, measured 5-GiB hole or native routing register input. A 35-GiB logical delta with a sub-page tail therefore does not by itself establish a 40-GiB physical decoder equation or select FBPA, FBHub, L2 or a particular HBM die. We do not transfer this foreign formula to our allocation layout. [Curated source hashes and derived offsets](../data/external-alias-contract.json) preserve these limits. No foreign code or hardware test executed; zero additional usable GiB.
