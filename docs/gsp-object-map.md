# Original GSP object and GA100 selection

Evidence level: static analysis of the unchanged615.71.09 `gsp_tu10x` input. No hardware execution or firmware modification was performed in this study.

## Connected original path

The original initializer assigns metadata405aaf0, whose class pointer4070010 contains classID7ef3cb and original object size0x5728. The pinned public NVIDIA class definition independently identifies that classID as OBJGPU. The original object points its+88 member to its own+40 subobject; the ChipHal value is therefore at object+50.

The original mapping code, rather than just a newer source enum, maps architecture17/implementation0 to key42. The method constructor at530737c splits this into group1/bit10. The original mask03f8fc00 selects the branch530931c, forms getter4b78dc0, and stores it at object+348 via5308e20. The complete small getter returns820000.

Thus the proven chain is:

`original OBJGPU → own GA100 mapping42 → original slot348 → getter4b78dc0 → 820000`.

## What this resolves

The slot's return value is no longer merely an inference from an unrelated object's offset. Current public headers corroborate the classID and chip mapping, but their field order and method names are not assigned to the older closed GSP layout. In particular, the current host method named `gpuGetPrimaryFuseBaseAddr` is not used as an unproven name for this binary slot.

## What remains open

Of126 original load candidates at slot+348, a conservative local object-alias filter found13 calls with the same object passed in a0. Seven fully traced functions read mapped status; no new topology write was found. They are not directly installed as final method targets by the traced GA100 construction branch. Ordinary static helper calls remain possible, but a specific active GA100 caller/object bridge is still needed.

The next concrete research step is an actual GPC/FBP status producer or consumer connected to this identified original GPU object. The constructed getter alone is not an unlock, a new mask address, or evidence of additional usable memory or SMs.

Public primary corroboration: [OBJGPU definition](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/ca2d03e6fafd4d4b56b383497d931c25b283bfcf/src/nvidia/generated/g_gpu_nvoc.c), [chip mapping](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/ca2d03e6fafd4d4b56b383497d931c25b283bfcf/src/nvidia/generated/g_chips2halspec_nvoc.c). Input hash and curated code points: [data/gsp-object-map.json](../data/gsp-object-map.json).
