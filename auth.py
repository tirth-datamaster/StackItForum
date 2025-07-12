from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import User
from forms import LoginForm, RegisterForm
from app import app, db
import logging

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create auth blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(
            (User.email == form.email_or_username.data) | 
            (User.username == form.email_or_username.data)
        ).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            flash(f'Welcome back, {user.display_name}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email/username or password', 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if user already exists
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered', 'error')
            return render_template('auth/register.html', form=form)
        
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken', 'error')
            return render_template('auth/register.html', form=form)
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        user.set_password(form.password.data)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Log in the user
            login_user(user)
            flash(f'Welcome to StackIt, {user.display_name}!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating user: {e}")
            flash('An error occurred during registration. Please try again.', 'error')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    from forms import ProfileForm
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.bio = form.bio.data
        
        try:
            db.session.commit()
            flash('Your profile has been updated!', 'success')
            return redirect(url_for('user_profile', user_id=current_user.id))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating profile: {e}")
            flash('An error occurred while updating your profile.', 'error')
    
    return render_template('auth/profile.html', form=form)

def require_login(f):
    """Decorator to require login for routes"""
    return login_required(f)