# Bounded load and effective memory bandwidth at 1350 MHz

On 16 October 2026, the Samsung 40-GiB CMP170HX (`10de:2082`) completed one requested additional load observation at **1350 MHz with a configured 175-W limit**. The recurring research task remains paused.

| Timed path | Intended load interval | Effective bandwidth, read+write | Fraction of 1728 GB/s interface arithmetic |
|---|---:|---:|---:|
| CUDA internal device-to-device copy | 30 s | 1534.8 GB/s (1.535 TB/s) | 88.8% |
| SM streaming kernel: read A+B, XOR, write C | 60 s | 1538.1 GB/s (1.538 TB/s) | 89.0% |

These are total-requested-byte / total-CUDA-event-time rates across all timed batches, not the single best sample. The active-bus model gives 1350 MHz × 2 DDR × 5120 bits / 8 = **1728 GB/s**. No new topology measurement or matched 1215-MHz bandwidth baseline was performed, so the 11.11% clock increase is not a measured 11.11% application or bandwidth improvement.

## Method and correctness scope

Three 512-MiB device buffers use 1.5 GiB total, far beyond the cache working set. Two independently generated 1-MiB random blocks repeat across the two inputs. A full 512-MiB output is checked by SHA256 after warmup, approximately every 15 s, and at each phase end. The XOR expectation is calculated separately on the CPU. All **8 full-output checks passed**; buffers, events, module and private context were released.

CUDA events surround 128 operations per batch. Copy counts 2N bytes (one read plus one write); the 16-byte-vector streaming kernel counts 3N (two reads plus one write). Host transfers, hashing and telemetry are outside timed intervals. Requested read+write accounting follows NVIDIA's [effective-bandwidth definition](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html#effective-bandwidth-calculation). This is effective global-memory throughput for these patterns, not a hardware DRAM-bus counter or a traced claim about which engine implements the CUDA copy.

The lab kernel uses 4096 blocks of 256 threads, grid-stride 16-byte vectors, L2-cache-policy loads and write-back stores. Launch geometry was fixed, not optimized in a parameter search. Checks apply to the tested working set and sampled outputs, not every iteration or all 40 GiB.

## Observed load behavior and limits

- Memory clock stayed at 1350 MHz in the recorded samples; power limit stayed 175 W. Maximum sampled board draw: **193.3 W**.
- Some NVML power samples exceeded the reported configured limit. Their cause was not determined; these spot readings are not wall power, a continuous average or proof of a hard 175-W ceiling.
- Maximum sampled GPU temperature: **51 °C**; HBM temperature: **72 °C**. Samples are approximately 5 s apart, not continuous maxima.
- No CUDA failure, mismatching checked output or new kernel-log Xid was observed in this run. SM count and ECC were not requalified.
- This bounded 90-s observation is not long-term stability, maximum clock, full-VRAM integrity or LLM performance qualification. A model was not loaded for this test.
- No clock/register/reset change or further load run was scheduled. Automatic continuation remains paused.

Evidence time: 2026-10-16T20:21:16.308274+00:00. Curated per-phase totals, percentile summaries, matching hashes and non-identifying telemetry are in [bandwidth-load.json](../data/bandwidth-load.json).
