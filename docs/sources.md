# Sources and attribution

## NVIDIA primary material

- [GA100 FLA-VASpace sizing](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/ca2d03e6fafd4d4b56b383497d931c25b283bfcf/src/nvidia/src/kernel/gpu/arch/ampere/kern_gpu_ga100.c#L92), [GSP-client FB region initialization](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/ca2d03e6fafd4d4b56b383497d931c25b283bfcf/src/nvidia/src/kernel/gpu/mem_mgr/mem_mgr_gsp_client.c), and the [memory-manager registry consumer](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/ca2d03e6fafd4d4b56b383497d931c25b283bfcf/src/nvidia/src/kernel/gpu/mem_mgr/mem_mgr.c#L204): separate virtual address space, reported FB and allocator domains.

- [Open GPU kernel modules, pinned revisionca2d03e6](https://github.com/NVIDIA/open-gpu-kernel-modules/tree/ca2d03e6fafd4d4b56b383497d931c25b283bfcf): public register and normal driver interfaces. Public headers do not expose every GA100 topology function.
- [BIOS Information Table](https://nvidia.github.io/open-gpu-doc/BIOS-Information-Table/BIOS-Information-Table.html): BIT-M pointer definitions, separate from the contents of the own original ROMs.
- [A10080 PCIe product brief](https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/a100/pdf/PB-10577-001_v02.pdf), table2:1512-MHz memory clock and native card specification.
- [A10040 PCIe product brief](https://www.nvidia.cn/content/dam/en-zz/Solutions/Data-Center/a100/pdf/A100-PCIE-Prduct-Brief.pdf): original40-GB reference.
- [NVIDIA GTC presentationS22047](https://developer.download.nvidia.com/video/gputechconf/gtc/2020/presentations/s22047-high-performance-next-generation-deep-learning-clusters.pdf): Samsung HBM2/40GB and original A100 context.
- [NVIDIA's SPEC submission](https://www.spec.org/hpc2021/results/res2021q4/hpc2021-20210917-00056.pdf):1593-MHz A10080SXM reference in a DGXA100 system.

## Memory and original reverse-engineering sources

- JESD235C, January2020,§3.2/Table4 and§13.2.3.15/Table99. A readable[mirror of the original standard](https://studylib.net/doc/28046328/hbm2) was consulted; this is not an official JEDEC download. Only derived parameters are retained here.
- [Envytools mem.c, pinned](https://github.com/envytools/envytools/blob/f102b82381f3f11cee113d16374c87091db039d9/nvbios/mem.c#L351): original UNK0D table parser, header/stride/count, no named00/07 payload semantics.
- [Envytools older PFB definitions](https://github.com/envytools/envytools/blob/f102b82381f3f11cee113d16374c87091db039d9/rnndb/memory/g80_pfb.xml): corroborative older row/column fields, not a complete GA100 specification.
- [Nouveau GP100 RAM initialization](https://github.com/torvalds/linux/blob/c7decec2f2d2ab0366567f9e30c0e1418cece43f/drivers/gpu/drm/nouveau/nvkm/subdev/fb/ramgp100.c): a separate RAMMAP path; applicability is not automatically transferred toGA100.
- [TechInsights APE-2108-801](https://www.techinsights.com/products/ape-2108-801): physical A10080PCIe analysis identifying SKHynix memory. This does not identify an exact speed bin for the lab card.
- [TechInsights MFR-2103-804](https://www.techinsights.com/products/mfr-2103-804): Samsung8-Gb memory die analysis from an A100. A die part number is not a full stacked-package speed-bin guarantee.

## Community work and external evidence

- [Earlier 40-GB overclock owner report](https://www.reddit.com/r/LocalLLaMA/comments/1wl9amq/reached_189_tbs_memory_bandwidth_overclocking_the/): explicitly labels the card 40GB and reports increased bandwidth; no independently verified same-card PCI/memory-ID and PLL dump here. This precludes a supported worldwide-first claim by this lab.
- [cachenetics/170tune](https://github.com/cachenetics/170tune) and its [reference matrices](https://github.com/cachenetics/170tune/blob/main/docs/reference-matrices.md): the project recognizes both variants, while the published reference measurements concern a 64-GB card.

- [amoghmunikote/cmpunlocker](https://github.com/amoghmunikote/cmpunlocker), including[the70→74SM commit](https://github.com/amoghmunikote/cmpunlocker/commit/6c442eeb6448b97c803e72b61da344a39e0a26ab).
- [admunch888/cmpunlocker](https://github.com/admunch888/cmpunlocker) and[sekkit/cmpunlocker-latest](https://github.com/sekkit/cmpunlocker-latest).
- [PixelML/club-170hx understanding](https://github.com/PixelML/club-170hx/blob/main/docs/CMP170HX-UNDERSTANDING.md): the author's BIOS, tuning and workload observations; not our measurements.
- [Schaka's BIOS notes](https://github.com/Schaka/170hx-journey/blob/main/BIOS.md): attributed firmware-profile observations, not universal cross-flash compatibility.
- [Consensus-Protocol80GB research archive](https://github.com/Consensus-Protocol/cmp170hx/blob/main/docs/frontier/80gb.md) and[open questions](https://github.com/Consensus-Protocol/cmp170hx/blob/main/docs/frontier/open-questions.md): external evidence and proposals. Coherent-access results are not silently converted into full DMA qualification.

Own original-PROM input hashes and vendor image versions are catalogued in[data/firmware-catalog.json](../data/firmware-catalog.json). Vendor update defaults are not live A100 state. Binaries, private transports and full host logs are not required to understand the curated findings and are kept outside this publication.

## Capacity counterevidence audit

The [pinned 77.5/72-GiB community record](https://github.com/Consensus-Protocol/cmp170hx/blob/d923a25fb2ecb6ee3d62654983f453194b66485f/docs/frontier/80gb.md) is an attributed report with an unreviewed original checking implementation. Archived `hbm45.cu` is separately identified by its source hash in [capacity evidence](capacity-evidence.md); its previously linked Gist API returned HTTP404 during this audit. The CPU counterexample is original lab code and supplies no hardware capacity measurement.

## Peer memory

[NVIDIA multi-GPU guide](https://docs.nvidia.com/cuda/cuda-programming-guide/03-advanced/multi-gpu-systems.html) and [directed peer API](https://docs.nvidia.com/cuda/cuda-runtime-api/cuda_runtime_api/group__CUDART__PEER.html): transfer/context rules and IOMMU scope. The [pinned opt-in fork](https://github.com/admunch888/cmpunlocker/blob/7d86a7f8f4ac3abbd0f48fa6d6cd09aa6b953f03/README.md) supplies source and owner reports, not a lab reproduction; [peer-memory.json](../data/peer-memory.json) records exact source hashes and current test limits.

## Driver candidates

[NVIDIA615.71.09 source](https://github.com/NVIDIA/open-gpu-kernel-modules/tree/615.71.09) and the [pinned mixed-profile fork](https://github.com/admunch888/cmpunlocker/tree/7d86a7f8f4ac3abbd0f48fa6d6cd09aa6b953f03) supplied the build inputs. Download fingerprints, the exact candidate hashes and limited live failure observations are in [driver-candidates.json](../data/driver-candidates.json). A successful build is not device readiness.

[NVIDIA BAR2 root-entry handoff](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/615.71.09/src/nvidia/src/kernel/gpu/bus/kern_bus.c#L831) documents the ordinary CPU/GSP table merge. [Linux device-I/O mapping semantics](https://cdn.kernel.org/doc/html/latest/driver-api/device-io.html) distinguish ordinary and write-combined mappings; they motivated C without establishing a root cause.

The [pinned BAR1 forcing patch](https://github.com/admunch888/cmpunlocker/blob/7d86a7f8f4ac3abbd0f48fa6d6cd09aa6b953f03/driver/patches/bar1-resize-unlock.patch) supplies the E/F comparison target. The [exact tested final delta](bar1-forcing-delta.md) attributes that fork and NVIDIA source; it is not a complete driver distribution.

## Mailbox candidate and mainboard boundary

- [NVIDIA static-BAR1 pair prerequisites](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/615.71.09/src/nvidia/src/kernel/gpu/bus/arch/hopper/kern_bus_gh100.c) and [force/auto size checks](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/615.71.09/src/nvidia/src/kernel/gpu/bus/arch/turing/kern_bus_tu102.c).
- [Native peer capability path](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/615.71.09/src/nvidia/src/kernel/platform/p2p/p2p_caps.c): chipset discovery precedes the ordinary topology and GPU checks.
- [Pinned bayley README](https://github.com/bayley/cmpunlocker/blob/5a7bb4b7e5056306fe49e8b824787659abb19914/README.md) and [architecture note](https://github.com/bayley/cmpunlocker/blob/5a7bb4b7e5056306fe49e8b824787659abb19914/docs/ARCHITECTURE.md): conflicting mailbox claims at the same revision; not our transfer result.
- [ASUS first-generation board BIOS/BMC releases](https://www.asus.com/us/supportonly/pro%20ws%20wrx80e-sage%20se%20wifi/helpdesk_bios/):1901/1801 package references and1.34.0 BMC listing. Firmware binaries remain external.
- [ASUS BIOS manual](https://dlcdnets.asus.com/pub/ASUS/mb/SocketTRX4/Pro_WS_WRX80E-SAGE_SE_WIFI/E18120_PRO_WS_WRX80E-SAGE_SE_WIFI_BIOS_Manual_EM_WEB.pdf): PCI Subsystem Settings, Above4G and Re-Size BAR controls. This is documentation, not a current-settings dump.

## Ordinary discovery and offline setup analysis

- [NVIDIA HVM passthrough setup](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/615.71.09/src/nvidia/src/kernel/gpu/gpu.c#L4938), [chipset initialization](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/615.71.09/src/nvidia/src/kernel/platform/chipset/chipset_pcie.c#L531), [hypervisor approval](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/615.71.09/src/nvidia/src/kernel/virtualization/hypervisor/hypervisor.c#L66) and [KVM callback](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/615.71.09/src/nvidia/src/kernel/virtualization/hypervisor/kvm/kvm.c#L31). Exact inspected file fingerprints and anchors are recorded in the curated data; preserved-F source supplied the unchanged setup function.
- [LongSoft UEFIExtract A75](https://github.com/LongSoft/UEFITool/releases/tag/A75) and [IFRExtractor-RS v1.6.1](https://github.com/LongSoft/IFRExtractor-RS/releases/tag/v1.6.1). Official GitHub asset SHA256 digests matched. The A75 AMD-specific parsing limitation is retained in the interpretation.

The [discovery/firmware note](discovery-and-firmware.md) reports facts derived from the original ASUS capsules and a narrowly scoped live read; it does not distribute firmware or a full NVRAM export.
