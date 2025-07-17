# Tax Advisor Application - Phase 1

## Overview
A web-based platform for salaried individuals to analyze tax liabilities and receive personalized, AI-powered tax-saving strategies.

## Phase 1 Features
- ✅ Modern landing page with responsive design
- ✅ Database schema setup (UserFinancials and TaxComparison tables)
- ✅ Basic Flask application structure
- ✅ Environment variable configuration

## Setup Instructions

### 1. Environment Setup
1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 2. Database Setup
1. Set up your Supabase PostgreSQL database
2. Copy `env_example.txt` to `.env`
3. Update `.env` with your actual credentials:
   ```env
   GEMINI_API_KEY = "your-actual-gemini-api-key"
   DB_URL = "postgresql://postgres:your-password@your-host:5432/postgres"
   ```

4. Run the database setup script:
   ```bash
   python supabase_db_create.py
   ```

### 3. Run the Application
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Project Structure
```
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── supabase_db_create.py  # Database schema setup
├── env_example.txt        # Environment variables template
├── README.md             # This file
├── templates/
│   └── index.html        # Landing page
└── uploads/              # File upload directory
```

## Database Schema
- **UserFinancials**: Stores user financial data with UUID session IDs
- **TaxComparison**: Stores tax calculation results and regime comparisons

## Next Steps (Phase 2)
- PDF upload and data extraction
- Manual data review form
- Tax calculation engine

## Technologies Used
- Flask (Python web framework)
- PostgreSQL (Supabase)
- HTML/CSS/JavaScript (Frontend)
- Aptos Display font
- Google Gemini AI (for future phases) 