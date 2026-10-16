# Open questions and next steps

## Priority

1. Find a genuinely different, concretely traced physical-availability input forCMP40 toward48 GiB.
2. Investigate supported CMP64 hypotheses toward80/96 GiB, preserving the distinction between physical population and usable storage.
3. Find a new normal topology mechanism for compute resources beyond the established74-SM baseline.
4. Record practical AI behavior under matched software, power and workload conditions as experiments become available.

## Current concrete source path

The original OBJGPU→GA10042→slot348→getter4b78dc0→820000 chain is now established. Find an actual normal GPC/FBP topology consumer or producer whose argument connects to that identified object, then distinguish a status read from a producing store. Seven locally verified reader candidates did not supply a new topology writer. A generic object+348 load and the current public header's method order are still insufficient. See[GSP object map](gsp-object-map.md).

The original MemoryManager class, its 38 actually selected GA100 method fields and the GPU+0x1e80 class-routing bridge are now connected independently of modern host layouts. A second original route identifies the adjacent GPU+0x1e78 KernelMemorySystem child. The later MemoryManager lifecycle path consumes pre-existing size/region data and caches OverrideFbSize in a separate field. One guarded parameter path now writes the actual unshifted MemoryManager+0x6a0/0x6a8 fields, but its ordinary physical-HBM role is unproved and its false-guard branch returns an error. Trace the source of the normal pre-existing memory regions; do not reinterpret the downstream region calls or the guarded parameter assignment as a new physical-capacity mechanism. The identified FLA sizing getter remains a virtual-address calculation. The App01 finalizer register bits also require their real producer/meaning before a geometry experiment. See [Memory sizing](memory-sizing.md).

## What would justify another hardware attempt

A new writer, latch, ordering condition or access context must be distinguishable from the previous negative experiments. Prepare the specific input, observable outcome, required reset scope and evidence capture before running it in the owner's authorized test environment. A proposal stays a proposal until execution evidence exists.

The complete ordinary rank accounting and identical partition table do not themselves yield an extra-capacity experiment. New evidence of other package/channel population, a different normal configuration path or a reproduced external method could reopen a hypothesis.

## Useful independent contributions

Matched original firmware versions with hashes and lawful access instructions; exact hardware identities without serial numbers; minimal, bounded topology observations; explicit announced/reported/usable capacity; and negative results with a distinguishable method. An unreproduced screenshot or nominal capacity is retained as a lead, not promoted to a result.
