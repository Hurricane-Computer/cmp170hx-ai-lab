# Original App08: normal command forms and selector groups

**The late initialization table has more than MMIO writes, but its normal per-group command path still selects an already active partition.** This is a bounded static follow-up to the [earlier mask-consumer study](firmware.md). It used unchanged original files only; no GPU access, firmware modification or execution occurred.

## Two dispatch levels

The outer list holds 32 entries expanded from packed 16-bit values. Low two bits select the operation; bits 2–15 hold its payload. Type 0 references a normal record sequence, type 1 passes payload times 1000 to the existing timing helper, type 2 is rejected here and type 3 terminates the list. No time unit is assigned from that multiplier alone.

Within a selected record, low two bits at decoded offset `+0x84` choose the operation. Type 0 is the previously reviewed constrained MMIO path. Type 1 sends up to 80 payload words as individual arguments to the original `0x1312` transfer helper. Type 2 supplies a command byte and data buffer with write direction; it has a literal length upper bound of 2560, while the helper receives an eight-bit length argument. Units and large-length behavior are not established. Type 3 is rejected.

These forms are ordinary stored initialization commands, not newly discovered host capacity parameters. The stored record instances and their conditional profile selection are mapped below. Execution in a particular boot has not been traced.

## The six ordered selector groups

Both original CMP files contain the same twelve bytes at DMEM `0x15c3`, used by helper `0x12aa`:

| Selector | First candidate FBP | Fallback FBP |
|---:|---:|---:|
| 0 | 0 | 2 |
| 1 | 1 | 4 |
| 2 | 3 | 5 |
| 3 | 7 | 9 |
| 4 | 6 | 11 |
| 5 | 8 | 10 |

The helper chooses the first candidate whose disable bit is clear. If both are disabled, it returns `0xff`; the transfer routine then returns false before accessing that normal port. Otherwise the FBPA index is twice the chosen FBP. This connects the command to a concrete existing-availability check rather than assuming every table slot names usable memory.

Applying the **historical** masks `0x840` and `0x852` to this source rule yields blocked selector 4 for CMP40, and selectors 1 and 4 for CMP64. These are calculations from earlier observations, not fresh GPU measurements. Six selector groups do not establish six populated or functional HBM stacks.

## The special path remains a separate question

An all-ones selection mask chooses special selector `0x80`, whose fixed port path is entered before the normal mask read. Its physical fanout and whether it can return independent responses are not established. Calling it a demonstrated way to reach an additional stack would exceed the evidence. No repeated disabled-port DEVICE_ID request or new register write was derived.

The four examined callers also do not check the transfer helper's boolean return. Consequently, completion of the enclosing sequence alone would not prove that a masked selector was accessed. This is a source-level status-propagation limit, not an allegation that any historical capacity test falsely passed.

[Exact source hashes, code anchors, original table bytes, dispatch limits and calculated cases](../data/training-commands.json). Raw firmware and derived assembly remain outside this publication. Additional usable capacity is still unproved; the external [77.5/72-GiB counterevidence](capacity-evidence.md) keeps the CMP40 80-GiB hypothesis open.

## Stored records and the two historical profiles

The normal App08 entry loads its argument pointer, adds the supplied 16-bit displacement and stores the result in `D1ad4`. The original ROM's normal-data layout matches that route: a 16-byte argument header leads to a 68-byte header whose `+0x38/+0x3c/+0x40` fields name the three tables. The normal reader relocates their BIOS-relative pointers and applies the stored header size, record stride and index. No fresh runtime argument capture was made.

Both CMP originals contain byte-identical copies of **4 lists, 12 sequences and 50 command records**. The command records are 48 MMIO records and two special-port records. This is a separate embedded App08 command format; it does not turn the previously empty BIT-I main-script roots into nonempty scripts.

The special route is represented by list 3, sequence 7 and records 48/49. The ordinary information matcher assigns it to profile 10. Applying the earlier observed own profiles to the unchanged tables gives:

| Variant | Historical profile | Information record | Selected list | Sequences | Special-port records |
|---|---:|---:|---:|---|---|
| CMP40 | 4 | 4 | 0 | 0, 1, 2 | None |
| CMP64 | 7 | 7 | 2 | 5 | None |

The first two list selectors are `0xff` in both records and are skipped; the third selects the listed command list. These are conditional static graphs using historical observations, not new observations that a current boot executed them. Selecting the other memory profile without establishing its hardware suitability is not a demonstrated capacity method.

## A100 controls: a genuine data difference, with a narrower scope

All three tables in A100 PCIe40 `92.00.90.00.08` are byte-identical to these CMP tables. A100 PCIe80 `92.00.90.00.04` has one changed list, two changed sequences and eighteen changed command records. This is a difference outside the previously compared 23-by-16 profile matrix.

