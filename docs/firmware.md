# Original firmware studies

All statements below concern identified unchanged input files and bounded static analyses. They are not claims that a particular past boot executed every branch. Original vendor binaries are not distributed in this repository.

## Ordinary App01/App45 RPR handoff

The own original App01 legacy descriptor exposes a DMEM directory atc4, header1/4/8/20. TypeE points to1c and type7 toa0. Type7's RPR pointer isd7d4 in all twelve examined images after respecting their own interface offsets.

The ordinary App45 mode0 caller requests the relevant App01 feature; the static default bit alone therefore cannot prove that the producer never runs. App01 conditionally copies448 raw RPR bytes tod7d4. App45 retrieves512 bytes into its local310c buffer and passes the buffer address to its reader. The transfer reserve is not additional object payload or memory capacity.

The exact format is `3s2bwbd4b54r2dR`. RawDWORD+8 is a pair count, maximum54. CMP40's count33 covers32 nonzero addresses and one null slot; CMP64's count0 does not process the unused address template. All values in the own records are0.

The helper writes `read(address) OR value`. For primary targets this cannot clear already-set bits. The special820814 case also copies the result to820818 without reading the destination; its mirror can therefore lose its own former bits. OR0 is not globally equivalent to no operation. The relevant mirror values had already been accepted in older experiments without changing physical availability; this is not a new untested enable method.

## Original InfoROM framing

The own images contain the custom JFFS structure atc1000, size31000, with128-byte frames and16-byte frame headers. The examined reader merges logical offsets and generations; a class bit is not a universal tombstone flag. Sixteen complete objects were recovered without holes in the own inputs. This is NVIDIA's format, not an assumption that standard LinuxJFFS semantics apply.

RRL is identical and has an all-zero body in both own images. The examined vendor update defaults also share the empty RRL; those defaults are not live A100 state. Schema names and strings are not proof of instantiated objects or writable hardware policies. Init-From-ROM (IFR) and InfoROM are distinct concepts.

## App08 physical-mask consumers

At4dfc..4e0e, the CMP original reads820c14 intoD1570. The early configuration has24 entries. Its96 parameter bytes are present in bothCMP originals and byte-equal to the compared modern A10040/80 originals after relocation. Disabled-unit entries are skipped.

Two24-unit completion polls at5597..55bc and6985..69ad use the same cache. A later constrained MMIO-table path also skips a disabled-unit record before its write loop; it does not supply a new physical-mask setter. The previously tested CTRL-before-Devinit timing is not made novel merely by naming this cache point.

## An earlier App08 request has an unchecked completion result

A bounded follow-up connects one real earlier path: the normal cold caller at `0x7f68` invokes `0x8257` before the existing effective-mask capture chain. It consumes 13 original bytes at DMEM `0xfe9` and forms selected fields at MMIO targets `0x20340`, `0x20414` and `0x2042c`. The two own original DMEMs contain the same input slice; their full DMEM images are different. These are static field outputs, not measured complete register words or an identified host parameter.

The routine then selects 0 and calls `0x80cd`, which preserves the other bits while requesting bit 0 at `0x2033c`. Its ordinary finite poll asks for that bit to read back as 0. The poll returns 1 for a match or 0 when its counter expires, but **neither caller checks that return**; the outer caller immediately overwrites it with −1 at `0x7f6c`. Reaching the later mask capture therefore does not by itself establish that this request completed.

The hardware block name and enable meaning of these targets remain unbound. Other calls lie before the later `0x820c14` capture; no semantic edge from this request to additional memory availability is established. Shared code and the 13-byte original input do not prove that a disabled pair can be enabled or that additional healthy cells exist. No request replay, selector change or memory-capacity write follows.

The same review keeps the H timing boundary precise: its host CFG1/LMR hook is after `kgspPrepareForBootstrap_HAL(KGSP_BOOT_MODE_NORMAL)` in `_kgspBootGspRm`. This does not establish a continuous execution order relative to the original FWSEC-SB/App08 HBM training. FRTS is a separate operation. Moving the failed geometry values earlier is not a new source-bound mechanism.

