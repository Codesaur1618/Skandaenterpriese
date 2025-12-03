"""
Migration script to add authorization columns to bills table
Run this once to update the database schema
"""

from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app('development')

with app.app_context():
    try:
        # Check if columns already exist
        result = db.session.execute(text("PRAGMA table_info(bills)"))
        columns = [row[1] for row in result]
        
        if 'is_authorized' not in columns:
            print("Adding is_authorized column...")
            db.session.execute(text("ALTER TABLE bills ADD COLUMN is_authorized BOOLEAN DEFAULT 0"))
            db.session.commit()
            print("✓ Added is_authorized column")
        else:
            print("✓ is_authorized column already exists")
        
        if 'authorized_by' not in columns:
            print("Adding authorized_by column...")
            db.session.execute(text("ALTER TABLE bills ADD COLUMN authorized_by INTEGER"))
            db.session.commit()
            print("✓ Added authorized_by column")
        else:
            print("✓ authorized_by column already exists")
        
        if 'authorized_at' not in columns:
            print("Adding authorized_at column...")
            db.session.execute(text("ALTER TABLE bills ADD COLUMN authorized_at DATETIME"))
            db.session.commit()
            print("✓ Added authorized_at column")
        else:
            print("✓ authorized_at column already exists")
        
        # Add foreign key constraint if it doesn't exist
        # SQLite doesn't support adding foreign keys after table creation easily,
        # but the relationship will work through SQLAlchemy
        
        print("\n" + "="*50)
        print("Migration completed successfully!")
        print("="*50)
        
    except Exception as e:
        print(f"Error during migration: {e}")
        db.session.rollback()
        raise

