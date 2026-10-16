# Evidence and methodology

## Claim levels

| Label | Meaning |
|---|---|
| `observed` | A particular value or behavior was recorded at the stated time. |
| `static-analysis` | A property was derived from the identified, unchanged source or firmware image. |
| `owner-established` | An existing baseline supplied by the hardware owner; not requalified during this campaign. |
| `theoretical` | Arithmetic based on stated inputs; not a measured workload result. |
| `third-party` | An attributed external report, not our own experiment. |
| `hypothesis` | A possible explanation that is not established by current evidence. |

## What proves what

A register readback proves what that access returned. It does not by itself prove a physical resource was enabled. A driver showing80 GiB is not evidence that80 GiB stores independent data. A64-MiB roundtrip proves that particular short transfer, not full-range integrity, training stability or long-term reliability.

For an additional-capacity claim, record the effective topology, address mapping, actually allocated range and an appropriate data-independence/integrity check. Bound the claim to the tested range and transfer method. Never silently turn CPU-coherent access into a DMA result, or a remote author's result into a lab measurement.

For an additional-SM claim, distinguish enumeration from actual independent execution. The owner's74-SM baseline is accepted; this campaign did not repeat that qualification. CUDA SMID values can have gaps and NSMID is an identifier-space size, not an active-SM count.

Host reads can differ from privileged firmware observations. A host-side zero is not a general proof of zero in every access context. Static control flow says what a branch would do with specified inputs, not that a past boot took that branch.

## Scope of this campaign

Experiments use the owner's test environment under explicit session authorization. They have used volatile settings and test drivers. No BIOS flashing, OTP programming or intensive full-VRAM stress was performed in this campaign. These project boundaries are not a universal statement about every possible hardware method.

Ordinary configuration, source analysis and undocumented field hypotheses remain separate. A numerical resemblance or a familiar field name from another GPU generation is insufficient to invent a write address.

## Evidence availability

This repository contains curated technical extracts and source hashes. Original private working logs and firmware inputs remain separate; they are not claimed to be fully published here. Independent reproductions should state their own board, software versions, methods and results. Original notes and aggregate data are licensed under the repository license; third-party material retains its original rights.
