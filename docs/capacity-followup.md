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