[Selected original-source relationships and limits](../data/normal-init-inputs.json) retain source hashes and the exact missing edge. Three small pinned public GA100 control headers did not name these literal targets; that limited lookup is not a whole-driver absence claim. No hardware access, firmware execution, build or new usable GiB occurred.

## A separate App01 finalization path

A newly bounded ordinary App01 path at `0x25e..0x298` conditionally clears bit5 of `0x9a3c80` and `0x9a3c7c`, then checks the cleared values. Its sole record gate is TypeE+6 bit0, already set in both original images; this differs from the TypeE+8 request word. The path follows the end-callback list within this App01 invocation. Its absolute order relative to a separate App08 invocation is not established. The hardware meaning of bit5 and any connection to memory geometry remain open; no size, stack or interleave input is demonstrated. No hardware write was derived.

## TPC source interpretation

The original selectors identify source0, source1, effective status and reconfiguration override as separate vectors. Stage31 measured all four once on both variants. In globally activeGPCs, source0=0 correlates with status1, and source0=1 with status0; source1 was host-visible0 throughout.

The examined CMP64 consumer popcounts source0 without inversion and exits when the source1 total is0. With the measured host inputs it would not explain the inverse correlation. Identical privileged visibility and historic boot inputs are not established. Precise field names and any safe activation polarity remain unknown.

## GSP object work

A new RV64C-aware scan filled the earlier aligned-word search gap. Its six literal control-transfer candidates were already present in the older scan; no new direct topology write resulted. Linear decoding can encounter inline data, so instruction candidates are not universal reachability claims.

An additional exact function-address search located original construction branches that install a getter returning820000 at object+348. Stage32 connects this branch to the original OBJGPU metadata and GA100 ChipHal42 selection. The exact original GA100 getter is4b78dc0. Seven locally verified consumers only read status; their individual active GA100 call bridge remains open. The next step is a genuine topology producer connected to this identified object. Current public header layouts are not blindly substituted for the original binary's layout. See[GSP object map](gsp-object-map.md).

## Ordinary BIT-I pointers: a bounded negative

Both own originals and their mirrors have the same version1, 36-byte BIT-I record. Seven of 14 documented pointer fields are nonzero and alias five targets; that is not a count of independent tables or scripts. The ordinary main-script list starts with a null terminator, so contains zero scripts, as already observed earlier. Four other documented direct script roots are zero. The final two bytes at `+0x22` are zero but unnamed in the cited format, so are not assigned an invented role.

The nonzero Devinit Tables pointer/size identifies exactly the already examined source35 data span, not a new script or geometry input. These findings do not imply firmware-wide absence of initialization code. The source basis is NVIDIA's [BIT_NVINIT_PTRS specification](https://nvidia.github.io/open-gpu-doc/BIOS-Information-Table/BIOS-Information-Table.html#_bit_nvinit_ptrs) and the pinned [envytools list reader](https://github.com/envytools/envytools/blob/f102b82381f3f11cee113d16374c87091db039d9/nvbios/nvbios.c#L1282). No loader replay or hardware test follows from the same empty roots.

Hashes and the twelve-image geometry comparison are in[firmware-catalog.json](../data/firmware-catalog.json). Primary references are in[Sources](sources.md).

## Other ordinary App08 command forms

The follow-up [command-contract study](training-commands.md) identifies the two non-MMIO forms, the six ordered selector groups and their existing-disable-mask gate. A separate special-port path is present but lacks an established physical fanout/response contract. No new physical enable or capacity test follows from script completion alone.


## Normal GA100 GFW status gate before the H hook

A narrower source follow-up now binds the **coarse host ordering** in the matching NVIDIA 615.71.09 code. In `kgspInitRm_IMPL`, a required GFW completion wait precedes the later `_kgspBootGspRm` call; failure exits through cleanup. The preserved H C source retains that gate, with its geometry block later than normal bootstrap preparation. This narrows the earlier ordering gap without establishing a complete HBM training timeline.

