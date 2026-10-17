# Current findings

Updated16 October2026. See[data/](../data/README.md) for the corresponding structured extracts.

## Memory and variants

- The observed2082 variant identifies Samsung density4/8-High memory, consistent with8 GiB per full stack. The20c2 variant identifies SKHynix densityA/8-High, consistent with16 GiB.
- Existing driver reports are40 and64 GiB. Additional actually usable48/80/96 GiB has not been established by this campaign.
- The active logical FBP counts observed in the older memory experiments were10 forCMP40 and8 forCMP64. Logical controllers, full HBM stacks, profile columns and memory layers are different things.
- The known five8-GiB-stack-equivalent and four16-GiB-stack-equivalent configurations explain the current capacities. Actual additional populated and functional stacks remain an open question.

## Compute

The owner had already established74 working SMs. A bounded review of the [original 70→74 implementation](https://github.com/amoghmunikote/cmpunlocker/pull/55) confirms eight full-byte reconfiguration overrides; the earlier observations already had `ff` on all eight. That same block provides no additional 2082/20c2 parameter or wider field, and this does not prove a universal physical 74-SM maximum. New source-vector measurements show that the two raw firmware-selected vectors cannot simply be renamed as the effective TPC-disable masks. Their precise hardware meaning remains unresolved. No additional working SMs were demonstrated.

## Memory-size interpretation

The original GA100 sizing getter corresponds to NVIDIA's FLA virtual-address-space calculation: both 40- and 64-GiB FB inputs can return 128 GiB. This is not evidence of extra HBM. The normal physical GSP memory-size/region source remains open. One connected conditional parameter path now writes the real base sizing fields. Its guard is connected to an original creator mode; both input globals now trace to a buffer passed to an earlier success-checked ECALL. The buffer contract and intervening calls remain open. No extra physical backing is demonstrated. See [Startup inputs](startup-memory.md). Original class routing now connects the sizing getter's GPU+0x1e80 child to MemoryManager and separately identifies GPU+0x1e78 as KernelMemorySystem. The later lifecycle path consumes existing sizes; its OverrideFbSize cache is a separate field. These are source anchors, not extra-capacity results. See [Memory sizing](memory-sizing.md).

## Firmware and configuration

The exact 615.71.09 public GA100 reader decodes a VBIOS-configured memory range, with six magnitude bits. An original formatter is present on both CMP variants, but its normal physical-geometry input is not closed. One original CPU-only region-insertion case separately resolves usable-versus-reserved bookkeeping. See [Configured size and region accounting](usable-size.md).

- The ordinary RPR path is now traced from original App01 output to original App45 consumption. Its primary register helper ORs requested bits into the read value; a special mirror has distinct semantics. It is not a discovered general enable script.
- Original App08 captures the effective FBPA-disable mask and uses it in24 configuration entries, two completion polls and a later constrained table path. The entries for the disabled units already exist in the original data.
- All twelve examined original CMP/A100/A800 images have the same16-byte Memory Partition Information Table. Their Memory Script List and RAMMAP pointers are zero. The six table records are not proof of six working HBM stacks.
- The original GSP object chain is now connected: OBJGPU, original GA100 ChipHal42, slot0x348 and getter0x4b78dc0 returning0x820000. Seven separately traced local consumers are status readers; their active GA100 call bridge is not established and they do not provide a topology writer. See[GSP object map](gsp-object-map.md).

## Clock

The CMP40 cold-initialization clock input reached 1242, 1269, 1296, 1323 and now **1350 MHz**, versus the original 1215 MHz (+11.11%). Each step passed a short 64-MiB copy roundtrip. An upper clock limit has not been determined; no worldwide-first claim is made. CMP64 already had an1836-MHz setting before this campaign; its older BIOS-reported maximum was1728 MHz. No fresh long-term clock qualification is claimed. See[Clock notes](clocks.md).

A subsequent one-off load at1350MHz measured1534.8GB/s for internal copies and1538.1GB/s for an SM streaming kernel, counting reads+writes. All checked outputs passed; this does not establish long-term/full-memory stability or LLM throughput. See[bounded load](bandwidth-load.md).

## Hypotheses that remain hypotheses

The CMP40 may belong to the40-GB A100 memory family and CMP64 to the80-GB family. Manufacturer and density are consistent with this comparison; neither proves that a particular CMP was previously a completed A100. Manufacturing binning, product segmentation, disabled stack population and stack health cannot be inferred from marketing labels alone.


## Enclosing topology gates, 17 October

The [complete normal topology wrappers](topology-gates.md) distinguish a special literal `0x20b0` block from CMP64's additional source-vector tail. Four source-bound read-only observations resolve the two current inputs without retrying old mask writes. This is a conditional source-routing result, not extra live resources or captured production execution.


## Normal register-layout route, 17 October

The original GA100 method selection and class metadata now connect a [register-range builder](ltc-register-layout.md) to the address families discussed in the capacity reports. The builder creates range descriptors; the actual field at relative offset `0x2b4` and its value producer remain open. No new hardware experiment or capacity gain follows yet.


## Cache-command correction and ordinary flush, 17 October

The follow-up [original GA100 consumers](ltc-cache-commands.md) explain `17e2a0` values `70000300`/`10000300` as completed ALL/LAST cache commands, correcting their use as per-channel capacity labels. One ordinary write-back/invalidate flush succeeded on each idle CMP; `2a4` changed while reported40/64GiB and clocks stayed constant. No new usable HBM or SM. The positive75/76GiB and77.5/72GiB reports remain open.
