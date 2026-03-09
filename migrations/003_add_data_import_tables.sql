-- Data import tables for Outstanding Outlets and Beat Master CSVs

CREATE TABLE IF NOT EXISTS outstanding_outlets (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    customer_code VARCHAR(100),
    customer_name VARCHAR(255) NOT NULL,
    channel_type VARCHAR(100),
    outlet_type VARCHAR(100),
    loyalty_program VARCHAR(100),
    credit_term VARCHAR(100),
    salesman_name VARCHAR(200),
    beat VARCHAR(200),
    salesman_type VARCHAR(100),
    document_type VARCHAR(100),
    document_no VARCHAR(100),
    document_date DATE,
    amount NUMERIC(12, 2) DEFAULT 0.00,
    balance NUMERIC(12, 2) DEFAULT 0.00,
    due_days INTEGER,
    over_due_days INTEGER,
    invoice_status VARCHAR(50),
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS beat_master_entries (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    ds_code VARCHAR(50),
    ds_name VARCHAR(200),
    ds_type VARCHAR(150),
    ds_status VARCHAR(50),
    beat_code VARCHAR(100),
    beat_name VARCHAR(200),
    beat_end_date DATE,
    customer_code VARCHAR(100),
    customer_name VARCHAR(255),
    customer_status VARCHAR(50),
    frequency VARCHAR(50),
    beat_modified_at TIMESTAMP,
    max_beat_count INTEGER,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_outstanding_outlets_tenant_id ON outstanding_outlets(tenant_id);
CREATE INDEX IF NOT EXISTS idx_outstanding_outlets_customer_code ON outstanding_outlets(customer_code);
CREATE INDEX IF NOT EXISTS idx_outstanding_outlets_salesman_name ON outstanding_outlets(salesman_name);
CREATE INDEX IF NOT EXISTS idx_outstanding_outlets_beat ON outstanding_outlets(beat);
CREATE INDEX IF NOT EXISTS idx_outstanding_outlets_document_no ON outstanding_outlets(document_no);

CREATE INDEX IF NOT EXISTS idx_beat_master_entries_tenant_id ON beat_master_entries(tenant_id);
CREATE INDEX IF NOT EXISTS idx_beat_master_entries_ds_code ON beat_master_entries(ds_code);
CREATE INDEX IF NOT EXISTS idx_beat_master_entries_beat_code ON beat_master_entries(beat_code);
CREATE INDEX IF NOT EXISTS idx_beat_master_entries_customer_code ON beat_master_entries(customer_code);

