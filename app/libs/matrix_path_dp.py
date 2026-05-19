"""행렬 경로 DP — B-3의 격자 DP 데모.

시간표 격자(day × slot)에서 강의 점유 셀의 누적 최대 합을 구한다.
실제 top-K 추출은 valuation.backtrack_top_k에서 호환성 제약과 함께 수행되며,
본 함수는 algorithms.md DP 카테고리의 단독 시연용 + 점수 합 상한 추정용.
"""
from __future__ import annotations

NEG_INF = -(10**18)


def max_path_sum(grid: list[list[float]]) -> float:
    """오른쪽·아래로만 이동. 셀 값 합 최대화. 빈 셀은 0."""
    if not grid or not grid[0]:
        return 0.0
    rows, cols = len(grid), len(grid[0])
    dp = [[NEG_INF] * cols for _ in range(rows)]
    dp[0][0] = grid[0][0]
    for r in range(rows):
        for c in range(cols):
            if r == 0 and c == 0:
                continue
            best = NEG_INF
            if r > 0:
                best = max(best, dp[r - 1][c])
            if c > 0:
                best = max(best, dp[r][c - 1])
            dp[r][c] = best + grid[r][c]
    return float(dp[rows - 1][cols - 1])
