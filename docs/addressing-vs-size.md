# Register addresses, size reports and actual HBM mapping

Static analysis on 17 October 2026 separates two normal code paths from physical HBM address decoding. **No new GPU access or configuration change was made.** The [previous upper-window alias](cache-alias.md) remains the last hardware result.

## A register-block translator

An original 615.71.09 helper at `0x4a58824` computes these ordinary success results, expressed as32-bit addresses:

| Selector | Index condition | Result |
|---|---|---|
| 0 | index0 | `0x9a0000 + (offset & 0x3fff)` |
| 1 | ordinary representable index | `0x900000 + index*0x4000 + (offset & 0x3fff)` |
| 2 | ordinary representable index | `0x980000 + index*0x4000 + (offset & 0x3fff)` |

The normal success branches return register addresses; they do not write hardware or translate a tensor's high HBM address. Their numerical layout agrees with [NVIDIA's published FBPA MMIO ranges](https://github.com/NVIDIA/open-gpu-doc/blob/master/pascal/gp100-fbpa.txt). The [subsequent per-controller analysis](controller-amounts.md) now binds the helper to the existing physical-context GA100 trace, slot520. That closes the earlier selection gap without changing its register-address semantics. Neither an older architecture's unit-count limit nor its mixed-density programming bit is assumed to apply here.

## Nouveau has two distinct sizing routes

At pinned Linux commit `c7decec2f2d2ab0366567f9e30c0e1418cece43f`, the [GA100 callback table](https://kernel.googlesource.com/pub/scm/linux/kernel/git/torvalds/linux/+/c7decec2f2d2ab0366567f9e30c0e1418cece43f/drivers/gpu/drm/nouveau/nvkm/subdev/fb/ga100.c) selects a GP102 size reader. That [reader](https://kernel.googlesource.com/pub/scm/linux/kernel/git/torvalds/linux/+/c7decec2f2d2ab0366567f9e30c0e1418cece43f/drivers/gpu/drm/nouveau/nvkm/subdev/fb/gp102.c) parses the configured LMR word at `0x100ce0`: magnitude bits9:4, exponent bits3:0, and a15/16 factor if bit30 is set. Derived examples `0x28a` and `0x28b` therefore parse as40 and80GiB when bit30 is clear. These are source calculations, not fresh card measurements. The [non-GSP allocator](https://kernel.googlesource.com/pub/scm/linux/kernel/git/torvalds/linux/+/c7decec2f2d2ab0366567f9e30c0e1418cece43f/drivers/gpu/drm/nouveau/nvkm/subdev/fb/ramgp102.c) uses this scalar size less its head/tail reservations.

GSP mode takes a different branch: [r535_fb_new](https://kernel.googlesource.com/pub/scm/linux/kernel/git/torvalds/linux/+/c7decec2f2d2ab0366567f9e30c0e1418cece43f/drivers/gpu/drm/nouveau/nvkm/subdev/fb/r535.c) replaces the RAM constructor. That constructor imports the GSP's framebuffer size and allocation regions. It must not be described as the same non-GSP LMR allocation path. These four files do not close the upstream firmware producer of those fields.

In either case a larger driver display, or an allocator accepting its size/regions, is insufficient proof of independently backed extra memory. Nouveau was not installed or executed in this study. This finding adds no usable GiB, sets no physical40-GiB ceiling and does not refute the positive third-party large-memory tests. Source fingerprints and the exact scope are in the [structured extract](../data/addressing-vs-size.json).
