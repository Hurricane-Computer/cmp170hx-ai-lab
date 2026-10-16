# Configured framebuffer size and reservation accounting

This is static original-code and public-source analysis. No hardware access or extra usable-memory result is claimed.

## The exact release's public size reader

The official NVIDIA tag **615.71.09** resolves to commit `61dcc93722ecb418bb5f2e00923f05b4b8051dd1`. Its [GA100 dispatch](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/generated/g_kern_mem_sys_nvoc.c#L363) selects `kmemsysReadUsableFbSize_GP102`. The [reader](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/src/kernel/gpu/mem_sys/arch/pascal/kern_mem_sys_gp102.c#L36) performs one read of `NV_PFB_PRI_MMU_LOCAL_MEMORY_RANGE` at `0x100ce0`:

`size_bytes = uint64(MAG) << (SCALE + 20)`

The included [register header](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/common/inc/swref/published/pascal/gp102/dev_fb.h#L26) defines MAG as **bits9:4**, SCALE as **bits3:0**, and ECC_MODE as bit30. If that bit is enabled, the reader applies `/16*15`. This is a conditional source contract; no current ECC mode was rechecked. The formula returns bytes, despite a brief source comment mentioning MB.

| Example input word | Decoded size before the ECC-mode adjustment |
|---|---:|
| `0x208` | 8 GiB |
| `0x28a` | 40 GiB |
| `0x20b` | 64 GiB |
| `0x28b` | 80 GiB |
| `0x50a` | **16 GiB** |

These are offline calculations, not observed memory values or write recommendations. In particular, bit10 is outside this reader's magnitude field; interpreting `0x50a` as 80 GiB would use the wrong field width.

The reader attributes the lower range values to **VBIOS Devinit**. It does not query HBM stack identities, train memory or validate physical addresses. The metadata constructor subsequently consumes a configured size; it is not an independent physical inventory.

## Exact-version metadata comparison

The exact release's [legacy metadata header](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/arch/nvalloc/common/inc/gsp/gsp_fw_wpr_meta.h) and [normal constructor](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/src/kernel/gpu/gsp/arch/turing/kernel_gsp_tu102.c#L619) are byte-identical to the previous public-source counterparts. The actual constructor uses **GspFwWprMetaV1**, asserts **256 bytes**, obtains `fbSize` through the normal getter and calculates the reservation boundary from its heap layout.

The dispatch, reader and included register header are also byte-identical at the exact release. Thus the six-bit magnitude is version-matched. The separate [seven-field legacy-layout candidate](startup-memory.md) still lacks an independent link to the original ECALL buffer; matching the release does not settle that service/type question.

## An original formatter on both variants

The existing original-ROM disassemblies contain an actual LMR formatter: **CMP40 App45 `0x624f..0x62a4`**, **CMP64 App45 `0x626f..0x62c4`**. Visible operations normalize the current r2 value into a six-bit magnitude and four-bit scale, insert the one-bit ECC mode and preserve other register fields. These operations agree with the public field contract.

This is a formatter of an input value, not a proved physical-geometry discovery routine or the sole initial Devinit producer. The current r2 input and the earlier saved size argument r4 remain the precise source boundary. Unexpanded calls and their register-preservation contract also bound the analysis. Adjacent protection logic and the existing access helpers were not expanded. No new write sequence is derived.

## Original region accounting

The connected initializer `0x4a5d80c` first describes `[0,T-1]`, then inserts the upper region `[R,T-1]` with its reserved flag. A strict **193-instruction CPU evaluation** of original insertion `0x4a58e4c` and its two actual helpers produces `[0,R-1]` plus reserved `[R,T-1]`; only the first region remains in the allocation-priority list. The inputs were deliberately illustrative **16-MiB total / 12-MiB boundary**, not card measurements.

The selected insertion leaves scalar fields `+0x698` and `+0x6c0` unchanged. Subsequent local caller arithmetic adds `R-T` to the former and `T-R` to the latter. With the caller's initial `T` and zero, these become `R` and `T-R`. This evaluates the insertion and its two normal helpers, not the entire outer initializer or all earlier callees. Firmware code addresses here are virtual addresses, not PCIe MMIO offsets.

This explains why the initializer's first total-byte assignment is not a permanent free-memory value. Size reporting, reservation accounting and genuinely backed HBM remain separate. The next physical-capacity lead needs the actual normal geometry source, not another larger LMR or software-size assignment.

Curated contracts, source hashes and the bounded synthetic result are in [usable-size.json](../data/usable-size.json).
