# Real-model parallelism: working inference, native P2P still unavailable

**Later application result:** The [owned CUDA-buffer adapter and actual PP2 model follow-up](cuda-application-transport.md) now demonstrate direct CE activation transfers and a matched speed comparison. The five native CUDA/NCCL runs below retain their original SHM-only scope.

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

## Can the application be forced onto P2P?

Observed follow-up on 19 October 2026 with the installed NCCL **2.29.7**: explicitly allow P2P, set its maximum topology distance to `SYS`, leave direct buffer access allowed, disable SHM, and disable lazy runtime connection so the channel choice is visible before a payload collective. The communicator uses one channel and a 1 MiB NCCL buffer limit. Both directed CUDA peer queries remain false. Every actual directed channel selects **`NET/Socket/0`**. A require-direct check rejects that route, and both communicators are destroyed successfully. **Zero payload collectives and zero additional model requests** were run. This is a transport-selection refusal, not a socket data-transfer test or a P2P speed result. [Curated settings and observations](../data/p2p-policy-trial.json).

NVIDIA's [environment documentation](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/env.html#nccl-p2p-level) describes `P2P_LEVEL` as a distance cutoff and explicitly says disabling SHM permits network fallback. The matching pinned [P2P transport source](https://github.com/NVIDIA/nccl/blob/b91894bd5b190c874d98a017f93f5daa515b65d0/src/transport/p2p.cc) checks `cudaDeviceCanAccessPeer` before accepting the route, including when its `P2P_USE_CUDA_MEMCPY` option is selected. [Transport selection](https://github.com/NVIDIA/nccl/blob/b91894bd5b190c874d98a017f93f5daa515b65d0/src/transport.cc) tries P2P, SHM and NET in that order. These are static source findings, distinct from the observed channel choice.

`IGNORE_DISABLED_P2P=1` suppresses diagnostic messages; the special value 2 skips NVML validation for hardware-simulating unit tests. The separate CUDA capability gate remains. These settings were source-inspected, not run as fake-capability experiments. Removing a fallback therefore cannot supply the missing peer mapping. A useful next mechanism needs to connect real CUDA/NCCL buffer exports to the proven native windows, with stream completion and reference cleanup, or supply a correctly qualified general peer mapping. Neither integration was built in this follow-up. The successful bounded kernel-owned CE copies remain valid within their original scope.

The local route parser was then extended offline to accept NCCL's explicit `[send]`/`[receive]` tags. Six parser cases, including actual socket lines and separately labelled synthetic P2P fixtures, pass. The executed version already rejected the observed socket route correctly; the parser correction was not a new hardware run or P2P result.
