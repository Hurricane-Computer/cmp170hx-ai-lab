# Original App08: normal command forms and selector groups

**The late initialization table has more than MMIO writes, but its normal per-group command path still selects an already active partition.** This is a bounded static follow-up to the [earlier mask-consumer study](firmware.md). It used unchanged original files only; no GPU access, firmware modification or execution occurred.

## Two dispatch levels

The outer list holds 32 entries expanded from packed 16-bit values. Low two bits select the operation; bits 2–15 hold its payload. Type 0 references a normal record sequence, type 1 passes payload times 1000 to the existing timing helper, type 2 is rejected here and type 3 terminates the list. No time unit is assigned from that multiplier alone.

Within a selected record, low two bits at decoded offset `+0x84` choose the operation. Type 0 is the previously reviewed constrained MMIO path. Type 1 sends up to 80 payload words as individual arguments to the original `0x1312` transfer helper. Type 2 supplies a command byte and data buffer with write direction; it has a literal length upper bound of 2560, while the helper receives an eight-bit length argument. Units and large-length behavior are not established. Type 3 is rejected.

These forms are ordinary stored initialization commands, not newly discovered host capacity parameters. The actual record instances and their runtime selection are not fully inventoried here.

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
