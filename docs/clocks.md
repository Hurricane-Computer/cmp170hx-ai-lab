# Memory-clock observations

## CMP40: 1215 → 1242 → 1269 → 1296 → 1323 → 1350 MHz

The lab's Samsung CMP40 (`10de:2082`, 40 GiB reported) has now operated at five higher memory-clock steps through the original cold-initialization input. The latest observed step is **1350 MHz, 11.11% above the original 1215 MHz**. An upper limit has not been determined.

| Stage | Operating memory clock | Change from 1215 MHz | Short copy-check time, UTC | Result |
|---|---:|---:|---|---|
| 25 | 1242 MHz | +2.22% | 16 Oct 2026, 14:35:28 | 64-MiB random-data roundtrip passed |
| 28 | 1269 MHz | +4.44% | 16 Oct 2026, 15:22:58 | Same limited check passed |
| 33 | 1296 MHz | +6.67% | 16 Oct 2026, 17:23:04 | Same limited check passed |
| 38 | 1323 MHz | +8.89% | 16 Oct 2026, 19:50:31 | Same limited check passed |
| 39 | 1350 MHz | +11.11% | 16 Oct 2026, 20:09:37 | Same limited check passed |

The driver continued to report its original 1215-MHz maximum while the actual memory-clock query showed the higher value. Power limit remained 175 W. Structured observations, matching data hashes and explicit scope are in [clock-trials.json](../data/clock-trials.json).

Each short check used two 64-MiB buffers and a private CUDA context, performed one random H2D → D2D → D2H roundtrip, compared the full returned data by SHA256, then freed the buffers and context. This checks a small transfer at the observed clock. It does **not** establish full-range integrity, long-term stability, measured bandwidth gain or LLM throughput. An 11.11% clock increase is not a measured 11.11% application speedup.

## Separate bounded load observation at 1350 MHz

Stage40 added 30 s of internal copy load and 60 s of SM streaming load at the same 1350 MHz / 175 W point. It measured 1534.8 and 1538.1 GB/s respectively, counting requested reads+writes. All checked 512-MiB outputs matched. This is an absolute single-clock bandwidth observation; no matched stock-clock comparison or long-term qualification was performed. See [method, temperatures and limits](bandwidth-load.md).

## Ordinary input established from original code

Original App08 reads PBUS Scratch13 at `0x1434` in the cold path. A nonzero value replaces the table PLL coefficient at `0x98bc98`; the examined warm path does not consume it. CMP40's original coefficient `0x00012d01` corresponds to N45 / 1215 MHz at the observed 27-MHz reference. Successful steps preserve the other coefficient bytes:

| Coefficient | N | Clock |
|---|---:|---:|
| `0x00012d01` | 45 | 1215 MHz, original |
| `0x00012e01` | 46 | 1242 MHz |
| `0x00012f01` | 47 | 1269 MHz |
| `0x00013001` | 48 | 1296 MHz |
| `0x00013101` | 49 | 1323 MHz |
| `0x00013201` | 50 | 1350 MHz |

The successful trials published one original Scratch13 input immediately after an exclusive card reset while the observed entry gates were pending, then allowed normal initialization with the installed driver. No direct PLL broadcast write or BIOS flash was used. The observed clock and successful copy are the outcome evidence; the input and gate readbacks alone do not prove a particular firmware instruction executed. A general divider format is not claimed.

The setting is volatile and may disappear after a later reset. The current frontier is a tested step, not a maximum-stability recommendation.

## Prior art: no worldwide-first claim

An [earlier original owner report](https://www.reddit.com/r/LocalLLaMA/comments/1wl9amq/reached_189_tbs_memory_bandwidth_overclocking_the/) explicitly describes a 40-GB CMP170HX memory overclock, with reported bandwidth increasing from 1386.2 to 1890.1 GB/s. The accessible text does not supply a PCI-ID / Samsung memory-ID confirmation or a same-card before/after PLL-and-MHz dump. This remains an attributed owner report, not an independently reproduced lab result; its existence is enough that we do not claim to be first worldwide. We do not import its token-rate claims or infer its exact clock from bandwidth.

The linked [170tune project](https://github.com/cachenetics/170tune) recognizes both device variants. Its published [reference measurements](https://github.com/cachenetics/170tune/blob/main/docs/reference-matrices.md) describe a 64-GB card with a 4096-bit bus and 1728-MHz stock setting; they are not a second technical proof for the Samsung 40-GB variant. No exact original-post publication date is inferred from relative page dates.

## CMP64 observations and the A100 comparison

| Observation | Evidence time, UTC | Limit |
|---|---|---|
| 1836 MHz operating in an older NVML query; reported maximum 1728 | 15 Oct 2026, 18:46:48 | Setting pre-existed this campaign; origin unresolved |
| PLL coefficient `0x00014401`, N68 at 27-MHz reference = 1836 MHz | 16 Oct 2026, 16:24:16 | Card was unbound; configured frequency, not an under-load NVML measurement |

Memory-clock MHz alone does not determine total bandwidth; active bus width also matters. With DDR accounting:

| Configuration | Theoretical bandwidth |
|---|---:|
| CMP64: 1836 MHz, 4096 active bits | 1880.064 GB/s |
| A10080 PCIe: 1512 MHz, 5120 bits | 1935.36 GB/s |
| A10080 SXM: 1593 MHz, 5120 bits | 2039.04 GB/s |

These are arithmetic comparisons, not measured kernel bandwidth or LLM throughput. The lab CMP64 uses VBIOS `92.00.6D.00.0A` with the faster 1728-MHz profile, plus the older existing 1836-MHz setting. The slower 64-GiB VBIOS `92.00.67.00.01` has a 1458-MHz profile; that is not this card's current profile.

Manufacturer and stack density are useful first comparisons. Exact speed bins and the origin of the pre-existing overclock remain unknown. No BIOS flash was performed in this campaign. Official A100 clock references and attributed community BIOS observations are listed in [Sources](sources.md).
