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
| Stage33, 16 Oct | Next original cold-init CMP40 clock step | 1296 MHz (+6.67% from 1215); one 64-MiB random-data roundtrip passed | Maximum clock, full memory, long stability, bandwidth gain or LLM speed |
| Stage38, 16 Oct | Further original cold-init CMP40 clock step | 1323 MHz (+8.89% from 1215); same limited copy check passed | Maximum clock, full memory, long stability, bandwidth gain or LLM speed |
| Stage39, 16 Oct | Final clock point before the requested pause | 1350 MHz (+11.11% from 1215); same limited copy check passed | Maximum clock, full memory, long stability, bandwidth gain or LLM speed |

Stage40 was a separate requested bounded load follow-up at the unchanged1350MHz point:30s copy /60s streaming, 1534.8/1538.1GB/s effective read+write bandwidth, with all checked outputs correct. Scope and temperature limits are in[the load report](bandwidth-load.md).

Stage41 was an offline capacity-evidence audit plus a CPU counterexample. It preserves the external77.5/72-GiB positive lead, audits the archived full-word checker and demonstrates two false-pass methods under a synthetic alias. It does not reproduce a historical GPU run or unlock memory. See [capacity evidence](capacity-evidence.md).

Stage42 resumed research and queried all six directed peer pairs in a passthrough guest. All capabilities were0; no data transfer followed. One exclusive CMP64 reset recovered device readiness, while its current8-GiB report remains separate from the historical64-GiB unlock. See [peer-memory observations](peer-memory.md).

Stage43 built and boot-tested two exact-release mixed-profile candidates. Both CMPs failed a BAR2 write/readback self-test; original PRAMIN placement alone did not fix it. No CUDA copy or P2P trial was reached. See [driver candidates](driver-candidates.md).

## Accepted readback versus effective topology

The memory CTRL values are separate from the effective FBP/FBPA/FBIO status. CMP40 retained the observed840/c03000 geometry and10 logicalFBPs; CMP64 retained852/c0330c and8 logicalFBPs in these experiments. Later source work confirmed that the original training paths consume those effective masks.

Stage20 deliberately used nonzero CP witnesses. OnCMP40, targets were840 andc03000; onCMP64,852 andc0330c. CP readbacks stayed0; clear0 readbacks stayed0. The positive markers demonstrated that the test context ran, but did not turn the rejected CP writes into successful writes. The public extract preserves the requested and observed technical fields.

## Not repeatedly tested

The established74-SM baseline and ECC were not requalified. Known unsuccessful CTRL/CP/EN sequences, the sticky additional-disable result and inaccessible memory-ID ports are not repeated without a materially different mechanism. Neither scripts nor generated reports are evidence that a proposed command actually ran.

Static studies, including A100 comparisons and original firmware flow analysis, are tracked separately in[Firmware notes](firmware.md). No LLM performance ranking is inferred from the clock checks.

Stage44 tested a distinct CMP-only uncached CPU BAR2 mapping request. The same-target four-byte BAR0 prechecks passed, but translated BAR2 still failed. No extra usable memory or P2P was proved. The ordinary CPU/GSP page-table join is the next diagnostic lead. See [driver candidates](driver-candidates.md).

Stage45 tested D/E root handoff diagnostics and F without BAR1 forcing. Both RPCs returned zero and independent eight-byte CPU/GSP root reads matched, but D/E still failed BAR2. F restored both CMPs and checked 8-MiB copies passed on all three GPUs. Six working-F P2P capabilities remain zero. This is recovered baseline usability, not additional capacity. See [driver candidates](driver-candidates.md).

Stage47 traced the normal guest discovery policy and independent fresh firmware-approval query, then compared BIOS definitions offline and read only the two relevant stored PCI settings. Both switches were already selected. No driver/firmware/VM change or GPU trial followed. See [discovery and firmware](discovery-and-firmware.md).
