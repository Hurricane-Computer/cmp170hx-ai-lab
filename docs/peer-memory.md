# Peer memory: mixed GPUs and the first directed matrix

**Identical cards are not a general CUDA P2P prerequisite.** Support depends on the actual device pair, driver and interconnect. Check each direction independently. Our first matrix advertises no supported route, so it is a baseline for further work, not an impossibility claim.

The latest [working driver candidate F](driver-candidates.md) restores CMP readiness and the 40/64-GiB reports. Its fresh six-direction query still advertises no P2P route. The first matrix below remains tied to its original module and timestamp; the later F observation is separate.

## Observed on 17 October 2026

Three physical GPUs were assigned to one Linux passthrough guest with open driver615.71.09. The initial boot left the CMP64 unable to initialize GSP. One reset confined to its exclusive PCIe branch made it CUDA-visible again. Other running guests retained their process IDs. After that reset it reports **8 GiB at1728MHz**, not the historical64-GiB unlock. CMP40 still reports40GiB at1350MHz. That earlier boot did not reproduce the ordinary 64-GiB unlock; device visibility alone was not that unlock.

The guest labels every pair PHB; the physical GPUs occupy separate CPU root ports. The six `cuDeviceCanAccessPeer` calls all returned success with capability0. The P2P access and native-atomic attributes were also0; management read/write matrices showed NS.

| Accessor \ memory owner | Blackwell | CMP40 | CMP64 variant |
|---|---|---|---|
| Blackwell | — | Not advertised | Not advertised |
| CMP40 | Not advertised | — | Not advertised |
| CMP64 variant | Not advertised | Not advertised | — |

No peer enable, explicit VRAM allocation, peer copy or peer-pointer kernel was attempted after these negative capabilities. The prepared trial uses8-MiB random inputs, checks the full copied output and separately checks a GPU kernel that dereferences peer memory. Neither result is claimed here. A host-staged copy can move data without establishing P2P.

The actual loaded guest module hashes to `3171edbeaea1c43f8b4c9711e45213dd01b986bacc2395fb6d040998a6596881`. Its registry string is empty and it lacks the known fork's CMPUNLOCK_P2P/CMPUNLOCK_BAR1P2P log markers. Both CMP BAR1 resources are64MiB; Blackwell's is128GiB. These observations are consistent with a guest build lacking that opt-in route. Marker absence alone does not audit every instruction or establish that changing settings will succeed. BAR resource size is not extra VRAM capacity.

## A concrete source lead, still untested

The [pinned fork](https://github.com/admunch888/cmpunlocker/blob/7d86a7f8f4ac3abbd0f48fa6d6cd09aa6b953f03/README.md) exposes an explicit P2P build option and includes both CMP device IDs. Its patches change BAR1 mappings, capability reporting and mailbox initialization. This makes it a distinguishable candidate from our present build. The fork describes live `RMForceStaticBar1` and `RMPcieP2PType` settings and warns that a successful copy call can transfer no data when setup is incomplete. We have not installed these patches or settings in this trial.

The same README contains an earlier common-switch requirement and a later owner report across two switches. Neither establishes our separate-root-port topology. The source also includes changes outside CMP-specific branches, so describe and check the actual patch scope before building a test driver. Do not blanket-apply a topology override or confuse an overridden capability with working transfers.

## Supported test context and next step

[NVIDIA's programming guide](https://docs.nvidia.com/cuda/cuda-programming-guide/03-advanced/multi-gpu-systems.html#host-iommu-hardware-pci-access-control-services-and-vms) excludes IOMMU-enabled Linux bare-metal PCIe P2P while supporting IOMMU with VM passthrough. This trial used the guest; no host IOMMU/ACS setting was changed. The [peer API](https://docs.nvidia.com/cuda/cuda-runtime-api/cuda_runtime_api/group__CUDART__PEER.html) defines capability and access per directed device pair.

Next: prepare the exact-release opt-in driver candidate offline, account for both CMP IDs, ordinary memory unlock, BAR1 support and actual topology, then use the already prepared bounded data/peer-kernel check if the configuration advertises a valid route. Keep capability, mapping creation, copied bytes and direct kernel access as separate outcomes. P2P would improve communication; it would not automatically merge all VRAM into one device.

[Curated matrix and source hashes](../data/peer-memory.json). Capacity research and further SM hypotheses continue separately. The scheduled research task was reactivated at the owner's request on17October.

Marker-method correction: Stage42 scanned the compressed module file. Stage43 decompressed it, checked ELF and confirmed the same absent markers. See [corrected hashes and method](driver-candidates.md#marker-method-correction).

## Working F baseline, 17 October 10:28 UTC

F reports CMP40 40 GiB / 1215 MHz and CMP64 64 GiB / 1728 MHz after its small checked copies passed. All six directed `cuDeviceCanAccessPeer` calls again returned success with capability zero; access and native-atomic attributes were also zero. This query allocated no memory, enabled no peer access and attempted no peer copies or kernels. P2P patches remain unapplied. The [separate structured F baseline](../data/peer-memory.json) records the exact module hash. Future work must start from F and preserve its non-forced BAR1 policy.

## Candidate G: per-device report alone is insufficient

The next [bounded mailbox experiment](mailbox-p2p.md) kept F's BAR1 policy and changed only CMP per-device reports. All three small ordinary copies passed, but native chipset discovery in this guest remained unavailable and all six peer directions stayed zero. No peer transfer or kernel ran. Current G and historical F are separately timestamped in the structured data.
