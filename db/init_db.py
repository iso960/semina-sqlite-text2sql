"""
SQLite DB 초기화 + 샘플 데이터
실습용 '장기 기억' DB 생성
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "memory.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 사용자 테이블
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # 메모/노트 테이블 (장기 기억)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS memos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # 샘플 데이터
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            [
                ("김철수", "kim@example.com"),
                ("이영희", "lee@example.com"),
                ("박소이", "park@example.com"),
            ],
        )
        cur.executemany(
            "INSERT INTO memos (user_id, title, content) VALUES (?, ?, ?)",
            [
                (1, "회의 메모", "월요일 스탠드업 10시"),
                (1, "할 일", "DB 설계 검토"),
                (2, "아이디어", "Text-to-SQL 데모 준비"),
                (3, "발표 노트", "MCP 스키마 + 파라미터화 쿼리"),
            ],
        )

    conn.commit()
    conn.close()
    print(f"DB 초기화 완료: {DB_PATH}")


if __name__ == "__main__":
    init_db()
