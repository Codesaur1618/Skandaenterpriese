"""
Picklist upload: parse CSV or OCR text and apply rows to create/update DeliveryOrders.
"""
import csv
import re
from io import StringIO
from datetime import datetime
from pathlib import Path

# Column header aliases: canonical name -> accepted names
PICKLIST_CSV_COLUMNS = {
    "invoice_no": [
        "Invoice No",
        "Invoice No.",
        "Bill Number",
        "Proxy Number",
        "invoice_no",
        "invoice no",
    ],
    "delivery_person": [
        "Delivery Person",
        "DeliveryPerson",
        "Delivery_User",
        "Delivery User",
        "delivery_person",
        "delivery person",
    ],
    "delivery_date": [
        "Delivery Date",
        "delivery_date",
        "delivery date",
        "Date",
    ],
    "delivery_address": [
        "Delivery Address",
        "Address",
        "delivery_address",
        "delivery address",
    ],
    "salesman": [
        "Salesman",
        "Salesman Name",
        "salesman",
        "salesman name",
    ],
}


def _normalize_header(h):
    if h is None:
        return ""
    return str(h).strip()


def _normalize_token(s):
    """Normalize labels for robust header matching (case/space/punctuation-insensitive)."""
    text = _normalize_header(s).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _find_column_index(headers, canonical_key):
    names = PICKLIST_CSV_COLUMNS.get(canonical_key, [])
    normalized_headers = [_normalize_token(h) for h in headers]
    for alias in names:
        alias_clean = _normalize_token(alias)
        for i, h in enumerate(normalized_headers):
            if h == alias_clean:
                return i
    return -1


