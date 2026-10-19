# Real-model parallelism: working inference, native P2P still unavailable

Observed on 19 October 2026: the existing **R3 V3 BF16 checkpoint (51.75 GiB of files)** generated responses on the mixed CMP40/CMP64 pair with both tensor parallelism (TP2) and pipeline parallelism (PP2). Each was tried with native automatic P2P selection permitted and with P2P explicitly disabled. CMP64 alone used the same checkpoint as a baseline. All 35 measured responses were nonempty; selected native GPU/kernel error checks were clean.

**None of these model runs used direct GPU peer memory.** Fresh Torch/CUDA capability queries were false in both directions. The final NCCL channel logs identify shared host memory for every two-GPU run. The earlier [successful 1 MiB native-window CE experiment](window-ce-proof.md) remains a real direct copy result, but its private kernel-owned allocation/lease hook is not called by CUDA/NCCL for model buffers.

## Short speed observation

| Variant | Actual transport | Median single-request decode estimate, tok/s | Median TTFT, ms | Four-request aggregate response tok/s |
|---|---|---:|---:|---:|
| TP2, native auto | NCCL_SHM | 16.88 | 193 | 40.87 |
| TP2, P2P disabled | NCCL_SHM | 17.46 | 145 | 41.45 |
| PP2, native auto | NCCL_SHM | 20.15 | 143 | 45.94 |
| PP2, P2P disabled | NCCL_SHM | 20.19 | 138 | 46.68 |
| CMP64 alone | single_gpu | 19.52 | 133 | 46.04 |

The single-request column is the median of three SSE estimates `(completion_tokens-1)/(last_arrival-first_arrival)`. TTFT is HTTP request start to first output arrival. The aggregate column counts all four responses over their common wall interval, including prompt processing and scheduling. These are different metrics, not interchangeable GPU kernel throughput. Model load and one 16-token warmup are excluded.

The three [fixed synthetic fixtures](../data/model-parallel-fixtures.json) test German explanatory text, a short Python function and fruit-box logic. Parallel mode repeats the text fixture as its fourth simultaneous request; it does not run the historical vision fixture. The limit is 384 output tokens, so `length` is an ordinary recorded finish reason. This is a functional/speed sample, not a formal quality evaluation, full-range VRAM check or long stability qualification. Output/logit equivalence across parallel backends was not established.

## Common configuration

vLLM 0.29.0, Torch 2.13.0+cu130, CUDA runtime 13.0, Transformers 5.17.0 and driver 615.71.09. All variants use BF16 weights, FlashAttention, 8192 context, 2048 maximum batched tokens, four maximum sequences, 2 GiB KV reservation **per GPU**, four CPU threads, greedy temperature 0/seed 42, no thinking, no prefix caching or speculative drafting, and eager execution. The optional FlashInfer sampler and custom all-reduce are disabled consistently. The two-GPU modes use actual multiprocessing TP2/PP2, not a single-GPU model hidden behind a router. [Measurements and per-request sizes](../data/model-parallel-trials.json) include observed GPU allocation peaks and clocks.

This checkpoint fits the 64-GiB card alone but exceeds the 40-GiB card's capacity. It gives a useful same-model baseline for distributing the weights; it is not an example requiring both cards' entire combined capacity. BF16 without drafting/eager execution must not be compared directly with earlier INT4/DFlash or graph-enabled results as if only the GPUs differed.

## Why auto is not a P2P-on result

`NCCL_P2P_DISABLE=0` permits supported native selection; it does not construct an unavailable route. NVIDIA documents that [P2P disable controls direct GPU communication, while SHM is the host-memory fallback](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/env.html#nccl-p2p-disable). The actual `via SHM/direct/direct` channels matter, not a generic `p2p channels` count or `Using network Socket` bootstrap message.

Small differences between auto and disabled runs are observations under the **same effective data transport**. They are not measured P2P speedups. No topology result, driver capability or registration failure was forced to success. A genuine P2P model comparison remains unavailable until normal communication buffers and their CUDA-stream/lifetime contracts are connected to the proven allocation-specific window mechanism.

## Setup corrections and final scope

The first server attempt loaded weights and initialized SHM, then optional sampler warmup failed because no CUDA compiler was installed. Restoring the historical source-supported sampler fallback fixed that requirement. A nested retry path then exceeded the 107-byte Unix-socket limit; a short dedicated task temp path resolved it. These are benchmark setup errors, not peer-data failures. The five measured variants share the corrected configuration.

Final transport extraction uses the completed server logs after shutdown; an earlier live snapshot lacked buffered channel lines. Only this lab's temporary loopback test servers were stopped between variants. No host IOMMU/ACS, BIOS, firmware, clock, driver or boot configuration changed, and no VM/GPU reset occurred. The original G/F recovery baselines remain preserved. This experiment establishes working distributed inference and a scoped speed comparison; it adds no memory or SMs and does not qualify direct application P2P.
