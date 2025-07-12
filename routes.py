from flask import session, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import current_user
from sqlalchemy import or_, desc, func
from app import app, db
from auth import require_login, auth_bp
from models import User, Question, Answer, Tag, Vote, question_tags
from forms import QuestionForm, AnswerForm, SearchForm, ProfileForm
from utils import process_tags, increment_question_views, get_popular_tags, format_relative_time

app.register_blueprint(auth_bp)

# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True

# Template globals
@app.template_global()
def relative_time(dt):
    return format_relative_time(dt)

@app.route('/')
def index():
    """Home page - shows recent questions."""
    if not current_user.is_authenticated:
        return render_template('landing.html')
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    questions = Question.query.order_by(Question.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    popular_tags = get_popular_tags(10)
    
    return render_template('index.html', questions=questions, popular_tags=popular_tags)

@app.route('/questions')
def questions_list():
    """List all questions with filtering and sorting."""
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'newest')
    tag_filter = request.args.get('tag')
    per_page = 10
    
    query = Question.query
    
    # Apply tag filter
    if tag_filter:
        query = query.join(Question.tags).filter(Tag.name == tag_filter)
    
    # Apply sorting
    if sort == 'newest':
        query = query.order_by(Question.created_at.desc())
    elif sort == 'oldest':
        query = query.order_by(Question.created_at.asc())
    elif sort == 'most-viewed':
        query = query.order_by(Question.views.desc())
    elif sort == 'most-answers':
        query = query.outerjoin(Answer).group_by(Question.id).order_by(func.count(Answer.id).desc())
    
    questions = query.paginate(page=page, per_page=per_page, error_out=False)
    popular_tags = get_popular_tags(10)
    
    return render_template('questions/list.html', 
                         questions=questions, 
                         popular_tags=popular_tags,
                         current_sort=sort,
                         current_tag=tag_filter)

@app.route('/question/<int:id>')
def question_detail(id):
    """Show question detail with answers."""
    question = Question.query.get_or_404(id)
    
    # Increment view count
    increment_question_views(question)
    
    # Get answers sorted by votes
    answers = Answer.query.filter_by(question_id=id).outerjoin(Vote).group_by(Answer.id).order_by(
        func.sum(func.case([(Vote.is_upvote == True, 1)], else_=0)) - 
        func.sum(func.case([(Vote.is_upvote == False, 1)], else_=0)).desc(),
        Answer.created_at.asc()
    ).all()
    
    # Get user votes for each answer (if logged in)
    user_votes = {}
    if current_user.is_authenticated:
        votes = Vote.query.filter_by(user_id=current_user.id).filter(
            Vote.answer_id.in_([a.id for a in answers])
        ).all()
        user_votes = {vote.answer_id: vote.is_upvote for vote in votes}
    
    form = AnswerForm()
    
    return render_template('questions/detail.html', 
                         question=question, 
                         answers=answers,
                         user_votes=user_votes,
                         form=form)

@app.route('/ask', methods=['GET', 'POST'])
@require_login
def ask_question():
    """Ask a new question."""
    form = QuestionForm()
    
    if form.validate_on_submit():
        question = Question(
            title=form.title.data,
            content=form.content.data,
            author_id=current_user.id
        )
        
        # Process tags
        if form.tags.data:
            question.tags = process_tags(form.tags.data)
        
        db.session.add(question)
        db.session.commit()
        
        flash('Your question has been posted!', 'success')
        return redirect(url_for('question_detail', id=question.id))
    
    return render_template('questions/ask.html', form=form)

@app.route('/question/<int:id>/edit', methods=['GET', 'POST'])
@require_login
def edit_question(id):
    """Edit a question."""
    question = Question.query.get_or_404(id)
    
    if question.author_id != current_user.id:
        abort(403)
    
    form = QuestionForm(obj=question)
    
    if form.validate_on_submit():
        question.title = form.title.data
        question.content = form.content.data
        
        # Update tags
        question.tags.clear()
        if form.tags.data:
            question.tags = process_tags(form.tags.data)
        
        db.session.commit()
        flash('Your question has been updated!', 'success')
        return redirect(url_for('question_detail', id=question.id))
    
    # Pre-populate tags
    if request.method == 'GET':
        form.tags.data = ', '.join([tag.name for tag in question.tags])
    
    return render_template('questions/edit.html', form=form, question=question)

