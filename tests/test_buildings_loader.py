"""buildings.csv + building_travel_times.csv 로더 + FW 산출 거리 검증.

체인 그래프 (사용자 제공):
    농심국제관 — 과학기술1관 — 과학기술2관 — 공공정책관 — 석원경상관 — 문화스포츠관
              2          2           1            2            1   (분)
"""
from pathlib import Path

import pytest

from app.libs.buildings_loader import (
    build_walk_matrix,
    load_building_codes,
    load_building_graph,
    load_direct_edges,
)
from app.libs.floyd_warshall import INF, floyd_warshall


_ROOT = Path(__file__).resolve().parents[1]
_BUILDINGS_CSV = _ROOT / "buildings.csv"
_TRAVEL_CSV = _ROOT / "building_travel_times.csv"


class TestLoader:
    def test_codes_loaded(self):
        codes = load_building_codes(_BUILDINGS_CSV)
        assert set(codes) == {
            "과학기술1관", "과학기술2관", "석원경상관",
            "농심국제관", "공공정책관", "문화스포츠관",
        }

    def test_direct_edges(self):
        edges = load_direct_edges(_TRAVEL_CSV)
        assert len(edges) == 5
        pairs = {tuple(sorted([a, b])): m for a, b, m in edges}
        assert pairs[("과학기술1관", "농심국제관")] == 2
        assert pairs[("과학기술1관", "과학기술2관")] == 2
        assert pairs[("공공정책관", "과학기술2관")] == 1
        assert pairs[("공공정책관", "석원경상관")] == 2
        assert pairs[("문화스포츠관", "석원경상관")] == 1

    def test_walk_matrix_is_symmetric(self):
        codes = load_building_codes(_BUILDINGS_CSV)
        edges = load_direct_edges(_TRAVEL_CSV)
        m = build_walk_matrix(codes, edges)
        n = len(codes)
        for i in range(n):
            assert m[i][i] == 0
            for j in range(n):
                assert m[i][j] == m[j][i]

    def test_unknown_code_in_edges_ignored(self):
        codes = ["A", "B"]
        edges = [("A", "B", 3), ("A", "NOSUCH", 10)]
        m = build_walk_matrix(codes, edges)
        assert m[0][1] == 3 and m[1][0] == 3


class TestFloydWarshallOnRealGraph:
    """B-2: 직접 간선만 입력 → 모든 쌍 최단 도보 산출."""

    @pytest.fixture(scope="class")
    def codes_and_shortest(self):
        codes, matrix = load_building_graph(_BUILDINGS_CSV, _TRAVEL_CSV)
        shortest = floyd_warshall(matrix)
        return codes, shortest

    def _d(self, codes, shortest, a: str, b: str) -> int:
        return shortest[codes.index(a)][codes.index(b)]

    def test_direct_edges_unchanged(self, codes_and_shortest):
        codes, shortest = codes_and_shortest
        assert self._d(codes, shortest, "농심국제관", "과학기술1관") == 2
        assert self._d(codes, shortest, "과학기술1관", "과학기술2관") == 2
        assert self._d(codes, shortest, "과학기술2관", "공공정책관") == 1
        assert self._d(codes, shortest, "공공정책관", "석원경상관") == 2
        assert self._d(codes, shortest, "석원경상관", "문화스포츠관") == 1

    def test_chain_indirect_paths(self, codes_and_shortest):
        codes, shortest = codes_and_shortest
        # 농심 → 문화스포츠 = 2+2+1+2+1 = 8 (체인 전체)
        assert self._d(codes, shortest, "농심국제관", "문화스포츠관") == 8
        # 과학기술1관 → 석원경상관 = 2+1+2 = 5
        assert self._d(codes, shortest, "과학기술1관", "석원경상관") == 5
        # 과학기술2관 → 문화스포츠관 = 1+2+1 = 4
        assert self._d(codes, shortest, "과학기술2관", "문화스포츠관") == 4
        # 농심 → 공공정책관 = 2+2+1 = 5
        assert self._d(codes, shortest, "농심국제관", "공공정책관") == 5

    def test_no_unreachable(self, codes_and_shortest):
        codes, shortest = codes_and_shortest
        n = len(codes)
        for i in range(n):
            for j in range(n):
                assert shortest[i][j] < INF, f"unreachable: {codes[i]}↔{codes[j]}"
