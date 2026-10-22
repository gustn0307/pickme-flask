from flask import Blueprint, render_template, request, jsonify, session, g
from services.chat_service import ChatService

bp = Blueprint('chat', __name__, url_prefix='/chat')

@bp.route('/')
def index():
    """AI 상담 챗봇 메인 화면 렌더링"""
    if 'chat_history' not in session:
        session['chat_history'] = []
    return render_template('chat/index.html')

@bp.route('/api/send', methods=['POST'])
def chat_send():
    """사용자 메시지 처리 및 AI 응답 API (AI 자율 판단 연동)"""
    data = request.get_json() or {}
    user_message = data.get('message', '')
    tone = data.get('tone', 'empathy')

    # 1. 기본 입력 유효성 검증
    is_valid, error_msg = ChatService.validate_input(user_message)
    if not is_valid:
        return jsonify({
            "status": "error",
            "reply": error_msg,
            "requires_more_info": True
        }), 200

    # 2. 키워드 검사 없이 오직 Gemini AI가 직접 문맥을 분석하여 판단
    ai_result = ChatService.get_ai_response(user_message, tone)

    # 위기 상황인 경우 처리
    if ai_result.get("is_crisis"):
        return jsonify({
            "status": "success",
            "reply": ai_result['reply'],
            "parsed_data": None,
            "requires_more_info": False
        })

    # 세션에 최신 파싱 데이터 저장 (결정 도우미 연동용)
    if ai_result.get('parsed_data'):
        session['latest_decision_payload'] = ai_result['parsed_data']
        session.modified = True

    return jsonify({
        "status": "success",
        "reply": ai_result['reply'],
        "parsed_data": ai_result.get('parsed_data'),
        "requires_more_info": False
    })

@bp.route('/api/clear', methods=['POST'])
def chat_clear():
    """대화 초기화 API"""
    session.pop('chat_history', None)
    session.pop('latest_decision_payload', None)
    return jsonify({"status": "success", "message": "대화가 초기화되었습니다."})