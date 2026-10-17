# Normal topology-wrapper gates

On 17 October we paired the complete normal plaintext debug App45 topology wrappers for both CMP variants, then read just their two source-bound inputs on each card. The earlier work had named the dispatcher and examined a later CMP64 source-vector tail; this follow-up supplies the enclosing gates and the different fall-through paths.

## Four current reads

Observed at 15:52:56 UTC, driver 615.71.09. Each BAR page was mapped read-only; no register writes, resets, configuration changes or CUDA allocations.

| Variant | Input at `0x8204d8` | Input at `0x8204bc` | Conditional route in its original debug wrapper |
|---|---|---|---|
|CMP40|0x2082|1|Skip special block; return 0|
|CMP64|0x20c2|1|Skip special block; continue into source-vector tail|

The shared outer gate requires a nonzero low byte from `0x8204bc`. The special inner block compares `0x8204d8` with literal `0x20b0`. Both observed values differ. In CMP40 the mismatch exits normally; CMP64 instead falls through into the tail already examined with the [historical TPC-source vectors](../data/tpc-sources.json). Those old source1 values were not measured again in this follow-up.

The special block includes arithmetic involving 54 and writes through a known OR helper to the per-GPC reconfiguration bank. Neither that constant nor an OR operation establishes 54 available TPCs or a physical activation polarity. The current two inputs do not select that special block in either debug wrapper.

## Scope

This is a source-bound conditional route, **not captured execution of production App85 at boot**. The observed `0x8204d8` words match the visible device IDs, but exact vendor register names, writable input producers and a useful hardware transformation are unproved. The CMP64 tail's existing source1-zero exit remains a separate condition; its old snapshot is not promoted to current state. No guard was forced and no old mask sequence was retried.

The accompanying ordinary snapshot reported 40/64 GiB, 1215/1728 MHz and zero used MiB. It did not requalify 74SM/ECC, process counts, full capacity or geometry. No extra HBM or SM was demonstrated. [Selected observations, source fingerprints and limits](../data/topology-gates.json).
