# Memory-size fields and virtual address spaces

## The original 128-GiB sizing getter

The original GA100 method at GPU slot `0x230`, entry `0x4b78e14`, has the same distinctive short calculation as NVIDIA's named [gpuGetFlaVasSize_GA100](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/ca2d03e6fafd4d4b56b383497d931c25b283bfcf/src/nvidia/src/kernel/gpu/arch/ampere/kern_gpu_ga100.c#L92). The public function scales total framebuffer size from MiB to bytes, returns 128 GiB when the virtualization argument is set or total FB is at most 64 GiB, and otherwise returns twice total FB. The original code follows the same numerical pattern.

The public function specifies **FLA virtual address-space size**. A 40-GiB or 64-GiB framebuffer therefore produces a 128-GiB return value in this separate calculation. That return does not demonstrate additional physical HBM.

| Input total FB | FLA address space, ordinary branch | With NVSwitch virtualization |
|---:|---:|---:|
| 40 GiB | 128 GiB | 128 GiB |
| 48 GiB | 128 GiB | 128 GiB |
| 64 GiB | 128 GiB | 128 GiB |
| 80 GiB | 160 GiB | 128 GiB |
| 96 GiB | 192 GiB | 128 GiB |

These are **function evaluations**, not new card measurements. The semantic correspondence uses the complete short branch/scaling pattern and the independently established original GA100 method installation. It is not a name assigned from a current header offset or a recovered debug symbol.

The original function loads a child pointer at `OBJGPU+0x1e80`, then a sizing field at child offset `0x6a0`. The public counterpart names `MemoryManager.Ram.fbTotalMemSizeMb`. The original child-class connection is now independently traced below. Its normal physical-size source remains open; a separate guarded parameter writer is connected below. The modern C-structure layout is not transferred to the binary.

## Distinct framebuffer sizes in the ordinary GSP client

NVIDIA's [ordinary GSP-client region initializer](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/ca2d03e6fafd4d4b56b383497d931c25b283bfcf/src/nvidia/src/kernel/gpu/mem_mgr/mem_mgr_gsp_client.c) distinguishes these domains:

| Value | Source in that path | Interpretation |
|---|---|---|
| `fbTotalMemSizeMb` | GSP static-info `fb_length`, rounded to MiB | Reported total framebuffer |
| `fbAddrSpaceSizeMb` | End of the last supplied FB region | FB address-space extent |
| `fbUsableMemSize` | Sum of nonreserved supplied region lengths | Allocator-facing nonreserved storage |
| `gpuGetFlaVasSize_GA100` | Total FB and virtualization boolean | Separate FLA virtual address-space size |

The CPU-side initializer copies GSP-supplied regions. A change in these metadata or allocator limits is not an independent physical integrity result. The original producer of the GSP-reported length is still a research target.

