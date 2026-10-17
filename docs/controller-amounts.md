# Configured memory amount per active controller

At **2026-10-17T18:13:23.684258+00:00**, one bounded read-only observation found uniform configured amounts on each card: **20 active FBPAs at2048MiB on CMP40, and16 at4096MiB on CMP64**. Their sums match the40/64-GiB driver reports. This describes the active configuration; it is not an inventory of extra physical HBM or a full-capacity integrity test.

## Original GA100 source contract

The saved original GA100/key42 constructor trace for physical-memory context class `0x174e21` installs:

| Owner slot | Original target | Role in this analysis |
|---|---|---|
| `0x520` | `0x4a58824` | Register-block address translator |
| `0xbf0` | `0x4a0e758` | Per-controller amount consumer and summation |

This closes the selection that was unresolved in the [preceding address analysis](addressing-vs-size.md). That analysis had searched the separate MemoryManager trace; the existing physical-context trace supplies the matching owner. The trace was reused, not rerun. Static installation is not a capture of production execution.

The amount consumer retains its owner, calls that owner's slot520 with selector1 and relative offset `0x20c`, word-aligns the resulting register address and performs a mapped32-bit read. Its actual arithmetic masks the **lower17 bits** and shifts the unsigned result by20 before summing. Thus the source-derived quantity is `(raw & 0x1ffff)` MiB at `0x90020c + index*0x4000`. This is a GA100-selected original consumer; the [older NVIDIA FBPA note](https://github.com/NVIDIA/open-gpu-doc/blob/master/pascal/gp100-fbpa.txt) is corroboration rather than the sole basis for a field contract.

Other candidates with the same `0x20c` displacement use the previously identified LTC range array. Their address space is different, so they are not treated as this FBPA amount field. No write is inferred from a matching displacement.

## Bounded observation

The current disable mask from the original App08 capture address selected which of the24 architectural FBPA indices could be read. Masked units were skipped. Existing canonical identity/lock checks and the current G module/source-version match preceded the observation. BAR0 pages were mapped with `PROT_READ`.

| Card | Active FBPAs read | Raw word per active FBPA | Decoded MiB each | Sum | Driver report |
|---|---:|---:|---:|---:|---:|
| CMP40 | 20 | `0x800` | 2048 | 40 GiB | 40 GiB |
| CMP64 | 16 | `0x1000` | 4096 | 64 GiB | 64 GiB |

CMP40's skipped indices were12,13,22,23; CMP64 additionally skipped2,3,8,9. The observed CFG1 words were `0x02669000` and `0x02779000`. All36 amount reads returned readable values. Including the two current-mask and two CFG1 reads, there were **40 MMIO reads and0 writes**, with no CUDA allocation, reset, driver change, model start or service interruption.

No unequal amount was observed among the active controllers. The status producer, whether these fields follow configured geometry, and the population/health of masked controllers remain open. This adds no usable GiB, establishes no physical40-GiB ceiling and does not refute the positive75/76-GiB or77.5/72-GiB reports. No H/profile/cache-window replay or new write experiment follows from these values alone.

The [structured extract](../data/controller-amounts.json) records the selected source contract, all36 deliberately curated amount rows, skipped indices, module/payload fingerprints and limits. Original firmware and private access/run logs remain external.
