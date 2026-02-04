from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'


def is_postgresql(database_uri):
    """Check if database URI is PostgreSQL"""
    return database_uri and ('postgresql' in database_uri.lower() or 'postgres' in database_uri.lower())
