# DB 스키마 (memory.db)

## 테이블: users
| 컬럼       | 타입    | 설명        |
|-----------|---------|-------------|
| id        | INTEGER | PK, 자동증가 |
| name      | TEXT    | 사용자 이름  |
| email     | TEXT    | 이메일(UNIQUE) |
| created_at| TEXT    | 생성일시     |

## 테이블: memos
| 컬럼       | 타입    | 설명        |
|-----------|---------|-------------|
| id        | INTEGER | PK, 자동증가 |
| user_id   | INTEGER | FK -> users.id |
| title     | TEXT    | 제목        |
| content   | TEXT    | 내용        |
| created_at| TEXT    | 생성일시     |

## 예시 쿼리 (파라미터화)
- 사용자 목록: `SELECT * FROM users`
- 이름으로 검색: `SELECT * FROM users WHERE name = ?`  -- 파라미터: (name,)
- 메모 검색: `SELECT * FROM memos WHERE title LIKE ?`   -- 파라미터: ('%키워드%',)
