"""결정 도우미 라우트. 개선 1~7 반영."""
from flask import Blueprint, render_template, request, jsonify

from models.entities import Decision, db
from services.decision_service import (
    get_ai_consultation, build_prompt, CATEGORIES, STYLES, CONDITION_CHIPS,
)

bp = Blueprint('decision', __name__, url_prefix='/decision')


@bp.route('/', methods=['GET', 'POST'])
def index():
    """개선 3: 자유로운 고민 제목 + 개선 4: 가이드 기반 입력으로 상담 요청을 받는다."""
    ai_result = None
    error = None

    if request.method == 'POST':
        # 개선 1: 카테고리 복수 선택
        categories = request.form.getlist('categories')
        style = request.form.get('style', 'objective')
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        # 개선 5: 칩(체크박스) + 자유 입력 조건을 모두 반영
        chips = request.form.getlist('conditions')
        free_text = request.form.get('conditions_free', '').strip()
        conditions = ", ".join(chips + ([free_text] if free_text else []))

        if not content:
            error = "고민 내용을 입력해 주세요."
        else:
            prompt = build_prompt(categories, style, title, content, conditions)
            ai_result = get_ai_consultation(prompt)

            # 상담 기록 저장 (로그인한 사용자만)
            if ai_result and not ai_result.startswith(("오류", "AI 응답")):
                if 'user_id' in session_guard():
                    try:
                        record = Decision(
                            user_id=session_guard()['user_id'],
                            title=title or content[:50],
                            question=content,
                            result_json={
                                "categories": categories, "style": style,
                                "conditions": conditions, "result": ai_result,
                            },
                        )
                        db.session.add(record)
                        db.session.commit()
                    except Exception:
                        db.session.rollback()

    return render_template(
        'decision/index.html',
        result=ai_result, error=error,
        categories=CATEGORIES, styles=STYLES, chips=CONDITION_CHIPS,
        # ★ 입력 리셋 방지: 제출한 값 그대로 돌려보내 화면에 유지
        form=request.form,
    )


def session_guard():
    from flask import session
    return session


# 개선 1: 카테고리별 인기 고민 Top 5 조회 API
@bp.get('/api/popular')
def api_popular():
    from sqlalchemy import func
    q = (
        db.session.query(Decision.title, func.count(Decision.id).label('cnt'))
        .group_by(Decision.title)
        .order_by(func.count(Decision.id).desc())
        .limit(5)
        .all()
    )
    return jsonify([{"title": t, "count": c} for t, c in q])


# 개선 2: 상담 결과 화면에서 스타일만 바꿔 다시 상담 (예: "공감은 됐고, 이제 팩트로 말해줘")
@bp.post('/api/restyle')
def api_restyle():
    data = request.get_json(silent=True) or {}
    style = data.get('style', 'fact')
    categories = data.get('categories', [])
    title = data.get('title', '')
    content = data.get('content', '')
    conditions = data.get('conditions', '')

    if not content:
        return jsonify({"error": "고민 내용이 없습니다."}), 400

    prompt = build_prompt(categories, style, title, content, conditions)
    return jsonify({"result": get_ai_consultation(prompt)})
