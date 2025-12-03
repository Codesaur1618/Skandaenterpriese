from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Permission, RolePermission, Tenant
from extensions import db
from auth_routes import permission_required
from audit import log_action

permission_bp = Blueprint('permission', __name__)


def get_default_tenant():
    return Tenant.query.filter_by(code='skanda').first()


@permission_bp.route('/')
@login_required
@permission_required('manage_permissions')
def list():
    """List all permissions organized by category and role"""
    permissions = Permission.query.order_by(Permission.category, Permission.name).all()
    roles = ['ADMIN', 'SALESMAN', 'DELIVERY', 'ORGANISER']
    
    # Get permission status for each role
    role_permissions = {}
    for role in roles:
        role_permissions[role] = {}
        for perm in permissions:
            role_perm = RolePermission.query.filter_by(
                role=role,
                permission_id=perm.id
            ).first()
            role_permissions[role][perm.code] = role_perm.granted if role_perm else False
    
    return render_template('permissions/list.html', 
                         permissions=permissions, 
                         roles=roles, 
                         role_permissions=role_permissions)


@permission_bp.route('/update', methods=['POST'])
@login_required
@permission_required('manage_permissions')
def update():
    """Update permissions for roles"""
    tenant = get_default_tenant()
    if not tenant:
        flash('Tenant not found.', 'danger')
        return redirect(url_for('permission.list'))
    
    # Get all permissions
    permissions = Permission.query.all()
    roles = ['ADMIN', 'SALESMAN', 'DELIVERY', 'ORGANISER']
    
    # Process form data
    for role in roles:
        if role == 'ADMIN':
            # Admin always has all permissions
            continue
            
        for perm in permissions:
            checkbox_name = f'perm_{role}_{perm.code}'
            is_granted = checkbox_name in request.form
            
            # Find or create role permission
            role_perm = RolePermission.query.filter_by(
                role=role,
                permission_id=perm.id
            ).first()
            
            if role_perm:
                role_perm.granted = is_granted
            else:
                role_perm = RolePermission(
                    role=role,
                    permission_id=perm.id,
                    granted=is_granted
                )
                db.session.add(role_perm)
    
    db.session.commit()
    log_action(current_user, 'UPDATE_PERMISSIONS', 'PERMISSIONS', 0)
    flash('Permissions updated successfully.', 'success')
    return redirect(url_for('permission.list'))

