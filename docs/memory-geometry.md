# HBM geometry and the48/80/96-GiB questions

## Identity-derived organization

Historical DEVICE_ID packets, linked to the ordinary original App08 reader, give the following organization. They were not repeatedly re-read during later offline studies.

The source connection is now precise: the normal command is DEVICE_ID `0x0e`, with an 82-bit response. Original App08 transfers three unmodified port DWORDs into its reply buffer and extracts density, height and manufacturer before comparing ROM records. The separate D1575 byte is derived from the selected ROM record; it is not the origin of those raw identity fields. Thus the historical density evidence is stronger than a chosen profile alone, while remaining a controller-interface response rather than an independent package inventory. Disabled-port population, exact memory part numbers and extra usable capacity remain unproved.

| Variant | Manufacturer | Density | Height | Rows | Capacity per complete stack |
|---|---|---:|---|---:|---:|
| CMP40 | Samsung |4 |8-High |14 bits |8 GiB |
| CMP64 | SK Hynix |A |8-High |15 bits |16 GiB |

The row organization follows the HBM2 standard for those density codes. In8-High organization, SID participates in bank addressing and is already included in the full capacity. It is not an uncounted extra rank.

For density4, the accounting is:

`2^14 rows × 2 SID choices × 16 banks × 1 KiB per pseudochannel page × 2 pseudochannels × 8 channels = 8 GiB`.

DensityA has one further row bit and gives16 GiB. At these identified densities,48 GiB requires six8-GiB-stack-equivalents;80/96 GiB requires five/six16-GiB-stack-equivalents. These are conditional accounting models, not observations of additional physical packages. They are not a reason to discard the external 77.5/72-GiB positive report. Independently validated dense results would require revisiting the density interpretation, population or board differences; the exact external test remains unavailable. See the [capacity-evidence audit](capacity-evidence.md).

## Controller fields and limits

The historically unlocked CFG1 values are02669000 forCMP40 and02779000 forCMP64. Interpreting the row fields using older public controller definitions yields14/14 and15/15, consistent with the identified full density. This row interpretation is corroborative; the older definitions are not a complete published GA100 register specification.

An independent part of original App01 reads CFG1[25:24] and selects4/8/16 banks, and uses CFG0bit2 as a factor1/2. All192 examined original matrix profiles have that bit clear. The ordinary profile selector is already part of the known unlock. A larger reported geometry alone would not create more independent storage.

## What the App01 bank/rank calculation produces

The already known CFG0/CFG1 decoder belongs to the normal RRL action: schema index8 calls original App01 `0x3d20` at `0x141f`. This 218-instruction routine filters 20-byte RRL records by the raw FBPA mask. Its bank/rank factors initialize **N = 48 × bank factor × rank factor**, then a fixed 1536-position scan classifies packed four-bit values. It writes a validity byte and 16-bit histogram counters at shared-result offsets `+0x72..+0x7d`.

This is a geometry-dependent status count, not a byte/GiB calculation or VRAM address test. The direct caller does not use the return as a size. The 21 previously decoded local query descriptors do not overlap these counters; their offsets are bytes, despite an older private label suggesting words. A further downstream consumer is not established. No new capacity experiment follows from this bounded result.

Curated provenance and limits: [geometry-inputs.json](../data/geometry-inputs.json).

## Partition and script tables

BIT-M-v2+0x0d points to the Memory Partition Information Table. The exact table is identical across both own CMP originals and ten vendor A100/A800 update images:

`10040206 0007 0007 0007 0007 0007 0007`

Version0x10, header4 bytes, record2 bytes, count6: total16 bytes. The original envytools parser calls the payload UNK0D. The bytes00/07 are not assigned a speculative enable-mask meaning. Neighbouring bytes are not part of this table.

BIT-M+0x11 (Memory Script List) and BIT-P-v2+4 (RAMMAP) are zero in all twelve images. This closes those existing-script avenues; it does not prove that all private initialization mechanisms are absent.

## Remaining question

A meaningful new capacity experiment needs a documented or concretely traced producer/adoption point that changes effective physical availability. The six-record table, existing profile columns, an extra address bit, or copied A100 defaults do not establish such a producer.

Sources: JESD235C§3.2/Table4 and§13.2.3.15; NVIDIA's public BIT specification; unchanged original App01/App08 code; pinned envytools parser. Full links and provenance limits are in[Sources](sources.md).

## Configured FBP and L2 geometry measured on 17 October

At 14:07 UTC both CMPs answered 28 targeted ordinary FB/GR GET queries under the retained 615.71.09 test driver. All returned success, and both temporary RM root handles were freed. No compute channel, CUDA allocation, direct MMIO access, SET control, clock change or reset was used.

| Variant | Reported active FBPs | Reported active FBPAs | Reported LTCs | Reported L2 slices |
|---|---:|---:|---:|---:|
| CMP40 | 10 | 20 | 20 | 80 |
| CMP64 | 8 | 16 | 16 | 64 |

Both report architectural dimensions of 12 FBPs, 24 FBPAs and 24 LTCs, with two FBPAs/two LTCs per FBP and four slices per LTC. The pinned GA100 [hwproject definition](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/common/inc/swref/published/ampere/ga100/hwproject.h) also defines the architectural 24-FBPA count. An architectural dimension is not proof that every disabled unit is healthy or can be enabled.

| Variant | Reported FBP mask | Reported FBPA mask | Reported LTC mask |
|---|---|---|---|
| CMP40 | `0x7bf` | `0x3fcfff` | `0x3fcfff` |
| CMP64 | `0x7ad` | `0x3fccf3` | `0x3fccf3` |

Mask popcounts agree with the reported counts. In each case, LTC count equals active FBP count times the reported two-LTC width, and slice count equals LTC count times four. Expanding each set FBP bit into two consecutive set bits also reproduces the LTC mask; this is numerical consistency, not independent proof of physical wiring.

The reported configuration therefore shows no partial-LTC deficit that would motivate the older mixed-memory hypothesis. NVIDIA's older [GP100 FBPA note](https://github.com/NVIDIA/open-gpu-doc/blob/master/pascal/gp100-fbpa.txt) discusses such coverage differences; its split-address programming is not established for GA100 by this measurement. We did not set its mixed-memory bit or probe a presumed upper physical address.

These are driver-reported configured units, not independently counted HBM packages or a test of extra capacity. They establish neither a physical 40/64-GiB ceiling nor a failure of the attributed 75/76 and 77.5/72-GiB reports. [Selected results, derived checks and exact source hashes](../data/configured-memory-geometry.json).
