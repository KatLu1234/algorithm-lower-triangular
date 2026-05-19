"""0-1 배낭 (DP) — B-3의 학점 용량 모델 데모 + 점수 상한 추정.

호환성 제약을 빼고 강의 가치만 본 단순 0-1 배낭. 시간 충돌·이동 제약을 함께
다루는 진짜 최적화는 valuation.backtrack_top_k(B-3 백트래킹)에서 처리한다.
본 함수는 algorithms.md DP 카테고리 단독 시연 + B-3 가지치기의 가치 상한 추정용.
"""
from __future__ import annotations


def knapsack_01(values: list[float], weights: list[int], capacity: int) -> float:
    """길이 N의 values·weights를 받아 capacity 한도 안에서 최대 가치 합."""
    if capacity <= 0 or not values:
        return 0.0
    n = len(values)
    if len(weights) != n:
        raise ValueError("values and weights must have the same length")
    prev = [0.0] * (capacity + 1)
    for i in range(n):
        w = weights[i]
        v = values[i]
        curr = prev[:]
        for c in range(w, capacity + 1):
            cand = prev[c - w] + v
            if cand > curr[c]:
                curr[c] = cand
        prev = curr
    return prev[capacity]
