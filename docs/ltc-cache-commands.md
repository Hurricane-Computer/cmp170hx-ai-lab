# Cache commands previously labelled as capacity decode

The values `0x70000300` and `0x10000300` at `0x17e2a0` are explained by cache-operation classes and a completed command. They are not a per-channel HBM-capacity encoding. This finding corrects the register interpretation in the [third-party 80-GiB comparison](https://github.com/Consensus-Protocol/cmp170hx/blob/d923a25fb2ecb6ee3d62654983f453194b66485f/docs/frontier/80gb.md). It does **not** refute the separately reported positive 75/76-GiB or 77.5/72-GiB write/read tests.

## Original GA100 code and public definitions

The saved GA100/key42 constructor trace selects original class `0x174e21` slot `+0xa08` as function `0x4a06eec`. This normal function takes operation flags, selects the last register-range object from the [previously connected range array](ltc-register-layout.md), writes relative offset `0x2a0` through its established ordinary write32 interface, then polls bit0 through read32 until completion or timeout. This is static analysis of the unchanged 615.71.09 GSP, SHA256 `78e0a2c8e4bd8a2faa1ff36137209669cdf60bd698b8f723dcf52869df82b909`; no proprietary firmware or disassembly is distributed here.

The [exact-release NVIDIA L2-control flag definitions](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/common/sdk/nvidia/inc/ctrl/ctrl2080/ctrl2080internal.h) name the input flags ALL, FIRST, LAST, NORMAL, CLEAN and WAIT_FB_PULL. The original selected code maps those class flags as follows:

| Requested class | Input flag | Invalidate command | After pending bit0 clears |
|---|---|---|---|
| ALL | `0x1` | `0x70000301` | `0x70000300` |
| FIRST | `0x2` | `0x40000301` | `0x40000300` |
| LAST | `0x4` | `0x10000301` | `0x10000300` |
| NORMAL | `0x8` | `0x20000301` | `0x20000300` |

These rows describe command construction; we did not issue four internal controls or directly write these words. NVIDIA's [public NvGPU GA10B definitions in a pinned mirror](https://github.com/OE4T/linux-nvgpu/blob/21d928824dc7ca3dc17603a53b11edc6641ace2d/drivers/gpu/nvgpu/include/nvgpu/hw/ga10b/hw_ltc_ga10b.h) independently name this address `TSTG_CMGMT0`: bit0 is invalidate-pending, `0x300` sets the invalidate spacing, and the three high masks select LAST/NORMAL/FIRST eviction classes. GA10B definitions alone would not prove a GA100 contract; here their exact numeric layout agrees with the original GA100-selected writer and completion poll.

Relative `0x2a4` is the corresponding clean-command register. Its public definitions use the same class masks, clean-pending at bit0, and `0x10000` for waiting for framebuffer pull. Neither command word measures installed memory.

## The `2b4` companion

The same existing GA100 trace selects slot `+0x880` as `0x4a02a0c`. With its object `+0x86d9` guard set, it reads the last range's relative `0x2b4`, ORs `0x00a00000`, and writes back through the normal interface. The matching public GA10B definitions call that register `TSTG_SET_MGMT_3` and identify those two bits as disallowing immediate clean for CE and FCLR. These matching fields support a cache-policy interpretation. They are not a physical-stack inventory or a new density switch. The static guard's current value and execution of that function were not observed.

## One bounded live trial on each CMP

At **2026-10-17T16:52:03.621530+00:00**, each idle card received one documented public `FB_FLUSH_GPU_CACHE` control (`0x2080130e`) with flags `0x38`: video memory, write back, invalidate, full cache. The ordinary API returned success and temporary RM-client cleanup returned success on both. We did not invoke the internal L2 command, force a successful result, patch the driver or directly write MMIO. Twelve total read-only register observations bracketed the two calls; no VRAM was allocated.

| Card | Reported memory before → after | Memory clock | `2a0` before → after | `2a4` before → after | `2b4` before → after |
|---|---|---|---|---|---|
| CMP40 | 40960 → 40960 MiB | 1215 MHz | `70000300` → `70000300` | `70010300` → `70000300` | `30` → `30` |
| CMP64 | 65536 → 65536 MiB | 1728 MHz | `70000300` → `70000300` | `70010300` → `70000300` | `30` → `30` |

The same `2a0` value is present on both different reported-capacity configurations. The immediate clean-register observation changes in a manner consistent with the documented operation; neither reported memory nor clock changes. We did not capture a firmware execution trace, prove the physical cause of earlier aliases, test data retention across the flush, qualify full memory or unlock extra HBM/SMs.

The practical addition is a working ordinary cache-flush route on both cards for a future carefully bounded data test. A meaningful follow-up must connect data written before the flush to checked data read afterwards, with independent result transfer. Cache-command residues must not be counted as extra-memory evidence. [Structured source anchors and observations](../data/ltc-cache-commands.json).
