# PickMe AI - Flask MVC Starter

## 공통 규칙
- MVC + Service: routes=Controller, templates=View, models=Model, services=Business logic
- 공통 DB 모델(`models/entities.py`), app.py, base.html 변경은 PM 사전 승인
- 앱은 `create_app()` 및 Blueprint 등록 방식
- Gemini 키는 `.env`에만 저장. 커밋 금지
- 로컬 SQLite, 배포는 영구 PostgreSQL `DATABASE_URL` 설정 권장
- 프로토타입 시연용: `db.create_all()` 사용. 운영에서는 Alembic/Flask-Migrate 적용 필요

## 시작 (Windows: VS Code 터미널 또는 명령 프롬프트)
1. Python 3.11+ 설치 확인
2. `python -m venv .venv`
3. `.venv\Scripts\activate`
4. `pip install -r requirements.txt`
5. `.env.example`을 `.env`로 복사, `SECRET_KEY` 수정
6. `python app.py`
7. http://127.0.0.1:5000 접속, `/health` 확인

## 브랜치
- main: 시연 및 배포 버전
- develop: 통합
- feature/member, feature/chat, feature/decision, feature/history, feature/community

## 임시 URL
- `/` 홈
- `/member/signup`, `/member/login`, `/member/mypage`, POST `/member/logout`
- `/chat/` 상담
- `/decision/` 결정 도우미
- `/history/` 고민 기록
- `/community/` 커뮤니티

## 공통 DB 계약
- `User(id, email, password_hash, nickname)`
- `Decision(id, user_id, title, question, result_json, created_at)`
- `Post(id, user_id, title, content, created_at)`
- `Comment(id, post_id, user_id, content)`

## 배포 예시
- Start command: `gunicorn 'app:app'`
- HTTPS 제공 웹 호스팅과 PostgreSQL을 별도로 준비 (실제 플랫폼 무료 정책 확인)
- 환경 변수: `SECRET_KEY`, `DATABASE_URL`, `GEMINI_API_KEY`
- 배포 시 `DATABASE_URL`은 `postgresql+psycopg://...` 형식으로 지정
- 무료/임시 파일 시스템에 SQLite DB를 배포하면 데이터가 유실될 수 있음
- 인증 보안(CSRF, 요청 제한 등), DB 마이그레이션, 테스트는 추후 보강 필요
