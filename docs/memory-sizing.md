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

The original function loads a child pointer at `OBJGPU+0x1e80`, then a sizing field at child offset `0x6a0`. The public counterpart names `MemoryManager.Ram.fbTotalMemSizeMb`. The actual original child-class connection and the producer of that field still need their own connected trace; the modern C-structure layout is not transferred to the binary.

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

The apparently relevant `sd ...,0x6a0(...)` in one called region helper uses an already shifted array base. It updates a region record, not the scalar sizing field. The original unshifted field producer and the independent GPU-child-class connection remain open.

No hardware was accessed in this study. The earlier clock and capacity observations keep their original timestamps. Curated distinctions and calculated examples are in [memory-sizing.json](../data/memory-sizing.json).
