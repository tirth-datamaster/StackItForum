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
