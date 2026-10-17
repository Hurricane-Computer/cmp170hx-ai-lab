# Normal CPU-RM geometry adoption and the CUDA admission boundary

On 17 October 2026 at approximately 23:21 UTC, a normal proprietary 615.71.09 start with GSP disabled retained both CMPs' existing geometry and reported 40/64 GiB. **The first CUDA call returned 101 before a context, allocation or copy.** This establishes register/report continuity through the ordinary driver lifecycle; it does not establish usable additional HBM or a working CPU-RM CUDA allocator.

| Variant | Reported MiB in CPU-RM | CFG1 before/after | LMR before/after | HBM_CFG0 before/after | CPU-mode data proof |
|---|---:|---|---|---|---|
| CMP40 |40960|`0x02669000`|`0x28a`|`0xa7`|None; CUDA initialization stopped first|
| CMP64 |65536|`0x02779000`|`0x20b`|`0xa7`|None; CUDA initialization stopped first|

The unchanged working Open modules were normally unloaded; stock proprietary modules of the **same version** were loaded with `NVreg_EnableGpuFirmware=0` and the existing `NVreg_EnableResizableBar=0` policy. The loaded proprietary module identity matched the separately built artifact and both CMPs reported GSP firmware `N/A`. No driverless chain, custom geometry write or firmware modification was used in this comparison. Normal drivers still perform their own initialization writes.

NVIDIA documents proprietary Ampere support and the [normal GSP-disable parameter](https://download.nvidia.com/XFree86/Linux-x86_64/615.71.09/README/gsp.html), while Blackwell requires [Open modules](https://download.nvidia.com/XFree86/Linux-x86_64/615.71.09/README/kernel_open.html). The actual 615.71.09 Runfile was fully checked against its [vendor SHA256](https://download.nvidia.com/XFree86/Linux-x86_64/615.71.09/NVIDIA-Linux-x86_64-615.71.09-no-compat32.run.sha256sum); its proprietary core is present. Removal of proprietary distribution packages in 615 does not mean that this Runfile is absent. No proprietary payload is distributed here.

## The admission failure has not been assigned a cause

`cuInit(0)` returned `CUDA_ERROR_INVALID_DEVICE` (101). NVIDIA's [cuInit reference](https://docs.nvidia.com/cuda/cuda-driver-api/group__CUDA__INITIALIZE.html) explicitly permits this error; the flags argument 0 is not a device ordinal. The planned 8-MiB check never reached its first allocation. Returning to the unchanged working Open driver made the same matched-version CUDA library initialize successfully and enumerate all three GPUs.

Two different candidate explanations remain unproved:

- The proprietary driver's Blackwell probe failed with its explicit Open-module requirement. Blackwell was absent from the proprietary NVML inventory, but its frontend also logged rejected opens. This is an observed compatibility issue, not proof that it caused CUDA 101. No GPU exclusion or process-visibility comparison was applied.
- The archived working build recipe applies a CMP product-information patch. For the two CMP IDs it changes the normal `GPU_GET_INFO` field `CMP_SKU` to NO. The [official field](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/common/sdk/nvidia/inc/ctrl/ctrl2080/ctrl2080gpu.h) is index `0x3c`, NO 0 / YES 1. Its live value under either manager and its consumer in the closed CUDA library were not measured. It is a concrete classification candidate, not a proven compute-enable flag or fix.

Automatic attempts to load the installed Open UVM companion while the proprietary core was active produced symbol errors. The explicit separately built proprietary UVM module then loaded successfully; its loaded source identity was not independently captured. A later comparison must keep this distinction explicit. These errors do not prove a hardware-memory fault.

## Limits and next discriminating step

The proprietary unload warned about remaining objects in `nvidia_stack_cache`. The guest kept running and the returned Open driver's CUDA initialization succeeded. A further mode comparison should start from a fresh guest boot, with the actual companion identities captured; the warning is not treated as clean teardown proof or as a reason to repeat resets without a new configuration.

The next small comparison should isolate the documented device-admission issue before any additional-capacity allocation. A single-CMP process selection or a source-bound normal GPU exclusion can distinguish an enumeration interaction. If that does not explain the failure, compare the ordinary CMP_SKU field before considering a change. Successful selection alone would still not demonstrate extra HBM.

For CMP40, a later larger-geometry comparison with a different working manager could distinguish the earlier GSP-mode fold result. For CMP64, additional healthy controllers or a legitimate larger-region contract remain separately unproved. Neither path permits guessing controller writes. The attributed 75/76 and 77.5/72 GiB positive reports remain open, and 48 GiB remains a first CMP40 goal without setting a ceiling.

[Selected structured observations and exact package/core hashes](../data/cpu-rm-capacity.json). Existing [capacity follow-up](capacity-followup.md).
