from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from models import (
    Question, Answer, User, Tag, Bounty, LiveSession, LiveSessionParticipant,
    LearningPath, LearningPathItem, Achievement, UserAchievement, 
    QuestionSuggestion, CollaborativeAnswer, ExpertVerification,
    MentorshipRequest, TrendingTopic, QuestionDifficulty
)
from forms import SearchForm
import random
import json

features_bp = Blueprint('features', __name__, url_prefix='/features')

# 1. BOUNTY SYSTEM
@features_bp.route('/bounties')
def bounties():
    """Display active bounties"""
    active_bounties = Bounty.query.filter_by(is_active=True).join(Question).all()
    return render_template('features/bounties.html', bounties=active_bounties)

@features_bp.route('/bounty/create/<int:question_id>', methods=['GET', 'POST'])
@login_required
def create_bounty(question_id):
    """Create a bounty for a question"""
    question = Question.query.get_or_404(question_id)
    
    if request.method == 'POST':
        bounty_amount = int(request.form['bounty_amount'])
        description = request.form.get('description', '')
        expires_days = int(request.form.get('expires_days', 7))
        
        # Check if user has enough reputation
        if current_user.reputation < bounty_amount:
            flash('Insufficient reputation to create this bounty', 'error')
            return redirect(url_for('question_detail', id=question_id))
        
        # Create bounty
        bounty = Bounty(
            question_id=question_id,
            creator_id=current_user.id,
            bounty_amount=bounty_amount,
            description=description,
            expires_at=datetime.now() + timedelta(days=expires_days)
        )
        
        # Deduct reputation from user
        current_user.reputation -= bounty_amount
        
        db.session.add(bounty)
        db.session.commit()
        
        flash(f'Bounty of {bounty_amount} reputation points created!', 'success')
        return redirect(url_for('question_detail', id=question_id))
    
    return render_template('features/create_bounty.html', question=question)

# 2. LIVE Q&A SESSIONS
@features_bp.route('/live-sessions')
def live_sessions():
    """Display upcoming and active live sessions"""
    upcoming_sessions = LiveSession.query.filter(
        LiveSession.scheduled_at > datetime.now()
    ).order_by(LiveSession.scheduled_at).all()
    
    active_sessions = LiveSession.query.filter_by(is_active=True).all()
    
    return render_template('features/live_sessions.html', 
                         upcoming_sessions=upcoming_sessions,
                         active_sessions=active_sessions)

@features_bp.route('/live-session/create', methods=['GET', 'POST'])
@login_required
def create_live_session():
    """Create a new live session"""
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        scheduled_at = datetime.strptime(request.form['scheduled_at'], '%Y-%m-%dT%H:%M')
        duration_minutes = int(request.form.get('duration_minutes', 60))
        max_participants = int(request.form.get('max_participants', 100))
        
        session = LiveSession(
            title=title,
            description=description,
            host_id=current_user.id,
            scheduled_at=scheduled_at,
            duration_minutes=duration_minutes,
            max_participants=max_participants
        )
        
        db.session.add(session)
        db.session.commit()
        
        flash('Live session created successfully!', 'success')
        return redirect(url_for('features.live_sessions'))
    
    return render_template('features/create_live_session.html')

@features_bp.route('/live-session/<int:session_id>/join')
@login_required
def join_live_session(session_id):
    """Join a live session"""
    session = LiveSession.query.get_or_404(session_id)
    
    # Check if already joined
    existing_participation = LiveSessionParticipant.query.filter_by(
        session_id=session_id, user_id=current_user.id
    ).first()
    
    if not existing_participation:
        participation = LiveSessionParticipant(
            session_id=session_id,
            user_id=current_user.id
        )
        db.session.add(participation)
        db.session.commit()
    
    return render_template('features/live_session_room.html', session=session)

# 3. LEARNING PATHS
@features_bp.route('/learning-paths')
def learning_paths():
    """Display available learning paths"""
    paths = LearningPath.query.filter_by(is_published=True).all()
    return render_template('features/learning_paths.html', paths=paths)

@features_bp.route('/learning-path/create', methods=['GET', 'POST'])
@login_required
def create_learning_path():
    """Create a new learning path"""
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        difficulty_level = request.form.get('difficulty_level', 'beginner')
        estimated_duration = int(request.form.get('estimated_duration', 60))
        
        path = LearningPath(
            title=title,
            description=description,
            creator_id=current_user.id,
            difficulty_level=difficulty_level,
            estimated_duration=estimated_duration
        )
        
        db.session.add(path)
        db.session.commit()
        
        flash('Learning path created! Now add questions to it.', 'success')
        return redirect(url_for('features.edit_learning_path', path_id=path.id))
    
    return render_template('features/create_learning_path.html')

