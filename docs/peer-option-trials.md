# Pair-option trials: activation and data are different outcomes

The single `ForceP2P=0x11` option on unchanged G now advertises the tested CMP pair and allows peer activation. **Working P2P data access was not demonstrated.** The peer-copy trial and separate direct remote-read trial both ended with a wrong destination hash in host readback. The later local-transfer diagnostic passed all twelve checks around activation. A subsequent independent GPU verdict establishes actual remote-read mismatches, with and without an ordinary owner cache flush.

## Bounded observed results, 17 October

| Trial | Observed result | Scope |
|---|---|---|
| Initial dispatch | Observer incorrectly rejected a normal PMA debug success message | No peer calls; harness error, not a GPU/P2P finding |
| Peer copy, completed 19:16 UTC | Forced capability 1; activation returns success; `cuMemcpyPeer`, synchronization and D2H all return 0; full 1-MiB destination hash is wrong | CMP40-owned data to CMP64; one peer copy, no peer kernel |
| Direct remote read, completed 19:20 UTC | Ordinary source/destination transfers pass before activation; activation returns success; remote-read kernel launch, synchronization and D2H return 0; destination hash is wrong | CMP64 reads CMP40; one 1-MiB remote-read kernel, no peer copy; remote write/reverse data direction not reached |
| Activation diagnostic, completed 19:23 UTC | All 12 ordinary 1-MiB comparisons pass, with 0 wrong bytes and changed host sentinels | Both directed activations; before enable, immediately after enable, and fresh upload after enable; no peer copy/kernel |

All owned-resource cleanup calls returned success in the completed data and diagnostic tests. Each mismatching data trial used the prepared recovery to remove its option and return to G. The final diagnostic retains the explicit option after checked cleanup and an eight-second delayed readiness observation. This retained setting is a test state, not a working-P2P configuration. No host reboot, IOMMU/ACS change, topology-field change, static-BAR1 or P2P-type forcing occurred. Blackwell received no test allocation or kernel, and its model was not restored.

## What the wrong hashes mean

Both wrong destination hashes equal the SHA256 of 1 MiB of zero bytes. Those earlier D2H host buffers were initially zero, so an unchanged result buffer remains a possible explanation. We do not claim that peer memory physically contained zeros or that the peer copy was a no-op.

The later diagnostic starts every D2H destination with fresh random sentinels and checks complete ordinary local data on both cards before and after activation. All twelve outputs match their expected data and replace their host sentinels. Thus activation alone did not break ordinary local transfer in that diagnostic. It does not certify the earlier result channel after an actual peer command. Forced capability, activation, copied bytes, remote read and remote write stay separate outcomes.

No framebuffer-size, memory-clock or SM setting was changed. These communication tests decide neither physical HBM capacity nor the foreign large-memory reports. Our separate [coherent 80-GiB alias result](cache-alias.md) remains an observed mapping failure; 48 GiB is a first capacity target, not a proven ceiling. The next peer approach needs a sourced mapping/transport difference, or a result channel independent of the failed operation, before another data replay. [Selected API statuses, comparisons, source hashes and counts](../data/peer-data-trials.json).

## Independent GPU verdict and owner-cache variation

The new verifier reads every one of 131,072 remote 64-bit words in a 1-MiB CMP40 allocation from CMP64. It counts both visited words and mismatches on the GPU. A separate local publisher writes the verdict into 64 bytes of mapped pinned host memory, with a fresh nonce, phase, complement and system fence. The CPU validates that protocol and the actual checked-word count. A separate 64-byte D2H result starts with a random host sentinel and is compared with the mapped result. This reuses the earlier checker components without rerunning their baseline controls. [NVIDIA mapped-host API](https://docs.nvidia.com/cuda/cuda-driver-api/group__CUDA__MEM.html), [PTX system fence](https://docs.nvidia.com/cuda/parallel-thread-execution/#parallel-synchronization-and-communication-instructions-membar).

| Scoped trial | GPU verdict | Independent result transport | Owner source |
|---|---|---|---|
| Stage73, no explicit cache flush | 131,072 checked; 131,072 wrong | Fresh mapped verdict valid; separate D2H matches it and changes its sentinel | Complete 1-MiB source matches before and after |
| Stage75, owner write-back/invalidate/full-cache before peer read | Flush control returns 0; 131,072 checked; 131,072 wrong | Fresh mapped verdict valid; separate D2H matches it and changes its sentinel | Complete 1-MiB source matches before and after |

Both verifier and publication launches, synchronizations and cleanup return success. Each trial launches one remote-read verifier and one local result publisher; neither calls peer copy or writes the peer's memory. The additional ordinary source-owner control is `FB_FLUSH_GPU_CACHE` (`0x2080130e`, flags `0x38`). Its temporary RM client is released successfully. The flush did not repair this tested route. These results rule out a stale D2H destination as the explanation of the Stage73/75 verdicts; they do not retroactively attest the older Stage69/70 channels or identify the bad returned values.

Two preparation failures are recorded separately. Stage72 lacked the deployed guest worker and ran no CUDA data test; its overly broad recovery caused one test-guest restart and two exclusive CMP resets. Stage74 used an unsupported device-query field; it stopped before any cache flush or peer activation, cleaned up its local allocation, and used one guest restart without CMP resets. The deployed-file check and the proven XML lookup replace those mistakes. Clean pre-peer preparation failures no longer justify a reset or restart.

Stage73 and Stage75 each used one guest restart to apply the explicit option, with no deliberate CMP bus reset. G is unchanged; the option remains a diagnostic setting after the final readiness observation. No additional usable GiB or SM is established. The original large-memory positive reports remain open. Further peer work needs a concrete mapping or selected-transport difference, rather than another identical option/flush trial. [Curated counts, statuses and hashes](../data/peer-data-trials.json).
