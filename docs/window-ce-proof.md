# Small BAR1 windows: actual CE peer reads in both directions

**Observed on 19 October 2026 at 11:57 UTC:** CMP64 read a checked 1 MiB allocation owned by CMP40, and CMP40 read a checked 1 MiB allocation owned by CMP64. Each GPU Copy Engine (CE) completed a real command through a native, allocation-specific BAR1 window. Every destination word matched. Both cards still had **64 MiB BAR1**; no motherboard BIOS change was needed.

This is a successful bounded device-to-device data path. It does **not** establish ordinary CUDA peer enablement, application/NCCL use, remote SM pointer access, performance, repeated stability or reboot persistence. It adds no HBM capacity or SMs. [Structured observations](../data/window-ce-trials.json) and [test sources](../prototypes/cmp-window/ce132/README.md) keep those distinctions explicit.

## What changed

The earlier [forced-capability experiments](peer-option-trials.md) enabled peer operations but returned wrong data. The [ordinary I/O registration](dynamic-peer-windows.md) and [VMM foreign-access request](vmm-peer-mapping.md) rejected before remote GPU work. Those remain valid results for their particular mechanisms.

This experiment gives a kernel-owned consumer a **real mapping of its particular source allocation**, rather than advertising the whole framebuffer as peer-accessible. It extends the previously compile-only [allocator component](../prototypes/cmp-window/README.md):

1. A single native RM session registers the two actual CMP variants and owns both devices, VA spaces and all test allocations.
2. The owner allocates a contiguous 1 MiB FB buffer. The native aperture allocator maps precisely that allocation, preserving the 36 MiB reserve and requiring a contiguous returned range.
3. An uncached system-address descriptor for that real owner BAR range is mapped through the accessor's native DMA/I/O-VA-space path. Allocation offset, aperture offset, CPU physical address and accessor DMA address remain separate.
4. The caller holds the acquired lease. A real supported non-GR CE reads its returned DMA address as a physical coherent-system source and writes the accessor's own virtual FB destination.
5. A fresh GPU semaphore release with a system flush is checked separately from all destination data. The CE channel is retired/destroyed before the DMA mapping and owner window are released.

No CPU source-to-destination copy stages the peer transfer. The CPU fills the sources and destination sentinel, then reads back and compares all words. Source words combine a fresh nonce with their index; the local-control and owner buffers use different tags. A stale local result or a uniform fill cannot satisfy the peer comparison.

The native mapping calls first passed separate resource-only probes in both directions. API success alone was not treated as a hardware route. The later CE data test supplies that missing observation. It does not trace the exact physical switch/root-port transaction path.

## Separate completion and data results

| Accessor ← owner | Local CE control | Peer CE read | Peer destination comparison | Owner after read | Cleanup |
|---|---:|---:|---|---|---|
| CMP64 ← CMP40 | 64 KiB passed | 1 MiB, fresh GPU completion | 262,144 words, zero wrong | 262,144 words, zero wrong | Lease released; no retained backing |
| CMP40 ← CMP64 | 64 KiB passed | 1 MiB, fresh GPU completion | 262,144 words, zero wrong | 262,144 words, zero wrong | Lease released; no retained backing |

The local control used the same channel and command builder with an owned physical FB source. Its destination check included the untouched sentinel outside the first 64 KiB. Both local source checks passed. The peer destination was refilled with its sentinel before the remote read.

Both peer commands reported no channel error. Session destruction and test-module removal returned success. Neither the guest's selected GPU/kernel-error query nor the host's scoped IOMMU/VFIO/AER fault query found a new selected error. These observations are bounded to the recorded run, not a long-term stability certificate. Some native unmap/free operations return void; they supply no independent hardware cleanup acknowledgement.

The temporary core was loaded from separate files. The established boot G and frozen F remained unchanged. The core inherits G's previously documented [CMP firmware-capability adjustments](mailbox-p2p.md); this experiment adds no general peer-capability success, topology override, I/O-overlap-guard removal or ordinary CUDA/UVM mapping policy. The kernel-only diagnostic selector accepts the owned small cross-CMP allocation and returns the real lease address. It publishes no general external PTEs.

## Mainboard and identical-card questions

The recorded platform is an ASUS Pro WS WRX80E-SAGE SE WIFI with BIOS1801. The stored Above4G and ReBAR settings were already enabled. Each CMP advertised only a 64 MiB supported ReBAR size on the host, and each guest BAR1 was also 64 MiB. Thus the small aperture was not merely a guest clipping of an already-large host resource.

No BIOS update, firmware flash, host IOMMU/ACS change, VM restart or GPU reset was needed for these copies. That establishes that this particular board/configuration can carry the tested peer traffic. It does not rule out resource-allocation or routing effects on a different P2P mechanism, topology or window size.

The successful pair has different reported memory sizes: 40 and 64 GiB, both GA100. Identical capacity was not necessary for this route. The separate [published static-BAR1 CMP report](https://github.com/satspace-cpu/cmp170hx-linux-p2p/blob/main/docs/STATIC-BAR1-P2P.md) uses 64 GiB BAR1 resources and reports both copies and SM reads/writes. That is useful attributed evidence on a different setup, not a benchmark or persistence result for our small-window experiment. Blackwell was not part of this two-CMP guest test.

## Corrected preparation mistakes

- The native passthrough virtualization enum is `UVM_VIRT_MODE_NONE`; an initially used HVM name did not exist. A GPL-only time symbol was also removed in favor of coarse jiffies timing. Both were build-time corrections, before the consumer was loaded.
- Automatic UVM loading raced an explicit module insertion. The already-loaded exact module was verified, and remaining loading continued without another core reload or a VM restart.
- The first CE selection wrongly required `sysmemRead`. NVIDIA defines that bit as an **enhanced-performance hint**, while `sysmem` is transaction support. The card reported supported non-GR engines with `sysmem=1`, `p2p=1`, `sysmemRead=0`. That first attempt sent no copy command. The corrected selection uses real support and treats performance hints as preferences.

The printed polling elapsed times have millisecond granularity and are not latency/bandwidth measurements. An insertion return code is also not the data verdict: the kernel consumer deliberately remains loaded when it must retain live backing after a timeout.

**Application follow-up:** The subsequent [same-model TP/PP tests](model-parallel.md) generated real responses, but every native two-GPU data channel used SHM. They do not yet consume this explicit CE-window route.

## Remaining implementation work

Application-facing external PTE construction and normal UVM teardown/lifetime integration still need implementation and review. The tested caller avoids those unfinished paths by owning every relevant object through CE retirement. It is an experiment, not a general replacement driver.

Follow-up evidence must distinguish external mapping, CUDA capability/activation, actual application copy, SM remote access, repeated operation and post-reboot reproduction. Do not replay forced capability settings or assume the successful explicit CE read makes those separate contracts work.

Native command contracts come from NVIDIA's pinned [Turing CE HAL](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/kernel-open/nvidia-uvm/uvm_turing_ce.c), [Ampere CE HAL](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/kernel-open/nvidia-uvm/uvm_ampere_ce.c), [Turing host submission](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/kernel-open/nvidia-uvm/uvm_turing_host.c), and [RM interface](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/kernel-open/common/inc/nv_uvm_interface.h). Addresses and submission pointers come from those native allocation/channel APIs; no guessed register address is used.
