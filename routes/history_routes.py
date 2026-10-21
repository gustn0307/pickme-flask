# pickme-flask-main/routes/history_routes.py
from flask import Blueprint, render_template, request, jsonify, session
from services.history_service import HistoryService

bp = Blueprint('history', __name__, url_prefix='/history')

@bp.get('/')
def index():
    return render_template('history/index.html')

# 담당 팀원이 이 파일의 엔드포인트를 구현합니다.

def get_current_user_id():
    """로그인 유저 ID 임시 처리 (회원가입/로그인 파트 연동 전)"""
    return session.get('user_id', 1)

@bp.get('/api/list')
def api_get_history_list():
    """[AJAX] 화면이 열린 후 자바스크립트가 데이터를 요청할 때 응답하는 API"""
    search_query = request.args.get('q', '').strip()
    category = request.args.get('category', '전체')
    bookmarked_only = request.args.get('bookmarked', 'false').lower() == 'true'
    sort_by = request.args.get('sort', 'latest')
    
    histories = HistoryService.get_user_histories(
        get_current_user_id(), search_query, category, bookmarked_only, sort_by
    )
    
    # 객체를 JSON으로 변환 (models.py의 Entity에 to_dict()가 구현되어 있다고 가정)
    # 만약 to_dict()가 없다면 여기서 딕셔너리로 매핑해주면 됩니다.
    result = []
    for h in histories:
        result.append({
            "id": h.id,
            "title": h.title,
            "dilemma": h.dilemma,
            "category": h.category,
            "created_at": h.created_at.strftime('%Y-%m-%d %H:%M') if h.created_at else "",
            "options_data": h.options_data,
            "recommendation_data": h.recommendation_data,
            "is_bookmarked": h.is_bookmarked,
            "actual_choice": h.actual_choice,
            "satisfaction_score": h.satisfaction_score,
            "retrospective_note": h.retrospective_note
        })
    return jsonify(result)

@bp.post('/api/<decision_id>/bookmark')
def api_toggle_bookmark(decision_id):
    """[AJAX] 북마크 토글"""
    new_status = HistoryService.toggle_bookmark(decision_id, get_current_user_id())
    if new_status is not None:
        return jsonify({"success": True, "is_bookmarked": new_status})
    return jsonify({"success": False, "error": "찾을 수 없습니다."}), 404

@bp.post('/api/<decision_id>/retrospective')
def api_update_retrospective(decision_id):
    """[AJAX] 회고 내용 업데이트"""
    data = request.get_json()
    success = HistoryService.update_retrospective(
        decision_id, 
        get_current_user_id(),
        data.get('actualChoice'),
        data.get('satisfactionScore'),
        data.get('retrospectiveNote')
    )
    return jsonify({"success": success})

@bp.delete('/api/<decision_id>')
def api_delete_history(decision_id):
    """[AJAX] 단건 삭제"""
    if HistoryService.delete_history(decision_id, get_current_user_id()):
        return jsonify({"success": True})
    return jsonify({"success": False}), 404

@bp.delete('/api/clear')
def api_clear_history():
    """[AJAX] 전체 기록 삭제"""
    HistoryService.clear_all_history(get_current_user_id())
    return jsonify({"success": True})