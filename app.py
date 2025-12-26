from flask import Flask
from config import config
from extensions import db, login_manager
from models import User
import os

# Import blueprints
from auth_routes import auth_bp
from main_routes import main_bp
from vendor_routes import vendor_bp
from bill_routes import bill_bp
from proxy_routes import proxy_bp
from credit_routes import credit_bp
from delivery_routes import delivery_bp
from ocr_routes import ocr_bp
from report_routes import report_bp
from permission_routes import permission_bp


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Make permission checking available in templates
    @app.context_processor
    def inject_permissions():
        from flask_login import current_user
        def has_permission(permission_code):
            if current_user.is_authenticated:
                return current_user.has_permission(permission_code)
            return False
        return dict(has_permission=has_permission)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/')
    app.register_blueprint(main_bp, url_prefix='/')
    app.register_blueprint(vendor_bp, url_prefix='/vendors')
    app.register_blueprint(bill_bp, url_prefix='/bills')
    app.register_blueprint(proxy_bp, url_prefix='/proxy-bills')
    app.register_blueprint(credit_bp, url_prefix='/credits')
    app.register_blueprint(delivery_bp, url_prefix='/deliveries')
    app.register_blueprint(ocr_bp, url_prefix='/ocr')
    app.register_blueprint(report_bp, url_prefix='/reports')
    app.register_blueprint(permission_bp, url_prefix='/permissions')
    
    # Create upload directories
    upload_folder = app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    
    # Serve service worker with correct MIME type
    @app.route('/service-worker.js')
    def service_worker():
        from flask import send_from_directory
        import os
        static_folder = app.static_folder or os.path.join(app.root_path, 'static')
        return send_from_directory(os.path.join(static_folder, 'js'), 'service-worker.js', mimetype='application/javascript')
    
    return app


# Create app instance for Gunicorn (production)
# Gunicorn will use: gunicorn app:app
app = create_app(os.environ.get('FLASK_ENV', 'production'))

if __name__ == '__main__':
    # Development server
    app = create_app('development')
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='127.0.0.1', port=5000)

