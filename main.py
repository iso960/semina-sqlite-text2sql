"""
Text-to-SQL 실습 실행기
자연어 질문 -> MCP 스키마 참고 -> 파라미터화 쿼리 실행 (SQL 주입 방지)
"""
import sys
from db.init_db import init_db
from agent import get_schema, ask, natural_to_sql


def main():
    init_db()
    print("=== SQLite Text-to-SQL 에이전트 (MCP 스키마 + 파라미터화 쿼리) ===\n")
    print("[MCP 스키마 리소스 미리보기]")
    print(get_schema()[:500] + "...\n")

    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        run_query(question)
        return

    # 대화형
    examples = [
        "사용자 목록 보여줘",
        "이름이 박소이인 사용자 찾아줘",
        "메모 목록",
        "제목에 회의 포함된 메모 검색",
        "사용자 수가 몇 명이야?",
    ]
    print("예시 질문:", examples)
    print()
    while True:
        try:
            q = input("질문 (Enter로 종료): ").strip()
            if not q:
                break
            run_query(q)
        except KeyboardInterrupt:
            break
    print("종료.")


def run_query(question: str):
    try:
        sql, params = natural_to_sql(question)
        print(f"  [생성된 SQL] {sql}")
        if params:
            print(f"  [파라미터]   {params}  <- SQL 주입 방지")
        rows = ask(question)
        print(f"  [결과] {len(rows)}건")
        for r in rows:
            print("   ", r)
    except Exception as e:
        print(f"  오류: {e}")
    print()


if __name__ == "__main__":
    main()
