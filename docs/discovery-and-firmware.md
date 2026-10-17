# Normal guest discovery and the mainboard BAR settings

**The source exposes two separate discovery boundaries; the relevant mainboard switches are already selected.** Stage47 traced the normal 615.71.09 driver and compared BIOS 1801/1901 offline. It made no driver, clock, resource, firmware or VM change. The last GPU and peer measurements remain those of [candidate G](mailbox-p2p.md).

## Why an uninitialized chipset flag is not a physical-board diagnosis

In `gpuSetupVirtualGuestOwnedHW`, the ordinary detected-HVM path sets `PDB_PROP_PFM_NO_HOSTBRIDGE_DETECT` when it obtains a PCI handle. `objClInitPcieChipset` requires that property to be false before its chipset-initialization block sets `ChipsetInitialized`. An intentionally skipped hostbridge scan is therefore consistent with G's zero flag. The producer branch was not separately runtime-traced; the zero flag alone does not prove a broken physical hostbridge.

The normal hypervisor approval sequence first considers valid peer-clique metadata, then general passthrough approval, and finally the hypervisor callback. General approval requires every device to be passthrough and issues a **fresh physical-RMAPI PCIe capability query**. It does not use the cached per-GPU fields modified by G. The KVM fallback itself returns false. The fresh query's response in that function was not measured here; this is a distinct source boundary, not a new observed firmware rejection.

This explains why the earlier cached override was insufficient without establishing that a modified approval would provide a working data path. No topology, clique identifier, chipset flag or hypervisor verdict was forced. KVM passthrough P2P is not ruled out globally. A future approach still needs a supported resource/mapping mechanism and independent transferred-data checks.

## BIOS comparison and a narrowly scoped live settings read

The correct first-generation ASUS Pro WS WRX80E-SAGE SE WIFI capsules were parsed with pinned LongSoft tools. Of 467 uniquely matched generic UEFI executable sections, 366 are byte-identical and 101 differ. Byte differences may include headers or data and are not evidence of changed behavior. UEFIExtract A75 does not cover AMD-specific images fully, so this is not an exhaustive AGESA/PSP comparison.

The 60,832-byte module containing the PCI setup controls is byte-identical across 1801 and 1901. Decoded English forms from that module and the separate main Setup module are also identical after removing the input-hash header. This establishes unchanged reviewed definitions, not unchanged behavior throughout the firmware.

The original IFR identifies an eight-byte `PCI_COMMON` variable and the two relevant offsets. At **17 October 2026, 11:29:38 UTC**, a read of only that named variable under installed BIOS 1801 found:

| Setting | Byte offset | Stored value | Meaning |
|---|---:|---:|---|
| Above 4G Decoding | 3 | 1 | Enabled |
| Re-Size BAR Support | 4 | 1 | Auto |

No unrelated variables or authentication material were collected. Stored settings do not prove effective device resizing and are not a NVRAM backup. The earlier host snapshot already had a 128-GiB Blackwell BAR1 while both CMPs advertised only 64 MiB; a forgotten global Above4G/ReBAR switch is therefore not the evident explanation. No firmware update or setting write followed.

## Consequences for the next experiment

Do not repeat G unchanged or treat a BIOS update as an established BAR repair. Continue from the actual normal passthrough-approval and mapping contract. The primary capacity investigation remains separate: CMP40 toward 48 GiB is a first target, the external 77.5/72-GiB counterevidence keeps 80 GiB open, and CMP64 toward 80/96 GiB remains a hypothesis.

[Curated hashes, source anchors, tool fingerprints, settings and limits](../data/discovery-and-firmware.json). Original firmware payloads and raw extraction logs stay outside this repository. Source references are listed in [sources](sources.md).
