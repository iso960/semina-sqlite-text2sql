# SQLite Text-to-SQL 실습 (박소이)

자연어 질문을 **파라미터화된 SQL 쿼리**로 변환해 SQLite DB를 조회하는  
**장기 기억(Long-term Memory) + MCP 스키마 + SQL Injection 방지** 데모 프로젝트입니다.

---

## 프로젝트 개요

- **무엇을 하는 프로젝트인가?**
  - 사용자가 `"사용자 목록 보여줘"`, `"이름이 박소이인 사용자 찾아줘"` 처럼 **자연어로 질문**하면
  - 에이전트가 **SQL 쿼리 + 파라미터**를 만들고
  - 로컬 SQLite DB(`memory.db`)를 조회해서 결과를 반환합니다.

- **핵심 포인트**
  - DB 구조를 **MCP 스키마 리소스**로 제공 → 모델/에이전트가 정확한 컬럼명·테이블명으로 SQL 생성
  - 모든 사용자 입력은 **파라미터화된 쿼리**로만 전달 → SQL Injection 방지
  - SQLite 파일을 간단한 **장기 기억 저장소**처럼 활용

---

## 폴더 및 파일 구조

- **`db/init_db.py`**
  - `memory.db` SQLite 파일을 생성하고, 기본 테이블과 샘플 데이터를 만듭니다.
  - 테이블
    - `users(id, name, email, created_at)`
    - `memos(id, user_id, title, content, created_at)` – 사용자별 메모(장기 기억)
  - 처음 실행 시 `users`, `memos`에 샘플 데이터 자동 삽입.

- **`resources/db_schema.md`**
  - DB 스키마를 문서로 정리한 파일 (테이블/컬럼/타입/설명).
  - MCP 환경에서는 이 파일을 **리소스**로 모델에게 제공해, Text-to-SQL 생성 시 참고하게 할 수 있습니다.
  - 없으면 `mcp_schema.ensure_schema_resource()` 호출 시 자동 생성됩니다.

- **`mcp_schema.py`**
  - 스키마 리소스를 다루는 헬퍼 모듈입니다.
  - 주요 함수
    - `get_schema_resource_path()` : `db_schema.md` 파일 경로 반환 (MCP 리소스 등록용).
    - `ensure_schema_resource()` : 스키마 파일이 없으면 생성.
    - `read_schema()` : 스키마 파일 전체 내용을 문자열로 읽어서 반환.
  - 실제 LLM 연동 시, 이 문자열을 프롬프트에 포함시켜 Text-to-SQL 정확도를 높일 수 있습니다.

- **`agent.py`**
  - 자연어 → (SQL, params) → 안전한 실행까지 담당하는 **Text-to-SQL 에이전트**입니다.
  - 주요 구성
    - `get_schema()` : `read_schema()`를 호출해 MCP 스키마 내용을 가져옵니다.
    - `execute_safe(sql, params)` :
      - `SELECT`로 시작하는 쿼리만 허용 (실습용 제한).
      - `;`를 사용한 다중 쿼리 차단.
      - `cur.execute(sql, params)` 로만 실행 → **파라미터화된 쿼리** 강제.
    - `natural_to_sql(natural)` :
      - 간단한 규칙 기반으로 자연어를 (SQL, params)로 변환합니다.
      - 예)
        - `"사용자 목록 보여줘"` → `SELECT id, name, email, created_at FROM users`, `()`
        - `"이름이 박소이인 사용자 찾아줘"` → `SELECT ... FROM users WHERE name = ?`, `('박소이',)`
        - `"메모 목록"` → `SELECT ... FROM memos m JOIN users u ...`
        - `"제목에 회의 포함된 메모 검색"` → `... WHERE m.title LIKE ?`, `('%회의%',)`
      - 실제 서비스에서는 이 부분을 LLM 호출로 교체하면 됩니다 (스키마 + 자연어를 모델에 전달).
    - `ask(natural)` :
      - 자연어 → `natural_to_sql()` → `execute_safe()`까지 한 번에 호출하는 편의 함수.

- **`main.py`**
  - **대화형 실행 진입점**입니다.
  - 동작 흐름
    1. `init_db()`로 SQLite DB 및 샘플 데이터 초기화.
    2. `[MCP 스키마 리소스 미리보기]`로 스키마 일부를 출력.
    3. CLI 인자 유무에 따라:
       - 인자가 있으면: 해당 자연어 질문 한 번만 실행 후 종료.  
         예: `python main.py 사용자 목록 보여줘`
       - 인자가 없으면: 대화형 모드로 진입.
         - 예시 질문 리스트 출력.
         - `질문 (Enter로 종료):` 에 입력한 자연어에 대해, 생성된 SQL / 파라미터 / 결과를 순서대로 출력.

