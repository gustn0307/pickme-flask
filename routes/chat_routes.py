from flask import Blueprint, render_template
bp = Blueprint('chat', __name__, url_prefix='/chat')

@bp.get('/')
def index():
    return render_template('chat/index.html')

# 담당 팀원이 이 파일의 엔드포인트를 구현합니다.
