
"""결정 도우미 라우트. 개선 1~7 반영."""
# Flask에서 화면 이동, 요청 데이터 처리, JSON 응답 등에 사용하는 기능을 가져온다.
from flask import Blueprint, render_template, request, jsonify, redirect, url_for

# Decision: 상담 기록을 저장하는 데이터 모델
# db: 데이터베이스 작업을 처리하는 객체
from models.entities import Decision, db

# 서비스 파일에서 AI 상담과 프롬프트 생성에 필요한 함수 및 설정을 가져온다.
from services.decision_service import (
    get_ai_consultation, build_prompt, CATEGORIES, STYLES, CONDITION_CHIPS,
)

# decision이라는 이름의 Blueprint를 생성한다.
# url_prefix='/decision'은 이 Blueprint의 기본 URL 경로를 지정한다.
# 예: /decision/, /decision/new, /decision/conditions
bp = Blueprint('decision', __name__, url_prefix='/decision')


@bp.route('/', methods=['GET', 'POST'])
def index():
    """개선 3: 자유로운 고민 제목 + 개선 4: 가이드 기반 입력으로 상담 요청을 받는다."""

    # AI 상담 결과와 오류 메시지를 저장할 변수
    # 처음에는 결과와 오류가 없으므로 None으로 초기화한다.
    ai_result = None
    error = None

    # GET은 화면을 조회할 때, POST는 사용자가 입력한 내용을 제출할 때 사용한다.
    if request.method == 'POST':

        # 개선 1: 카테고리 복수 선택
        # getlist()는 체크박스처럼 같은 이름으로 전달된 여러 값을 리스트로 가져온다.
        categories = request.form.getlist('categories')

        # 선택한 상담 스타일을 가져온다.
        # 스타일이 전달되지 않으면 objective를 기본값으로 사용한다.
        style = request.form.get('style', 'objective')

        # 사용자가 입력한 고민 제목을 가져오고 앞뒤 공백을 제거한다.
        title = request.form.get('title', '').strip()

        # 사용자가 작성한 고민 내용을 가져오고 앞뒤 공백을 제거한다.
        content = request.form.get('content', '').strip()

        # HTML에서 보낸 선택지들을 리스트로 받아오는 코드
        # option_names라는 이름으로 전달된 여러 선택지 이름을 가져온다.
        options = request.form.getlist('option_names')

        # 개선 5: 칩(체크박스) + 자유 입력 조건을 모두 반영
        # 사용자가 체크박스에서 선택한 추가 조건을 리스트로 가져온다.
        chips = request.form.getlist('conditions')

        # 사용자가 직접 입력한 추가 조건을 가져오고 앞뒤 공백을 제거한다.
        free_text = request.form.get('conditions_free', '').strip()

        # 체크박스로 선택한 조건과 직접 입력한 조건을 하나의 문자열로 합친다.
        # 자유 입력이 비어 있으면 빈 문자열을 리스트에 추가하지 않는다.
        conditions = ", ".join(chips + ([free_text] if free_text else []))

        # 고민 내용이 비어 있으면 AI 상담을 진행하지 않는다.
        if not content:
            error = "고민 내용을 입력해 주세요."

        else:
            # 사용자가 입력한 내용을 AI가 이해할 수 있는 프롬프트로 구성한다.
            # 카테고리, 스타일, 제목, 내용, 추가 조건, 선택지를 전달한다.
            prompt = build_prompt(categories, style, title, content, conditions, options)

            # 생성한 프롬프트를 AI 서비스에 전달하고 상담 결과를 받아온다.
            ai_result = get_ai_consultation(prompt)

            # 상담 기록 저장 (로그인한 사용자만)
            # AI 결과가 존재하고 오류 메시지로 시작하지 않는지 확인한다.
            if ai_result and not ai_result.startswith(("오류", "AI 응답")):

                # 현재 세션에 로그인 사용자 ID가 있는지 확인한다.
                if 'user_id' in session_guard():
                    try:
                        # 데이터베이스에 저장할 상담 기록 객체를 생성한다.
                        record = Decision(
                            # 상담 기록과 로그인 사용자의 ID를 연결한다.
                            user_id=session_guard()['user_id'],

                            # 제목이 있으면 제목을 사용하고,
                            # 없으면 고민 내용의 앞 50글자를 제목으로 사용한다.
                            title=title or content[:50],

                            # 사용자가 작성한 원본 고민 내용
                            question=content,

                            # 상담에 사용한 설정과 AI 응답을 딕셔너리로 저장한다.
                            result_json={
                                "categories": categories,  # 선택한 카테고리
                                "style": style,            # 선택한 상담 스타일
                                "conditions": conditions,  # 추가 조건
                                "result": ai_result,       # AI 상담 결과
                                "options": options,        # 선택지 목록
                            },
                        )

                        # 생성한 상담 기록을 DB 저장 대기 상태로 등록한다.
                        db.session.add(record)

                        # 대기 중인 변경 사항을 실제 데이터베이스에 반영한다.
                        db.session.commit()

                    except Exception:
                        # 저장 도중 오류가 발생하면 DB 변경 사항을 취소한다.
                        db.session.rollback()

    # 상담 결과 화면을 렌더링한다.
    return render_template(
        'decision/index.html',  # 보여줄 HTML 템플릿 파일
        result=ai_result,        # AI 상담 결과 전달
        error=error,             # 오류 메시지 전달
        categories=CATEGORIES,   # HTML에서 사용할 카테고리 목록
        styles=STYLES,           # HTML에서 사용할 상담 스타일 목록
        chips=CONDITION_CHIPS,   # HTML에서 사용할 추가 조건 목록

        # ★ 입력 리셋 방지: 제출한 값 그대로 돌려보내 화면에 유지
        # HTML에서 이 값을 활용하면 제출했던 내용을 다시 표시할 수 있다.
        form=request.form,
    )


