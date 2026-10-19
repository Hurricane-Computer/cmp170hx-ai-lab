# Stage132 bounded CE window consumer

**One 1 MiB peer read passed in each direction on the mixed CMP40/CMP64 pair, 19 October 2026.** The [measurement and limits](../../../docs/window-ce-proof.md) are separate from general application P2P. This is experimental kernel-owned test code, not a general CUDA/UVM P2P implementation or an automatic installer.

Files deliberately published here:

- `cmp_ce132.c`: the tested kernel consumer, including a 64 KiB local CE control, nonce/index-dependent data, full comparisons and a separate GPU semaphore completion.
- `cmp_ce_abi.h`, `cmp_rm_abi.h`: exact declarations from the pinned native MIT interface; ordinary types still come from the real driver headers.
- `cmp_window_ce_lease.inc`: private kernel-only acquire/release selector, with validated allocation/pair/bounds and actual native lease addresses.
- `cmp_window_native.inc`: the native adapter with the three measured mapping diagnostics. Only its leading historical compile-only comment is updated; [hashes](../../../data/window-ce-trials.json) distinguish published and tested text.
- `nv-gpu-ops-window-hook.patch`: the small source hook against pinned615.71.09's `nv_gpu_ops.c`. It does not contain the inherited G patches or advertise a general peer route.
- `Makefile`: caller compilation against an explicit source tree. `LICENSE.NVIDIA` accompanies adapted NVIDIA MIT code; our adaptation is MIT.

Use the existing [parent lease implementation](../cmp_window_lease.h). In a **separate**, preserved615.71.09 research source tree, apply/check the hook, place that header and this native adapter beside `nv_gpu_ops.c`, and copy `cmp_window_ce_lease.inc` there under the included name `cmp_window_probe.inc`. Build the core with its usual kernel configuration. Then build the caller against that same tree and its generated `kernel-open/Module.symvers`:

```sh
make -C /lib/modules/$(uname -r)/build M="$PWD" \
  NVIDIA_SOURCE="$NVIDIA_SOURCE" \
  KBUILD_EXTRA_SYMBOLS="$NVIDIA_SOURCE/kernel-open/Module.symvers" modules
```

This compiles code; it does not install or load anything. The measured source tree inherited G, whose baseline changes are documented in [mailbox P2P](../../../docs/mailbox-p2p.md). A vanilla build was not separately qualified.

Runtime requires the two GPUs' ordinary device files to be held open through registration, a single admitted kernel test session, actual UUID/device identity matching, idle GPUs and exclusive test ownership. `owner_uuid`, `accessor_uuid`, `owner_gib` and fresh nonzero32-bit `nonce` parameters select the bounded pair. The GPU must report C56F/C6B5 and ordinary passthrough, and a real supported non-GR system-memory CE must exist. No numeric physical address is accepted as a module parameter.

The module's finish record is the verdict, **not** successful insertion. It distinguishes local completion, peer attempt, peer completion, wrong words, RM status and retained backing. If the command times out or the lease cannot be safely retired, the module retains its references and prevents removal; recover the test guest instead of freeing active backing or forcing module removal. Native void cleanup calls remain an acknowledgement limit. The published run did not exercise this timeout recovery.

No managed migration, general foreign mapping, SM pointer read, fatal-client teardown, concurrent-window scheme, production boot integration, bandwidth result or additional HBM is supplied by this component. Only the explicit small kernel-owned CE route was tested.
