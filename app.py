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
    
    # Database initialization endpoint (for Render free tier - no shell access)
    @app.route('/init-db')
    def init_database():
        from flask import jsonify
        from models import Tenant, User, Permission
        from extensions import db
        
        try:
            with app.app_context():
                # Create all tables
                db.create_all()
                
                # Check if already initialized
                tenant = Tenant.query.filter_by(code='skanda').first()
                if tenant:
                    return jsonify({
                        'success': True,
                        'message': 'Database already initialized. Tenant exists.',
                        'tenant': tenant.name
                    }), 200
                
                # Run seed logic
                from seed import PERMISSIONS, DEFAULT_ROLE_PERMISSIONS
                
                # Create tenant
                tenant = Tenant(
                    name='Skanda Enterprises',
                    code='skanda',
                    is_active=True
                )
                db.session.add(tenant)
                db.session.flush()
                
                # Create permissions
                for perm_data in PERMISSIONS:
                    perm = Permission(
                        name=perm_data['name'],
                        code=perm_data['code'],
                        description=perm_data['description'],
                        category=perm_data['category']
                    )
                    db.session.add(perm)
                
                db.session.flush()
                
                # Create role permissions
                from models import RolePermission
                permissions = Permission.query.all()
                roles = ['ADMIN', 'SALESMAN', 'DELIVERY', 'ORGANISER']
                
                for role in roles:
                    if role == 'ADMIN':
                        for perm in permissions:
                            role_perm = RolePermission(
                                role=role,
                                permission_id=perm.id,
                                granted=True
                            )
                            db.session.add(role_perm)
                    else:
                        default_perms = DEFAULT_ROLE_PERMISSIONS.get(role, [])
                        for perm_code in default_perms:
                            perm = Permission.query.filter_by(code=perm_code).first()
                            if perm:
                                role_perm = RolePermission(
                                    role=role,
                                    permission_id=perm.id,
                                    granted=True
                                )
                                db.session.add(role_perm)
                
                # Create users
                users_to_create = [
                    {'username': 'admin', 'role': 'ADMIN', 'password': 'admin123'},
                    {'username': 'salesman', 'role': 'SALESMAN', 'password': 'salesman123'},
                    {'username': 'delivery', 'role': 'DELIVERY', 'password': 'delivery123'},
                    {'username': 'organiser', 'role': 'ORGANISER', 'password': 'organiser123'}
                ]
                
                for user_data in users_to_create:
                    user = User(
                        tenant_id=tenant.id,
                        username=user_data['username'],
                        role=user_data['role'],
                        is_active=True
                    )
                    user.set_password(user_data['password'])
                    db.session.add(user)
                
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Database initialized successfully!',
                    'tenant': tenant.name,
                    'users_created': [u['username'] for u in users_to_create],
                    'login_url': '/login'
                }), 200
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
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