For the stored path corresponding to historical CMP40 profile 4, six consumed command records differ, containing **72 changed active payload words**. For the path corresponding to historical CMP64 profile 7, the selected list, sequence and command are byte-identical. Thus the particular Hynix path does not acquire a different initialization sequence merely by copying this A10080 table. Other profiles and other firmware versions are separate questions.

The source also exposes one explicit normal bit-0 toggle at `0x9a0218` in the CMP40 graph. Its hardware field name and any capacity-adoption role remain unknown. It is not yet a proved geometry latch or a justified standalone write. The A100 data differences likewise do not establish their cause as capacity, nor demonstrate that a transplant is suitable. No raw vendor command payloads were published or executed.

The useful next source task is to identify the consumed command/interface semantics and the normal toggle's full state requirements. More bytes, a different script or a completed script alone would not establish more independent storage.


## Expanded original controls and command completion limits

The command-record comparison now covers ten existing original vendor images. These are stored-data projections through the examined CMP consumer, conditional on the earlier own profile IDs. They do not show which profile a physical A100 actually selects. In particular, the presence of profile 4 in an 80-GB firmware does not establish that an 80-GB card executes it.

| Stored-data group | Original firmware images | Profile 4 projection | Profile 7 projection |
|---|---|---|---|
| Four 40-GB controls | HGX40 `92.00.36.00.05`; SXM4-40 `92.00.19.00.19`; PCIe40 `92.00.25.00.08` and `92.00.90.00.08` | Matches CMP | Matches CMP |
| Five 80-GB controls | HGX80 `92.00.94.00.0b`; SXM4-80 `92.00.38.00.01`; A800-SXM4-80 `92.00.ac.00.0d`; PCIe80 `92.00.a0.00.03` and `92.00.90.00.04` | Same six changed records in every image | Matches CMP |
| One separate 40-GB case | SXM4-40 `92.00.48.00.01` | The selected records have zero stored lengths | Record 29 has zero stored length |

The five 80-GB projections are identical in the examined active record fields, including the six changed records already identified. That strengthens a systematic firmware-family correlation across these images. It still does not identify the changes as a physical-capacity mechanism. The zero-length case is kept separate; its native boot behavior has not been traced. Whole-table hashes differ in additional places outside these conditional paths.

The original MMIO consumer alternates the declared addresses while writing each payload word. Of the 72 changed active words in the six-record comparison, **71 go to `0x9a0090` and one to `0x9a0094`**. No per-word status or readback is checked in this particular store loop. Reaching the loop end establishes that the declared words were submitted; it does not establish completion of the device commands or acceptance of a new memory geometry.

The normal FE marker's intervening helper waits on elapsed IO-counter ticks. It does not poll `0x9a0218`, a ready bit or memory size. The counter's time unit and the toggled bit's hardware meaning remain unresolved. Other ordinary setup code also packs settings into the same register. None of this justifies replaying the isolated toggle.

