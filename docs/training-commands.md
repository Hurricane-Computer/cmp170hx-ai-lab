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
