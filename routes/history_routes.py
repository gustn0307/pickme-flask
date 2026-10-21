from flask import Blueprint, render_template
bp = Blueprint('history', __name__, url_prefix='/history')

@bp.get('/')
def index():
    return render_template('history/index.html')

# 담당 팀원이 이 파일의 엔드포인트를 구현합니다.
from flask import Blueprint, render_template, jsonify, request

history_bp = Blueprint('history', __name__)

# 임시 고민 기록 데이터 (DB 연결 전 바로 화면 확인 가능)
MOCK_HISTORY = [
    {
        "id": 1,
        "date": "2026-10-21",
        "question": "오늘 점심 메뉴 삼겹살 vs 회 추천해줘",
        "answer": "팀 회식이나 여러 사람과 함께하는 자리라면 호불호가 적고 단합에 좋은 삼겹살을 추천합니다!"
    },
    {
        "id": 2,
        "date": "2026-10-20",
        "question": "발표 자료 오늘 밤 완성할까, 내일 아침에 검토할까?",
        "answer": "오늘 밤 핵심 내용을 마무리하고, 내일 아침 개운한 상태에서 최종 검토하는 것이 오류를 줄이는 데 가장 좋습니다."
    }
]

@history_bp.route('/history')
def get_history_page():
    return render_template('history/index.html', history_list=MOCK_HISTORY)