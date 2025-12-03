from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Vendor, Bill, CreditEntry, DeliveryOrder, Tenant
from forms import ReportDateRangeForm
from extensions import db
from sqlalchemy import func
from auth_routes import permission_required

report_bp = Blueprint('report', __name__)


def get_default_tenant():
    return Tenant.query.filter_by(code='skanda').first()


@report_bp.route('/outstanding')
@login_required
@permission_required('view_reports')
def outstanding():
    tenant = get_default_tenant()
    if not tenant:
        flash('Tenant not found.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    vendors = Vendor.query.filter_by(tenant_id=tenant.id).all()
    results = []
    
    for vendor in vendors:
        # Total billed (confirmed bills)
        total_billed = db.session.query(func.sum(Bill.amount_total)).filter_by(
            tenant_id=tenant.id, vendor_id=vendor.id, status='CONFIRMED'
        ).scalar() or 0
        
        # Total incoming payments (from credit entries)
        total_incoming = db.session.query(func.sum(CreditEntry.amount)).filter_by(
            tenant_id=tenant.id, vendor_id=vendor.id, direction='INCOMING'
        ).scalar() or 0
        
        # Total outgoing payments
        total_outgoing = db.session.query(func.sum(CreditEntry.amount)).filter_by(
            tenant_id=tenant.id, vendor_id=vendor.id, direction='OUTGOING'
        ).scalar() or 0
        
        # Outstanding = Total Billed - Total Incoming + Total Outgoing
        outstanding = float(total_billed) - float(total_incoming) + float(total_outgoing)
        
        if outstanding != 0 or total_billed > 0:
            results.append({
                'vendor': vendor,
                'total_billed': float(total_billed),
                'total_incoming': float(total_incoming),
                'total_outgoing': float(total_outgoing),
                'outstanding': outstanding
            })
    
    return render_template('reports/outstanding.html', results=results)


@report_bp.route('/collection', methods=['GET', 'POST'])
@login_required
@permission_required('view_reports')
def collection():
    tenant = get_default_tenant()
    if not tenant:
        flash('Tenant not found.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    form = ReportDateRangeForm()
    results = None
    
    if form.validate_on_submit():
        start_date = form.start_date.data
        end_date = form.end_date.data
        
        # Total incoming
        total_incoming = db.session.query(func.sum(CreditEntry.amount)).filter(
            CreditEntry.tenant_id == tenant.id,
            CreditEntry.direction == 'INCOMING',
            CreditEntry.payment_date >= start_date,
            CreditEntry.payment_date <= end_date
        ).scalar() or 0
        
        # Total outgoing
        total_outgoing = db.session.query(func.sum(CreditEntry.amount)).filter(
            CreditEntry.tenant_id == tenant.id,
            CreditEntry.direction == 'OUTGOING',
            CreditEntry.payment_date >= start_date,
            CreditEntry.payment_date <= end_date
        ).scalar() or 0
        
        net = float(total_incoming) - float(total_outgoing)
        
        results = {
            'start_date': start_date,
            'end_date': end_date,
            'total_incoming': float(total_incoming),
            'total_outgoing': float(total_outgoing),
            'net': net
        }
    
    return render_template('reports/collection.html', form=form, results=results)


@report_bp.route('/deliveries')
@login_required
@permission_required('view_reports')
def deliveries():
    tenant = get_default_tenant()
    if not tenant:
        flash('Tenant not found.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Count by status
    pending = DeliveryOrder.query.filter_by(tenant_id=tenant.id, status='PENDING').count()
    in_transit = DeliveryOrder.query.filter_by(tenant_id=tenant.id, status='IN_TRANSIT').count()
    delivered = DeliveryOrder.query.filter_by(tenant_id=tenant.id, status='DELIVERED').count()
    cancelled = DeliveryOrder.query.filter_by(tenant_id=tenant.id, status='CANCELLED').count()
    total = DeliveryOrder.query.filter_by(tenant_id=tenant.id).count()
    
    stats = {
        'pending': pending,
        'in_transit': in_transit,
        'delivered': delivered,
        'cancelled': cancelled,
        'total': total
    }
    
    return render_template('reports/deliveries.html', stats=stats)

