# Skanda Credit & Billing System

A simple, low-cost monolithic web application for managing vendors, bills, proxy bills, credits, deliveries, and reports for a wholesaler.

## Features

- **Vendor Management**: Create and manage vendors (suppliers/customers)
- **Bill Management**: Create bills with line items, track status (DRAFT/CONFIRMED/CANCELLED)
- **Proxy Bills**: Split bills into proxy bills for end customers
- **Credit Management**: Track incoming and outgoing payments
- **Delivery Orders**: Manage delivery orders with status tracking
- **OCR Integration**: Optional OCR for bill images using EasyOCR
- **Reports**: Outstanding amounts, collection reports, and delivery statistics
- **Role-Based Access**: ADMIN, SALESMAN, DELIVERY, ORGANISER roles
- **Mobile-Friendly**: Responsive design that works on phone browsers

## Technology Stack

- **Backend**: Python Flask
- **Templates**: Jinja2 with HTML + CSS + JavaScript
- **Styling**: Bootstrap 5 (via CDN)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Flask-Login with session-based auth
- **Forms**: Flask-WTF
- **OCR**: EasyOCR (optional)

## Setup Instructions

### 1. Create Virtual Environment

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: EasyOCR installation may take some time as it downloads model files on first use. If you don't need OCR functionality, you can skip installing EasyOCR and the app will work without it (showing a message that OCR is not installed).

### 3. Initialize Database

Run the seed script to create the database and default data:

```bash
python seed.py
```

This will:
- Create all database tables
- Create default tenant: "Skanda Enterprises" (code: "skanda")
- Create admin user with credentials:
  - Username: `admin`
  - Password: `admin123`

### 4. Run the Application

```bash
python app.py
```

The application will start on `http://127.0.0.1:5000`

### 5. Login

Navigate to `http://127.0.0.1:5000/login` and use:
- **Username**: `admin`
- **Password**: `admin123`

## Project Structure

```
skanda_app/
├── app.py                 # Flask app entry point
├── config.py              # Configuration classes
├── extensions.py          # Database and login manager
├── models.py              # SQLAlchemy models
├── forms.py               # Flask-WTF forms
├── auth_routes.py         # Authentication routes
├── main_routes.py         # Dashboard routes
├── vendor_routes.py       # Vendor CRUD routes
├── bill_routes.py         # Bill routes
├── proxy_routes.py        # Proxy bill routes
├── credit_routes.py       # Credit entry routes
├── delivery_routes.py     # Delivery routes
├── ocr_routes.py          # OCR upload/view routes
├── report_routes.py       # Report routes
├── audit.py               # Audit logging helper
├── ocr_utils.py           # OCR utility functions
├── seed.py                # Database seeding script
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── static/
│   ├── css/
│   │   └── style.css     # Custom CSS
│   ├── js/
│   │   └── main.js       # Custom JavaScript
│   └── uploads/
│       └── bills/        # Uploaded bill images
└── templates/
    ├── base.html         # Base template
    ├── layout/           # Layout components
    ├── auth/             # Login templates
    ├── vendors/          # Vendor templates
    ├── bills/            # Bill templates
    ├── proxy_bills/      # Proxy bill templates
    ├── credits/          # Credit templates
    ├── deliveries/       # Delivery templates
    ├── ocr/              # OCR templates
    └── reports/          # Report templates
```

## Usage

### Creating a Bill

1. Navigate to **Bills** → **New Bill**
2. Select a vendor, enter bill number and date
3. Add line items (description, quantity, unit price)
4. Amounts are auto-calculated
5. Save the bill (status: DRAFT)
6. From the bill detail page, you can:
   - Confirm the bill
   - Create a proxy bill
   - Add credit payments
   - Upload OCR image

### Creating a Proxy Bill

1. Navigate to **Proxy Bills** → **New Proxy Bill**
2. Select parent bill and end customer vendor
3. Add items for the proxy bill
4. Save and confirm

### Adding Credit Entries

1. Navigate to **Credits** → **New Credit Entry**
2. Or click "Add Credit Payment" from a bill/proxy bill detail page
3. Enter payment details (amount, direction, method, date)
4. Link to bill or proxy bill (optional)

### Managing Deliveries

1. Navigate to **Deliveries** → **New Delivery Order**
2. Select bill/proxy bill, delivery user, address, and date
3. Update status from the delivery detail page

### OCR Processing

1. Navigate to **OCR** → **Upload**
2. Select a bill and upload an image (JPG, PNG, or PDF)
3. The system will extract text (if EasyOCR is installed)
4. View extracted text on the OCR view page

### Reports

- **Outstanding Report**: Shows outstanding amounts per vendor
- **Collection Report**: Shows incoming/outgoing payments for a date range
- **Deliveries Report**: Shows delivery statistics by status

## Default Credentials

- **Username**: `admin`
- **Password**: `admin123`

**Important**: Change the default password after first login in a production environment.

## Notes

- The application uses a single tenant ("skanda") by default
- All file uploads are stored in `static/uploads/bills/`
- The database file (`skanda.db`) is created in the project root
- OCR functionality requires EasyOCR to be installed. The app will work without it but will show a message that OCR is not available.

## Development

To run in development mode:

```bash
python app.py
```

The app runs with debug mode enabled by default. For production, modify `config.py` to use `ProductionConfig`.

## License

This is a private application for internal use.

