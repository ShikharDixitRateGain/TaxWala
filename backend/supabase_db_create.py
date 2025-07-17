import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_database_schema():
    """Create the database schema for the Tax Advisor Application"""
    
    # Get database connection
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(os.getenv('DB_URL'))
        cursor = conn.cursor()
        
        # Create UserFinancials table
        create_user_financials_table = """
        CREATE TABLE IF NOT EXISTS UserFinancials (
            session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            gross_salary NUMERIC(15, 2) NOT NULL,
            basic_salary NUMERIC(15, 2) NOT NULL,
            hra_received NUMERIC(15, 2) DEFAULT 0,
            rent_paid NUMERIC(15, 2) DEFAULT 0,
            deduction_80c NUMERIC(15, 2) DEFAULT 0,
            deduction_80d NUMERIC(15, 2) DEFAULT 0,
            standard_deduction NUMERIC(15, 2) DEFAULT 50000,
            professional_tax NUMERIC(15, 2) DEFAULT 0,
            tds NUMERIC(15, 2) DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Create TaxComparison table
        create_tax_comparison_table = """
        CREATE TABLE IF NOT EXISTS TaxComparison (
            session_id UUID PRIMARY KEY REFERENCES UserFinancials(session_id) ON DELETE CASCADE,
            tax_old_regime NUMERIC(15, 2) NOT NULL,
            tax_new_regime NUMERIC(15, 2) NOT NULL,
            best_regime VARCHAR(10) NOT NULL CHECK (best_regime IN ('old', 'new')),
            selected_regime VARCHAR(10) NOT NULL CHECK (selected_regime IN ('old', 'new')),
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Execute the table creation queries
        cursor.execute(create_user_financials_table)
        cursor.execute(create_tax_comparison_table)
        
        # Commit the changes
        conn.commit()
        
        print("✅ Database schema created successfully!")
        print("✅ UserFinancials table exists")
        print("✅ TaxComparison table exists")
        
    except Exception as e:
        print(f"❌ Error creating database schema: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    create_database_schema() 