@features_bp.route('/learning-path/<int:path_id>')
def view_learning_path(path_id):
    """View a learning path"""
    path = LearningPath.query.get_or_404(path_id)
    return render_template('features/view_learning_path.html', path=path)

# 4. ACHIEVEMENT SYSTEM
@features_bp.route('/achievements')
def achievements():
    """Display all achievements"""
    all_achievements = Achievement.query.filter_by(is_active=True).all()
    
    user_achievements = []
    if current_user.is_authenticated:
        user_achievements = [ua.achievement_id for ua in current_user.achievements]
    
    return render_template('features/achievements.html', 
                         achievements=all_achievements,
                         user_achievements=user_achievements)

@features_bp.route('/leaderboard')
def leaderboard():
    """Display top users by reputation and achievements"""
    top_users = User.query.order_by(User.reputation.desc()).limit(20).all()
    
    # Get achievement counts for each user
    user_achievement_counts = {}
    for user in top_users:
        user_achievement_counts[user.id] = len(user.achievements)
    
    return render_template('features/leaderboard.html', 
                         users=top_users,
                         achievement_counts=user_achievement_counts)

# 5. TRENDING TOPICS
@features_bp.route('/trending')
def trending_topics():
    """Display trending topics"""
    trending = TrendingTopic.query.order_by(TrendingTopic.trend_score.desc()).limit(10).all()
    return render_template('features/trending.html', trending=trending)

# 6. MENTORSHIP SYSTEM
@features_bp.route('/mentorship')
@login_required
def mentorship():
    """Mentorship hub"""
    my_requests = MentorshipRequest.query.filter_by(mentee_id=current_user.id).all()
    my_mentoring = MentorshipRequest.query.filter_by(mentor_id=current_user.id).all()
    available_requests = MentorshipRequest.query.filter_by(status='pending').all()
    
    return render_template('features/mentorship.html',
                         my_requests=my_requests,
                         my_mentoring=my_mentoring,
                         available_requests=available_requests)

@features_bp.route('/mentorship/request', methods=['GET', 'POST'])
@login_required
def request_mentorship():
    """Request mentorship"""
    if request.method == 'POST':
        topic_area = request.form['topic_area']
        description = request.form['description']
        
        mentorship_request = MentorshipRequest(
            mentee_id=current_user.id,
            topic_area=topic_area,
            description=description
        )
        
        db.session.add(mentorship_request)
        db.session.commit()
        
        flash('Mentorship request submitted!', 'success')
        return redirect(url_for('features.mentorship'))
    
    return render_template('features/request_mentorship.html')

# 7. AI-POWERED QUESTION SUGGESTIONS
@features_bp.route('/suggestions')
@login_required
def question_suggestions():
    """Get AI-powered question suggestions"""
    # Mock AI suggestions (in production, this would use actual AI)
    suggestions = generate_mock_suggestions(current_user.id)
    
    return render_template('features/suggestions.html', suggestions=suggestions)

def generate_mock_suggestions(user_id):
    """Generate mock AI suggestions based on user activity"""
    # This would be replaced with actual AI in production
    sample_suggestions = [
        {
            'title': 'How to implement OAuth2 authentication in Flask?',
            'content': 'I need to add secure authentication to my Flask application...',
            'tags': 'flask, oauth2, authentication',
            'confidence': 0.85
        },
        {
            'title': 'Best practices for database migrations in production?',
            'content': 'What are the safest ways to handle database schema changes...',
            'tags': 'database, migrations, production',
            'confidence': 0.92
        },
        {
            'title': 'How to optimize React component performance?',
            'content': 'My React components are rendering slowly...',
            'tags': 'react, performance, optimization',
            'confidence': 0.78
        }
    ]
    
    return sample_suggestions[:2]  # Return 2 random suggestions

# 8. COLLABORATIVE FEATURES
@features_bp.route('/collaborate/answer/<int:answer_id>')
@login_required
def collaborate_on_answer(answer_id):
    """Collaborate on an answer"""
    answer = Answer.query.get_or_404(answer_id)
    collaborations = CollaborativeAnswer.query.filter_by(answer_id=answer_id).order_by(
        CollaborativeAnswer.contribution_order
    ).all()
    
    return render_template('features/collaborate_answer.html', 
                         answer=answer, 
                         collaborations=collaborations)

