# CMP 170HX AI Research Lab

An evidence-led notebook for CMP 170HX memory, topology, firmware and practical AI experiments. Maintained by Hurricane Computer with AI-assisted analysis.

[Deutsch](README.de.md) · [Current findings](docs/findings.md) · [Experiments](docs/experiments.md) · [Open questions](docs/roadmap.md) · [Sources](docs/sources.md)

## CMP40 memory overclock: 1215 → 1296 MHz

**Our Samsung 40-GiB CMP 170HX (`10de:2082`) now operates at 1296 MHz, up 6.67% from its original 1215 MHz.** We established the clock input from the card's original cold-initialization code and reached 1242, 1269 and 1296 MHz. A short random-data copy check passed at each step. No BIOS flash was involved.

**Exploration is ongoing: 1296 MHz is a tested step, not an established maximum.** We have not qualified long-term stability, the full HBM address space, bandwidth gain or LLM speed. The setting is volatile. See the [clock method and results](docs/clocks.md) and [curated trial records](data/clock-trials.json).

We do not claim a worldwide first: an [earlier owner's report explicitly describes a 40-GB memory overclock](https://www.reddit.com/r/LocalLLaMA/comments/1wl9amq/reached_189_tbs_memory_bandwidth_overclocking_the/). That external result and its evidence limits are documented separately from our measurements.

## Current status — 16 October 2026

This campaign has not demonstrated additional usable memory above the existing 40/64-GiB baselines, or additional working SMs beyond the owner's established 74-SM baseline. It has produced successful CMP40 clock steps, useful negative results and more precise maps of the original initialization paths.

| Lab variant | PCI device ID | Memory identity, observed earlier | Existing reported capacity | Latest clock evidence |
|---|---|---|---:|---|
| CMP40 | `10de:2082` | Samsung, density4, 8-High | 40 GiB | 1296 MHz operating, 16 Oct 17:23 UTC |
| CMP64 | `10de:20c2` | SK Hynix, densityA, 8-High | 64 GiB | 1836 MHz PLL configuration on an unbound card, 16 Oct 16:24 UTC |

The two variants must not be treated as identical hardware. A reported capacity is not a full-range integrity test. The small clock checks copied 64 MiB; they do not qualify the complete HBM address space. Timestamps describe observations, not a live hardware inventory.

## What is here

- A [result ledger](docs/experiments.md), including failed approaches and the limits of each conclusion.
- [Memory geometry](docs/memory-geometry.md), [original firmware paths](docs/firmware.md), and the [clock comparison](docs/clocks.md).
- Sanitized, machine-readable observations under [data/](data/README.md).
- [Methodology](docs/methodology.md), [maintenance rules](MAINTENANCE.md), and a small publication validator.

The principal questions are CMP40 toward 48 GiB, CMP64 toward 80/96 GiB, and further working compute resources. These are research targets, not advertised unlocks. We record successful writes, effective topology changes, reported capacity and demonstrated usable capacity separately.

## Validate a contribution

```sh
python scripts/validate_publication.py
```

The validator checks data consistency, local documentation links and common accidental disclosures. It does not access a GPU or execute a driver experiment. New technical records should use the [experiment template](templates/experiment.md).

## Attribution

The existing unlock and many community results originate with their respective authors, notably [amoghmunikote/cmpunlocker](https://github.com/amoghmunikote/cmpunlocker), its forks, [PixelML/club-170hx](https://github.com/PixelML/club-170hx), and the original sources listed in [Sources](docs/sources.md). This lab documents its own observations and analysis; it does not claim authorship of those projects.
