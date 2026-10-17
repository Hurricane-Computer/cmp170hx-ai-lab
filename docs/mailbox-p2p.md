# Mailbox candidate G and the BAR1 prerequisite

**Changing the CMP-specific firmware capability report did not unlock P2P in this guest.** G initialized both CMPs and Blackwell; all three passed complete 8-MiB random H2D, D2D and D2H comparisons. CMP40 reported 40 GiB / 1215 MHz, CMP64 64 GiB / 1728 MHz. These are small-copy observations, with owned buffers and context references released, not whole-HBM qualification or new capacity.

## What changed and what the test found

G was built in a separate copy of the [working F](driver-candidates.md) source. The frozen F artifacts remain available. Only the CMP per-device PCIe read/write report changed to OK, with diagnostic messages added. The normal mailbox path, BIF defaults, platform, topology and compatibility checks remained. No global ResizableBar override, BAR1 force writes, static-BAR1 patches or host IOMMU/ACS changes were introduced.

Both original CMP firmware reports were status 2, GPU_NOT_SUPPORTED, and both retained `skipChipsetCheck = 0`. The normal code still returned status 5, NOT_SUPPORTED, for each device pair. Its diagnostics show `ChipsetInitialized = 0`, chipset read/write capability 0 and a detected hypervisor. The native early exit precedes topology enumeration. The logged `commonSwitch = 1` is still its initial local value here; it is not evidence of a shared physical switch.

All six directed CUDA capability queries returned API success with capability 0; access and native-atomic attributes were also 0. Therefore no peer activation, copy or remote-pointer kernel ran. A bounded 1-MiB random-data and SM read/write checker was prepared, but remains unexecuted. No transfer failure is invented for this negative-capability result.

Exact G module SHA256: `e020919bb8d6048a1f58a9994947b80576125335365906bb33b0ff40318ab6fe`. Evidence timestamps, source hashes, ordinary-copy hashes and the six directions are in [mailbox-candidate.json](../data/mailbox-candidate.json). There was one controlled guest restart and one exclusive reset per CMP; other running guests retained their process IDs. No automatic model/service restoration followed.

## Why a small buffer does not rescue the static-BAR1 patch

The exact driver source requires both devices to enable static BAR1. Its force-enable case still requires aligned client-visible framebuffer size to fit the mappable aperture; automatic mode additionally includes reservations and padding. The two CMP apertures are currently 64 MiB. A 1 MiB test buffer does not remove that whole-framebuffer prerequisite. This excludes that particular full-static route under the present resource assignment, without ruling out different mapping designs.

## A contradictory external source

The pinned [bayley architecture note](https://github.com/bayley/cmpunlocker/blob/5a7bb4b7e5056306fe49e8b824787659abb19914/docs/ARCHITECTURE.md) describes mailbox P2P with a small BAR1 as working. At the same revision, its [README](https://github.com/bayley/cmpunlocker/blob/5a7bb4b7e5056306fe49e8b824787659abb19914/README.md) reports successful mailbox setup with zero data movement and identifies static BAR1 as its working route. The BAR1 patch is byte-identical to the previously pinned fork's patch. These are conflicting owner claims, not an independently reproduced new 64 MiB method. G distinguishes our guest's earlier native discovery refusal from either external transfer claim.

## Mainboard firmware lead

The host uses an ASUS Pro WS WRX80E-SAGE SE WIFI, first generation, with BIOS 1801 and BMC 1.34. ASUS currently lists BIOS 1901 dated 14 August 2026 and BMC 1.34.0. The BIOS notes describe AGESA ChagallWS PI 1.0.0.E and security changes; no explicit BAR fix is stated. Both 1801 and 1901 vendor packages were downloaded for offline review and matched ASUS's ZIP hashes. No firmware was installed. A downloaded 1801 capsule is not a backup of live NVRAM/settings.

At the host PCI snapshot, all three BAR1 bases were already above 4 GiB. Blackwell had 128 GiB BAR1; each CMP advertised only 64 MiB as its supported ReBAR size. This is evidence that large host address windows already work for Blackwell, not proof that every alternative resource assignment fits. Current UEFI settings were not exported. Mainboard firmware, host resource assignment and the guest driver's missing chipset discovery are separate questions.

Further work should trace ordinary guest chipset initialization or a documented supported mapping path. Do not rerun G unchanged or turn a forced capability into a data-integrity claim. Main capacity targets, including the open 80 GiB CMP40 counterevidence, remain separate.