For the normal non-VF GA100 case, the pinned [GSP HAL dispatch](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/generated/g_kernel_gsp_nvoc.c#L1727) and [GPU HAL dispatch](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/generated/g_gpu_nvoc.c#L2769) select the TU102 helpers. The selected [ordinary wait](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/src/kernel/gpu/arch/turing/kern_gpu_tu102.c#L459) requires successful firmware-core halt and a readable completed GFW status. Its included [field definition](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/common/inc/swref/published/turing/tu102/dev_gc6_island_addendum.h#L32) defines progress bits 7:0 and completion `0xff`. The TU102 status body is byte-identical to the earlier source cache; the new result is the connected selection/order contract.

**An accepted completion status is not a fresh App08 execution count.** Previously completed original phases can skip App08. No currently loaded complete helper set was re-hashed here, no new runtime trace was taken, and no native decoder-latch or particular HBM training phase was identified. The normal bootstrap preparer conditionally prepares FRTS; it does not turn this hook into an SB/App08 execution. An earlier identical CFG1/LMR write is therefore still not a source-backed capacity experiment. The [structured follow-up](../data/normal-init-inputs.json) retains exact source hashes and these limits. No hardware access or additional usable GiB; positive foreign reports remain open.

## Bounded App45 control and finalizer paths

A later static follow-up binds two ordinary calls in the retained **CMP40 debug App45** to complete selected bodies and two small address helpers. Their 340 instructions and 1,021 bytes match the pinned original input. Range ends below are exclusive. This does not identify the production App85 implementation, a CMP64 function at the same address or an executed boot path. Firmware binaries and disassembly remain external.

| Selected body | Static role | Instructions / bytes |
|---|---|---:|
| `0x66cf..0x6762` | Finalizer for existing TPC-disable groups | 50 / 147 |
| `0x6b55..0x6ea7` | Filtered control-table and resource-limiting consumer | 282 / 850 |
| `0x7302..0x730e` | Indexed read-address calculation | 4 / 12 |
| `0x730e..0x731a` | Indexed write-address calculation | 4 / 12 |

The finalizer reads existing TPC-disable vectors through the previously qualified helper. Across eight DWORD slots, a fully set low-byte group `0x07`, `0x38` or `0xc0` produces its corresponding output bit. That result reaches `0x8209bc + 4*i` through the existing OR helper. The formula was checked for all 256 low-byte inputs and 2,048 single-bit extensions; this is an offline source projection, not firmware execution or an activation measurement.

The control consumer exits when its `D3349` gate is zero. Its record path accepts only the previously qualified target filters and nonzero values before calling the same OR helper. Three other direct OR sites target `0x82081c`, `0x820970 + 4*i` and `0x820800`. The two address helpers map twelve slots to reads at `0x820d70 + 4*i` and writes at `0x820970 + 4*i`; their native field names remain unbound. A local `x OR (x+1)` step adds a set bit while preserving old set bits, with the all-ones input trapped in that selected path. Existing resource-limiting helpers are reused rather than re-audited here. The input table's exact identity is not assigned to RRL or BIT-M partition data.

The [known OR-helper mirror exception](#ordinary-app01app45-rpr-handoff) still matters: copying the `0x820814` result to `0x820818` can remove bits from the destination's own prior value. A global claim that every physical target only gains set bits would therefore be wrong. This existing exception does not supply a new mask or replay experiment.

**No new physical-memory backing input, typed BIT-M+0x0d consumer or additional usable GiB is established.** Runtime table values, native field names, complete transitive behavior and actual execution remain unresolved. No hardware trial, gate/mode/CTRL change or further SM trial followed. Positive foreign capacity reports remain open; normal 64 GiB remains baseline capacity. [Curated body hashes, formulas and limits](../data/normal-init-inputs.json) preserve the new scope alongside the earlier findings.