# 9. EXPERT VERIFICATION
@features_bp.route('/expert/verify/<int:answer_id>', methods=['POST'])
@login_required
def verify_answer(answer_id):
    """Expert verification of an answer"""
    # In production, check if user is qualified as expert
    if current_user.reputation < 1000:
        flash('You need at least 1000 reputation to verify answers', 'error')
        return redirect(url_for('question_detail', id=answer_id))
    
    answer = Answer.query.get_or_404(answer_id)
    verification_note = request.form.get('note', '')
    
    # Check if already verified by this expert
    existing_verification = ExpertVerification.query.filter_by(
        answer_id=answer_id, expert_id=current_user.id
    ).first()
    
    if existing_verification:
        flash('You have already verified this answer', 'info')
    else:
        verification = ExpertVerification(
            answer_id=answer_id,
            expert_id=current_user.id,
            verification_note=verification_note
        )
        db.session.add(verification)
        db.session.commit()
        flash('Answer verified successfully!', 'success')
    
    return redirect(url_for('question_detail', id=answer.question_id))

# 10. ANALYTICS AND INSIGHTS
@features_bp.route('/analytics')
@login_required
def analytics():
    """Personal analytics dashboard"""
    # User statistics
    user_stats = {
        'questions_asked': Question.query.filter_by(author_id=current_user.id).count(),
        'answers_given': Answer.query.filter_by(author_id=current_user.id).count(),
        'reputation': current_user.reputation,
        'achievements': len(current_user.achievements)
    }
    
    # Recent activity
    recent_questions = Question.query.filter_by(author_id=current_user.id).order_by(
        Question.created_at.desc()
    ).limit(5).all()
    
    recent_answers = Answer.query.filter_by(author_id=current_user.id).order_by(
        Answer.created_at.desc()
    ).limit(5).all()
    
    return render_template('features/analytics.html',
                         stats=user_stats,
                         recent_questions=recent_questions,
                         recent_answers=recent_answers)

# Helper functions for achievement tracking
def check_achievements(user_id):
    """Check if user has earned any new achievements"""
    user = User.query.get(user_id)
    if not user:
        return
    
    # Check for various achievements
    achievements_to_award = []
    
    # First Question achievement
    if user.questions.count() >= 1:
        first_question = Achievement.query.filter_by(name='First Question').first()
        if first_question and not any(ua.achievement_id == first_question.id for ua in user.achievements):
            achievements_to_award.append(first_question)
    
    # Helpful Member achievement (10 answers)
    if user.answers.count() >= 10:
        helpful_member = Achievement.query.filter_by(name='Helpful Member').first()
        if helpful_member and not any(ua.achievement_id == helpful_member.id for ua in user.achievements):
            achievements_to_award.append(helpful_member)
    
    # Award achievements
    for achievement in achievements_to_award:
        user_achievement = UserAchievement(
            user_id=user_id,
            achievement_id=achievement.id
        )
        db.session.add(user_achievement)
        user.reputation += achievement.points
    
    if achievements_to_award:
        db.session.commit()
        return achievements_to_award
    
    return []

# Initialize default achievements
def init_achievements():
    """Initialize default achievements"""
    default_achievements = [
        {
            'name': 'First Steps',
            'description': 'Ask your first question',
            'icon': 'fas fa-baby',
            'category': 'beginner',
            'points': 10
        },
        {
            'name': 'Helpful Member',
            'description': 'Answer 10 questions',
            'icon': 'fas fa-hands-helping',
            'category': 'contributor',
            'points': 50
        },
        {
            'name': 'Expert',
            'description': 'Reach 1000 reputation',
            'icon': 'fas fa-star',
            'category': 'expert',
            'points': 100
        },
        {
            'name': 'Mentor',
            'description': 'Complete 5 mentorship sessions',
            'icon': 'fas fa-chalkboard-teacher',
            'category': 'mentor',
            'points': 150
        }
    ]
    
    for achievement_data in default_achievements:
        existing = Achievement.query.filter_by(name=achievement_data['name']).first()
        if not existing:
            achievement = Achievement(**achievement_data)
            db.session.add(achievement)
    
    db.session.commit()