- **`run_demo.py`**
  - 여러 개의 **예시 질문을 한 번에 실행**하는 데모 스크립트입니다.
  - 발표/데모 시에 커맨드 한 번으로 전체 흐름을 보여주기에 좋습니다.
  - 내부에서 사용하는 예시 질문:
    - 사용자 목록 보여줘
    - 이름이 박소이인 사용자 찾아줘
    - 메모 목록
    - 제목에 회의 포함된 메모 검색
    - 사용자 수가 몇 명이야?

- **`requirements.txt`**
  - 현재 코드는 Python 표준 라이브러리(`sqlite3`, `os`, `re` 등)만 사용하므로 필수 외부 의존성은 없습니다.
  - 추후 OpenAI/Anthropic 등 LLM을 붙일 때 사용할 수 있는 패키지 예시를 주석으로 남겨두었습니다.

---

## 실행 방법

### 1) 대화형 모드 실행

```bash
cd c:\Users\PC\Desktop\semina
python main.py
```

- 실행 후 예시 질문이 출력됩니다.
- `질문 (Enter로 종료):` 프롬프트에 자연어를 입력해 보세요.
  - 예시:
    - `사용자 목록 보여줘`
    - `이름이 박소이인 사용자 찾아줘`
    - `메모 목록`
    - `제목에 회의 포함된 메모 검색`
    - `사용자 수가 몇 명이야?`

### 2) 한 줄로 특정 질문만 실행

```bash
python main.py 사용자 목록 보여줘
python main.py 이름이 박소이인 사용자 찾아줘
```

- 인자로 넘긴 자연어 한 번만 처리하고 바로 종료합니다.

### 3) 데모 스크립트로 전체 흐름 보기

```bash
python run_demo.py
```

- 여러 질문에 대해 **생성된 SQL / 파라미터 / 결과 요약**을 한 번에 출력합니다.

---

## 보안: SQL 주입(SQL Injection) 방지

- **위험한 방식 (예시, 이 프로젝트에서는 사용하지 않음)**
  ```python
  sql = f"SELECT * FROM users WHERE name = '{user_input}'"
  # user_input에 ' OR '1'='1 같은 문자열이 들어가면 전체 데이터 노출 가능
  ```

- **이 프로젝트에서 사용하는 안전한 방식**
  - SQL에는 **플레이스홀더**만 사용: `WHERE name = ?`
  - 실제 값은 **params 튜플**로 분리해서 전달:
    ```python
    sql = "SELECT * FROM users WHERE name = ?"
    params = (user_input,)
    cur.execute(sql, params)
    ```
  - `agent.execute_safe()`에서 추가로:
    - `SELECT`로 시작하는 쿼리만 허용 (실습용 제한).
    - `;`를 이용한 다중 쿼리 실행 차단.

→ **사용자 입력이 SQL 문자열에 직접 붙지 않도록 설계**되어 있어, 기본적인 SQL Injection 공격을 막을 수 있습니다.

---

## MCP 활용 포인트

- `resources/db_schema.md`는 다음과 같이 활용할 수 있습니다.
  - Cursor MCP 리소스로 등록해서, 모델이 Text-to-SQL 프롬프트에서 이 스키마를 참고하게 함.
  - 에이전트 코드에서 `read_schema()`로 읽어, LLM 호출 시 “현재 DB 구조”를 설명하는 컨텍스트로 전달.
- 이 구조의 장점
  - 테이블이 추가/변경되면, **스키마 문서만 업데이트**해도 모델이 새로운 구조를 참고할 수 있음.
  - 환경마다 DB 구조가 달라도, 스키마 리소스를 바꿔 끼우면 동일한 에이전트를 재사용 가능.

---

## 확장 아이디어

- `natural_to_sql()`를 규칙 기반이 아니라 실제 LLM 호출로 교체
  - 입력: 자연어 질문 + `read_schema()`로 읽은 스키마
  - 출력: `SELECT` 쿼리와 파라미터 구조
- `memos` 테이블을 활용해
  - 챗봇의 “장기 기억” 저장소로 확장
  - 사용자별 대화 요약/노트 저장 후 검색

이 레포지토리는 **“MCP + Text-to-SQL + 안전한 쿼리 실행”**의 최소 예제로,  
발표, 포트폴리오, 학습용으로 바로 활용할 수 있습니다.
