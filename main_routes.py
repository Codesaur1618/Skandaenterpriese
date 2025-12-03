from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Vendor, Bill, CreditEntry, Tenant
from sqlalchemy import func
from extensions import db
from auth_routes import permission_required

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Allow all authenticated users to access dashboard
    # But show different content based on role
    # Get default tenant
    tenant = Tenant.query.filter_by(code='skanda').first()
    if not tenant:
        return render_template('dashboard.html', stats={})
    
    # Get stats
    vendor_count = Vendor.query.filter_by(tenant_id=tenant.id).count()
    bill_count = Bill.query.filter_by(tenant_id=tenant.id).count()
    
    # Calculate outstanding: total billed - total incoming payments
    total_billed = db.session.query(func.sum(Bill.amount_total)).filter_by(
        tenant_id=tenant.id, status='CONFIRMED'
    ).scalar() or 0
    
    total_incoming = db.session.query(func.sum(CreditEntry.amount)).filter_by(
        tenant_id=tenant.id, direction='INCOMING'
    ).scalar() or 0
    
    total_outgoing = db.session.query(func.sum(CreditEntry.amount)).filter_by(
        tenant_id=tenant.id, direction='OUTGOING'
    ).scalar() or 0
    
    outstanding = float(total_billed) - float(total_incoming) + float(total_outgoing)
    
    stats = {
        'vendor_count': vendor_count,
        'bill_count': bill_count,
        'outstanding': outstanding
    }
    
    return render_template('dashboard.html', stats=stats)

