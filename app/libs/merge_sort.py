"""안정 합병 정렬 — C-1 (상위 N개 정렬·동률 처리).

동률에서 입력 순서를 보존하므로, 다양성 후처리 전 원본 순위를 유지하는 데 쓴다.
"""
from __future__ import annotations

from typing import Callable, TypeVar

T = TypeVar("T")
Key = Callable[[T], float]


def merge_sort(items: list[T], key: Key, reverse: bool = False) -> list[T]:
    if len(items) <= 1:
        return list(items)
    mid = len(items) // 2
    left = merge_sort(items[:mid], key, reverse)
    right = merge_sort(items[mid:], key, reverse)
    return _merge(left, right, key, reverse)


def _merge(left: list[T], right: list[T], key: Key, reverse: bool) -> list[T]:
    out: list[T] = []
    i = j = 0
    while i < len(left) and j < len(right):
        lk, rk = key(left[i]), key(right[j])
        take_left = (lk >= rk) if reverse else (lk <= rk)
        if take_left:
            out.append(left[i])
            i += 1
        else:
            out.append(right[j])
            j += 1
    out.extend(left[i:])
    out.extend(right[j:])
    return out
