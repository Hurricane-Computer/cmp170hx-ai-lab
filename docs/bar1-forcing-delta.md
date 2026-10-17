# Exact final BAR1 forcing delta: E to working F

This is the last tested source difference, not a complete installer or a proven minimal set of driver changes. F retains the earlier uncached CPU BAR2 mapping and root diagnostics. [Observed scope and results](driver-candidates.md) distinguish the working baseline from additional memory or P2P.

The zero-context patch uses the listed input fingerprint as its base. It removes two existing fork forcing writes and the global ResizableBar override while retaining passive snapshots and native policy. In this guest the parameter was zero, both CMPs retained the original passive values and all three GPUs passed checked 8-MiB copies. It does not establish which forcing element was responsible individually or how a native host would behave.

- Input file SHA256: `736793e5d8f11b6ccf21370977ad9a7d1c9b68ec4527d3560d65d7c7ac909930`
- Output file SHA256: `e5659bf84222ded51f5465202548866e6388831f4dda7d230ad6548f26aec9a9`
- Exact UTF-8 patch SHA256: `58583d6751b0a45856cfbee16d522fd98b9c56eaf96e27445f13e9330d173493`
- Working module SHA256: `29c491f1c02b0d11d9b314c299094f61c834d3a4079846df30ffa92ca715f229`

```diff
diff --git a/kernel-open/nvidia/nv-pci.c b/kernel-open/nvidia/nv-pci.c
--- a/kernel-open/nvidia/nv-pci.c
+++ b/kernel-open/nvidia/nv-pci.c
@@ -512 +512 @@
-        "NVRM: CMP BAR1: before CYA=0x%08x CFG=0x%08x CAP=0x%08x\n",
+        "NVRM: CMP BAR1 passive: before CYA=0x%08x CFG=0x%08x CAP=0x%08x\n",
@@ -515,2 +515 @@
-    writel(0x30,         pcfg + 0x724);
-    writel(0x8000000A,   pcfg + 0xDCC);
+    /* CMP diagnostic F: no BAR1 force writes. */
@@ -522 +521 @@
-        "NVRM: CMP BAR1: after  CYA=0x%08x CFG=0x%08x CAP=0x%08x\n",
+        "NVRM: CMP BAR1 passive: after  CYA=0x%08x CFG=0x%08x CAP=0x%08x\n",
@@ -527 +525,0 @@
-    NVreg_EnableResizableBar = 1;
@@ -529 +527 @@
-        "NVRM: CMP BAR1: resize enabled, will attempt up to 64 GB\n");
+        "NVRM: CMP BAR1 passive: force writes and parameter override disabled\n");
```

The NVIDIA file's [upstream notice](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/615.71.09/kernel-open/nvidia/nv-pci.c#L1) identifies MIT licensing. The forcing implementation is attributed to the [pinned fork](https://github.com/admunch888/cmpunlocker/blob/7d86a7f8f4ac3abbd0f48fa6d6cd09aa6b953f03/driver/patches/bar1-resize-unlock.patch). No driver binary, firmware, access helper or private configuration is included. Upstream notice retained:

```text
Copyright (c) 2019-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
```
