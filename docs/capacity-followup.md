# Capacity report follow-up and small verifier controls

## One proposed difference was already tested

Our historical 20 September sample used NVIDIA 610.43.03, CFG1 `0x02779000`, LMR `0x28b` and an 80-GiB framebuffer declaration, matching the principal fields in the [attributed 75/76-GiB report](https://gist.github.com/sekkit/b30da03773768d0cd4e3de18e0619656/2f65500f3c81609f7d46522b1c7df5dea16dd5c6). Its 47-GiB test exposed upper-write/lower-corruption aliasing. Repeating those declarations alone would not distinguish a new approach. Common fields do not establish identical patches, samples or runtime state. The foreign positive result remains open.

## New live control: the checker detects a deliberately wrong word

On 17 October at 13:24 UTC, both CMPs ran a new bounded check in their supported 40/64-GiB configurations. Each context requested three 8-MiB chunks, 1 MiB of staging and 64 B of device results: **26,214,464 bytes of VRAM**, plus 64 B of mapped host results. All chunks were filled before verification.

| Fill path | Clean result, each card | One deliberately changed word, each card |
|---|---:|---:|
| Device kernel | 0 errors | 1 error at global word 1,048,593 |
| Host-to-device copy | 0 errors | 1 error at global word 1,048,593 |
| Host copy to staging, then kernel copy | 0 errors | 1 error at global word 1,048,593 |

The GPU reduced mismatches in device memory and published a 64-byte verdict by two paths: a checked device-to-host copy and a system-fenced write to mapped host memory. Fresh nonce, phase, completion and complement fields were verified; host buffers began with non-result sentinels. Both verdicts matched in all 12 cases. Every called CUDA operation was checked, including cleanup. The subsequent readiness read succeeded and found no new GPU kernel errors.

This validates the small verifier control and its intentional-error detection. It does not qualify 40, 64 or 75 GiB, identify the actual physical copy engine, measure bandwidth, or reproduce a foreign success or failure. No accepted 74-SM/ECC baseline was requalified. No geometry, clocks, driver or services changed and no reset was used.

## Matching-version fault anchor

The original [NVIDIA 610.43.03 release](https://download.nvidia.com/XFree86/Linux-x86_64/610.43.03/) was downloaded as data; its full package SHA256 matched the vendor checksum. The unchanged `gsp_tu10x.bin` member was read without running the installer. Its SHA256 is `73065619db9ec921d19fc4e519dd04d91a9199b525eaca9b257b89fb8c5ec52c`.

In that exact image, the recurring reported PC `0x5b2ba28` maps to a byte load through an ordinary RM object-pointer chain. It is not enough to name a copy-engine routine or establish the original cause. The report supplies no runtime register set or effective fault address for resolving that pointer. Other listed PCs were mapped only to file-backed sections; addresses outside them do not establish their original cause. No firmware patch follows from this observation, and no original firmware or derived assembly is distributed here.

The next capacity approach still needs a distinct applicable physical-layout mechanism. The checked small verdict path can then be reused, without routinely repeating this control or the completed CPU alias demonstration. [Selected values, source hashes and 12 case records](../data/capacity-followup.json).

## Ordinary region policy is not a new physical map

The pinned public NVIDIA 615.71.09 [HAL binding](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/generated/g_mem_mgr_nvoc.c) selects `memmgrHandleSizeOverrides_GP100` for GA100 despite the older suffix. The [handler](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/src/kernel/gpu/mem_mgr/arch/pascal/mem_mgr_gp100.c) only restricts existing allocatable regions: an override above a row's limit skips that row; otherwise it reserves the suffix while retaining the original limit and subtracting usable bytes. Raising this override does not create another address range.

The same public build's ordinary non-VF base-region path imports GSP-supplied regions. Its later region HAL returns success without adding a region. Changing those software tables alone would not establish a different physical HBM map.

Separately, original-firmware analysis found the ordinary `RMIgnoreUpperMemory` lookup and a conditional Boolean cache write in the original MemoryManager. That name and cache write do not establish an applicable upper-region producer, a changed address decoder, or a useful unlock. Same-offset accesses in unrelated objects were kept separate. No raw firmware or derived assembly is distributed.

This was an offline source result, with no hardware access or new capacity/SM test. It does not set a physical capacity ceiling or refute the attributed 75/76 and 77.5/72-GiB results. The useful next target is a distinct applicable physical address-layout producer, rather than a size-cache toggle or repetition of the scalar/carveout path. Source hashes and scope are recorded in the [structured follow-up](../data/capacity-followup.json).

## Normal manager-mode follow-up

A later [ordinary CPU-RM comparison](cpu-rm-capacity.md) retained both cards' geometry and reported 40/64 GiB without GSP, but CUDA initialization returned 101 before the first allocation. This is a distinct admission boundary, not another upper-memory data result.

The subsequent fresh-kernel CMP-only configuration passed small CPU-RM allocation/copy checks on **both** cards. Stock CPU-RM returned `CMP_SKU=YES` while CUDA succeeded. The [updated comparison](cpu-rm-capacity.md) records both this admission result and the subsequently completed larger-geometry data trial; the cause of the earlier error 101 remains unresolved.

## Whole-mechanism comparison on both variants

The entire retained H `kernel_gsp.c` is now checked: reversing exactly its three capacity constants reproduces G's complete file hash. H introduces no fourth change in that file. This establishes the H/G delta; it does not establish byte-identical drivers or startup conditions with either foreign positive run.

| Variant and configuration | CFG1 | LMR | Logical export |
|---|---|---|---|
| CMP40 / G | `0x02669000` | `0x28a` |40 GiB|
| CMP40 / H | `0x02779000` | `0x28b` |80 GiB|
| CMP64 / G and H | `0x02779000` | `0x20b` |64 GiB|

Both normal profiles already include the shared stores `0x82381c=0x88888888` and `0x823820=0x8`; this audit does not establish a new native field meaning for them. The later logical export also conditionally changes the last region's limit, reserved length and attributes. A larger allowed range remains separate from independent backing.

The [later original owner report](https://gist.github.com/sekkit/b30da03773768d0cd4e3de18e0619656/2f65500f3c81609f7d46522b1c7df5dea16dd5c6) describes the same three coherent CMP40 values under 610.43.03 Open/GSP; its two additional build-check literals are not extra runtime geometry writes. The distinct [July 77.5/72-GiB account](https://github.com/Consensus-Protocol/cmp170hx/blob/d923a25fb2ecb6ee3d62654983f453194b66485f/docs/frontier/80gb.md) remains a maintainer-attributed account without the complete original initialization script or checker. Its broad manager handoff resembles the completed H-to-CPU trial, but the original ordinary ordering and side conditions are not fully known. Our observed alias therefore neither validates nor refutes those foreign results.

For CMP64, the [original ES/g250 report](https://github.com/amoghmunikote/cmpunlocker/commit/a3ea84b251db490d73a12b3fffbc9e6658e6b0cd) explicitly concerns 20c2, but describes **8 to 32 GiB on a single-rank variant**. It does not show 32 to 64 GiB on that same card or 20c2 to 80/96 GiB. Our archived CFG0 bits 0/1 are already set; repeating them supplies no new input. The inspected normal public path and H retain the known 64-GiB profile.

No additional ordinary physical address/backing or availability input was identified, so no unchanged geometry, rank-bit or CPU-handoff trial follows. The useful missing evidence is the complete ordinary positive-run initialization contract, or a separately sourced physical mechanism with a different effect. This source comparison adds **zero usable GiB** and sets no physical ceiling. [Hashes, scoped source relations and decisions](../data/capacity-followup.json) preserve the result.
