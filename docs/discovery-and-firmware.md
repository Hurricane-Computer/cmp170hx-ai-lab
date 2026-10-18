# Normal guest discovery and the mainboard BAR settings

**The source exposes two separate discovery boundaries; the relevant mainboard switches are already selected.** Stage47 traced the normal 615.71.09 driver and compared BIOS 1801/1901 offline. It made no driver, clock, resource, firmware or VM change. The GPU and peer values quoted in that historical section are the archived [candidate G](mailbox-p2p.md) snapshot; a [later runtime recovery](cache-alias.md#later-g-runtime-return-and-a-separate-blackwell-reset-timeout) is documented separately.

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


## PCI-protocol executable follow-up after the reset timeout

A later offline check of the same pinned capsules extends the equal-form observation. Literal GUID references from the primary [PCI host-bridge resource-allocation](https://raw.githubusercontent.com/tianocore/edk2/master/MdePkg/Include/Protocol/PciHostBridgeResourceAllocation.h) and [root-bridge I/O](https://raw.githubusercontent.com/tianocore/edk2/master/MdePkg/Include/Protocol/PciRootBridgeIo.h) declarations select 14 generic executable bodies in each image. Twelve whole bodies are byte-identical; two differ. Both modules referencing both protocols are unchanged, including the 81,664-byte body containing the name **AMI PCI Bus Driver**. A protocol reference is not proof of a producer, a called reset routine or a particular upstream implementation.

| Focused vendor file GUID | Whole-body bytes, 1801→1901 | Comparison |
|---|---:|---|
|3C1DE39F-D207-408A-AACC-731CFB7F1DD7|81,664→81,664|Identical; contains AMI PCI Bus Driver name|
|80E66E0A-CCD1-43FA-A7B1-2D5EE0F13910|43,520→43,520|Identical; references both protocols|
|8F4B8F82-9B91-4028-86E6-F4DB7D4C1DFF|100,288→100,352|Different executable-section bytes; changed behavior unresolved|
|A062CF1F-8473-4AA3-8793-600BC4FFE9A8|53,504→53,664|Different executable-section bytes; changed behavior unresolved|

The two changed candidates reference root-bridge I/O, but neither a semantic reset change nor a link to the observed Blackwell FLR timeout has been established. The retained generic inventories and capsule pins were rechecked; unsupported AMD-specific regions remain outside this selection. This does not exclude changes elsewhere in firmware. **No verified FLR/BAR fix or additional usable CMP memory follows**, and no setting, firmware, VM or GPU change was made. The comparison does not justify an immediate restart, flash or unchanged H replay; the capacity investigation still needs a distinct initialization/address-backing mechanism.

## Relocation-aware capsule follow-up

A later static comparison examines only the **101 previously byte-different** generic UEFI executable pairs from the saved 1801/1901 extraction. It distinguishes changes in executable code bytes from declared load-address fixups and selected header metadata. The earlier 366 equal whole bodies are inherited evidence, not a repeated discovery.

| Result after the defined comparison | Pairs |
|---|---:|
| Whole extracted body equal after declared fixups and selected header normalization | 70 |
| Code sections equal after fixups, with other bytes still different | 8 |
| Code bytes still different | 23 |

All 101 pairs were parsed. Fourteen of the 23 remaining code-different pairs also change section layout; those changes remain recorded. Ten code-section pairs were already raw-byte equal. This is a byte comparison, not proof that the remaining differences change a particular behavior.

The reader follows the primary [PE/COFF section and base-relocation format](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format) and [EDK II TE header definition](https://github.com/tianocore/edk2/blob/master/MdePkg/Include/IndustryStandard/PeImage.h). It subtracts ImageBase only at declared HIGHLOW/DIR64 fixup slots, skips ABSOLUTE padding, and zeros only ImageBase, the PE COFF timestamp and the PE optional checksum for whole-image comparison. Other bytes are retained. Temporary comparison copies stay in memory; no normalized firmware image or flash payload is produced.

The small `PCI_COMMON`-referencing PEI body `79AA6086-035A-4AD9-A89A-A6D5AA27F0E2` is fully explained by those fixups/header fields. Both previously changed root-bridge-I/O candidates, `8F4B8F82-9B91-4028-86E6-F4DB7D4C1DFF` and `A062CF1F-8473-4AA3-8793-600BC4FFE9A8`, retain code differences. Their reset/resource semantics remain unresolved.

Code-byte equality does not establish identical data-driven behavior, effective BAR allocation or complete AMD/AGESA coverage. **No verified BAR/FLR fix, firmware action or additional usable CMP memory results.** [Structured counts, method and selected vendor-module fields](../data/discovery-and-firmware.json) preserve this scope.
