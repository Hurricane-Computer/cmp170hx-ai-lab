# Memory-clock observations

| Variant | Observation | Evidence time, UTC | Limit |
|---|---|---|---|
| CMP40 |1215→1242→1269 MHz through ordinary cold-init Scratch13 input |1269 observed16 Oct2026,15:22:58 | Short64-MiB roundtrip only; no full-VRAM or long stability claim |
| CMP64 |1836 MHz operating in older NVML query; reported maximum1728 |15 Oct2026,18:46:48 | Setting pre-existed this campaign; origin unresolved |
| CMP64 | PLL coefficient00014401, N68 at27-MHz reference =1836 MHz |16 Oct2026,16:24:16 | Card was unbound; configured frequency, not an under-load NVML measurement |

## Ordinary input established from original code

Original App08 reads PBUS Scratch13 at0x1434 in the cold path. A nonzero value replaces the table PLL coefficient at0x98bc98; the warm path examined does not consume it. CMP40's original coefficient00012d01 corresponds to N45/1215 MHz. The successful1269-MHz value is00012f01, N47. Other divider bytes were preserved; a general divider format is not claimed.

The1269-MHz result is volatile. A later reset may remove it. The short copy check used two64-MiB buffers, compared a complete random-data SHA256 after H2D/D2D/D2H, then freed buffers and its private context.

## Why the64er can have higher MHz than A10080

MHz is pin rate; total bandwidth also depends on active bus width. With DDR accounting:

| Configuration | Theoretical bandwidth |
|---|---:|
| CMP64:1836 MHz,4096 active bits |1880.064 GB/s |
| A10080 PCIe:1512 MHz,5120 bits |1935.36 GB/s |
| A10080 SXM:1593 MHz,5120 bits |2039.04 GB/s |

These are arithmetic comparisons, not measured kernel bandwidth or LLM throughput. The labCMP64 uses VBIOS92.00.6D.00.0A with the faster1728-MHz profile, plus the older existing1836-MHz setting. The slower64-GiB VBIOS92.00.67.00.01 has a1458-MHz profile; that is not this card's current profile.

Manufacturer and stack density are useful first comparisons. Exact speed bins and the origin of the pre-existing overclock remain unknown. No BIOS flash was performed in this campaign. Official A100 clock references and attributed community BIOS observations are listed in[Sources](sources.md).
