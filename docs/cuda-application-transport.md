# Actual CUDA buffers and model activations over the small-window CE path

Observed on 19 October 2026: the mixed CMP40/CMP64 pair passed direct copies of real CUDA allocations, ordinary PyTorch pool views across two processes, and **actual pipeline activations of the existing 51.75-GiB R3 V3 BF16 checkpoint**. Source and destination hashes match for every transferred model tensor. Both CMPs retain 64 MiB BAR1. No motherboard BIOS change was needed. [Selected data](../data/cuda-application-transport.json).

This extends the [kernel-owned CE proof](window-ce-proof.md). Native CUDA peer capability still reports false in both directions, and ordinary NCCL still does not select this route. The application uses a deliberately isolated adapter for its PP2/TP1 activation dictionaries. No fake peer capability or success status is injected.

## Evidence in increasing scope

- Six real-CUDA data cases pass: 1 MiB random sources, 1 MiB GPU-produced sources, and 65,540-byte transfers with different source/destination offsets, in both directions. Full CPU and independent GPU comparisons pass, including untouched destination sentinels and source rechecks. Both GPU verifiers detect a deliberately changed word at index 17. Total payload: 4,325,384 bytes.
- Two ordinary PyTorch processes transfer a 5,123-byte view and a 2 MiB + 123-byte view in each direction. Full GPU-generated expected tensors and outside-view guards match. Total payload: 4,204,796 bytes. Both processes exit normally; CUDA peer queries remain false.
- Two real-model CE variants and a matched native SHM baseline each complete the three fixed sequential fixtures and four concurrent requests. A separate 16-token pilot is excluded from speed measurements. Model activation tensors use actual native copies, and independently computed full source/destination SHA256 must match before release.

## Buffer and execution contract

The exporter synchronizes the owning CUDA device, sets `SYNC_MEMOPS`, and exports a real allocation subrange with ordinary DMA-BUF flags 0. Export windows are 64-KiB aligned, bounded by the actual allocation and at most 1 MiB. Tensor offsets and multi-window payloads are handled explicitly. A private Unix descriptor channel carries shapes, metadata, descriptors and hashes. **It never carries activation payload bytes.** CPU reads for validation are nevertheless real work and are included in timing.

The first normal duplication attempt refused the export's kernel client with numeric RM status 27, before a data copy. The revised entry accepts only a held, validated NVIDIA-owned export and duplicates that legitimate object using the native kernel-to-kernel contract. The ordinary UVM duplication entry and its kernel-client rejection remain unchanged. The core validates ownership, memory kind, ranges and real device identity; maps only the held export's actual source range; obtains real native DMA addresses and destination pages; and keeps references through fresh GPU semaphore completion, FIFO retirement and teardown.

vLLM 0.29.0's actual `GroupCoordinator.isend_tensor_dict` / `irecv_tensor_dict` path is replaced only for the selected PP2 group with TP1. The synchronous prototype returns no pending work only after the actual copy and hash acknowledgement. Source tensors and export descriptors remain alive throughout. Other native control/output collectives can still use SHM. This is not an NCCL transport plugin or a tensor-parallel collective implementation.

## Measured application speed

|Variant|Activation transport|Median sequential decode estimate tok/s|Median TTFT ms|Four-request aggregate tok/s|
|---|---|---:|---:|---:|
|pp2-ce-validated|CE windows|3.32|641|5.61|
|pp2-shm-matched|NCCL SHM|20.10|135|45.70|
|pp2-ce-payload-only|CE windows|10.57|229|20.76|
|pp2-ce-persistent|CE windows, held channel|18.18|153|38.92|

