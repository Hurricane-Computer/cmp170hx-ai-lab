ifndef NVIDIA_SOURCE
$(error Set NVIDIA_SOURCE to the pinned open driver source tree)
endif
obj-m += cmp_ce132.o
ccflags-y += -I$(NVIDIA_SOURCE)/kernel-open/common/inc
ccflags-y += -I$(NVIDIA_SOURCE)/src/common/sdk/nvidia/inc