def session_guard():
    # Flask의 session 객체를 가져온다.
    # 세션은 사용자별 로그인 정보 등을 요청 사이에 유지하는 데 사용된다.
    from flask import session

    # 현재 요청에서 사용할 세션 객체를 반환한다.
    return session


# 개선 1: 카테고리별 인기 고민 Top 5 조회 API
@bp.get('/api/popular')
def api_popular():
    # SQLAlchemy의 집계 함수인 count()를 사용하기 위해 가져온다.
    from sqlalchemy import func

    # 데이터베이스에서 상담 제목별 저장 횟수를 조회한다.
    q = (
        # 상담 제목과 해당 제목의 상담 기록 개수를 조회한다.
        db.session.query(Decision.title, func.count(Decision.id).label('cnt'))

        # 같은 제목을 가진 상담 기록끼리 그룹으로 묶는다.
        .group_by(Decision.title)

        # 상담 기록 개수가 많은 제목부터 내림차순으로 정렬한다.
        .order_by(func.count(Decision.id).desc())

        # 상위 5개 제목만 조회한다.
        .limit(5)

        # 쿼리를 실행하고 조회 결과를 가져온다.
        .all()
    )

    # 조회한 제목과 횟수를 JSON 배열로 반환한다.
    # 각 항목은 제목(title)과 횟수(count)로 구성된다.
    return jsonify([{"title": t, "count": c} for t, c in q])


# 개선 2: 상담 결과 화면에서 스타일만 바꿔 다시 상담
# 예: "공감은 됐고, 이제 팩트로 말해줘"
@bp.post('/api/restyle')
def api_restyle():
    # 요청 본문에서 JSON 데이터를 가져온다.
    # JSON이 없거나 읽을 수 없으면 빈 딕셔너리를 사용한다.
    data = request.get_json(silent=True) or {}

    # 다시 상담할 스타일을 가져온다.
    # 별도 스타일이 전달되지 않으면 fact를 기본값으로 사용한다.
    style = data.get('style', 'fact')

    # 이전 상담에서 사용한 카테고리 목록
    categories = data.get('categories', [])

    # 이전 상담의 고민 제목
    title = data.get('title', '')

    # 다시 상담할 때 사용할 고민 내용
    content = data.get('content', '')

    # 이전 상담의 추가 조건
    conditions = data.get('conditions', '')

    # 다시 상담할 때 사용할 선택지 목록
    options = data.get('options',[])

    # 고민 내용이 없으면 상담할 수 없으므로 HTTP 400 응답을 반환한다.
    if not content:
        return jsonify({"error": "고민 내용이 없습니다."}), 400

    # 기존 고민 정보와 새 스타일을 이용해 프롬프트를 다시 생성한다.
    prompt = build_prompt(categories, style, title, content, conditions, options)

    # 새 스타일로 생성한 상담 결과를 JSON으로 반환한다.
    return jsonify({"result": get_ai_consultation(prompt)})


  #── [2단계] 비교할 선택지 작성 (스크린샷 2/5 화면) ──
  # 사용자가 비교하고 싶은 선택지를 작성하는 단계다.


