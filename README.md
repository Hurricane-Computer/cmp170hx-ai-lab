# CMP 170HX AI Research Lab

An evidence-led notebook for CMP 170HX memory, topology, firmware and practical AI experiments. Maintained by Hurricane Computer with AI-assisted analysis.

[Deutsch](README.de.md) · [Current findings](docs/findings.md) · [Experiments](docs/experiments.md) · [Open questions](docs/roadmap.md) · [Sources](docs/sources.md)

**Status, 16 October 2026:** this campaign has not demonstrated additional usable memory above the existing 40/64 GiB baselines, or additional working SMs beyond the owner's established 74-SM baseline. It has produced useful negative results, a modest CMP40 memory-clock increase, and more precise maps of the original initialization paths.

| Lab variant | PCI device ID | Memory identity, observed earlier | Existing reported capacity | Latest clock evidence |
|---|---|---|---:|---|
| CMP40 | `10de:2082` | Samsung, density4, 8-High | 40 GiB | 1269 MHz operating, 16 Oct 15:22 UTC |
| CMP64 | `10de:20c2` | SK Hynix, densityA, 8-High | 64 GiB | 1836 MHz PLL configuration on an unbound card, 16 Oct 16:24 UTC |

The two variants must not be treated as identical hardware. A reported capacity is not a full-range integrity test. The small clock checks copied64 MiB; they do not qualify the complete HBM address space. Timestamps describe observations, not a live hardware inventory.

## What is here

- A [result ledger](docs/experiments.md), including failed approaches and the limits of each conclusion.
- [Memory geometry](docs/memory-geometry.md), [original firmware paths](docs/firmware.md), and the [clock comparison](docs/clocks.md).
- Sanitized, machine-readable observations under [data/](data/README.md).
- [Methodology](docs/methodology.md), [maintenance rules](MAINTENANCE.md), and a small publication validator.

The principal questions are CMP40 toward48 GiB, CMP64 toward80/96 GiB, and further working compute resources. These are research targets, not advertised unlocks. We record successful writes, effective topology changes, reported capacity and demonstrated usable capacity separately.

## Validate a contribution

```sh
python scripts/validate_publication.py
```

The validator checks data consistency, local documentation links and common accidental disclosures. It does not access a GPU or execute a driver experiment. New technical records should use the [experiment template](templates/experiment.md).

## Attribution

The existing unlock and many community results originate with their respective authors, notably [amoghmunikote/cmpunlocker](https://github.com/amoghmunikote/cmpunlocker), its forks, [PixelML/club-170hx](https://github.com/PixelML/club-170hx), and the original sources listed in [Sources](docs/sources.md). This lab documents its own observations and analysis; it does not claim authorship of those projects.
