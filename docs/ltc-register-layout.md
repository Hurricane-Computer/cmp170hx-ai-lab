# Normal LTC register-range construction

On 17 October we connected the register-layout dataflow in the original 615.71.09 GSP to the saved GA100 method selection. This was offline analysis of unchanged files. No firmware was executed, no hardware was accessed and no configuration changed.

## Selected original methods

The already identified physical-memory-context class has ID `0x174e21`, size `0x8840` and metadata at `0x4054e00`. Its exact vendor class name remains unassigned. Extraction from the existing key42/GA100 constructor trace gives:

| Object slot | Selected function | Result |
|---|---|---|
|`+0xda8`|`0x49fa810`|Writes `0x140000`, `0x17e000`, `0x2000` to three caller output buffers|
|`+0xe00`|`0x49faa34`|Returns `0x140000`|

These output-buffer stores describe addresses and an extent; they do not write those GPU register addresses. The original class metadata at `+0x180` contains callback `0x49ecc8c`. That callback calls `0x49ec60c` with its object argument retained; the latter invokes the `+0xda8` method at `0x49ec70c`.

## What the normal builder does

The builder keeps an array of `0x90`-byte range objects at object `+0x8760` and its count at `+0x8768`. It passes the selected outputs to the already analyzed ordinary `IoAperture` / `RegisterAperture` constructor `0x5310360`:

- The last descriptor has offset `0x17e000` and extent `0x2000`, covering `0x17e000..0x17ffff`.
- Preceding descriptors start at `0x140000`, advance by `0x2000` and have the same extent, when the count requires them.

The addresses `0x17e2b4` and `0x1402b4` discussed in earlier capacity reports lie inside these ranges. This supplies a concrete normal address route. It does **not** establish the meaning of the field at relative offset `0x2b4`, a physical decoder write, execution in the current boot or additional usable HBM. The generic aperture constructor was reused from the earlier analysis, not retraced as a new mechanism.

The next source question is the actual consumer of this particular range array or selected base method, followed by the value producer for an access at offset `0x2b4`. A different register readback or an address descriptor alone would not justify another capacity experiment. [Structured source anchors and limits](../data/ltc-register-layout.json).
