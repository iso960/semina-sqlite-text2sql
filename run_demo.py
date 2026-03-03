"""한 번에 예시 질문들을 실행하는 데모 (인코딩 이슈 회피용)"""
from db.init_db import init_db
from agent import natural_to_sql, ask

init_db()
questions = [
    "사용자 목록 보여줘",
    "이름이 박소이인 사용자 찾아줘",
    "메모 목록",
    "제목에 회의 포함된 메모 검색",
    "사용자 수가 몇 명이야?",
]
print("=== Text-to-SQL Demo ===\n")
for q in questions:
    print(f"Q: {q}")
    try:
        sql, params = natural_to_sql(q)
        print(f"   SQL: {sql}")
        if params:
            print(f"   Params: {params}")
        rows = ask(q)
        print(f"   Result: {len(rows)} rows -> {rows[:3]}{'...' if len(rows) > 3 else ''}")
    except Exception as e:
        print(f"   Error: {e}")
    print()
