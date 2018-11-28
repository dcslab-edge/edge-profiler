# coding: UTF-8

from typing import Iterable, Set


def convert_to_set(hyphen_str: str) -> Set[int]:
    ret = set()
    for elem in hyphen_str.split(','):
        #mapping wrong character "\n"
        elem_stripped = elem.rstrip()
        if elem_stripped!='' :
            group = tuple(map(int, elem_stripped.split('-')))
            if len(group) is 1:
                ret.add(group[0])
            elif len(group) is 2:
                ret.update(range(group[0], group[1] + 1))
    print("well stripped")
    return ret


def convert_to_hyphen(core_ids: Iterable[int]) -> str:
    # TODO
    return ','.join(map(str, set(core_ids)))
