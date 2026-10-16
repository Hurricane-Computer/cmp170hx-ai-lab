# Original startup inputs to memory sizing

Code and global-data addresses on this page are virtual addresses in the original firmware image, not PCIe MMIO offsets or a register-write procedure.

## The writer's runtime condition is connected

The [previous size-field analysis](memory-sizing.md) reached a genuine writer guarded by MemoryManager+`0x2d4`. A conditional branch alone does not establish that this is an unused fallback or a virtual-only path.

The original creator call at `0x45bbd74/78` explicitly supplies **a7=4** to `0x533fbb8`. That creator preserves the value and passes it as a5 to original initializer `0x533f60c`. The initializer installs the original RmHalspecOwner metadata at GPU+`0x58`; for input 4 it writes **HAL index3** at owner+`0x10`. The owner identity comes from original class `0x34a6d6` and NVIDIA's pinned [class definition](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/ca2d03e6fafd4d4b56b383497d931c25b283bfcf/src/nvidia/generated/g_gpu_halspec_nvoc.h#L86), not a modern offset transferred into the binary.

The MemoryManager creator queries that exact owner class and passes it to data initialization. A strict CPU-only evaluation of the connected **GA10042/RM3** case completes in 127 original instructions and sets **MemoryManager+0x2d4=1** at `0x5382564`. No unknown argument or memory values are silently supplied. The evaluated program makes no calls or I/O accesses.

This connects the original creator's runtime configuration to the guard. It is not a live execution trace, and no modern public name is assigned to the original key3/input 4. The condition is not an identified HBM-density fuse.

## The two parameters now have an upstream source

The genuine size writer receives its inputs from original globals `0x4397ec8` and `0x4397ed0`. Routine `0x5503284` copies both from a buffer at **`0x43b6b68`**. Earlier it passes that same buffer to the unchanged ECALL at `0x5503348`, with **raw argument `0x100`**, and checks the return status. Other initialization calls occur between the ECALL and the copies; their complete side effects are not closed:

| Original buffer field | Connected global | Downstream use |
|---|---|---|
| `+0xb0`, loaded at `0x5503474` | `0x4397ec8`, store `0x5503480` | a2; rounded into the real `+0x6a0/0x6a8` size fields |
| `+0x58`, loaded at `0x5503484` | `0x4397ed0`, store `0x5503490` | a3 in the same guarded initializer |

The exact unchanged ECALL register inputs are retained in [curated data](../data/startup-memory.json). This establishes the buffer-to-global-to-size-field connection and the earlier call's use of the same buffer. It does not prove that the ECALL alone wrote these fields or returned 256 bytes. The service, buffer direction, complete record schema and intervening calls remain open. A known host boot structure with similarly placed fields would not establish identity.

The intervening calls are now reduced to twelve specific sites and two helper targets: one wrapper makes ECALL `0x54ee2e4` with t0=7, and eleven calls use a record helper with ECALL `0x54ee4f8`, t0=5. Their explicit record arguments and visible stores refer to other nonoverlapping records. This bounds the remaining question; it does not establish that the ECALLs or every implicit alias are harmless to the source buffer.

An aligned pointer in the original ELF `.manifest` at `0x4012748` references this producer. The outer ELF entry is `0x4009000`. Without the complete manifest/dispatcher contract, the pointer is retained as an entry candidate rather than proof that this routine was invoked at a particular startup stage.

## A concrete metadata-layout candidate

The complete official [GspFwWprMeta layout](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/ca2d03e6fafd4d4b56b383497d931c25b283bfcf/src/nvidia/arch/nvalloc/common/inc/gsp/gsp_fw_wpr_meta.h) is exactly `0x100` bytes. Seven visible accesses in the original producer fit that layout, including the two halfword widths:

| Original offset | Width | Member in the legacy public layout |
|---|---|---|
| `+0x58` | 8 | `gspFwRsvdStart` |
| `+0xa0` | 8 | `frtsSize` |
| `+0xa8` | 8 | `gspFwWprEnd` |
| `+0xb0` | 8 | `fbSize` |
| `+0xd0` | 8 | `partitionRpcAddr` |
| `+0xd8` | 2 | `partitionRpcRequestOffset` |
| `+0xda` | 2 | `partitionRpcReplyOffset` |

The four first fields are shared by [GspFwWprMetaV1](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/ca2d03e6fafd4d4b56b383497d931c25b283bfcf/src/nvidia/arch/nvalloc/common/inc/gsp/gsp_fw_wpr_meta_v1.h). Its `+0xd0..+0xdf` bytes are reserved, so the partition-field names apply to the legacy type only. The original flow tests `+0xd0` before consuming the two halfwords; this also fits their documented relationship. The visible base remains the same buffer under the ordinary callee-saved calling convention.

This is a stronger structural candidate than two isolated offsets. It still does not independently establish the original record type, service ABI, header-version equivalence or actual returned byte count. The metadata header's diagram describes `fbSize` as the framebuffer end and `gspFwRsvdStart` as a reservation boundary below it; they are not two independent physical-density readings.

The pinned public [host metadata constructor](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/ca2d03e6fafd4d4b56b383497d931c25b283bfcf/src/nvidia/src/kernel/gpu/gsp/arch/turing/kernel_gsp_tu102.c#L619) obtains `fbSize` through `kmemsysGetUsableFbSize_HAL` and calculates `gspFwRsvdStart` from the heap layout. That version uses V1. Its generated GA100 dispatch selects `kmemsysReadUsableFbSize_GP102` through the normal kernel getter. These public counterparts provide the next ordinary size-source target; they are not a completed bridge into the original buffer or a new physical-memory-enable mechanism.

## Earlier constructors were bounded separately

The original early MemoryManager hook creates eight indexed software children of size `0xf0`. They are not eight discovered HBM stacks. The selected early constructor of original class `0x174e21` prepares configuration lists and has four selected return0 callbacks. Neither followed constructor supplied another connected memory-region producer.

The examined data-initializer bodies have no calls; the MemoryManager body was additionally bounded by its complete reachable control flow. That excludes an unseen delegated initializer in that body, not direct stores or sources in other initialization stages.

## What remains open

The public GA100 reader and exact-release metadata counterpart have now been followed: see [Configured size and region accounting](usable-size.md). The original buffer's service/type identity and the ordinary physical-geometry origin remain open. Their relationship to populated, enabled and trained HBM must be established before deriving a geometry experiment. The connected software parameters are not evidence that raising them creates backing storage.

Results on this page are static analysis of the unchanged original firmware and pinned public source counterparts. No hardware access, capacity gain, new working SM, reset or clock change was performed for this stage.
