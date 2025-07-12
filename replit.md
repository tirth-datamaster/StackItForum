# StackIt - Q&A Community Platform

## Overview

StackIt is a Stack Overflow-inspired Q&A community platform built with Flask. It allows users to ask questions, provide answers, vote on content, and build reputation within the community. The application features a modern, responsive design with comprehensive user management and content organization capabilities.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask web framework with Python
- **Database**: SQLAlchemy ORM with PostgreSQL (configurable via DATABASE_URL)
- **Authentication**: Replit Auth integration with OAuth2 flow
- **Session Management**: Flask-Login for user session handling
- **Forms**: Flask-WTF for form handling and validation

### Frontend Architecture
- **Templates**: Jinja2 templating engine
- **CSS Framework**: Bootstrap 5.3.0 for responsive design
- **JavaScript**: Vanilla JavaScript with modern ES6+ features
- **Rich Text**: TinyMCE integration for content editing
- **Icons**: Font Awesome 6.4.0

### Database Schema
- **Users**: Core user management with reputation system
- **Questions**: Question posts with metadata (views, timestamps)
- **Answers**: Answer posts linked to questions
- **Tags**: Categorization system with many-to-many relationship to questions
- **Votes**: Voting system for questions and answers
- **OAuth**: Required table for Replit Auth integration

## Key Components

### Authentication System
- Replit Auth integration for secure OAuth2 authentication
- User session storage with browser session tracking
- Profile management with customizable user information
- Mandatory OAuth and User tables for Replit compatibility

### Content Management
- Question creation with rich text editor support
- Answer system with voting capabilities
- Tag-based categorization and filtering
- Search functionality across questions and tags
- View counting and engagement tracking

### Voting System
- Upvote/downvote functionality for questions and answers
- Reputation calculation based on community feedback
- Vote tracking to prevent duplicate voting

### User Interface
- Responsive Bootstrap-based design
- Professional SaaS-style interface
- Breadcrumb navigation
- Error pages (404, 403) with user-friendly messaging
- Interactive features with JavaScript enhancements

## Data Flow

1. **User Authentication**: Users authenticate via Replit Auth OAuth2 flow
2. **Content Creation**: Authenticated users create questions/answers with form validation
3. **Content Discovery**: Users browse questions via multiple filtering/sorting options
4. **Engagement**: Community votes on content, affecting author reputation
5. **Search**: Full-text search across questions with tag filtering

## External Dependencies

### Authentication
- **Replit Auth**: OAuth2 provider for user authentication
- **Flask-Dance**: OAuth consumer for handling authentication flow

### Frontend Libraries
- **Bootstrap 5.3.0**: UI framework via CDN
- **Font Awesome 6.4.0**: Icon library via CDN
- **TinyMCE 6**: Rich text editor via CDN

### Python Packages
- **Flask**: Web framework
- **Flask-SQLAlchemy**: Database ORM
- **Flask-Login**: Session management
- **Flask-WTF**: Form handling
- **WTForms**: Form validation
- **PyJWT**: JWT token handling
- **Werkzeug**: WSGI utilities

## Deployment Strategy

### Environment Configuration
- **DATABASE_URL**: PostgreSQL connection string
- **SESSION_SECRET**: Flask session encryption key
- **Debug Mode**: Configurable for development/production

### Production Considerations
- ProxyFix middleware for HTTPS handling
- Database connection pooling with health checks
- Session permanence for user experience
- Logging configuration for debugging

### File Structure
- **app.py**: Application factory and database initialization
- **routes.py**: URL routing and view functions
- **models.py**: Database models and relationships
- **forms.py**: Form definitions and validation
- **utils.py**: Helper functions for common operations
- **replit_auth.py**: Authentication handling
- **templates/**: Jinja2 template hierarchy
- **static/**: CSS, JavaScript, and asset files

The application follows Flask best practices with clear separation of concerns, making it maintainable and scalable for a community-driven Q&A platform.