@app.route('/question/<int:question_id>/answer', methods=['POST'])
@require_login
def post_answer(question_id):
    """Post an answer to a question."""
    question = Question.query.get_or_404(question_id)
    form = AnswerForm()
    
    if form.validate_on_submit():
        answer = Answer(
            content=form.content.data,
            question_id=question_id,
            author_id=current_user.id
        )
        db.session.add(answer)
        db.session.commit()
        
        flash('Your answer has been posted!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{error}', 'error')
    
    return redirect(url_for('question_detail', id=question_id))

@app.route('/answer/<int:id>/edit', methods=['GET', 'POST'])
@require_login
def edit_answer(id):
    """Edit an answer."""
    answer = Answer.query.get_or_404(id)
    
    if answer.author_id != current_user.id:
        abort(403)
    
    form = AnswerForm(obj=answer)
    
    if form.validate_on_submit():
        answer.content = form.content.data
        db.session.commit()
        flash('Your answer has been updated!', 'success')
        return redirect(url_for('question_detail', id=answer.question_id))
    
    return render_template('answers/edit.html', form=form, answer=answer)

@app.route('/vote', methods=['POST'])
@require_login
def vote():
    """Handle voting on answers."""
    answer_id = request.form.get('answer_id', type=int)
    vote_type = request.form.get('vote_type')  # 'up' or 'down'
    
    if not answer_id or vote_type not in ['up', 'down']:
        flash('Invalid vote request', 'error')
        return redirect(request.referrer or url_for('index'))
    
    answer = Answer.query.get_or_404(answer_id)
    
    # Check if user already voted
    existing_vote = Vote.query.filter_by(user_id=current_user.id, answer_id=answer_id).first()
    
    is_upvote = vote_type == 'up'
    
    if existing_vote:
        if existing_vote.is_upvote == is_upvote:
            # Remove vote if clicking the same vote type
            db.session.delete(existing_vote)
        else:
            # Change vote type
            existing_vote.is_upvote = is_upvote
    else:
        # Create new vote
        new_vote = Vote(user_id=current_user.id, answer_id=answer_id, is_upvote=is_upvote)
        db.session.add(new_vote)
    
    db.session.commit()
    return redirect(url_for('question_detail', id=answer.question_id))

@app.route('/search')
def search():
    """Search questions."""
    form = SearchForm()
    questions = None
    query = request.args.get('q', '').strip()
    tag = request.args.get('tag', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    if query or tag:
        questions_query = Question.query
        
        if query:
            questions_query = questions_query.filter(
                or_(
                    Question.title.contains(query),
                    Question.content.contains(query)
                )
            )
        
        if tag:
            questions_query = questions_query.join(Question.tags).filter(Tag.name == tag)
        
        questions = questions_query.order_by(Question.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
    popular_tags = get_popular_tags(10)
    
    return render_template('search.html', 
                         questions=questions, 
                         query=query, 
                         tag=tag,
                         popular_tags=popular_tags,
                         form=form)

@app.route('/user/<user_id>')
def user_profile(user_id):
    """Show user profile."""
    user = User.query.get_or_404(user_id)
    
    questions = Question.query.filter_by(author_id=user_id).order_by(Question.created_at.desc()).limit(10).all()
    answers = Answer.query.filter_by(author_id=user_id).order_by(Answer.created_at.desc()).limit(10).all()
    
    return render_template('users/profile.html', user=user, questions=questions, answers=answers)

@app.route('/profile/edit', methods=['GET', 'POST'])
@require_login
def edit_profile():
    """Edit current user's profile."""
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.bio = form.bio.data
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('user_profile', user_id=current_user.id))
    
    return render_template('users/profile.html', form=form, edit_mode=True)

@app.route('/tags')
def tags_list():
    """List all tags."""
    tags = Tag.query.order_by(Tag.name).all()
    return render_template('tags/list.html', tags=tags)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('403.html'), 403
