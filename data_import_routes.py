from datetime import datetime
from decimal import Decimal
import csv
from io import StringIO

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy import or_

from auth_routes import permission_required
from extensions import db
from models import Tenant, OutstandingOutlet, BeatMasterEntry


data_import_bp = Blueprint("data_import", __name__)


def _get_tenant():
    return Tenant.query.filter_by(code="skanda").first()


def _normalize(text):
    if text is None:
        return ""
    return str(text).strip()


def _to_decimal(value):
    raw = _normalize(value).replace(",", "")
    if not raw or raw.lower() in {"none", "nan", "null", "-"}:
        return Decimal("0.00")
    try:
        return Decimal(raw)
    except Exception:
        return Decimal("0.00")


def _to_int(value):
    raw = _normalize(value).replace(",", "")
    if not raw or raw.lower() in {"none", "nan", "null", "-"}:
        return None
    try:
        return int(float(raw))
    except Exception:
        return None


def _to_date(value):
    raw = _normalize(value)
    if not raw:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _to_datetime(value):
    raw = _normalize(value)
    if not raw:
        return None
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def _read_csv_rows(file_storage):
    payload = file_storage.read()
    if not payload:
        raise ValueError("Uploaded CSV is empty")

    text = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1", "iso-8859-1"):
        try:
            text = payload.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise ValueError("Could not decode CSV file")

    reader = csv.reader(StringIO(text), delimiter=",", quotechar='"')
    rows = [row for row in reader if any(_normalize(cell) for cell in row)]
    if not rows:
        raise ValueError("CSV has no usable rows")
    return rows


def _find_header(rows, required_columns):
    req = {c.strip().lower() for c in required_columns}
    for idx, row in enumerate(rows):
        normalized = {_normalize(c).lower() for c in row}
        if req.issubset(normalized):
            return idx, [_normalize(c) for c in row]
    return None, None


def _row_to_map(header, row):
    mapped = {}
    for i, col in enumerate(header):
        if not col:
            continue
        mapped[col] = _normalize(row[i]) if i < len(row) else ""
    return mapped


