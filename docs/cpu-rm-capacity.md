# Normal CPU-RM geometry adoption and CUDA admission

## New CMP-only result: both cards pass small CPU-RM copies

On 17 October 2026 at 23:48 UTC, **both CMPs initialized CUDA and passed bounded H2D/D2D/D2H copies under the unchanged proprietary 615.71.09 CPU-RM driver with GSP disabled**. This closes the ordinary CPU-RM admission obstacle for this configuration. It establishes a working allocator and small data path, with zero additional usable GiB demonstrated so far.

| Variant | Reported MiB | cuInit / visible count | Temporary buffers | Full returned-data comparison | Native CMP_SKU: Open → CPU |
|---|---:|---|---|---|---|
|CMP40|40960|0 / 1|2 × 8 MiB|SHA256 matched|NO 0 → YES 1|
|CMP64|65536|0 / 1|2 × 8 MiB|SHA256 matched|NO 0 → YES 1|

The comparison started with a fresh guest kernel because of the earlier teardown warning. After normal Open-module unload, the existing Blackwell function received Linux's documented [`driver_override=none`](https://github.com/torvalds/linux/blob/v6.8/Documentation/ABI/testing/sysfs-bus-pci#L323-L342) before proprietary module loading. It remained unbound; only the two CMPs bound to NVIDIA. This changes normal driver matching and leaves the PCI device present. No IOMMU/ACS change, bus reset, geometry write or firmware modification was used.

The exact loaded proprietary core and UVM source identities were both independently checked against the stock built modules. An Open modeset module also autoloaded; this is recorded separately and does not become a claim that every companion was stock. Each fresh CUDA process selected one currently observed complete CMP UUID before its first CUDA call and checked that the returned PCI identity matched its intended card. All CUDA, full-buffer readback and cleanup calls succeeded. No performance or full-capacity qualification follows from 16 MiB of live buffers per card.

Native `GPU_GET_INFO` queries and cleanup also succeeded on both cards under both managers: the working Open build returned `CMP_SKU=NO`, while the unmodified stock CPU driver returned `YES`. **YES alone therefore does not prevent CUDA in the successful CPU configuration.** No CPU classification patch was needed. This does not identify the closed CUDA consumer or prove that the field is irrelevant in every configuration.

The prior error 101 was replaced by success in the combined fresh-kernel, Blackwell-unbound, matched-UVM, single-CMP-visible configuration. These simultaneous changes do not isolate one sole cause. NVIDIA emitted the expected unprobed-device warning for the deliberately unbound Blackwell; it was not silently counted as another initialized device.

CPU-RM remains active for the next capacity work; Blackwell remains unbound and the normally stopped RTX cooling service's full-fan stop policy remains in effect. Installed Open modules and the frozen rollback were preserved; the model was not restarted. The next proposed comparison is a normal larger-geometry initialization followed by this now-working manager, with small independently tagged lower/upper data windows. It has not yet run. CMP64 still separately needs an applicable additional-controller or larger-region producer; no unsupported mask writes follow from this admission result.

[Selected native call statuses, exact module identities, hashes and limits](../data/cpu-rm-admission.json).

## Earlier mixed-device comparison: report continuity, then CUDA101

The following is the earlier 23:21 UTC observation and the questions it left open at that time. The later successful result above supersedes its untested-admission status, while preserving the actual failure and teardown warning.

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
