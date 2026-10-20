from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, g, flash
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User

bp = Blueprint('member', __name__, url_prefix='/member')

def login_required(fn):
    @wraps(fn)
    def decorated(*args, **kwargs):
        if not g.user:
            flash('로그인이 필요합니다.')
            return redirect(url_for('member.login'))
        return fn(*args, **kwargs)
    return decorated

@bp.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        nickname = request.form.get('nickname','').strip()
        if not email or '@' not in email or len(password) < 8 or not nickname:
            flash('이메일, 닉네임, 8자 이상 비밀번호를 확인해주세요.')
        elif db.session.query(User).filter_by(email=email).first():
            flash('이미 가입된 이메일입니다.')
        else:
            user = User(email=email, nickname=nickname, password_hash=generate_password_hash(password))
            db.session.add(user); db.session.commit()
            flash('회원가입되었습니다. 로그인해주세요.')
            return redirect(url_for('member.login'))
    return render_template('member/signup.html')

@bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        user = db.session.query(User).filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, request.form.get('password','')):
            session.clear(); session['user_id'] = user.id
            return redirect(url_for('main.index'))
        flash('이메일 또는 비밀번호가 올바르지 않습니다.')
    return render_template('member/login.html')

@bp.post('/logout')
def logout():
    session.clear(); return redirect(url_for('main.index'))

@bp.get('/mypage')
@login_required
def mypage():
    return render_template('member/mypage.html')
