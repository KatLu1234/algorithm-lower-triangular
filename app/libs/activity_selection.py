"""활동 선택 (탐욕) — A-3 가지치기에서 mutual compatibility·최대 비충돌 개수 확인.

intervals: (start, end) 튜플 리스트. 반환: 입력 인덱스 부분집합 (종료시간 오름차순).
"""
from __future__ import annotations


def activity_selection(intervals: list[tuple[int, int]]) -> list[int]:
    if not intervals:
        return []
    order = sorted(range(len(intervals)), key=lambda i: (intervals[i][1], intervals[i][0]))
    chosen: list[int] = []
    last_end = -1
    for idx in order:
        s, e = intervals[idx]
        if s >= last_end:
            chosen.append(idx)
            last_end = e
    return chosen


def all_mutually_compatible(indices: list[int], compatible: list[list[bool]]) -> bool:
    n = len(indices)
    for a in range(n):
        for b in range(a + 1, n):
            if not compatible[indices[a]][indices[b]]:
                return False
    return True