The [documented OverrideFbSize registry key](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/ca2d03e6fafd4d4b56b383497d931c25b283bfcf/src/nvidia/interface/nvrm_registry.h#L923) reduces FB for memory-management tests. Its [normal constructor consumer](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/ca2d03e6fafd4d4b56b383497d931c25b283bfcf/src/nvidia/src/kernel/gpu/mem_mgr/mem_mgr.c#L204) caches a heap-sizing override. No additional-HBM initialization follows from these examined lines; the later heap-clamp consumer was not traced here.

## A new original memory-object anchor

The unchanged GSP image contains the public MemoryManager class identity `0x22ad47`, with its own class definition `0x406c5b0`, object size `0xc20` and metadata `0x403d158`. Its dynamic creator `0x538b6b0` is a tail thunk to `0x538b3a4`; the latter stores those metadata in the newly created object.

That body calls method initialization `0x5544dbc`, followed by separate data/flag initialization `0x5382018`. A bounded CPU-only trace of the actual GA100 key 42 through the original owner field completed in 192 instructions and determined 38 final method fields. This gives a concrete set of memory-object targets for further source work; it establishes neither extra memory nor a new hardware-enable input.

One of those selected methods is now bounded more closely: slot `0x1c8` / `0x4a5de18` invokes its installed boundary getter at slot `0x1c0` / `0x4a581d0`, using the same original object. For a present range, it rounds the upper byte boundary to 64 KiB and compares the MiB-scaled value with field `+0x6a0`; a mismatch returns `0x40`. This is a size-consistency consumer. It does not increase that scalar or enable another stack.

The apparently relevant `sd ...,0x6a0(...)` in one called region helper uses an already shifted array base. It updates a region record, not the scalar sizing field. The normal physical-size source remains open. A separate conditional scalar writer and the child-class connection have since been resolved below.

## Original child-class routing is now connected

The original GPU class router at `0x4b66aec` extracts the descriptor's class identity. Its own comparison with class `0x22ad47` selects the pointer at **GPU+0x1e80**. A strict CPU-only evaluation follows 40 original instructions through that case to the common engine-state cast boundary. This connects the child used by the sizing getter to the independently anchored original MemoryManager class.

A second original case compares class `0x7faff1` and selects **GPU+0x1e78** in 33 instructions. The original class definition at `0x406bd98` has this identity and size `0x4d0`; NVIDIA's pinned [generated KernelMemorySystem header](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/ca2d03e6fafd4d4b56b383497d931c25b283bfcf/src/nvidia/generated/g_kern_mem_sys_nvoc.h) supplies the class name. The [public GPU class router](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/ca2d03e6fafd4d4b56b383497d931c25b283bfcf/src/nvidia/src/kernel/gpu/gpu.c#L1290) provides semantic context, not replacement binary offsets.

A third original case connects class `0x174e21` to **GPU+0x1e70** in 29 instructions. Its own class definition at `0x406f9f0` specifies size `0x8840`. No public class name is assigned solely from its position beside the other children.

All three evaluations use explicit synthetic object pointers and stop before executing the external cast. Only saved caller state is seeded; unknown argument or memory inputs are rejected. These are static routing results, not observations of a live object's contents or additional memory.

The subsequent original MemoryManager lifecycle hook is also connected through its own metadata: interface slot `+0x68` reaches thunk `0x5370574`, which dispatches metadata `+0xc8` to `0x4a54cec`. Its first followed sizing load uses existing field **base+0x6a8**, shifted to bytes. The selected callees reserve regions and initialize a heap from existing sizes; none of the followed operations establishes the producer of base `+0x6a0`.

The original `OverrideFbSize` lookup caches its result separately at **base+0x6b8**, with `u64(-1)` as the default. That cache store does not rewrite base `+0x6a0`. Later heap-clamp behavior and any physical capacity effect are not established by this lookup.

## Earlier configuration receiver

The original KernelMemorySystem metadata connects its normal pre-initialization hook to `0x4a4541c`. This allocates and zeros a 40-byte block, stores its pointer at KMS+`0x228`, then calls the original builder `0x4a40d5c`. That builder obtains flags and callback results from **GPU+0x1e70**, independently connected above to class `0x174e21`. It is a configuration receiver; the examined builder does not write MemoryManager base+`0x6a0`.

The pinned [public configuration contract](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/ca2d03e6fafd4d4b56b383497d931c25b283bfcf/src/common/sdk/nvidia/inc/ctrl/ctrl2080/ctrl2080internal.h#L96) describes compression/comptag flags, ECC-FBPA support, L2 cache size, RAM type and LTC/LTS counts. It contains no total-HBM-capacity member. This is semantic context, not a licence to rename original fields from today's layout. The concrete callback supplying original output `+0x8` has now been resolved independently: the original GA100 initialization selects slot `+0x680` → `0x4a0f7cc`. It multiplies two fields of a packed result for selector `0x58c` by its selected `+0x730` count getter, then scales by 1024; an optional context branch halves the value. That count getter, `0x49fd2e4`, returns `MMIO[0x12006c] & 0x1f` on its normal path. This formula and the complete configuration contract support an **L2 cache-size** interpretation, not total HBM. No live register read was performed.

## A conditional writer of the actual size fields

The original class `0x174e21` pre-initialization path is connected to selected slot `+0xc38` → `0x49fa1c8`. It obtains the original MemoryManager through GPU+`0x1e80`. If the existing region count at MemoryManager+`0x6c8` is zero, its call at `0x49fa49c/4a0` reaches `0x4a6730c`, then `0x4a5d80c`, with that same base object.

This final helper contains **actual unshifted scalar stores**: `0x4a5d8ec` writes `+0x6a0`, `0x4a5d8f0` writes `+0x6a8`, and `0x4a5d8f8` writes `+0x698`. The first two receive `(a2+0xfffff)>>20`; the last initially receives `a2` bytes, before later region accounting. These are distinct from the earlier shifted region-row false positive at `0x4a58f90`.

The result is conditional: the examined path requires MemoryManager+`0x2d4` to be nonzero, valid input parameters, and no existing regions. Its size/base parameters come from original global fields `0x4397ec8` and `0x4397ed0`. The `+0x2d4 == 0` alternative returns error `0x40`; it does not invoke a hidden normal HBM-size supplier.

This closes one real parameter-to-size-field contract. It does **not** establish that the examined path supplies normal HBM on these cards, that its global inputs can be enlarged into backed storage, or that another physical stack is initialized. The source of the normal pre-existing memory regions remains open. No value was changed and no extra usable GiB were demonstrated.

No hardware was accessed in this study. The earlier clock and capacity observations keep their original timestamps. Curated distinctions and calculated examples are in [memory-sizing.json](../data/memory-sizing.json).
