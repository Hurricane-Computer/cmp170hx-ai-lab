# Pair-option trials: activation and data are different outcomes

The single `ForceP2P=0x11` option on unchanged G now advertises the tested CMP pair and allows peer activation. **Working P2P data access was not demonstrated.** The peer-copy trial and separate direct remote-read trial both ended with a wrong destination hash in host readback. The later local-transfer diagnostic passed all twelve checks around activation.

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
