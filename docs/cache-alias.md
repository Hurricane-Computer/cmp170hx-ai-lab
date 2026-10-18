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
