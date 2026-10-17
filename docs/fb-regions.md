# Exported framebuffer regions

On 17 October 2026 at 13:00 UTC, the ordinary NVIDIA RM `GET_FB_REGION_INFO` control succeeded on both CMP variants under the retained G driver. This reads the memory manager's exported region table; it does not allocate or fill framebuffer memory. All temporary RM handles were released successfully. No driver, service or hardware setting changed.

| Variant | Reported total | Exported base | Inclusive limit | Exported range size | Relative performance field |
|---|---:|---:|---:|---:|---:|
| cmp40 | 40 GiB | `0xa100000` | `0x9eca9ffff` | 39.540649 GiB | 20 |
| cmp64 | 64 GiB | `0x10080000` | `0xfe95cffff` | 63.395813 GiB | 16 |

Each card returned **one** region, with compression/ISO support and without protected status. There was no second exported upper range. These range sizes differ from the reported totals because this is a filtered allocation view, not a package-capacity inventory. The performance fields are not measured TB/s or an established inter-card ratio.

The [official export handler](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/src/kernel/gpu/mem_mgr/mem_mgr_ctrl.c#L641) omits reserved and internal-heap regions. Its [GSP client initialization](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/nvidia/src/kernel/gpu/mem_mgr/mem_mgr_gsp_client.c#L37) imports base regions from GSP static configuration. The [public ABI](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/common/sdk/nvidia/inc/ctrl/ctrl2080/ctrl2080fb.h#L852) defines inclusive limits and up to 16 entries. The examined export handler does not assign the region-tag field, so the query does not interpret its zero-initialized value as a measured tag.

## The mixed-region hypothesis remains separate

[NVIDIA's earlier FBPA note](https://github.com/NVIDIA/open-gpu-doc/blob/master/pascal/gp100-fbpa.txt) describes non-contiguous lower/upper mapping for certain mixed-memory configurations. This is a reason not to treat an old linear alias failure as a test of every possible layout. It does not establish that GA100 implements an unlockable alternative on either of these CMPs. No legacy mixed-mode register was changed and no speculative high-address probe was made.

The new observation excludes only an already-exported second region in this retained configuration. Disabled, unexposed or differently initialized physical storage remains outside the query. A distinct future approach needs an applicable region producer and mapping mechanism before a live memory experiment. The external [capacity counterevidence](capacity-evidence.md) remains open.

[Curated values, source hashes and ABI sizes](../data/fb-regions.json).
