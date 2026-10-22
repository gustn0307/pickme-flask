# PickMe Flask community implementation

기존 Flask 스타터를 바탕으로 Remix `CommunityPage`의 기능을 Flask/Jinja2로 옮긴 MVP입니다. `/community/` 게시판은 모든 방문자가 같은 DB 게시물·투표 결과·공감·댓글을 읽습니다. 게시글 작성, 투표, 재투표, 공감, 댓글은 로그인 사용자만 가능합니다. 회원별 투표는 게시물당 1개이며 재투표하면 기존 선택이 바뀝니다.

전체 게시물 기준으로 공감 상위 3개와 댓글 상위 3개를 오른쪽 인기 목록에 표시합니다. 목록 제목을 누르면 해당 게시글로 이동합니다. 특정 카테고리를 고르면 현재 검색 결과 안에서 공감 수와 댓글 수를 합친 점수가 가장 높은 게시물이 먼저 나오고, 나머지는 최신순으로 표시됩니다.

## 실행

1. Python 3.12 환경에서 `pip install -r requirements.txt`
2. `.env.example`을 `.env`로 복사하고 `SECRET_KEY`, `DATABASE_URL` 설정
3. `python app.py`
4. `/member/signup`에서 계정을 만든 뒤 `/community/` 사용

SQLite 기본값으로 로컬 실행할 수 있으며 PostgreSQL 설정 예시는 `postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME`입니다. 스타터는 `db.create_all()`을 사용하므로 운영 및 기존 DB에는 Flask-Migrate/Alembic 마이그레이션이 필요합니다. 기존 SQLite의 `user`/`post` 구조와 호환되는 자동 변경은 하지 않습니다.

## 구조

- `routes/community_routes.py`: HTTP 요청, 검증, 로그인/CSRF 검사
- `services/community_service.py`: 게시글 조회·생성, 투표·공감·댓글 처리
- `models/entities.py`: 사용자 및 커뮤니티 테이블/관계
- `templates/community/index.html`: 검색/카테고리/피드/게시글 모달
- `static/css/style.css`: 커뮤니티 반응형 스타일

## DB 스키마 제안

스타터의 회원 테이블은 `users` (복수형)로 정규화했고 기존 `Decision.user_id` FK도 `users.id`로 맞췄습니다. 테이블 이름이나 공통 엔티티를 팀 합의 없이 통합 DB에 적용하지 마세요. 투표 수는 별도 카운터 컬럼 대신 `community_votes` 행을 집계해 일관성을 유지합니다.

| 테이블 | 주요 컬럼 | 용도 |
|---|---|---|
| `users` | `id` PK, `email` UNIQUE, `password_hash`, `nickname`, `created_at` | 공통 회원 |
| `posts` | `id` PK, `user_id` FK, `title`, `content`, `category`, `ai_recommendation` nullable, `created_at` | 커뮤니티 고민 글 |
| `post_options` | `id` PK, `post_id` FK, `name` | 글마다 2~5개 선택지 |
| `community_votes` | `id` PK, `post_id` FK, `option_id` FK, `user_id` FK, `created_at`; UNIQUE(`post_id`,`user_id`) | 회원당 게시물 투표 1개 |
| `community_likes` | `id` PK, `post_id` FK, `user_id` FK, `created_at`; UNIQUE(`post_id`,`user_id`) | 회원당 게시물 공감 1개 |
| `comments` | `id` PK, `post_id` FK, `user_id` FK, `content`, `created_at` | 댓글과 작성자 |
| `decisions` | `id` PK, `user_id` FK, `title`, `question`, `result_json`, `created_at` | 개인 결정 기록, 커뮤니티 글과 별도 |

모든 FK는 `users.id`를 가리키며 삭제 시 하위 데이터도 삭제되도록 설정했습니다. 실제 통합 전에는 담당자와 테이블 명세를 합의하고 마이그레이션으로 반영하세요.

## 엔드포인트

- `GET /community/?q=검색어&category=음식/식사`
- `GET /community/updates` (변경 감지 JSON)
- `POST /community/create`
- `POST /community/<post_id>/vote/<option_id>`
- `POST /community/<post_id>/like`
- `POST /community/<post_id>/comments`

## 제한 및 후속 작업

공유 상태는 공용 DB에 저장되고, 5초 간격 변경 감지로 다른 사용자의 게시글·투표·공감·댓글 변경 시 피드를 갱신합니다. WebSocket/SSE 푸시보다 단순한 폴링 기반으로 갱신에 최대 약 5초 지연이 있습니다. 코드에는 세션 CSRF 토큰과 로그인 검사를 넣었지만 배포 전 Flask-WTF 등 정식 CSRF 보호, rate limit, 마이그레이션 및 HTTPS 설정을 적용하세요. `ai_recommendation`은 데이터 필드만 마련되어 있으며 AI 호출은 커뮤니티 MVP 범위에서 수행하지 않습니다.

