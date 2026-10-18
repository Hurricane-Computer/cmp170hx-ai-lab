# CMP40 capacity: keep the positive evidence in view

**48 GiB is our first target, not an established physical ceiling. An 80-GiB-class CMP40 remains an open hypothesis.** Current identity decoding suggests 8 GiB per complete stack on the examined card. That is useful evidence, but a trustworthy conflicting capacity result would require us to revisit the decoding, population or differences between boards.

## Different records, different limits

| Record | What it contributes | What remains unproved |
|---|---|---|
| External 77.5/72-GiB report | Reported positive counterevidence worth pursuing | Exact test implementation and independent reproduction |
| Archived 75–76-GiB `hbm45.cu` report | Full-word pattern and correct global fill/check ordering | Reliability of its unchecked result-copy channel in historical runs |
| Our 20 September 47-GiB experiment | An upper region read correctly while corrupting lower data | Availability under a different mapping or physical absence of more memory |
| Recovered owner 70-/78-GiB window tests | Clean small upper windows; larger selected writes expose lower corruption | Whole-allocation independence, original run date and current physical-card identity |

The [pinned community record](https://github.com/Consensus-Protocol/cmp170hx/blob/d923a25fb2ecb6ee3d62654983f453194b66485f/docs/frontier/80gb.md) reports 310 × 256-MiB blocks, a later 72-GiB pass and severe lifecycle limits. It describes tags in every page, but does not provide the exact checking implementation in the examined documentation tree. We cannot tell whether that means a single tagged word or a completely filled page. The script-driven initialization was followed by a stock-driver handoff; “driverless” does not establish that subsequent data tests bypassed CUDA. These are attributed reports, not this lab's new measurements.

The archived `hbm45.cu`, SHA256 `b0dece433f94394c5a730637dc9ffe09e95e1c3970f5faf4adc809b598c8cb33`, fills and checks every 64-bit word. All fills precede verification. A sparse-tag objection therefore does **not** apply to that implementation. Its separate problem is line70: the host error count starts at zero, and the subsequent device-to-host copy's status is ignored. A failed copy that leaves the destination unchanged can look clean. Earlier synchronization does not certify a later copy. We have not established that this happened in a historical run. The attributed Gist API returned HTTP404 during this audit, so the preserved source was used.

Our earlier coherent-geometry run allocated 47 GiB, leaving 39–41 GiB untouched. The 41–47-GiB view read its own data correctly, while 1–7 GiB had 805,306,368 wrong 64-bit words. Selected low words contained the corresponding upper pattern at word288, byte offset0x900. This proves an alias in that experiment. It does not prove every possible configuration lacks 80 GiB. No GPU run was repeated for this audit.

## Original 40-to-48 announcement: a positive workload lead

The [original chemist_slime announcement](https://www.reddit.com/r/LocalLLaMA/comments/1x0rjzb/attn_cmp170hx_10gb_card_owners_unlock_from_40gb/) includes a visually inspected NVIDIA-SMI screenshot showing **49,152 MiB total**, **44,542 MiB used** and `VLLM::EngineCore` using **44,530 MiB**, with 80% GPU utilization. The image displays 7 October 2026 and driver/KMD 615.71.09. These are attributed screenshot values, not this lab's measurements or independently verified post time. The used total is **43.50 GiB**, about 3.50 GiB above 40 GiB; the screenshot does not show all 48 GiB in use.

This is concrete positive allocation/accounting and workload evidence on a card the author describes as originally 10GB. The examined material supplies no generated model output, independently checked expanded-data comparison, exact initialization recipe or named 48GB patch. Neither correctness of the entire allocation nor a false pass is established. The [author's follow-up](https://www.reddit.com/r/LocalLLaMA/comments/1x0rjzb/comment/pene17u/) still describes 48GB as hoped-for. Another commenter suggests the generic cmpunlocker repository; its [pinned README](https://github.com/amoghmunikote/cmpunlocker/blob/2d10f891a58824f0591c3332c4eccf37ff36b086/README.md) documents 40GB/64GB profiles and does not bind that screenshot to a 48GB implementation. This README scope is not a repository-wide absence claim.

Keep this separate from a [different historical report](https://www.reddit.com/r/LocalLLM/comments/1w2x0lp/comment/p6x2l0b/) of approximately 48GB initially usable on a card reporting 64GB. A concrete 48GB change set or original checked run would be useful next evidence. No hardware trial or additional usable capacity resulted from this source audit. [Selected fields and limits](../data/external-48gb-announcement.json).

## Original 32GB variant report: rank and checker contracts remain open

The [original owner discussion](https://github.com/PixelML/club-170hx/issues/48) reports a card limited to 32GB alongside successful 64GB cards. Its attached image shows 32768 MiB and a patched `_kgspBootGspRm` message selecting 32GB geometry with `fbpaDisable=0x00000cf3`. This binds a displayed size and software message; the physical rank label and exact detector condition remain unverified here. The related [PR50](https://github.com/PixelML/club-170hx/pull/50) changes documentation only.

A [second owner](https://github.com/PixelML/club-170hx/issues/48#issuecomment-5740629144) reports clean CUDA tests to “63.5GB” on four cards. The attached image shows four 65536-MiB cards and 64022 MiB used on one, with vLLM accounting for 64010 MiB. It shows workload accounting, not the checker execution or verdict. Keep the positive report while leaving its exact test source and result-transfer contract open. No historical false pass or physical ceiling follows. [Selected image fields and bounded source lookup](../data/external-rank-variant-report.json). No hardware was tested or additional GiB unlocked in this audit.

## A small executable counterexample

Run `python scripts/capacity_method_demo.py`. It uses only the CPU and models 80 logical 4-KiB pages over 40 backing pages. The upper view changes the within-page offset by XOR0x900. This is a synthetic example consistent with one observed offset, **not a reconstruction of the complete GPU decoder**. Each case runs with two seeds.

| Method in this model | Result despite aliased backing |
|---|---|
| One unique word per page; fill all, verify all | All80 tags pass |
| Two tags at offsets0/0x900; fill all, verify all | 80 words fail |
| Full pages with address-dependent words; fill all, verify all | 20,480 words fail |
| Full page fill/check immediately, then next page | All checks pass before later overwrites |
| Original `hbm45` pattern with global fill/check | 20,480 words fail, assuming the result reaches the host |

Independent backing and a plain fold are controls. Fault-injected result-copy cases distinguish `CLEAN`, `DATA_ERROR` and `TRANSPORT_ERROR`; transport failure never becomes success in the checked path. This demonstrates method blind spots, not an actual false pass by the external 77.5-GiB test. Two tags detect this particular example but still do not qualify a whole page's capacity.

## Next useful evidence

Obtain the original 77.5-GiB test code and establish exactly which bytes were filled, whether all regions stayed allocated, whether all writes finished before any final verification, and how completion and errors reached the host. A future capacity test should use independent address-dependent data throughout the tested range, recheck lower canaries after upper writes, check every API/synchronization/result transfer, and report transport failures separately. Sparse probes and allocation success remain leads rather than capacity proofs.

Curated sources, historical limits and reproducible CPU results: [capacity-evidence.json](../data/capacity-evidence.json). This audit was completed during the 16 October pause; scheduled research resumed on 17 October. No new GiB or SMs were unlocked by the audit.

## Recovered checker files, 17 October follow-up

A separate [pinned primary report](https://gist.github.com/sekkit/b30da03773768d0cd4e3de18e0619656/2f65500f3c81609f7d46522b1c7df5dea16dd5c6) includes `hbm45.cu`, `hbmh2d.cu` and `hbmstage.cu`. Its kernel checker matches the archived source after newline normalization, retaining the unchecked result-copy return. The attributed 75/76-GiB successes remain positive counterevidence; a historical false pass has not been demonstrated. This is not recovery of the separate original 77.5/72-GiB checker.

Both copy programs allocate every chunk before their first fill copy. Their reported failure during write progress therefore does not isolate an allocation-time threshold. A first-allocated staging buffer also does not establish its physical FB address. No program or CPU counterexample was rerun. [File hashes and scoped observations](../data/capacity-evidence.json) preserve the comparison.

## Matching-version comparison and new small GPU controls

The [next follow-up](capacity-followup.md) checks the principal old configuration against our historical coherent80 trial, maps the repeated fault in matching original 610.43.03 firmware, and records 12 new small GPU verifier controls across both CMPs. The controls distinguish clean from deliberately wrong data and agree over two checked verdict paths. They are not a new high-capacity result.

## Recovered owner window tests

Five preserved outputs recover a more precise version of our own large-allocation history. These are **historical records audited on 17 October**, not new GPU runs. The checker source uses checked launches, synchronization and D2H copies; it compares every returned 64-bit word on the CPU. All low windows are filled and checked before upper writes, then rechecked afterwards.

| Allocated | Unique selected bytes written | Lower wrong 64-bit words after upper writes | Upper self-check |
|---|---|---|---|
|70 GiB|14 MiB|0|Clean|
|70 GiB|1,600 MiB|81,668,976|Clean|
|78 GiB|16 MiB|0|Clean|
|78 GiB|1,792 MiB|106,834,960|Clean|
|41 GiB|3 MiB|0|Clean|

The 78-GiB light test includes a checked 1-MiB window starting at 77 GiB. That is real selected-window readback evidence. Both larger-footprint tests nevertheless find upper-pattern words in lower windows. Their first reported example pairs a lower word at 0.5 GiB with upper data from 40.5 GiB+0x900, consistent with the earlier observed offset. Clean upper readback therefore coexists with lower corruption in these records.

Cache residency is a plausible **unproved explanation** for the small-window difference. NVIDIA's [PTX contract](https://docs.nvidia.com/cuda/parallel-thread-execution/#cache-operators) allows L2 caching for the checker's `st.cg` stores. The [A100 whitepaper](https://images.nvidia.com/aem-dam/en-zz/Solutions/data-center/nvidia-ampere-architecture-whitepaper.pdf) documents 40 MB L2 as architecture context. Neither establishes actual cache residency in these runs. The small and larger tests also used different boots and allocations, so this is not an isolated cache experiment.

The archived runners pin a common executable hash; exact source-to-executable build provenance and a binding to either currently installed physical card are not re-established here. [Selected ranges, counters, source fingerprints and limits](../data/legacy-window-evidence.json) retain the useful evidence without publishing raw logs. These own records neither prove an 80-GiB mapping nor establish a physical 40-GiB ceiling, and do not dispose of the separate foreign 77.5/72-GiB reports. If a distinct expanded mapping becomes available, bounded future checks should record the active footprint/cache condition and preserve lower canaries; these old mappings need no unchanged replay.


## The separate 75-GiB raster record

Another preserved owner output declares a 75-GiB cap and allocates 73.875 GiB. It completes two globally ordered passes over 68 lower/upper pairs, spaced every 512 MiB with a 40-GiB separation. Each window is 64 KiB. All 408 window-check records visit every selected word and report zero mismatches; the upper starts extend through 73.5 GiB. The preserved source checks kernel launch, synchronization and D2H status, and uses a second pass with inverted payloads and new tags.

Across both passes the **distinct written footprint is only 8.5 MiB**; repeated writes total 17 MiB and checked readback totals 25.5 MiB. These are positive sparse observations, with the same unresolved cache-residency question as the small window tests. The attempted 1-MiB variant returned `cuInit` error100 before allocating or writing anything. It is neither a failed data test nor a memory-size threshold.

[Selected configuration, ranges, counters and source hashes](../data/legacy-window-evidence.json) preserve this record. Its original execution date and binding to a currently installed physical card remain unestablished. It is a separate own checker, not the foreign full-word `hbm45` implementation or the still-sought original 77.5/72-GiB test. No historical run was replayed.

## Named checker leads, 17 October follow-up

The [pinned artifact catalogue](https://github.com/Consensus-Protocol/cmp170hx/blob/d923a25fb2ecb6ee3d62654983f453194b66485f/docs/appendix/artifacts.md) names `check_fold.py` and `cuda_dbg.py`, explicitly marking both as not archived files and distributed outside the repository. It describes a page-index PTX check and a separate sparse alias probe. These are concrete search leads, not recovered implementations or proof that either is the exact 77.5/72-GiB checker. Targeted searches have not recovered that source; the positive reports remain open. [Selected catalogue fingerprint](../data/peer-option-followup.json).
