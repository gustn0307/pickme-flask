from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, g, session, abort, jsonify
from services.community_service import CATEGORIES, list_posts, create_post, cast_vote, toggle_like, add_comment, latest_update, top_posts_by_engagement

bp = Blueprint('community', __name__, url_prefix='/community')

def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not g.user:
            flash('투표, 공감, 댓글, 게시글 작성은 로그인 후 이용할 수 있습니다.')
            return redirect(url_for('member.login', next=request.path))
        return fn(*args, **kwargs)
    return wrapped

def valid_csrf():
    return bool(session.get('_csrf_token') and request.form.get('_csrf_token') == session.get('_csrf_token'))

@bp.get('/updates')
def updates():
    return jsonify(updated_at=latest_update())

@bp.get('/')
def index():
    category = request.args.get('category', '전체')
    query = request.args.get('q', '').strip()[:100]
    posts, voted, liked, vote_counts = list_posts(category, query, g.user.id if g.user else None)
    featured_post_id = None
    if category in CATEGORIES:
        posts.sort(key=lambda post: post.created_at, reverse=True)
        if category != '전체' and posts:
            featured = max(posts, key=lambda post: (len(post.likes) + len(post.comments), post.created_at, post.id))
            featured_post_id = featured.id
            posts.remove(featured)
            posts.insert(0, featured)
    return render_template('community/index.html', posts=posts, categories=CATEGORIES, selected_category=category, query=query, voted=voted, liked=liked, vote_counts=vote_counts, latest_update=latest_update(), featured_post_id=featured_post_id, top_liked_posts=top_posts_by_engagement('likes'), top_commented_posts=top_posts_by_engagement('comments'))

@bp.post('/create')
@login_required
def create():
    if not valid_csrf(): abort(400)
    title, content = request.form.get('title', '').strip(), request.form.get('content', '').strip()
    category = request.form.get('category', '')
    options = [x.strip() for x in request.form.getlist('options') if x.strip()]
    if not title or len(title) > 200 or not content or len(content) > 5000 or category not in CATEGORIES or not 2 <= len(options) <= 5 or any(len(x) > 120 for x in options):
        flash('제목, 내용, 카테고리와 2~5개의 선택지를 확인해주세요. (제목 200자, 내용 5,000자 이내)')
        return redirect(url_for('community.index'))
    create_post(g.user, title, content, category, options)
    flash('고민 투표를 등록했습니다.')
    return redirect(url_for('community.index'))

@bp.post('/<int:post_id>/vote/<int:option_id>')
@login_required
def vote(post_id, option_id):
    if not valid_csrf(): abort(400)
    ok, message = cast_vote(post_id, option_id, g.user.id)
    flash(message)
    if not ok: abort(404)
    return redirect(url_for('community.index', _anchor=f'post-{post_id}'))

@bp.post('/<int:post_id>/like')
@login_required
def like(post_id):
    if not valid_csrf(): abort(400)
    if not toggle_like(post_id, g.user.id): abort(404)
    return redirect(url_for('community.index', _anchor=f'post-{post_id}'))

@bp.post('/<int:post_id>/comments')
@login_required
def comment(post_id):
    if not valid_csrf(): abort(400)
    content = request.form.get('content', '').strip()
    if not content or len(content) > 2000:
        flash('댓글은 1~2,000자로 작성해주세요.')
    elif not add_comment(post_id, g.user, content):
        abort(404)
    else:
        flash('댓글을 등록했습니다.')
    return redirect(url_for('community.index', _anchor=f'post-{post_id}'))
