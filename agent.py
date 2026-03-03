"""
Text-to-SQL 에이전트: 자연어 -> 파라미터화된 SQL 실행
- MCP 스키마 리소스를 참고해 쿼리 생성
- SQL 주입 방지: 모든 사용자 입력은 ? 파라미터로만 전달
"""
import sqlite3
import os
import re
from typing import Optional

from mcp_schema import read_schema

DB_PATH = os.path.join(os.path.dirname(__file__), "db", "memory.db")


def get_schema() -> str:
    """MCP 리소스에서 스키마 로드 (모델이 정확한 쿼리 생성에 활용)"""
    return read_schema()


def execute_safe(sql: str, params: tuple = ()) -> list[tuple]:
    """
    파라미터화된 쿼리만 실행. SQL 주입 방지.
    - sql에 사용자 입력을 직접 넣지 말고 ? 플레이스홀더 사용
    - params로 값 전달
    """
    # SELECT만 허용 (실습용; 필요시 INSERT/UPDATE도 파라미터화로 허용 가능)
    normalized = sql.strip().upper()
    if not normalized.startswith("SELECT"):
        raise ValueError("실습에서는 SELECT 쿼리만 허용됩니다.")
    # 위험 패턴 차단 (추가 보안)
    if ";" in sql.rstrip().rstrip(";"):
        raise ValueError("다중 쿼리(;)는 허용되지 않습니다.")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = [tuple(r) for r in cur.fetchall()]
    conn.close()
    return rows


def natural_to_sql(natural: str) -> tuple[str, tuple]:
    """
    간단한 자연어 -> (SQL, params) 매핑 (실습용).
    실제 서비스에서는 스키마 + 자연어를 LLM에 넘겨 생성합니다.
    """
    natural = natural.strip().lower()
    schema = get_schema()

    # 1) 사용자 전체 목록
    if any(k in natural for k in ("사용자 목록", "유저 목록", "전체 사용자", "users")):
        return "SELECT id, name, email, created_at FROM users", ()

    # 2) 이름으로 사용자 검색 (파라미터화로 SQL 주입 방지)
    m = re.search(r"이름이\s+(.+?)\s*(?:인\s*사용자|찾|조회)", natural)
    if m:
        name = m.group(1).strip()
        if name.endswith("인") and len(name) > 1:
            name = name[:-1]  # "박소이인" -> "박소이"
        return "SELECT id, name, email, created_at FROM users WHERE name = ?", (name,)
    m = re.search(r"([가-힣a-zA-Z]+)\s*사용자\s*(찾|조회)", natural)
    if m:
        return "SELECT id, name, email, created_at FROM users WHERE name = ?", (m.group(1).strip(),)

    # 3) 메모 목록
    if any(k in natural for k in ("메모 목록", "메모 전체", "memos")):
        return "SELECT m.id, m.title, m.content, u.name, m.created_at FROM memos m JOIN users u ON m.user_id = u.id", ()

    # 4) 제목에 키워드 포함된 메모 (LIKE 파라미터화)
    m = re.search(r"제목에\s+([^\s]+)\s+포함", natural)
    if not m:
        m = re.search(r"(메모|제목).*?['\"]?([가-힣a-zA-Z0-9]+)['\"]?\s*(?:포함|검색)", natural)
        if m:
            keyword = m.group(2)
        else:
            keyword = None
    else:
        keyword = m.group(1).strip()
    if keyword:
        return (
            "SELECT m.id, m.title, m.content, u.name FROM memos m JOIN users u ON m.user_id = u.id WHERE m.title LIKE ?",
            (f"%{keyword}%",),
        )

    # 5) 기본: 사용자 수
    if any(k in natural for k in ("몇 명", "사용자 수", "count")):
        return "SELECT COUNT(*) FROM users", ()

    # 기본: 사용자 목록
    return "SELECT id, name, email, created_at FROM users", ()


def ask(natural: str) -> list[tuple]:
    """자연어 질문 -> 스키마 참고 후 파라미터화 쿼리 실행"""
    sql, params = natural_to_sql(natural)
    return execute_safe(sql, params)
