# coding: UTF-8

import subprocess
from typing import ClassVar

from .cgroup import Cgroup
from .machine_type import NodeType, MachineChecker


class GPUDVFS:
    # FREQ_RANGE_INDEX : 0 ~ 11
    GPU_TYPE = MachineChecker.get_node_type()
    # ARCH = 'desktop'
    FREQ_RANGE = list()
    JETSONTX2_GPU_FREQ_RANGE = [140250000, 229500000, 318750000, 408000000, 497250000, 586500000, 675750000, 765000000,
                                854250000, 943500000, 1032750000, 1122000000, 1211250000, 1300500000]
    DESKTOP_GPU_FREQ_RANGE = [345600, 499200, 652800, 806400, 960000, 1113600, 1267200, 1420800,
                              1574400, 1728000, 1881600, 2035200]  # GPU Server nodes
    # TODO: Desktop GPU Freq Range should be re-initialized (BC5 freq..)
    MIN_IDX: ClassVar[int] = 0
    STEP_IDX: ClassVar[int] = 1  # STEP is defined with its index
    MAX_IDX: ClassVar[int] = 13  # MAX of Jetson TX2 GPU Freq.
    if GPU_TYPE == NodeType.IntegratedGPU:
        MIN: ClassVar[int] = JETSONTX2_GPU_FREQ_RANGE[0]
        MAX: ClassVar[int] = JETSONTX2_GPU_FREQ_RANGE[13]
        FREQ_RANGE = JETSONTX2_GPU_FREQ_RANGE
    elif GPU_TYPE == NodeType.DiscreteGPU:
        MIN: ClassVar[int] = DESKTOP_GPU_FREQ_RANGE[0]
        MAX: ClassVar[int] = DESKTOP_GPU_FREQ_RANGE[11]
        FREQ_RANGE = DESKTOP_GPU_FREQ_RANGE

    def __init__(self, group_name):
        self._group_name: str = group_name
        self._cur_cgroup = Cgroup(self._group_name, 'cpuset')

    @staticmethod
    def get_freq_range():
        return GPUDVFS.FREQ_RANGE

    @staticmethod
    def set_gpu_freq(target_freq: int) -> None:
        """
        Set the freq. to the specified cores
        :param target_freq: freq. to set
        :return:
        """
        # GPU Path /sys/devices/17000000.gp10b/devfreq/17000000.gp10b/userspace/set_freq
        subprocess.run(args=('sudo', 'tee', f'/sys/devices/17000000.gp10b/devfreq/17000000.gp10b/userspace/set_freq'),
                       check=True, input=f'{target_freq}\n', encoding='ASCII', stdout=subprocess.DEVNULL)
