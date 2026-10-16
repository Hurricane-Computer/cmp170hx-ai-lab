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

## A separate App01 finalization path

A newly bounded ordinary App01 path at `0x25e..0x298` conditionally clears bit5 of `0x9a3c80` and `0x9a3c7c`, then checks the cleared values. Its sole record gate is TypeE+6 bit0, already set in both original images; this differs from the TypeE+8 request word. The path follows the end-callback list within this App01 invocation. Its absolute order relative to a separate App08 invocation is not established. The hardware meaning of bit5 and any connection to memory geometry remain open; no size, stack or interleave input is demonstrated. No hardware write was derived.

## TPC source interpretation

The original selectors identify source0, source1, effective status and reconfiguration override as separate vectors. Stage31 measured all four once on both variants. In globally activeGPCs, source0=0 correlates with status1, and source0=1 with status0; source1 was host-visible0 throughout.

The examined CMP64 consumer popcounts source0 without inversion and exits when the source1 total is0. With the measured host inputs it would not explain the inverse correlation. Identical privileged visibility and historic boot inputs are not established. Precise field names and any safe activation polarity remain unknown.

## GSP object work

A new RV64C-aware scan filled the earlier aligned-word search gap. Its six literal control-transfer candidates were already present in the older scan; no new direct topology write resulted. Linear decoding can encounter inline data, so instruction candidates are not universal reachability claims.

An additional exact function-address search located original construction branches that install a getter returning820000 at object+348. Stage32 connects this branch to the original OBJGPU metadata and GA100 ChipHal42 selection. The exact original GA100 getter is4b78dc0. Seven locally verified consumers only read status; their individual active GA100 call bridge remains open. The next step is a genuine topology producer connected to this identified object. Current public header layouts are not blindly substituted for the original binary's layout. See[GSP object map](gsp-object-map.md).

Hashes and the twelve-image geometry comparison are in[firmware-catalog.json](../data/firmware-catalog.json). Primary references are in[Sources](sources.md).
