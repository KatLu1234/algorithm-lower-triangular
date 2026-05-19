"""정렬된 키 배열 위의 이진 탐색 — A-2 / B-1 / B-3에서 짝꿍·다음 후보 조회용."""
from __future__ import annotations

from typing import Callable, Sequence, TypeVar

T = TypeVar("T")


def lower_bound(sorted_keys: Sequence[int], target: int) -> int:
    """target 이상이 처음 등장하는 인덱스."""
    lo, hi = 0, len(sorted_keys)
    while lo < hi:
        mid = (lo + hi) // 2
        if sorted_keys[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo


def upper_bound(sorted_keys: Sequence[int], target: int) -> int:
    """target 초과가 처음 등장하는 인덱스."""
    lo, hi = 0, len(sorted_keys)
    while lo < hi:
        mid = (lo + hi) // 2
        if sorted_keys[mid] <= target:
            lo = mid + 1
        else:
            hi = mid
    return lo


def search_by_key(items: Sequence[T], target: int, key: Callable[[T], int]) -> int:
    """items가 key 오름차순일 때 target에 매칭되는 첫 인덱스. 없으면 -1."""
    lo, hi = 0, len(items)
    while lo < hi:
        mid = (lo + hi) // 2
        k = key(items[mid])
        if k == target:
            return mid
        if k < target:
            lo = mid + 1
        else:
            hi = mid
    return -1
