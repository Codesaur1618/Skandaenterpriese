"""
Migration script to add additional fields to vendors table for Excel import
Run this once to update the database schema
"""

from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app('development')

with app.app_context():
    try:
        # Check if columns already exist
        result = db.session.execute(text("PRAGMA table_info(vendors)"))
        columns = [row[1] for row in result]
        
        print("Checking for missing columns in vendors table...")
        print(f"Existing columns: {', '.join(columns)}\n")
        
        # List of new columns to add
        # Note: SQLite doesn't support UNIQUE constraint in ALTER TABLE ADD COLUMN
        # Uniqueness is handled in application logic
        new_columns = [
            ('customer_code', 'VARCHAR(100)'),
            ('billing_address', 'TEXT'),
            ('shipping_address', 'TEXT'),
            ('pincode', 'VARCHAR(20)'),
            ('city', 'VARCHAR(100)'),
            ('country', 'VARCHAR(100)'),
            ('state', 'VARCHAR(100)'),
            ('status', 'VARCHAR(20)'),
            ('block_status', 'VARCHAR(10)'),
            ('contact_person', 'VARCHAR(200)'),
            ('alternate_name', 'VARCHAR(200)'),
            ('alternate_mobile', 'VARCHAR(20)'),
            ('whatsapp_no', 'VARCHAR(20)'),
            ('pan', 'VARCHAR(50)'),
            ('additional_data', 'TEXT')
        ]
        
        for col_name, col_type in new_columns:
            if col_name not in columns:
                print(f"Adding {col_name} column...")
                db.session.execute(text(f"ALTER TABLE vendors ADD COLUMN {col_name} {col_type}"))
                db.session.commit()
                print(f"✓ Added {col_name} column")
            else:
                print(f"✓ {col_name} column already exists")
        
        print("\n" + "="*50)
        print("Migration completed successfully!")
        print("="*50)
        print("\nAll vendor fields have been added to the vendors table.")
        print("You can now use Excel import functionality to bulk import vendors.")
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        db.session.rollback()
        raise