def _parse_date(s):
    """Parse date string; return date or None."""
    if not s or not str(s).strip():
        return None
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def parse_picklist_csv(filepath):
    """
    Parse a picklist CSV file. Returns list of dicts with keys:
    invoice_no, delivery_person, delivery_date, delivery_address, salesman (optional).
    Raises ValueError if required columns are missing or file cannot be read.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise ValueError("File not found")

    csv_data = None
    encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252", "iso-8859-1"]
    for encoding in encodings:
        try:
            with open(filepath, "r", encoding=encoding, newline="") as f:
                reader = csv.reader(f, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
                csv_data = list(reader)
            if csv_data:
                break
        except (UnicodeDecodeError, Exception):
            continue

    if not csv_data or len(csv_data) < 2:
        raise ValueError("CSV file is empty or has no data rows")

    # Some picklist exports include metadata rows first and headers later.
    # Find the best header row by required-column coverage.
    best_header_idx = -1
    best_score = -1
    best_indices = None
    for row_idx, header_row in enumerate(csv_data):
        idx_inv_candidate = _find_column_index(header_row, "invoice_no")
        idx_person_candidate = _find_column_index(header_row, "delivery_person")
        idx_date_candidate = _find_column_index(header_row, "delivery_date")
        idx_address_candidate = _find_column_index(header_row, "delivery_address")
        score = 0
        if idx_inv_candidate >= 0:
            score += 2
        if idx_person_candidate >= 0:
            score += 1
        if idx_date_candidate >= 0:
            score += 1
        if idx_address_candidate >= 0:
            score += 1
        if score > best_score:
            best_score = score
            best_header_idx = row_idx
            best_indices = (
                idx_inv_candidate,
                idx_person_candidate,
                idx_date_candidate,
                idx_address_candidate,
                _find_column_index(header_row, "salesman"),
            )

    if best_indices is None:
        raise ValueError("Could not detect a valid CSV header row")

    headers = csv_data[best_header_idx]
    data_rows = csv_data[best_header_idx + 1 :]
    idx_inv, idx_person, idx_date, idx_address, idx_salesman = best_indices
    idx_customer_name = -1
    normalized_headers = [_normalize_token(h) for h in headers]
    for i, h in enumerate(normalized_headers):
        if h in {"customer name", "customer"}:
            idx_customer_name = i
            break

    # Metadata fallback values (from lines like "Delivery Person :,,,John")
    metadata_delivery_person = None
    metadata_delivery_date = None
    metadata_delivery_address = None
    for meta_row in csv_data[: best_header_idx if best_header_idx > 0 else 0]:
        non_empty_cells = [_normalize_header(c) for c in meta_row if _normalize_header(c)]
        if not non_empty_cells:
            continue
        row_text = " ".join(non_empty_cells)
        key_text = _normalize_token(row_text)
        last_value = non_empty_cells[-1]
        if ("delivery person" in key_text or "delivery user" in key_text) and last_value:
            metadata_delivery_person = last_value
        elif "delivery date" in key_text and last_value:
            metadata_delivery_date = last_value
        elif "delivery address" in key_text and last_value:
            metadata_delivery_address = last_value

    missing = []
    if idx_inv < 0:
        missing.append("Invoice No")
    if idx_person < 0 and not metadata_delivery_person:
        missing.append("Delivery Person")
    if idx_date < 0 and not metadata_delivery_date:
        missing.append("Delivery Date")
    if idx_address < 0 and not metadata_delivery_address and idx_customer_name < 0:
        missing.append("Delivery Address")
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))

    rows = []
    for row in data_rows:
        if len(row) <= max(idx_inv, idx_person, idx_date, idx_address):
            continue
        non_empty_count = sum(1 for cell in row if _normalize_header(cell))
        invoice_no = _normalize_header(row[idx_inv]) if idx_inv < len(row) else ""
        delivery_person = _normalize_header(row[idx_person]) if idx_person >= 0 and idx_person < len(row) else ""
        delivery_date_raw = _normalize_header(row[idx_date]) if idx_date >= 0 and idx_date < len(row) else ""
        delivery_address = _normalize_header(row[idx_address]) if idx_address >= 0 and idx_address < len(row) else ""
        customer_name = _normalize_header(row[idx_customer_name]) if idx_customer_name >= 0 and idx_customer_name < len(row) else ""
        salesman = _normalize_header(row[idx_salesman]) if idx_salesman >= 0 and idx_salesman < len(row) else None
        if not invoice_no and not delivery_person and not delivery_address and not customer_name:
            continue
        if not delivery_person and metadata_delivery_person:
            delivery_person = _normalize_header(metadata_delivery_person)
        if not delivery_date_raw and metadata_delivery_date:
            delivery_date_raw = _normalize_header(metadata_delivery_date)
        if not delivery_address:
            if customer_name:
                delivery_address = customer_name
            elif metadata_delivery_address:
                delivery_address = _normalize_header(metadata_delivery_address)
        invoice_key = _normalize_token(invoice_no)
        if invoice_key in {"invoice no", "salesman", "grand total", "picklist"}:
            continue
        if invoice_key.startswith("page "):
            continue
        if re.fullmatch(r"[-_\s]+", invoice_no or ""):
            continue
        if not delivery_address and idx_customer_name >= 0 and non_empty_count <= 2:
            # Skip section rows in picklist exports like "Salesman ..." and page totals.
            continue
        if (
            not delivery_address
            and idx_customer_name >= 0
            and not re.search(r"\d", invoice_no or "")
            and "/" not in (invoice_no or "")
        ):
            continue
        delivery_date = _parse_date(delivery_date_raw)
        rows.append({
            "invoice_no": invoice_no,
            "delivery_person": delivery_person,
            "delivery_date": delivery_date,
            "delivery_address": delivery_address or "",
            "salesman": salesman if salesman else None,
        })
    return rows


def parse_picklist_ocr_text(ocr_text):
    """
    Parse OCR-extracted text into delivery rows (best-effort).
    Looks for patterns like "Delivery Person: X", "Invoice No: Y", "Date: Z", "Address: ..."
    or table-like lines. Returns list of dicts same shape as parse_picklist_csv.
    """
    if not ocr_text or not str(ocr_text).strip():
        return []

    lines = [ln.strip() for ln in str(ocr_text).splitlines() if ln.strip()]
    rows = []
    current = {}

    label_patterns = {
        "invoice_no": re.compile(r"^(?:invoice\s*no\.?|bill\s*number|proxy\s*number)\s*[:\-]?\s*(.+)$", re.I),
        "delivery_person": re.compile(r"^(?:delivery\s*person|delivery\s*user)\s*[:\-]?\s*(.+)$", re.I),
        "delivery_date": re.compile(r"^(?:delivery\s*)?date\s*[:\-]?\s*(.+)$", re.I),
        "delivery_address": re.compile(r"^(?:delivery\s*)?address\s*[:\-]?\s*(.+)$", re.I),
        "salesman": re.compile(r"^salesman\s*(?:name)?\s*[:\-]?\s*(.+)$", re.I),
    }

    def flush_current():
        if current.get("invoice_no") or current.get("delivery_person") or current.get("delivery_address"):
            rows.append({
                "invoice_no": current.get("invoice_no", "").strip(),
                "delivery_person": current.get("delivery_person", "").strip(),
                "delivery_date": _parse_date(current.get("delivery_date", "")) if current.get("delivery_date") else None,
                "delivery_address": (current.get("delivery_address") or "").strip(),
                "salesman": (current.get("salesman") or "").strip() or None,
            })
        current.clear()

    for line in lines:
        matched = False
        for key, pat in label_patterns.items():
            m = pat.match(line)
            if m:
                current[key] = m.group(1).strip()
                matched = True
                break
        if not matched and current:
            if "address" in line.lower() or len(line) > 30:
                current["delivery_address"] = (current.get("delivery_address") or "") + " " + line
            else:
                flush_current()

    flush_current()
    return rows


def apply_picklist_rows(tenant_id, rows):
    """
    Create or update DeliveryOrders from parsed rows.
    Uses models.DeliveryOrder, Bill, ProxyBill, User and extensions.db (imported inside to avoid circular import).
    Returns dict: created (int), updated (int), skipped (list of (row_dict, reason_string)).
    """
    from models import DeliveryOrder, Bill, ProxyBill, User
    from extensions import db
    from sqlalchemy import and_

    def _normalize_lookup_key(value):
        text = (value or "").strip().lower()
        text = re.sub(r"[^a-z0-9/]+", "", text)
        return text

    created = 0
    updated = 0
    skipped = []

    bills = Bill.query.filter_by(tenant_id=tenant_id).all()
    proxy_bills = ProxyBill.query.filter_by(tenant_id=tenant_id).all()
    users = User.query.filter(
        User.tenant_id == tenant_id,
        User.role.in_(["DELIVERY", "SALESMAN"]),
        User.is_active == True,
    ).all()

    bill_lookup = {_normalize_lookup_key(b.bill_number): b for b in bills if b.bill_number}
    proxy_lookup = {_normalize_lookup_key(p.proxy_number): p for p in proxy_bills if p.proxy_number}
    user_lookup = {_normalize_lookup_key(u.username): u for u in users if u.username}
    default_delivery_user = next((u for u in users if u.role == "DELIVERY"), None)

    for row in rows:
        invoice_no = (row.get("invoice_no") or "").strip()
        delivery_person = (row.get("delivery_person") or "").strip()
        delivery_date = row.get("delivery_date")
        delivery_address = (row.get("delivery_address") or "").strip()
        salesman_name = (row.get("salesman") or "").strip() or None

        if not invoice_no:
            skipped.append((row, "Invoice No is empty"))
            continue
        if not delivery_person:
            skipped.append((row, "Delivery Person is empty"))
            continue
        if not delivery_date:
            skipped.append((row, "Delivery Date is missing or invalid"))
            continue
        if not delivery_address:
            skipped.append((row, "Delivery Address is empty"))
            continue

        normalized_invoice = _normalize_lookup_key(invoice_no)
        bill = bill_lookup.get(normalized_invoice)
        proxy_bill = None
        if not bill:
            proxy_bill = proxy_lookup.get(normalized_invoice)
        if not bill and not proxy_bill:
            skipped.append((row, f"No Bill or ProxyBill found for Invoice No '{invoice_no}'"))
            continue

        delivery_user = user_lookup.get(_normalize_lookup_key(delivery_person))
        if not delivery_user and _normalize_lookup_key(delivery_person) in {
            "defaultdeliveryrepresentative",
            "defaultdeliveryperson",
            "deliveryrepresentative",
            "deliveryperson",
        }:
            delivery_user = default_delivery_user
        if not delivery_user:
            skipped.append((row, f"No active user (DELIVERY/SALESMAN) found for '{delivery_person}'"))
            continue

        salesman_user = None
        if salesman_name:
            salesman_user = user_lookup.get(_normalize_lookup_key(salesman_name))

        bill_id = bill.id if bill else None
        proxy_bill_id = proxy_bill.id if proxy_bill else None

        if bill_id:
            existing = DeliveryOrder.query.filter_by(
                tenant_id=tenant_id,
                bill_id=bill_id,
                delivery_user_id=delivery_user.id,
                delivery_date=delivery_date,
            ).first()
        else:
            existing = DeliveryOrder.query.filter_by(
                tenant_id=tenant_id,
                proxy_bill_id=proxy_bill_id,
                delivery_user_id=delivery_user.id,
                delivery_date=delivery_date,
            ).first()

        if existing:
            existing.delivery_address = delivery_address
            if salesman_user is not None:
                existing.salesman_id = salesman_user.id
            else:
                existing.salesman_id = None
            updated += 1
        else:
            delivery = DeliveryOrder(
                tenant_id=tenant_id,
                bill_id=bill_id,
                proxy_bill_id=proxy_bill_id,
                delivery_user_id=delivery_user.id,
                delivery_address=delivery_address,
                delivery_date=delivery_date,
                status="PENDING",
                salesman_id=salesman_user.id if salesman_user else None,
            )
            db.session.add(delivery)
            created += 1

    return {"created": created, "updated": updated, "skipped": skipped}