@data_import_bp.route("/outstanding", methods=["GET", "POST"])
@login_required
@permission_required("view_reports")
def outstanding():
    tenant = _get_tenant()
    if not tenant:
        flash("Tenant not found.", "danger")
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        file = request.files.get("csv_file")
        if not file or not file.filename:
            flash("Please select a CSV file.", "danger")
            return redirect(url_for("data_import.outstanding"))

        replace_existing = request.form.get("replace_existing") == "on"
        try:
            rows = _read_csv_rows(file)
            header_index, header = _find_header(
                rows,
                [
                    "Customer Code",
                    "Customer Name",
                    "Salesman Name",
                    "Beat",
                    "Document No.",
                    "Balance (?)",
                ],
            )
            if header_index is None:
                raise ValueError("Could not locate Outstanding header row in CSV.")

            data_rows = rows[header_index + 1 :]
            entries = []
            for row in data_rows:
                row_map = _row_to_map(header, row)
                customer_name = row_map.get("Customer Name")
                if not customer_name:
                    continue
                entries.append(
                    OutstandingOutlet(
                        tenant_id=tenant.id,
                        customer_code=row_map.get("Customer Code") or None,
                        customer_name=customer_name,
                        channel_type=row_map.get("Channel Type") or None,
                        outlet_type=row_map.get("Outlet Type") or None,
                        loyalty_program=row_map.get("Loyalty Program") or None,
                        credit_term=row_map.get("Credit Term") or None,
                        salesman_name=row_map.get("Salesman Name") or None,
                        beat=row_map.get("Beat") or None,
                        salesman_type=row_map.get("Salesman Type") or None,
                        document_type=row_map.get("Document Type") or None,
                        document_no=row_map.get("Document No.") or None,
                        document_date=_to_date(row_map.get("Document Date")),
                        amount=_to_decimal(row_map.get("Amount (?)")),
                        balance=_to_decimal(row_map.get("Balance (?)")),
                        due_days=_to_int(row_map.get("Due Days")),
                        over_due_days=_to_int(row_map.get("Over Due days")),
                        invoice_status=row_map.get("Invoice Status") or None,
                    )
                )

            if replace_existing:
                OutstandingOutlet.query.filter_by(tenant_id=tenant.id).delete(
                    synchronize_session=False
                )
            if entries:
                db.session.bulk_save_objects(entries)
            db.session.commit()
            flash(
                f"Outstanding upload complete: {len(entries)} rows imported.",
                "success",
            )
        except Exception as exc:
            db.session.rollback()
            flash(f"Outstanding upload failed: {exc}", "danger")

        return redirect(url_for("data_import.outstanding"))

    search = request.args.get("search", "").strip()
    salesman = request.args.get("salesman", "").strip()
    beat = request.args.get("beat", "").strip()
    invoice_status = request.args.get("invoice_status", "").strip()

    query = OutstandingOutlet.query.filter_by(tenant_id=tenant.id)
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                OutstandingOutlet.customer_name.ilike(like),
                OutstandingOutlet.customer_code.ilike(like),
                OutstandingOutlet.document_no.ilike(like),
            )
        )
    if salesman:
        query = query.filter(OutstandingOutlet.salesman_name == salesman)
    if beat:
        query = query.filter(OutstandingOutlet.beat == beat)
    if invoice_status:
        query = query.filter(OutstandingOutlet.invoice_status == invoice_status)

    rows = query.order_by(
        OutstandingOutlet.salesman_name.asc(),
        OutstandingOutlet.customer_name.asc(),
    ).limit(1000).all()

    salesmen = [
        x[0]
        for x in db.session.query(OutstandingOutlet.salesman_name)
        .filter(OutstandingOutlet.tenant_id == tenant.id, OutstandingOutlet.salesman_name.isnot(None))
        .distinct()
        .order_by(OutstandingOutlet.salesman_name.asc())
        .all()
    ]
    beats = [
        x[0]
        for x in db.session.query(OutstandingOutlet.beat)
        .filter(OutstandingOutlet.tenant_id == tenant.id, OutstandingOutlet.beat.isnot(None))
        .distinct()
        .order_by(OutstandingOutlet.beat.asc())
        .all()
    ]
    statuses = [
        x[0]
        for x in db.session.query(OutstandingOutlet.invoice_status)
        .filter(OutstandingOutlet.tenant_id == tenant.id, OutstandingOutlet.invoice_status.isnot(None))
        .distinct()
        .order_by(OutstandingOutlet.invoice_status.asc())
        .all()
    ]

    filters = [
        {
            "name": "search",
            "label": "Search",
            "type": "search",
            "placeholder": "Customer code/name or document no...",
            "value": search,
            "icon": "bi-search",
            "col_size": 4,
        },
        {
            "name": "salesman",
            "label": "Salesman",
            "type": "select",
            "value": salesman,
            "options": [{"value": s, "label": s} for s in salesmen],
            "icon": "bi-person-badge",
            "col_size": 3,
        },
        {
            "name": "beat",
            "label": "Beat",
            "type": "select",
            "value": beat,
            "options": [{"value": b, "label": b} for b in beats],
            "icon": "bi-geo-alt",
            "col_size": 3,
        },
        {
            "name": "invoice_status",
            "label": "Invoice Status",
            "type": "select",
            "value": invoice_status,
            "options": [{"value": s, "label": s} for s in statuses],
            "icon": "bi-info-circle",
            "col_size": 2,
        },
    ]

    active_filters = {}
    if search:
        active_filters["search"] = search
    if salesman:
        active_filters["salesman"] = salesman
    if beat:
        active_filters["beat"] = beat
    if invoice_status:
        active_filters["invoice_status"] = invoice_status

    return render_template(
        "data_imports/outstanding.html",
        rows=rows,
        filters=filters,
        active_filters=active_filters,
    )


