from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import CreditEntry, Bill, ProxyBill, Vendor, Tenant
from forms import CreditEntryForm
from extensions import db
from audit import log_action
from auth_routes import permission_required

credit_bp = Blueprint('credit', __name__)


def get_default_tenant():
    return Tenant.query.filter_by(code='skanda').first()


@credit_bp.route('/')
@login_required
@permission_required('view_credits')
def list():
    tenant = get_default_tenant()
    if not tenant:
        flash('Tenant not found.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    from models import Bill, Vendor
    from sqlalchemy import func
    from datetime import datetime
    
    # Get filter parameters
    search = request.args.get('search', '').strip()
    vendor_id = request.args.get('vendor_id', type=int)
    direction = request.args.get('direction', '')
    payment_method = request.args.get('payment_method', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    amount_min = request.args.get('amount_min', type=float)
    amount_max = request.args.get('amount_max', type=float)
    show_unpaid_bills = request.args.get('show_unpaid_bills', 'true') == 'true'
    
    # Get all credit entries with filters
    credit_query = CreditEntry.query.filter_by(tenant_id=tenant.id)
    
    if search:
        credit_query = credit_query.filter(
            CreditEntry.reference_number.ilike(f'%{search}%')
        )
    
    if vendor_id:
        credit_query = credit_query.filter(CreditEntry.vendor_id == vendor_id)
    
    if direction:
        credit_query = credit_query.filter(CreditEntry.direction == direction)
    
    if payment_method:
        credit_query = credit_query.filter(CreditEntry.payment_method == payment_method)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            credit_query = credit_query.filter(CreditEntry.payment_date >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            credit_query = credit_query.filter(CreditEntry.payment_date <= date_to_obj)
        except ValueError:
            pass
    
    if amount_min is not None:
        credit_query = credit_query.filter(CreditEntry.amount >= amount_min)
    
    if amount_max is not None:
        credit_query = credit_query.filter(CreditEntry.amount <= amount_max)
    
    credits = credit_query.order_by(CreditEntry.payment_date.desc()).all()
    
    # Get all unpaid bills (outstanding) with filters
    unpaid_bills = []
    if show_unpaid_bills:
        bill_query = Bill.query.filter_by(tenant_id=tenant.id, status='CONFIRMED')
        
        if vendor_id:
            bill_query = bill_query.filter(Bill.vendor_id == vendor_id)
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                bill_query = bill_query.filter(Bill.bill_date >= date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                bill_query = bill_query.filter(Bill.bill_date <= date_to_obj)
            except ValueError:
                pass
        
        all_bills = bill_query.all()
        
        for bill in all_bills:
            total_paid = db.session.query(func.sum(CreditEntry.amount)).filter_by(
                tenant_id=tenant.id,
                bill_id=bill.id,
                direction='INCOMING'
            ).scalar() or 0
            
            remaining = float(bill.amount_total) - float(total_paid)
            if remaining > 0:
                if amount_min is not None and remaining < amount_min:
                    continue
                if amount_max is not None and remaining > amount_max:
                    continue
                unpaid_bills.append({
                    'bill': bill,
                    'total': float(bill.amount_total),
                    'paid': float(total_paid),
                    'outstanding': remaining
                })
    
    # Get vendors for filter dropdown
    vendors = Vendor.query.filter_by(tenant_id=tenant.id).order_by(Vendor.name).all()
    
    # Prepare filter data for template
    filters = [
        {
            'name': 'search',
            'label': 'Search',
            'type': 'search',
            'placeholder': 'Search by reference number...',
            'value': search,
            'icon': 'bi-search',
            'col_size': 3
        },
        {
            'name': 'vendor_id',
            'label': 'Vendor',
            'type': 'select',
            'value': vendor_id,
            'options': [{'value': v.id, 'label': v.name} for v in vendors],
            'icon': 'bi-person',
            'col_size': 2
        },
        {
            'name': 'direction',
            'label': 'Direction',
            'type': 'select',
            'value': direction,
            'options': [
                {'value': 'INCOMING', 'label': 'Incoming'},
                {'value': 'OUTGOING', 'label': 'Outgoing'}
            ],
            'icon': 'bi-arrow-left-right',
            'col_size': 2
        },
        {
            'name': 'payment_method',
            'label': 'Payment Method',
            'type': 'select',
            'value': payment_method,
            'options': [
                {'value': 'CASH', 'label': 'Cash'},
                {'value': 'CHEQUE', 'label': 'Cheque'},
                {'value': 'BANK_TRANSFER', 'label': 'Bank Transfer'},
                {'value': 'UPI', 'label': 'UPI'},
                {'value': 'OTHER', 'label': 'Other'}
            ],
            'icon': 'bi-wallet2',
            'col_size': 2
        },
        {
            'name': 'payment_date',
            'label': 'Date Range',
            'type': 'date-range',
            'value_from': date_from,
            'value_to': date_to,
            'icon': 'bi-calendar',
            'col_size': 3
        },
        {
            'name': 'amount',
            'label': 'Amount Range',
            'type': 'number-range',
            'value_min': amount_min,
            'value_max': amount_max,
            'icon': 'bi-currency-rupee',
            'col_size': 3
        }
    ]
    
    # Active filters for display
    active_filters = {}
    if search:
        active_filters['Search'] = search
    if vendor_id:
        vendor = Vendor.query.get(vendor_id)
        if vendor:
            active_filters['Vendor'] = vendor.name
    if direction:
        active_filters['Direction'] = direction
    if payment_method:
        active_filters['Method'] = payment_method
    if date_from or date_to:
        active_filters['Date'] = f"{date_from or 'Any'} to {date_to or 'Any'}"
    if amount_min is not None or amount_max is not None:
        active_filters['Amount'] = f"₹{amount_min or 0} - ₹{amount_max or '∞'}"
    
    return render_template('credits/list.html', credits=credits, unpaid_bills=unpaid_bills, 
                         filters=filters, active_filters=active_filters)


@credit_bp.route('/new', methods=['GET', 'POST'])
@login_required
@permission_required('create_credit')
def create():
    tenant = get_default_tenant()
    if not tenant:
        flash('Tenant not found.', 'danger')
        return redirect(url_for('credit.list'))
    
    form = CreditEntryForm()
    
    # Pre-fill from query params
    bill_id = request.args.get('bill_id', type=int)
    proxy_bill_id = request.args.get('proxy_bill_id', type=int)
    vendor_id = request.args.get('vendor_id', type=int)
    
    # Populate choices - use empty string for None option
    form.bill_id.choices = [('', 'None')] + [(b.id, f"{b.bill_number} - {b.vendor.name}") 
                                               for b in Bill.query.filter_by(tenant_id=tenant.id).all()]
    form.proxy_bill_id.choices = [('', 'None')] + [(pb.id, f"{pb.proxy_number} - {pb.vendor.name}") 
                                                    for pb in ProxyBill.query.filter_by(tenant_id=tenant.id).all()]
    form.vendor_id.choices = [(v.id, v.name) for v in Vendor.query.filter_by(tenant_id=tenant.id).order_by(Vendor.name).all()]
    
    if bill_id:
        form.bill_id.data = bill_id
        bill = Bill.query.get(bill_id)
        if bill:
            form.vendor_id.data = bill.vendor_id
    
    if proxy_bill_id:
        form.proxy_bill_id.data = proxy_bill_id
        proxy_bill = ProxyBill.query.get(proxy_bill_id)
        if proxy_bill:
            form.vendor_id.data = proxy_bill.vendor_id
    
    if vendor_id:
        form.vendor_id.data = vendor_id
    
    if form.validate_on_submit():
        bill_id_val = form.bill_id.data if form.bill_id.data and form.bill_id.data != '' else None
        proxy_bill_id_val = form.proxy_bill_id.data if form.proxy_bill_id.data and form.proxy_bill_id.data != '' else None
        
        credit = CreditEntry(
            tenant_id=tenant.id,
            bill_id=bill_id_val,
            proxy_bill_id=proxy_bill_id_val,
            vendor_id=form.vendor_id.data,
            amount=form.amount.data,
            direction=form.direction.data,
            payment_method=form.payment_method.data,
            payment_date=form.payment_date.data,
            reference_number=form.reference_number.data,
            notes=form.notes.data
        )
        db.session.add(credit)
        db.session.commit()
        log_action(current_user, 'CREATE_CREDIT', 'CREDIT_ENTRY', credit.id)
        flash('Credit entry created successfully.', 'success')
        return redirect(url_for('credit.list'))
    
    return render_template('credits/form.html', form=form, title='New Credit Entry')


@credit_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('edit_credit')
def edit(id):
    credit = CreditEntry.query.get_or_404(id)
    form = CreditEntryForm(obj=credit)
    
    tenant = get_default_tenant()
    form.bill_id.choices = [('', 'None')] + [(b.id, f"{b.bill_number} - {b.vendor.name}") 
                                             for b in Bill.query.filter_by(tenant_id=tenant.id).all()]
    form.proxy_bill_id.choices = [('', 'None')] + [(pb.id, f"{pb.proxy_number} - {pb.vendor.name}") 
                                                   for pb in ProxyBill.query.filter_by(tenant_id=tenant.id).all()]
    form.vendor_id.choices = [(v.id, v.name) for v in Vendor.query.filter_by(tenant_id=tenant.id).order_by(Vendor.name).all()]
    
    if form.validate_on_submit():
        credit.bill_id = form.bill_id.data if form.bill_id.data and form.bill_id.data != '' else None
        credit.proxy_bill_id = form.proxy_bill_id.data if form.proxy_bill_id.data and form.proxy_bill_id.data != '' else None
        credit.vendor_id = form.vendor_id.data
        credit.amount = form.amount.data
        credit.direction = form.direction.data
        credit.payment_method = form.payment_method.data
        credit.payment_date = form.payment_date.data
        credit.reference_number = form.reference_number.data
        credit.notes = form.notes.data
        db.session.commit()
        log_action(current_user, 'UPDATE_CREDIT', 'CREDIT_ENTRY', credit.id)
        flash('Credit entry updated successfully.', 'success')
        return redirect(url_for('credit.list'))
    
    return render_template('credits/form.html', form=form, credit=credit, title='Edit Credit Entry')

