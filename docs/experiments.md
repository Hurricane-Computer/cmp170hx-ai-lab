# Experiment ledger

Dates are campaign dates in UTC. The stage numbers are stable notebook references, not software release numbers. Machine-readable extracts: [experiment-ledger.json](../data/experiment-ledger.json), [CP witness](../data/cp-witness.json), [TPC sources](../data/tpc-sources.json).

| Notebook | Method | Result | What it does not prove |
|---|---|---|---|
| Stage3,15 Oct | HBM DEVICE_ID on available ports | Samsung8-GiB-stack organization onCMP40, Hynix16-GiB onCMP64 | Hidden/disabled package population or health |
| Stage5,15 Oct | Direct host writes to known disable fields, with a separate writable control | Requested raw memory mask changes rejected onCMP64; active topology unchanged | Every privileged or earlier-init method is impossible |
| Stages7–10,15 Oct | CTRL/EN order and initialization-phase experiments | Some CTRL/EN values accepted; no new physical availability | Accepted values imply enabled memory |
| Stage8,15 Oct | Additional-disable control | Further disabling was possible; reversal needed reset | Ability to enable below original availability |
| Stage13,16 Oct | Volatile TPC override control on globally inactiveGPCs | Marker changes were visible | Those GPCs execute work |
| Stages14–15,16 Oct | Distinct memory CTRL sequences on both variants | Readbacks accepted, effective masks unchanged | A new capacity unlock |
| Stage19,16 Oct | CP-bank requests for one extraGPC and memory candidates | GPC/FBP availability unchanged | Writable CTRL values can overcome the physical gate |
| Stage20,16 Oct | Nonzero CP witnesses followed by clear values | All three memory CP witnesses ignored on both cards | Reading zero after writing zero proves writability |
| Stages21/23,16 Oct | Alternate warm initialization and subsequent device-readiness recovery | Successful binding/persistence return codes did not establish device readiness; a targeted card reset recoveredCMP40 | A warm call or return code proves fresh memory training or NVML readiness |
| Stages25/28,16 Oct | Ordinary cold-init memory-clock input |1242 then1269 MHz onCMP40; short64-MiB copy checks passed | Full-range integrity, long stability or extra capacity |
| Stage31,16 Oct | First read of original TPC source0/source1 versus effective status | Source values differ from status semantics; no causal enable formula established | A raw0/1 is a healthy/defective-core label |

## Accepted readback versus effective topology

The memory CTRL values are separate from the effective FBP/FBPA/FBIO status. CMP40 retained the observed840/c03000 geometry and10 logicalFBPs; CMP64 retained852/c0330c and8 logicalFBPs in these experiments. Later source work confirmed that the original training paths consume those effective masks.

Stage20 deliberately used nonzero CP witnesses. OnCMP40, targets were840 andc03000; onCMP64,852 andc0330c. CP readbacks stayed0; clear0 readbacks stayed0. The positive markers demonstrated that the test context ran, but did not turn the rejected CP writes into successful writes. The public extract preserves the requested and observed technical fields.

## Not repeatedly tested

The established74-SM baseline and ECC were not requalified. Known unsuccessful CTRL/CP/EN sequences, the sticky additional-disable result and inaccessible memory-ID ports are not repeated without a materially different mechanism. Neither scripts nor generated reports are evidence that a proposed command actually ran.

Static studies, including A100 comparisons and original firmware flow analysis, are tracked separately in[Firmware notes](firmware.md). No LLM performance ranking is inferred from the clock checks.