All rows use the [same fixtures and settings](model-parallel.md#common-configuration): max 384 output tokens, temperature 0 / seed 42, BF16, eager execution, no drafting/thinking/prefix cache. Sequential decode estimates and aggregate response speed are different metrics. These four rows are a direct application comparison; the earlier five-row TP/PP matrix remains a native-SHM observation.

The first adapter repeats local qualification allocation/fill/copy/MMIO comparisons for every chunk. The explicit payload-only mode skips those redundant diagnostics and honestly reports `local_done=0`. Its first real peer command initializes the channel; `peer_done=1`, fresh completion, bounds, lifetime, cleanup and full model-tensor hashes remain mandatory. Existing qualification modes keep their controls. This changes diagnostic overhead, not peer capability or the data verdict.

The first payload-only attempt returned EIO because the old wrapper still required `local_done=1`, despite a fresh peer completion. It stopped before destination-data verification and supplies no positive data verdict. The corrected explicit-mode contract requires the real peer completion and its own truthful local-control state; userspace still rejects every ioctl error. The complete GPU data/guard qualification then passes in both directions.

Full validation readbacks remain in all direct variants. The first two CE variants repeat native session/channel setup for each chunk; the persistent variant holds those resources as described below. These measurements do not give peak P2P bandwidth, and the presence of a direct path does not guarantee an inference speedup. 6/7 initial-CE and 6/7 payload-only answer hashes match the SHM baseline. That is a small deterministic-output observation, not formal quality/logit equivalence.

## Persistent native contexts and small TP collectives

A later separate root-only consumer holds native session/devices/VA/TSG/channel/push backing per open direction. It performs the 64-KiB local qualification once, records a context generation and monotonically increasing use count, and keeps payload `local_done=0`. Held DMA-BUF imports, native duplicates and bounded real source windows remain per-request. Fresh GPU semaphore completion and actual FIFO GET/PUT retirement are still required before release or push reuse. Uncertain work retains backing/module references and blocks further requests.

The independent two-process test passes **20 directed tensors / 4,729,860 bytes / 24 requests on two contexts, 12 uses each**. Full GPU expected tensors, source/destination hashes and outside-view guards pass. Both contexts are released on close. The real PP2 model then transfers **2,682 activation tensors / 42,803,200 bytes on one context with 2,682 uses**, exceeding the 1,024-entry FIFO ring. Every full tensor hash and lifecycle check passes. Three total sessions/channels across qualification and model are created and closed; no context/module reference remains. The earlier consumer, core and recovery files remain available. [Selected persistent and collective data](../data/persistent-collective-transport.json).

Median sequential decode rises from 10.57 to **18.18 tok/s**, with median TTFT 153 ms and four-request aggregate 38.92 tok/s. The matched earlier SHM reference is 20.10 / 135 ms / 45.70 tok/s. No unchanged baseline is replayed. The same seven measured request hashes are used; 6/7 answer hashes match SHM, which is not formal quality/logit equivalence. Full CPU validation readbacks remain in timing, so these are diagnostic application observations rather than peak transport bandwidth. vLLM still emits process-manager/resource-tracker shutdown warnings; native session destruction succeeds and both GPUs actually settle idle.

On the unchanged persistent transport, **10 all-reduce-sum and 10 all-gather contracts** then pass. Both real inputs are sent to the opposite GPU in deterministic role order; CUDA add or rank-ordered concatenation computes each result locally. Both ranks independently generate expected inputs and compare every output value: 40 GPU verdicts, matching full rank-output hashes, unchanged source/scratch guards and two deliberate result-checker errors detected. The tests cover int32/float32/BF16, scalar-size, two-dimensional gathers along both axes, an input above 2 MiB, and alternating repeated calls. Floating patterns use bounded exact eighths, allowing exact sum checks without a hiding tolerance. The 40 actual directed inputs / 4,317,000 bytes use 44 requests and two contexts, both closed.

These are synchronous out-of-place application collective prototypes, **not an NCCL backend or a TP model run**. Ordinary CUDA peer queries remain false. Rank order and matching counts/dtypes follow the [NCCL2.29.7 semantic contract](https://docs.nvidia.com/deeplearning/nccl/archives/nccl_2297/user-guide/docs/usage/collectives.html); no NCCL support is implied. Arbitrary numerical reductions/nonfinite data, more ranks, async Work/streams and other operations need separate qualification. Channel-destroy counters count actual API calls, not an independent hardware acknowledgement; successful native session destruction and zero live references are also checked.

## Limits and remaining work

Both cards return idle in the final read-only snapshots and selected GPU/kernel error checks remain clean. After all 14 initial measured requests completed, the initial harness's immediate post-shutdown idle assertion saw 564 MiB on CMP64 with zero clients and stopped. A later snapshot confirmed zero use on both; the original error remains recorded and no measurement was replayed. The payload-only harness waits up to 45 seconds for teardown accounting to settle. vLLM shutdown also prints IPC semaphore/shared-memory cleanup warnings; those are separate from native CE backing, whose per-request retained/cleanup statuses remain zero. The temporary core and separate consumer are left available; known working boot/recovery files are preserved.

No general remote SM pointer mapping, stock CUDA peer activation, native NCCL P2P, actual TP model, long stability or reboot persistence is qualified. No HBM capacity or SM count is added. Exact TP-model collective coverage, retained import/lease caching, less intrusive validation and a proper stream-aware application backend remain follow-up work.

Static contracts: NVIDIA's pinned [DMA-BUF implementation](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/kernel-open/nvidia/nv-dmabuf.c), [RM GPU operations](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/src/kernel/rmapi/nv_gpu_ops.c), [Ampere CE HAL](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/kernel-open/nvidia-uvm/uvm_ampere_ce.c), [CUDA memory API](https://docs.nvidia.com/cuda/archive/13.0.0/cuda-driver-api/group__CUDA__MEM.html), and [vLLM 0.29.0 parallel-state source](https://github.com/vllm-project/vllm/blob/v0.29.0/vllm/distributed/parallel_state.py). Experimental extensions and observed data are distinct from those upstream contracts.