@bp.route('/new', methods=['GET', 'POST'])
def new():
    """선택지를 최소 2개, 최대 5개까지 받아 세션에 임시 저장."""

    # GET 요청이면 선택지 입력 화면을 보여주고,
    # POST 요청이면 사용자가 입력한 선택지를 처리한다.
    if request.method == 'POST':

        # HTML 폼에서 option_title이라는 이름으로 전달된 선택지 이름들을 가져온다.
        titles = request.form.getlist('option_title')   # 선택지 이름들

        # 각 선택지에 대한 설명을 가져온다.
        notes = request.form.getlist('option_note')     # 설명들

        # 최종적으로 사용할 선택지를 담을 빈 리스트
        options = []

        # zip()은 같은 순서에 있는 제목과 설명을 하나씩 묶어준다.
        # 예: 첫 번째 제목 + 첫 번째 설명
        for t, n in zip(titles, notes):

            # 선택지 이름의 앞뒤 공백을 제거한다.
            t = t.strip()

            # 이름이 비어 있지 않은 선택지만 수집한다.
            if t:

                # 선택지 이름과 설명을 딕셔너리로 만들어 리스트에 추가한다.
                options.append({"title": t, "note": n.strip()})

        # 선택지가 2개 미만이면 다음 단계로 진행하지 않는다.
        if len(options) < 2:

            # 현재 입력한 선택지와 오류 메시지를 화면에 전달한다.
            return render_template('decision/new.html',
                options=options, error="선택지를 최소 2개 이상 입력해 주세요.")

        # 3단계(판단 기준)로 넘기기 위해 세션에 임시 저장
        # 세션에 저장하면 다음 요청에서도 선택지 정보를 사용할 수 있다.
        from flask import session

        # decision_options라는 키에 선택지 목록을 저장한다.
        session['decision_options'] = options

        # 선택지 입력이 완료되면 판단 기준 설정 화면으로 이동한다.
        return redirect(url_for('decision.conditions'))  # → 3단계로 이동

    # GET 요청일 때 선택지 입력 화면을 보여준다.
    # 아직 입력한 선택지가 없으므로 빈 리스트를 전달한다.
    return render_template('decision/new.html', options=[])


# ── [3단계] 판단 기준 및 중요도 가중치 (스크린샷 3/5 화면) ──
# 2단계에서 작성한 선택지를 기준으로 판단할 항목을 선택하는 단계다.


@bp.route('/conditions', methods=['GET', 'POST'])
def conditions():

    # 현재 사용자의 세션 객체를 가져온다.
    from flask import session

    # 2단계에서 세션에 저장한 선택지 목록을 가져온다.
    # 저장된 선택지가 없으면 빈 리스트를 사용한다.
    options = session.get('decision_options', [])

    # 선택지 없이 이 화면에 직접 접근하면 2단계로 되돌려 보낸다.
    if not options:
        return redirect(url_for('decision.new'))  # 선택지 없이 접근하면 2단계로 되돌림

    # 사용자가 판단 기준을 제출했을 때 실행한다.
    if request.method == 'POST':

        # 체크한 판단 기준 칩 수집 (최대 5개)
        # HTML에서 criteria라는 이름으로 제출한 값을 리스트로 가져온다.
        criteria = request.form.getlist('criteria')

        # 선택한 각 판단 기준에 연결된 중요도 값을 가져온다.
        # 예: {"가격": "5", "거리": "3"}
        # 실제 기준 이름과 HTML의 weight_ 필드 이름이 일치해야 한다.
        weights = {c: request.form.get(f'weight_{c}') for c in criteria}

        # 선택한 판단 기준을 세션에 저장한다.
        session['decision_criteria'] = criteria

        # 판단 기준을 제출한 뒤 최종 상담 화면으로 이동한다.
        return redirect(url_for('decision.index'))  # 최종 상담(기존 메인)으로

    # GET 요청이면 선택지 목록을 판단 기준 화면에 전달한다.
    return render_template('decision/conditions.html', options=options)
