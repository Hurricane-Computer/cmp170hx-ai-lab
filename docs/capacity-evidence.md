# CMP40 capacity: keep the positive evidence in view

**48 GiB is our first target, not an established physical ceiling. An 80-GiB-class CMP40 remains an open hypothesis.** Current identity decoding suggests 8 GiB per complete stack on the examined card. That is useful evidence, but a trustworthy conflicting capacity result would require us to revisit the decoding, population or differences between boards.

## Three records, three different limits

| Record | What it contributes | What remains unproved |
|---|---|---|
| External 77.5/72-GiB report | Reported positive counterevidence worth pursuing | Exact test implementation and independent reproduction |
| Archived 75–76-GiB `hbm45.cu` report | Full-word pattern and correct global fill/check ordering | Reliability of its unchecked result-copy channel in historical runs |
| Our 20 September 47-GiB experiment | An upper region read correctly while corrupting lower data | Availability under a different mapping or physical absence of more memory |

The [pinned community record](https://github.com/Consensus-Protocol/cmp170hx/blob/d923a25fb2ecb6ee3d62654983f453194b66485f/docs/frontier/80gb.md) reports 310 × 256-MiB blocks, a later 72-GiB pass and severe lifecycle limits. It describes tags in every page, but does not provide the exact checking implementation in the examined documentation tree. We cannot tell whether that means a single tagged word or a completely filled page. The script-driven initialization was followed by a stock-driver handoff; “driverless” does not establish that subsequent data tests bypassed CUDA. These are attributed reports, not this lab's new measurements.

The archived `hbm45.cu`, SHA256 `b0dece433f94394c5a730637dc9ffe09e95e1c3970f5faf4adc809b598c8cb33`, fills and checks every 64-bit word. All fills precede verification. A sparse-tag objection therefore does **not** apply to that implementation. Its separate problem is line70: the host error count starts at zero, and the subsequent device-to-host copy's status is ignored. A failed copy that leaves the destination unchanged can look clean. Earlier synchronization does not certify a later copy. We have not established that this happened in a historical run. The attributed Gist API returned HTTP404 during this audit, so the preserved source was used.

Our earlier coherent-geometry run allocated 47 GiB, leaving 39–41 GiB untouched. The 41–47-GiB view read its own data correctly, while 1–7 GiB had 805,306,368 wrong 64-bit words. Selected low words contained the corresponding upper pattern at word288, byte offset0x900. This proves an alias in that experiment. It does not prove every possible configuration lacks 80 GiB. No GPU run was repeated for this audit.

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

Curated sources, historical limits and reproducible CPU results: [capacity-evidence.json](../data/capacity-evidence.json). No new GiB or SMs were unlocked. Scheduled work remains paused.
