"""플로이드-워셜 (DP, 모든 쌍 최단 경로) — A 단계에서 계산, B-2가 룩업.

§9.9 계약 (가): 건물 간 이동 시간을 한 번 전계산한 뒤 B는 O(1) 룩업으로만 사용.
"""
from __future__ import annotations

INF = 10**9


def floyd_warshall(base_dist: list[list[int]]) -> list[list[int]]:
    n = len(base_dist)
    if any(len(row) != n for row in base_dist):
        raise ValueError("base_dist must be a square matrix")
    dist = [row[:] for row in base_dist]
    for k in range(n):
        dk = dist[k]
        for i in range(n):
            di = dist[i]
            dik = di[k]
            if dik >= INF:
                continue
            for j in range(n):
                via = dik + dk[j]
                if via < di[j]:
                    di[j] = via
    return dist
