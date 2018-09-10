# coding: UTF-8

import asyncio
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Optional

import aiofiles
from aiofiles.base import AiofilesContextManager


def len_of_mask(mask: str) -> int:
    cnt = 0
    num = int(mask, 16)
    while num is not 0:
        cnt += 1
        num >>= 1
    return cnt

class ResCtrl:
    MOUNT_POINT = Path('/sys/fs/resctrl')
    MAX_MASK: str = Path('/sys/fs/resctrl/info/L3/cbm_mask').read_text(encoding='ASCII').strip()
    MIN_BITS = int((MOUNT_POINT / 'info' / 'L3' / 'min_cbm_bits').read_text())
    MAX_BITS = len_of_mask((MOUNT_POINT / 'info' / 'L3' / 'cbm_mask').read_text())

    def __init__(self) -> None:
        self._group_name: str = str()
        self._group_path: Path = ResCtrl.MOUNT_POINT

        self._monitors: Dict[str, List[AiofilesContextManager]] = \
            dict(llc_occupancy=list(), mbm_local_bytes=list(), mbm_total_bytes=list())

    @property
    def group_name(self):
        return self._group_name

    @group_name.setter
    def group_name(self, new_name):
        self._group_name = new_name
        self._group_path: Path = ResCtrl.MOUNT_POINT / new_name

    async def create_group(self) -> None:
        proc = await asyncio.create_subprocess_exec('sudo', 'mkdir', '-p', str(self._group_path))
        await proc.communicate()

        for mon in (self._group_path / 'mon_data').iterdir():
            llc_monitor_path = mon / 'llc_occupancy'
            local_mem_path = mon / 'mbm_local_bytes'
            total_mem_path = mon / 'mbm_total_bytes'

            self._monitors['llc_occupancy'].append(await aiofiles.open(llc_monitor_path))
            self._monitors['mbm_local_bytes'].append(await aiofiles.open(local_mem_path))
            self._monitors['mbm_total_bytes'].append(await aiofiles.open(total_mem_path))

    async def add_tasks(self, pids: Iterable[int]) -> None:
        for pid in pids:
            proc = await asyncio.create_subprocess_exec('sudo', 'tee', str(self._group_path / 'tasks'),
                                                        stdin=asyncio.subprocess.PIPE,
                                                        stdout=asyncio.subprocess.DEVNULL)
            await proc.communicate(str(pid).encode())

    async def assign_llc(self, *masks: str) -> None:
        masks = (f'{i}={m}' for i, m in enumerate(masks))
        schemata = 'L3:{}\n'.format(';'.join(masks))

        proc = await asyncio.create_subprocess_exec('sudo', 'tee', str(self._group_path / 'schemata'),
                                                    stdin=asyncio.subprocess.PIPE,
                                                    stdout=asyncio.subprocess.DEVNULL)
        await proc.communicate(schemata.encode())

    @staticmethod
    def gen_mask(start: int, end: Optional[int] = None) -> str:
        if end is None or end > ResCtrl.MAX_BITS:
            end = ResCtrl.MAX_BITS

        if start < 0:
            raise ValueError('start must be greater than 0')

        ret_mask = format(((1 << (end - start)) - 1) << (ResCtrl.MAX_BITS - end), 'x')
        return ret_mask

    @staticmethod
    def cbm_ranges_to_list(cbm_ranges: str) -> List[List[str]]:
        splited_cbm_ranges = cbm_ranges.split(',')
        cbm_ranges_list = [cbm_range.split('-') for cbm_range in splited_cbm_ranges]
        return cbm_ranges_list

    async def read(self) -> Tuple[int, int, int]:
        ret = list()

        for mons in self._monitors.values():
            s = 0

            for mon in mons:
                await mon.seek(0)
                line = await mon.readline()
                s += int(line)

            ret.append(s)

        return tuple(ret)

    async def delete(self) -> None:
        for mon_list in self._monitors.values():
            for mon in mon_list:
                await mon.close()

        proc = await asyncio.create_subprocess_exec('sudo', 'rmdir', str(self._group_path))
        await proc.communicate()
