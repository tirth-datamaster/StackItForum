from models import Tag
from app import db
import re

def process_tags(tag_string):
    """Process a comma-separated tag string and return tag objects."""
    if not tag_string:
        return []
    
    # Split by comma and clean up
    tag_names = [tag.strip().lower() for tag in tag_string.split(',') if tag.strip()]
    tag_objects = []
    
    for tag_name in tag_names:
        # Validate tag name (alphanumeric and hyphens only)
        if not re.match(r'^[a-zA-Z0-9-]+$', tag_name):
            continue
            
        # Get or create tag
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.session.add(tag)
        
        if tag not in tag_objects:
            tag_objects.append(tag)
    
    return tag_objects

def increment_question_views(question):
    """Increment question view count."""
    question.views += 1
    db.session.commit()

def get_popular_tags(limit=20):
    """Get popular tags by question count."""
    return db.session.query(Tag).join(Tag.questions).group_by(Tag.id).order_by(db.func.count().desc()).limit(limit).all()

def format_relative_time(dt):
    """Format datetime as relative time."""
    from datetime import datetime, timedelta
    
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "just now"
