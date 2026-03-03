# SQLite Text-to-SQL 실습 (박소이)

자연어 질문 → AI/에이전트가 **파라미터화된 SQL**로 DB 조회하는 장기 기억 실습 코드입니다.

## 구성

- **db/init_db.py** – SQLite DB 생성 및 샘플 데이터 (users, memos)
- **resources/db_schema.md** – MCP 리소스용 스키마 문서 (실행 시 자동 생성)
- **mcp_schema.py** – 스키마 리소스 읽기 (모델이 쿼리 생성 시 참고)
- **agent.py** – Text-to-SQL 에이전트: 자연어 → (SQL, params) → **파라미터화 실행** (SQL 주입 방지)
- **main.py** – 실행 진입점

## 실행 방법

```bash
cd c:\Users\PC\Desktop\semina
python main.py
```

한 줄로 질문만 실행:

```bash
python main.py 사용자 목록 보여줘
python main.py 이름이 박소이인 사용자 찾아줘
python main.py 메모 목록
python main.py 제목에 회의 포함된 메모 검색
```

## 보안 (SQL 주입 방지)

- 사용자 입력은 **절대 SQL 문자열에 붙이지 않고**, `?` 플레이스홀더 + `params` 인자로만 전달합니다.
- `agent.execute_safe()` 에서 `cur.execute(sql, params)` 형태로만 실행합니다.

## MCP 활용

- 스키마는 `resources/db_schema.md` 에 두고, 에이전트가 `read_schema()` 로 불러와 쿼리 생성에 사용합니다.
- Cursor 등에서 MCP 리소스로 이 스키마를 제공하면, 모델이 테이블/컬럼 정보를 보고 더 정확한 SQL을 생성할 수 있습니다.