[NVIDIA's FBPA relocation note](https://github.com/NVIDIA/open-gpu-doc/blob/master/pascal/gp100-fbpa.txt) establishes the older-to-newer register-family mapping. The bounded [envytools register reference](https://github.com/envytools/envytools/blob/f102b82381f3f11cee113d16374c87091db039d9/rnndb/memory/gf100_pbfb.xml) and [Nouveau RAM code](https://github.com/torvalds/linux/blob/v6.12/drivers/gpu/drm/nouveau/nvkm/subdev/fb/ramgf100.c) provide older-family context, without decoding the required GA100 command fields. No claim of global absence of public definitions is made. Reusing older GDDR command meanings for this HBM interface remains an unverified inference.

There was no hardware access or new usable-memory/SM result in this follow-up. The next distinct source control is the manually constructed ordinary command sequence in the same original App08, to help identify the encoded operations before selecting a live experiment. Raw command payloads and firmware-derived assembly remain private.


## The manually constructed route has its own state contract

The direct command sequence has one direct caller in the examined original App08. The normal entry first dispatches on bit 0 of `0x12e0`. With that bit clear, the direct route is selected only when bits 10–11 of `0x11823c` equal 2 and bit 30 of `0x118f78` is set. The other branch calls the regular initialization path. At its end, the direct routine clears bit 30 itself. A later clear bit therefore cannot distinguish a route that was never taken from one that consumed the flag.

Its small direct command sequence makes four writes to each of `0x9a0090`, `0x9a0094` and the additional control `0x9a0154`. The values written to `0x9a0094` use more than its low bit. This is a state-specific sequence with additional controls; it does not reveal named constructors for the table's encoded command fields. No isolated replay or route-selector change follows from it.

The pinned [NVIDIA GPU administration source](https://github.com/NVIDIA/gpu-admin-tools/blob/44f261a7ebff96559488230b420e4a3035b30d58/nvidia_gpu_tools.py) uses `0x118f78` as scratch for other after-reset fields. Those fields do not define the original route's bit 30. Sharing the register address does not establish shared field meaning. No ECC or MIG test/change was made.

The same source provides a useful completion contract. Its `clear_memory()` wrapper calls a wait method: that method waits for boot and then polls an existing memory-clear completion state. These methods do not launch a new clear. In the relevant pre-Hopper source branch, the expectations are:

| Observation | Register | Expected full 32-bit value |
|---|---|---|
| Boot completed | `0x118234` | `0x000003ff` |
| Memory clear finished | `0x100b20` | `0x00000001` |

The polling implementation uses the default mask `0xffffffff` at these call sites, so these are equality tests, rather than tests for selected bits being set. They are source-level candidates for a future relevant experiment. Their accessibility on the actual CMP setup has not been tested. A blocked or poison read provides no completion result. Even valid completion would establish initialization status, not an independent physical-memory inventory or usable additional capacity.

This source follow-up performed no hardware access. The next distinct question is the ordinary producer and meaning of the route flag and additional command control; the exact state condition is not itself a capacity mechanism. Original command payloads and derived assembly remain private.

## Native zero-length control

The separate SXM4-40 `92.00.48.00.01` case has now been checked in its own App08 consumer, rather than assuming the CMP code is identical. Its record reader uses the same declared length field. A zero length reaches the initial index-versus-length test and skips the payload store; it is not a hidden full-length sentinel in this path.

Conditionally following stored profile 4 selects 29 zero-length records and one FE marker; profile 7 selects one zero-length record without an FE marker. The enclosing prologue/cleanup and any FE marker can still run. This does not establish that the firmware performs no initialization, nor reveal its runtime-selected profile. No firmware was executed and no new capacity mechanism follows. Exact source fingerprints and anchors are in the [structured record](../data/training-commands.json).

## Post-matrix DRAM mode settings

The original App08 continues beyond the known23-row configuration block: the same cached profile selects six further mode-command words at the attributed MR0/1/2/3/4/15 registers. Their store instructions and complete stored DMEM bytes are bound to both original PROM windows. Mirrored occurrences in a PROM window are duplicate data, not additional independent images. This follow-up compares only three selected source cases, not another full profile sweep.

Two numeric correlations connect controller-side and DRAM-side values:

| Original source case | Controller WR / MRS1 low6 | Controller RAS / MRS3 low6 |
|---|---:|---:|
| CMP40 profile4 | 19 /19 | 42 /42 |
| CMP40 profile7, comparison only | 27 /27 | 47 /47 |
| CMP64 profile7 | 25 /25 | 43 /43 |

These are conditional source values, not new live selections. The WR/RAS names are corroborated by a [published timing analysis at a pinned commit](https://github.com/bayley/cmpunlocker/blob/5a7bb4b7e5056306fe49e8b824787659abb19914/overclocking/timings/reference/hbm2-timings-decoded.md). The complete GitHub file is now retrieved and hashed; the earlier Tangled location remains inaccessible, so byte identity between the two locations is not established. The underlying vendor header was not independently audited. Our numeric correlations and store/table bindings come from the original files.

Under that external layout, bits19:18 are zero in all six selected words. The complete published analysis also omits the native rank enum: it does not establish “only rank0” or an uninitialized second rank. This rank lead is deferred until a definition or distinct native consumer supplies the missing meaning. The extra initialization settings are real, but no new density/address-enable control follows from the demonstrated timing matches. No profile/MRS transplant, devinit replay or hardware test was performed. [Selected source evidence and limits](../data/training-commands.json) preserve this negative decision; raw mode-word tables and assembly remain private.

## Original lane-state capture and its controller mirror

A different ordinary call at `0x7d53` uses the existing `0x1312` helper with instruction `0x12`, read direction and72 bits. The preceding12-byte local zero fill prepares the receive buffer; it is not a repair-write payload. This differs from the already decoded DEVICE_ID instruction `0x0e` with82 bits. The original active-pair selection remains in force.

[JESD235C Table84 and section13.2.3.19](https://studylib.net/doc/28046328/hbm2), read as original standard text on a third-party mirror, identify this as SOFT_LANE_REPAIR capture of the existing routing vector. An update is a separate operation. No update or permanent programming occurred.

The original consumer at `0x143d..0x14d4` extracts four16-bit halves and omits one intervening byte. These structurally match the standard's data-lane and address-lane fields respectively; that alignment is an inference, since the standard does not define NVIDIA port packing and no new72-bit reply was measured. A pre-existing table selects controller index `p`; the effective-disable guard remains. For each non-`0xffff` half `h`, the code stores `h` and then `h |0x10000` to `0x9011b4 +0x4000*p +0x10*(channel&1) +4*slot`. These are full stores, not read-modify-writes. The native name of bit16 remains unbound.

This binds an actual controller data-routing producer from the original reply, rather than another reported-size or register-range descriptor. **It does not bind a density/rank/stack enable, explain the saved larger-geometry alias, or demonstrate extra cells.** No current reply values were collected and no hardware candidate follows. [Selected relationships, hashes and limits](../data/lane-routing.json) contain no raw firmware, assembly or reply payloads.
