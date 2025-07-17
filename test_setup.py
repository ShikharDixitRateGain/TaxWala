#!/usr/bin/env python3
"""
Test script to verify Phase 1 setup
"""

import os
import sys

def test_file_structure():
    """Test that all required files and directories exist"""
    print("🔍 Testing Phase 1 file structure...")
    
    required_files = [
        'app.py',
        'requirements.txt',
        'supabase_db_create.py',
        'env_example.txt',
        'README.md'
    ]
    
    required_dirs = [
        'templates',
        'uploads'
    ]
    
    required_templates = [
        'templates/index.html'
    ]
    
    all_good = True
    
    # Check main files
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            all_good = False
    
    # Check directories
    for dir in required_dirs:
        if os.path.isdir(dir):
            print(f"✅ {dir}/ directory exists")
        else:
            print(f"❌ {dir}/ directory missing")
            all_good = False
    
    # Check template files
    for template in required_templates:
        if os.path.exists(template):
            print(f"✅ {template} exists")
        else:
            print(f"❌ {template} missing")
            all_good = False
    
    return all_good

def test_app_structure():
    """Test the Flask app structure"""
    print("\n🔍 Testing Flask app structure...")
    
    try:
        with open('app.py', 'r') as f:
            content = f.read()
            
        required_imports = [
            'from flask import Flask',
            'import os',
            'from dotenv import load_dotenv',
            'import psycopg2'
        ]
        
        required_routes = [
            '@app.route(\'/\')',
            'def index():',
            'return render_template(\'index.html\')'
        ]
        
        all_good = True
        
        for import_line in required_imports:
            if import_line in content:
                print(f"✅ Import found: {import_line}")
            else:
                print(f"❌ Import missing: {import_line}")
                all_good = False
        
        for route in required_routes:
            if route in content:
                print(f"✅ Route found: {route}")
            else:
                print(f"❌ Route missing: {route}")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"❌ Error reading app.py: {e}")
        return False

def test_database_schema():
    """Test the database schema script"""
    print("\n🔍 Testing database schema...")
    
    try:
        with open('supabase_db_create.py', 'r') as f:
            content = f.read()
            
        required_elements = [
            'UserFinancials',
            'TaxComparison',
            'session_id UUID PRIMARY KEY',
            'gross_salary NUMERIC(15, 2)',
            'tax_old_regime NUMERIC(15, 2)',
            'tax_new_regime NUMERIC(15, 2)'
        ]
        
        all_good = True
        
        for element in required_elements:
            if element in content:
                print(f"✅ Schema element found: {element}")
            else:
                print(f"❌ Schema element missing: {element}")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"❌ Error reading supabase_db_create.py: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Tax Advisor Application - Phase 1 Setup Test\n")
    
    file_structure_ok = test_file_structure()
    app_structure_ok = test_app_structure()
    db_schema_ok = test_database_schema()
    
    print("\n" + "="*50)
    print("📊 TEST RESULTS SUMMARY")
    print("="*50)
    
    if file_structure_ok and app_structure_ok and db_schema_ok:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Phase 1 setup is complete and ready")
        print("\n📝 Next steps:")
        print("1. Create virtual environment: python -m venv venv")
        print("2. Activate venv: venv\\Scripts\\activate (Windows)")
        print("3. Install dependencies: pip install -r requirements.txt")
        print("4. Copy env_example.txt to .env and add your credentials")
        print("5. Run database setup: python supabase_db_create.py")
        print("6. Start app: python app.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 