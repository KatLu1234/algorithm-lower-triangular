"""캠퍼스 건물 + 직접 도보 거리 CSV 로더.

두 CSV는 Supabase 테이블 스키마(`buildings`, `building_travel_times`)와 *컬럼명까지
동일*하다 — 같은 CSV를 SQL Editor의 `\\copy`나 동등한 INSERT로 그대로 적재 가능.

buildings.csv          : code, name, campus
building_travel_times.csv : from_code, to_code, minutes, is_direct

알고리즘 트리 B-2(Floyd-Warshall)가 직접 간선만 받아 모든 쌍 최단 도보를 산출하므로
CSV에는 *직접 간선만* 채우면 된다. 캠퍼스 도보는 양방향 동일 가정이라 두 방향 모두
채우지 않고 한쪽만 적어도 본 로더가 양방향으로 복사한다.

미연결 쌍은 `app.libs.floyd_warshall.INF` 값으로 표시 — FW가 이 값을 무한대로 간주.
"""
from __future__ import annotations

import csv
from pathlib import Path

from app.libs.floyd_warshall import INF
from app.schemas import BuildingCode


def load_building_codes(buildings_csv: Path) -> list[BuildingCode]:
    """CSV에서 건물 코드 리스트 (입력 행 순서 보존)."""
    out: list[BuildingCode] = []
    seen: set[BuildingCode] = set()
    with buildings_csv.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            code = (row.get("code") or "").strip()
            if code and code not in seen:
                out.append(code)
                seen.add(code)
    return out


def load_direct_edges(
    travel_csv: Path,
) -> list[tuple[BuildingCode, BuildingCode, int]]:
    """직접 간선 리스트 (from, to, minutes). is_direct=false 행은 건너뜀."""
    edges: list[tuple[BuildingCode, BuildingCode, int]] = []
    with travel_csv.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            a = (row.get("from_code") or "").strip()
            b = (row.get("to_code") or "").strip()
            if not a or not b or a == b:
                continue
            try:
                minutes = int((row.get("minutes") or "").strip())
            except ValueError:
                continue
            if minutes < 0:
                continue
            is_direct = (row.get("is_direct") or "true").strip().lower()
            if is_direct in ("false", "0", "no"):
                continue
            edges.append((a, b, minutes))
    return edges


def build_walk_matrix(
    codes: list[BuildingCode],
    edges: list[tuple[BuildingCode, BuildingCode, int]],
) -> list[list[int]]:
    """직접 간선 → 대칭 N×N 행렬. 대각=0, 미연결=INF.

    같은 쌍이 양방향 모두 정의돼 있으면 *더 짧은* 쪽 채택 (대칭 가정에 어긋나면
    측정 오차로 간주).
    """
    n = len(codes)
    idx = {c: i for i, c in enumerate(codes)}
    m = [[0 if i == j else INF for j in range(n)] for i in range(n)]
    for a, b, minutes in edges:
        if a not in idx or b not in idx:
            continue  # buildings.csv에 없는 코드 — 조용히 무시
        ia, ib = idx[a], idx[b]
        if minutes < m[ia][ib]:
            m[ia][ib] = minutes
            m[ib][ia] = minutes
    return m


def load_building_graph(
    buildings_csv: Path,
    travel_csv: Path,
) -> tuple[list[BuildingCode], list[list[int]]]:
    """한 번에 — (master 건물 코드, 직접 간선 대칭 행렬) 반환."""
    codes = load_building_codes(buildings_csv)
    edges = load_direct_edges(travel_csv)
    matrix = build_walk_matrix(codes, edges)
    return codes, matrix
