from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import UniqueConstraint, func
import secrets
import string

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    profile_image_url = db.Column(db.String(200), nullable=True)
    reputation = db.Column(db.Integer, default=0)
    bio = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    questions = db.relationship('Question', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    answers = db.relationship('Answer', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    votes = db.relationship('Vote', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def generate_username(email):
        """Generate a unique username from email"""
        base_username = email.split('@')[0].lower()
        # Remove special characters
        base_username = ''.join(c for c in base_username if c.isalnum())
        
        # Ensure minimum length
        if len(base_username) < 3:
            base_username += ''.join(secrets.choice(string.ascii_lowercase) for _ in range(3 - len(base_username)))
        
        # Check if username exists and add suffix if needed
        username = base_username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        return username

    @property
    def display_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        return self.username

    def __repr__(self):
        return f'<User {self.username}>'

# Association table for many-to-many relationship between questions and tags
question_tags = db.Table('question_tags',
    db.Column('question_id', db.Integer, db.ForeignKey('question.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    views = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    answers = db.relationship('Answer', backref='question', lazy='dynamic', cascade='all, delete-orphan')
    tags = db.relationship('Tag', secondary=question_tags, lazy='subquery', backref=db.backref('questions', lazy=True))

    @property
    def answer_count(self):
        return self.answers.count()

    @property
    def latest_activity(self):
        latest_answer = self.answers.order_by(Answer.created_at.desc()).first()
        if latest_answer:
            return max(self.updated_at, latest_answer.created_at)
        return self.updated_at

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_accepted = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    votes = db.relationship('Vote', backref='answer', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def vote_score(self):
        upvotes = self.votes.filter_by(is_upvote=True).count()
        downvotes = self.votes.filter_by(is_upvote=False).count()
        return upvotes - downvotes

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    color = db.Column(db.String(7), default='#007bff')  # Bootstrap primary color
    
    created_at = db.Column(db.DateTime, default=datetime.now)

    @property
    def question_count(self):
        return len(self.questions)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'), nullable=False)
    is_upvote = db.Column(db.Boolean, nullable=False)  # True for upvote, False for downvote
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Ensure one vote per user per answer
    __table_args__ = (UniqueConstraint('user_id', 'answer_id', name='unique_user_answer_vote'),)

# UNIQUE FEATURES - Making StackIt stand out

# 1. AI-Powered Question Suggestions
class QuestionSuggestion(db.Model):
    """AI-generated question suggestions based on user activity and trends"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    suggested_title = db.Column(db.String(200), nullable=False)
    suggested_content = db.Column(db.Text, nullable=False)
    suggested_tags = db.Column(db.String(200), nullable=True)
    is_used = db.Column(db.Boolean, default=False)
    confidence_score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    user = db.relationship('User', backref='question_suggestions')

# 2. Knowledge Bounty System
class Bounty(db.Model):
    """Bounty system for difficult questions"""
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    bounty_amount = db.Column(db.Integer, nullable=False)  # Reputation points
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    winner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    awarded_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    question = db.relationship('Question', backref='bounties')
    creator = db.relationship('User', foreign_keys=[creator_id], backref='created_bounties')
    winner = db.relationship('User', foreign_keys=[winner_id], backref='won_bounties')

# 3. Collaborative Answer Building
class CollaborativeAnswer(db.Model):
    """Multiple users can collaborate on a single answer"""
    id = db.Column(db.Integer, primary_key=True)
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'), nullable=False)
    contributor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    contribution_text = db.Column(db.Text, nullable=False)
    contribution_order = db.Column(db.Integer, nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    answer = db.relationship('Answer', backref='collaborations')
    contributor = db.relationship('User', backref='answer_contributions')

# 4. Expert Verification System
class ExpertVerification(db.Model):
    """Experts can verify answers as accurate"""
    id = db.Column(db.Integer, primary_key=True)
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'), nullable=False)
    expert_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    verification_note = db.Column(db.Text, nullable=True)
    is_verified = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    answer = db.relationship('Answer', backref='expert_verifications')
    expert = db.relationship('User', backref='verifications_given')

# 5. Live Q&A Sessions
class LiveSession(db.Model):
    """Live Q&A sessions with experts"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    host_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=60)
    is_active = db.Column(db.Boolean, default=False)
    max_participants = db.Column(db.Integer, default=100)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    host = db.relationship('User', backref='hosted_sessions')

class LiveSessionParticipant(db.Model):
    """Participants in live sessions"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('live_session.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.now)
    
    session = db.relationship('LiveSession', backref='participants')
    user = db.relationship('User', backref='session_participations')

# 6. Smart Learning Paths
class LearningPath(db.Model):
    """Curated learning paths through questions"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    difficulty_level = db.Column(db.String(20), default='beginner')  # beginner, intermediate, advanced
    estimated_duration = db.Column(db.Integer, nullable=True)  # in minutes
    is_published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    creator = db.relationship('User', backref='created_paths')

class LearningPathItem(db.Model):
    """Questions included in learning paths"""
    id = db.Column(db.Integer, primary_key=True)
    path_id = db.Column(db.Integer, db.ForeignKey('learning_path.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    order_index = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    path = db.relationship('LearningPath', backref='items')
    question = db.relationship('Question', backref='path_inclusions')

# 7. Achievement System
class Achievement(db.Model):
    """Achievements users can earn"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    points = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

class UserAchievement(db.Model):
    """Achievements earned by users"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.now)
    
    user = db.relationship('User', backref='achievements')
    achievement = db.relationship('Achievement', backref='earned_by')

# 8. Question Difficulty Prediction
class QuestionDifficulty(db.Model):
    """AI-predicted difficulty levels for questions"""
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    difficulty_score = db.Column(db.Float, nullable=False)  # 0-1 scale
    complexity_factors = db.Column(db.JSON, nullable=True)  # JSON of factors
    predicted_at = db.Column(db.DateTime, default=datetime.now)
    
    question = db.relationship('Question', backref='difficulty_assessment')

# 9. Trending Topics Tracking
class TrendingTopic(db.Model):
    """Track trending topics and questions"""
    id = db.Column(db.Integer, primary_key=True)
    topic_name = db.Column(db.String(100), nullable=False)
    trend_score = db.Column(db.Float, nullable=False)
    related_tags = db.Column(db.JSON, nullable=True)
    question_count = db.Column(db.Integer, default=0)
    growth_rate = db.Column(db.Float, default=0.0)
    tracked_at = db.Column(db.DateTime, default=datetime.now)

# 10. Mentorship Program
class MentorshipRequest(db.Model):
    """Users can request mentorship"""
    id = db.Column(db.Integer, primary_key=True)
    mentee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    topic_area = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, matched, active, completed
    created_at = db.Column(db.DateTime, default=datetime.now)
    matched_at = db.Column(db.DateTime, nullable=True)
    
    mentee = db.relationship('User', foreign_keys=[mentee_id], backref='mentorship_requests')
    mentor = db.relationship('User', foreign_keys=[mentor_id], backref='mentorship_assignments')
