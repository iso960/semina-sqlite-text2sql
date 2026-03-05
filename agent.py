"""
Text-to-SQL 에이전트: 자연어 -> 파라미터화된 SQL 실행
- MCP 스키마 리소스를 참고해 쿼리 생성 (Gemini API 또는 규칙 기반)
- SQL 주입 방지: 모든 사용자 입력은 ? 파라미터로만 전달
"""
import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from mcp_schema import read_schema

# .env 로드 (프로젝트 루트 = semina-sqlite-text2sql)
load_dotenv(Path(__file__).resolve().parent / ".env")

DB_PATH = os.path.join(os.path.dirname(__file__), "db", "memory.db")

# Gemini 사용 여부 (API 키가 있으면 True)
_USE_GEMINI = bool(os.getenv("GEMINI_API_KEY", "").strip())


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


def _natural_to_sql_gemini(natural: str, schema: str) -> Optional[tuple[str, tuple]]:
    """
    Gemini API로 자연어 -> (SQL, params) 생성.
    반환 형식: JSON {"sql": "SELECT ...", "params": [...]}
    실패 시 None 반환 (규칙 기반으로 폴백).
    """
    try:
        from google import genai

        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        prompt = f"""당신은 SQLite용 Text-to-SQL 변환기입니다. 아래 스키마만 사용하고, 반드시 파라미터화된 쿼리만 생성하세요.

## DB 스키마
{schema}

## 규칙
- SELECT 쿼리만 생성하세요.
- 사용자 입력 값은 반드시 ? 플레이스홀더로 두고, params 배열에 순서대로 넣으세요.
- LIKE 검색이면 params에 '%키워드%' 형태로 넣으세요.
- 다른 설명 없이 아래 JSON만 한 줄로 출력하세요.

## 자연어 질문
{natural}

## 출력 형식 (JSON만)
{{"sql": "SELECT ... WHERE col = ?", "params": ["값1", "값2"]}}
params가 없으면 빈 배열: {{"sql": "SELECT * FROM users", "params": []}}
"""
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
        )
        text = (response.text or "").strip()
        # 마크다운 코드블록 제거
        if "```" in text:
            for part in text.split("```"):
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                if part.startswith("{"):
                    text = part
                    break
        data = json.loads(text)
        sql = (data.get("sql") or "").strip()
        params = data.get("params")
        if not sql.upper().startswith("SELECT"):
            return None
        if params is None:
            params = []
        return (sql, tuple(params))
    except Exception:
        return None


def natural_to_sql(natural: str) -> tuple[str, tuple]:
    """
    자연어 -> (SQL, params) 변환.
    GEMINI_API_KEY가 있으면 Gemini 사용, 없거나 실패 시 규칙 기반 폴백.
    """
    natural_trimmed = natural.strip()
    schema = get_schema()

    if _USE_GEMINI and natural_trimmed:
        llm_result = _natural_to_sql_gemini(natural_trimmed, schema)
        if llm_result is not None:
            return llm_result

    # 규칙 기반 폴백
    natural = natural_trimmed.lower()

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