@data_import_bp.route("/beat-master", methods=["GET", "POST"])
@login_required
@permission_required("view_reports")
def beat_master():
    tenant = _get_tenant()
    if not tenant:
        flash("Tenant not found.", "danger")
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        file = request.files.get("csv_file")
        if not file or not file.filename:
            flash("Please select a CSV file.", "danger")
            return redirect(url_for("data_import.beat_master"))

        replace_existing = request.form.get("replace_existing") == "on"
        try:
            rows = _read_csv_rows(file)
            header_index, header = _find_header(
                rows,
                ["DS Code", "Beat Code", "Beat Name", "Customer Code", "Customer Name"],
            )
            if header_index is None:
                raise ValueError("Could not locate Beat Master header row in CSV.")

            data_rows = rows[header_index + 1 :]
            entries = []
            for row in data_rows:
                row_map = _row_to_map(header, row)
                if not row_map.get("Customer Name") and not row_map.get("Beat Name"):
                    continue
                entries.append(
                    BeatMasterEntry(
                        tenant_id=tenant.id,
                        ds_code=row_map.get("DS Code") or None,
                        ds_name=row_map.get("DS Name") or None,
                        ds_type=row_map.get("DS Type") or None,
                        ds_status=row_map.get("DS Status") or None,
                        beat_code=row_map.get("Beat Code") or None,
                        beat_name=row_map.get("Beat Name") or None,
                        beat_end_date=_to_date(row_map.get("Beat End Date")),
                        customer_code=row_map.get("Customer Code") or None,
                        customer_name=row_map.get("Customer Name") or None,
                        customer_status=row_map.get("Customer Status") or None,
                        frequency=row_map.get("Frequency") or None,
                        beat_modified_at=_to_datetime(row_map.get("Date of Beat Modification")),
                        max_beat_count=_to_int(row_map.get("Max Beat Count")),
                    )
                )

            if replace_existing:
                BeatMasterEntry.query.filter_by(tenant_id=tenant.id).delete(
                    synchronize_session=False
                )
            if entries:
                db.session.bulk_save_objects(entries)
            db.session.commit()
            flash(f"Beat Master upload complete: {len(entries)} rows imported.", "success")
        except Exception as exc:
            db.session.rollback()
            flash(f"Beat Master upload failed: {exc}", "danger")

        return redirect(url_for("data_import.beat_master"))

    search = request.args.get("search", "").strip()
    ds_name = request.args.get("ds_name", "").strip()
    beat_name = request.args.get("beat_name", "").strip()
    frequency = request.args.get("frequency", "").strip()

    query = BeatMasterEntry.query.filter_by(tenant_id=tenant.id)
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                BeatMasterEntry.customer_name.ilike(like),
                BeatMasterEntry.customer_code.ilike(like),
                BeatMasterEntry.ds_code.ilike(like),
                BeatMasterEntry.beat_code.ilike(like),
            )
        )
    if ds_name:
        query = query.filter(BeatMasterEntry.ds_name == ds_name)
    if beat_name:
        query = query.filter(BeatMasterEntry.beat_name == beat_name)
    if frequency:
        query = query.filter(BeatMasterEntry.frequency == frequency)

    rows = query.order_by(
        BeatMasterEntry.ds_name.asc(),
        BeatMasterEntry.beat_name.asc(),
        BeatMasterEntry.customer_name.asc(),
    ).limit(1000).all()

    ds_names = [
        x[0]
        for x in db.session.query(BeatMasterEntry.ds_name)
        .filter(BeatMasterEntry.tenant_id == tenant.id, BeatMasterEntry.ds_name.isnot(None))
        .distinct()
        .order_by(BeatMasterEntry.ds_name.asc())
        .all()
    ]
    beat_names = [
        x[0]
        for x in db.session.query(BeatMasterEntry.beat_name)
        .filter(BeatMasterEntry.tenant_id == tenant.id, BeatMasterEntry.beat_name.isnot(None))
        .distinct()
        .order_by(BeatMasterEntry.beat_name.asc())
        .all()
    ]
    frequencies = [
        x[0]
        for x in db.session.query(BeatMasterEntry.frequency)
        .filter(BeatMasterEntry.tenant_id == tenant.id, BeatMasterEntry.frequency.isnot(None))
        .distinct()
        .order_by(BeatMasterEntry.frequency.asc())
        .all()
    ]

    filters = [
        {
            "name": "search",
            "label": "Search",
            "type": "search",
            "placeholder": "Customer/beat/DS code...",
            "value": search,
            "icon": "bi-search",
            "col_size": 4,
        },
        {
            "name": "ds_name",
            "label": "DS Name",
            "type": "select",
            "value": ds_name,
            "options": [{"value": s, "label": s} for s in ds_names],
            "icon": "bi-person",
            "col_size": 3,
        },
        {
            "name": "beat_name",
            "label": "Beat Name",
            "type": "select",
            "value": beat_name,
            "options": [{"value": b, "label": b} for b in beat_names],
            "icon": "bi-signpost-2",
            "col_size": 3,
        },
        {
            "name": "frequency",
            "label": "Frequency",
            "type": "select",
            "value": frequency,
            "options": [{"value": f, "label": f} for f in frequencies],
            "icon": "bi-arrow-repeat",
            "col_size": 2,
        },
    ]

    active_filters = {}
    if search:
        active_filters["search"] = search
    if ds_name:
        active_filters["ds_name"] = ds_name
    if beat_name:
        active_filters["beat_name"] = beat_name
    if frequency:
        active_filters["frequency"] = frequency

    return render_template(
        "data_imports/beat_master.html",
        rows=rows,
        filters=filters,
        active_filters=active_filters,
    )
