# CMP 170HX AI Research Lab

An evidence-led notebook for CMP 170HX memory, topology, firmware and practical AI experiments. Maintained by Hurricane Computer with AI-assisted analysis.

[Deutsch](README.de.md) · [Current findings](docs/findings.md) · [Experiments](docs/experiments.md) · [Open questions](docs/roadmap.md) · [Sources](docs/sources.md)

## CMP40 memory overclock: 1215 → 1350 MHz

**The highest recorded operating clock of our Samsung 40-GiB CMP 170HX (`10de:2082`) is 1350 MHz, up 11.11% from its original 1215 MHz.** We established the clock input from the card's original cold-initialization code and reached 1242, 1269, 1296, 1323 and 1350 MHz. A short random-data copy check passed at each step. No BIOS flash was involved.

**Research resumed on 17 October: 1350 MHz is a tested step, not an established maximum.** We have not qualified long-term stability, the full HBM address space, bandwidth gain or LLM speed. The setting is volatile. See the [clock method and results](docs/clocks.md) and [curated trial records](data/clock-trials.json).

We do not claim a worldwide first: an [earlier owner's report explicitly describes a 40-GB memory overclock](https://www.reddit.com/r/LocalLLaMA/comments/1wl9amq/reached_189_tbs_memory_bandwidth_overclocking_the/). That external result and its evidence limits are documented separately from our measurements.

A subsequent bounded load observation at 1350 MHz measured **1.53 TB/s** for internal copies and **1.54 TB/s** for an SM streaming kernel, counting reads+writes. All checked outputs matched. See the [90-second load observation and limits](docs/bandwidth-load.md).

## Current status — 17 October 2026

This campaign has not demonstrated additional usable memory above the existing 40/64-GiB baselines, or additional working SMs beyond the owner's established 74-SM baseline. It has produced successful CMP40 clock steps, useful negative results and more precise maps of the original initialization paths.

| Lab variant | PCI device ID | Memory identity, observed earlier | Historical unlocked capacity | Latest guest observation |
|---|---|---|---:|---|
| CMP40 | `10de:2082` | Samsung, density4, 8-High | 40 GiB | Unavailable under candidate B, 17 Oct 09:40 UTC; previously 40 GiB / 1350 MHz |
| CMP64 | `10de:20c2` | SK Hynix, densityA, 8-High | 64 GiB | Unavailable under candidate B, 17 Oct 09:40 UTC; previously 8 GiB / 1728 MHz |

The two variants must not be treated as identical hardware. A reported capacity is not a full-range integrity test. The small clock checks copied 64 MiB; they do not qualify the complete HBM address space. Timestamps describe observations, not a live hardware inventory.

The first [P2P matrix](docs/peer-memory.md) advertised no route among the two CMP variants and Blackwell with the earlier guest module. At that point CMP64 was CUDA-visible after a targeted reset and reported its 8-GiB base configuration; the historical 64-GiB unlock was not reproduced in that boot.

Subsequent [mixed-driver trials](docs/driver-candidates.md) built two concrete candidates, but both CMPs failed their BAR2 initialization test. Only Blackwell is currently NVML-visible in that guest; no new usable-memory or P2P result is claimed.

## What is here

- A [result ledger](docs/experiments.md), including failed approaches and the limits of each conclusion.
- [Memory geometry](docs/memory-geometry.md), [size fields and virtual address spaces](docs/memory-sizing.md), [original firmware paths](docs/firmware.md), and the [clock comparison](docs/clocks.md).
- Sanitized, machine-readable observations under [data/](data/README.md).
- [Methodology](docs/methodology.md), [maintenance rules](MAINTENANCE.md), and a small publication validator.

The principal questions are CMP40 toward 48 GiB, CMP64 toward 80/96 GiB, and further working compute resources. **48 GiB is a first target, not a CMP40 ceiling: the external 77.5-GiB report keeps the 80-GiB hypothesis open.** See the [capacity-evidence audit and CPU counterexample](docs/capacity-evidence.md). These are research targets, not advertised unlocks. We record successful writes, effective topology changes, reported capacity and demonstrated usable capacity separately.

## Validate a contribution

```sh
python scripts/validate_publication.py
```

The validator checks data consistency, local documentation links and common accidental disclosures. It does not access a GPU or execute a driver experiment. New technical records should use the [experiment template](templates/experiment.md).

## Attribution

The existing unlock and many community results originate with their respective authors, notably [amoghmunikote/cmpunlocker](https://github.com/amoghmunikote/cmpunlocker), its forks, [PixelML/club-170hx](https://github.com/PixelML/club-170hx), and the original sources listed in [Sources](docs/sources.md). This lab documents its own observations and analysis; it does not claim authorship of those projects.
