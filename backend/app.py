from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.utils import secure_filename
import PyPDF2
import pytesseract
from PIL import Image
import io
import pdf2image
import google.generativeai as genai
import json
import re
from tax_calculator import compare_regimes
from datetime import datetime
import csv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

USER_FINANCIALS_CSV = 'user_financials.csv'
TAX_COMPARISON_CSV = 'tax_comparison.csv'

# In-memory session fallback for local testing
SESSION_FALLBACK = {}

ALLOWED_EXTENSIONS = {'pdf'}
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Helper to check allowed file
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Remove GEMINI_MODEL constant and debug prints

def structure_with_gemini(extracted_text):
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return None, 'Gemini API key not found.'
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = (
            """
            You are an expert at reading Indian salary slips and Form 16s. Given the following extracted text, return a JSON object with the following fields (use 0 or empty string if not found):
            - gross_salary
            - basic_salary
            - hra_received
            - rent_paid
            - deduction_80c
            - deduction_80d
            - standard_deduction
            - professional_tax
            - tds
            
            Only return a valid JSON object, no explanation or extra text.
            
            Extracted text:
            """
            + extracted_text
        )
        response = model.generate_content(prompt)
        import json
        import re
        match = re.search(r'\{[\s\S]*\}', response.text)
        if match:
            data = json.loads(match.group(0))
            return data, None
        else:
            return None, 'Gemini did not return valid JSON.'
    except Exception as e:
        return None, f'Gemini API error: {e}'

# PDF extraction logic (basic, can be improved)
def extract_pdf_data(pdf_path):
    print(f"[DEBUG] Starting extraction for: {pdf_path}")
    extracted_text = ""
    try:
        # Try text extraction with PyPDF2
        print("[DEBUG] Trying PyPDF2 extraction...")
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text() or ""
                extracted_text += page_text
        print(f"[DEBUG] PyPDF2 extracted {len(extracted_text)} characters.")
        # If text is empty, try OCR
        if not extracted_text.strip():
            print("[DEBUG] PyPDF2 found no text, trying OCR with pdf2image + pytesseract...")
            try:
                images = pdf2image.convert_from_path(pdf_path)
                for img in images:
                    ocr_text = pytesseract.image_to_string(img)
                    extracted_text += ocr_text
                print(f"[DEBUG] OCR extracted {len(extracted_text)} characters.")
            except Exception as ocr_e:
                print(f"[ERROR] OCR extraction failed: {ocr_e}")
    except Exception as e:
        print(f"[ERROR] PDF extraction failed: {e}")
        extracted_text = f"Error extracting PDF: {e}"
    if not extracted_text.strip():
        print("[WARNING] No text extracted from PDF!")
    # Use Gemini to structure data
    gemini_data, gemini_error = structure_with_gemini(extracted_text)
    is_salary_slip = False
    note = None
    if gemini_data:
        # Detect if it's a salary slip (not Form 16)
        if 'form 16' not in extracted_text.lower():
            is_salary_slip = True
            note = "Detected as salary slip. All values multiplied by 12 to estimate annual amounts. Please verify."
            # Multiply relevant fields by 12 if they are numbers
            for key in ['gross_salary', 'basic_salary', 'hra_received', 'rent_paid', 'deduction_80c', 'deduction_80d', 'professional_tax', 'tds']:
                try:
                    val = gemini_data.get(key, '')
                    if val is not None and str(val).strip() != '':
                        gemini_data[key] = str(round(float(val) * 12, 2))
                except Exception as mult_e:
                    print(f"[ERROR] Failed to multiply {key}: {mult_e}")
        gemini_data['raw_text'] = extracted_text[:1000]
        gemini_data['is_salary_slip'] = is_salary_slip
        gemini_data['note'] = note
        return gemini_data
    else:
        # Fallback: dummy parse
        print(f"[WARNING] Gemini structuring failed: {gemini_error}")
        return {
            'gross_salary': '',
            'basic_salary': '',
            'hra_received': '',
            'rent_paid': '',
            'deduction_80c': '',
            'deduction_80d': '',
            'standard_deduction': '50000',
            'professional_tax': '',
            'tds': '',
            'raw_text': extracted_text[:1000],
            'gemini_error': gemini_error,
            'is_salary_slip': False,
            'note': None
        }

def save_user_financials_csv(session_id, reviewed_data):
    fieldnames = [
        'session_id', 'gross_salary', 'basic_salary', 'hra_received', 'rent_paid',
        'deduction_80c', 'deduction_80d', 'standard_deduction', 'professional_tax', 'tds'
    ]
    row = {
        'session_id': session_id,
        'gross_salary': reviewed_data.get('gross_salary', 0) or 0,
        'basic_salary': reviewed_data.get('basic_salary', 0) or 0,
        'hra_received': reviewed_data.get('hra_received', 0) or 0,
        'rent_paid': reviewed_data.get('rent_paid', 0) or 0,
        'deduction_80c': reviewed_data.get('deduction_80c', 0) or 0,
        'deduction_80d': reviewed_data.get('deduction_80d', 0) or 0,
        'standard_deduction': reviewed_data.get('standard_deduction', 50000) or 50000,
        'professional_tax': reviewed_data.get('professional_tax', 0) or 0,
        'tds': reviewed_data.get('tds', 0) or 0
    }
    write_header = not os.path.exists(USER_FINANCIALS_CSV)
    with open(USER_FINANCIALS_CSV, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(row)

def save_tax_comparison_csv(session_id, comparison, selected_regime):
    fieldnames = [
        'session_id', 'tax_old_regime', 'tax_new_regime', 'best_regime', 'selected_regime'
    ]
    row = {
        'session_id': session_id,
        'tax_old_regime': comparison['tax_old_regime'],
        'tax_new_regime': comparison['tax_new_regime'],
        'best_regime': comparison['best_regime'],
        'selected_regime': selected_regime
    }
    write_header = not os.path.exists(TAX_COMPARISON_CSV)
    with open(TAX_COMPARISON_CSV, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(row)

def get_session_data_csv(session_id):
    user = None
    tax = None
    if os.path.exists(USER_FINANCIALS_CSV):
        with open(USER_FINANCIALS_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['session_id'] == session_id:
                    user = row
                    break
    if os.path.exists(TAX_COMPARISON_CSV):
        with open(TAX_COMPARISON_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['session_id'] == session_id:
                    tax = row
                    break
    if user and tax:
        return {'user': user, 'tax': tax}
    return None

def get_session_data(session_id):
    # Try CSV first, then fallback to in-memory
    data = get_session_data_csv(session_id)
    if data:
        return data
    # fallback
    data = SESSION_FALLBACK.get(session_id)
    if data:
        if 'selected_regime' not in data['tax'] and 'selected_regime' in data['user']:
            data['tax']['selected_regime'] = data['user']['selected_regime']
    return data

def log_ai_conversation(session_id, role, message):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": session_id,
        "role": role,
        "message": message
    }
    try:
        with open("ai_conversation_log.json", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Error logging AI conversation: {e}")

def parse_gemini_suggestions(suggestions):
    # Try to parse as numbered or bulleted list, or split by double newlines
    import re
    cards = []
    # Try Markdown numbered or bulleted list
    lines = suggestions.strip().splitlines()
    for line in lines:
        m = re.match(r"^(\d+\.|[-*•])\s*(.+?)(:|\-|—)\s*(.+)$", line)
        if m:
            title = m.group(2).strip()
            desc = m.group(4).strip()
            cards.append({"title": title, "desc": desc})
        else:
            # Try splitting by colon
            if ':' in line:
                title, desc = line.split(':', 1)
                cards.append({"title": title.strip(), "desc": desc.strip()})
            elif line.strip():
                cards.append({"title": '', "desc": line.strip()})
    # If nothing parsed, fallback to splitting by double newlines
    if not cards:
        for chunk in suggestions.split('\n\n'):
            if chunk.strip():
                cards.append({"title": '', "desc": chunk.strip()})
    return cards

@app.route('/')
def index():
    """Serve the landing page"""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "Tax Advisor Application is running"})

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            return render_template('form.html', error='No file part')
        file = request.files['pdf_file']
        if file.filename == '':
            return render_template('form.html', error='No selected file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            # Extract data
            extracted_data = extract_pdf_data(file_path)
            # Delete file after extraction
            os.remove(file_path)
            return render_template('form.html', extracted=extracted_data, error=None)
        else:
            return render_template('form.html', error='Invalid file type')
    return render_template('form.html', extracted=None, error=None)

@app.route('/review', methods=['POST'])
def review():
    # Get reviewed data from form
    reviewed_data = request.form.to_dict()
    # For now, just show the data back (Phase 3 will process it)
    return render_template('form.html', extracted=reviewed_data, error=None, reviewed=True)

@app.route('/calculate', methods=['POST'])
def calculate():
    reviewed_data = request.form.to_dict()
    session_id = str(uuid.uuid4())
    selected_regime = reviewed_data.get('selected_regime', 'new')
    comparison = compare_regimes(reviewed_data)
    # Save to CSVs
    save_user_financials_csv(session_id, reviewed_data)
    save_tax_comparison_csv(session_id, comparison, selected_regime)
    # Also update in-memory fallback for this session
    SESSION_FALLBACK[session_id] = {
        "user": reviewed_data,
        "tax": {
            "tax_old_regime": comparison['tax_old_regime'],
            "tax_new_regime": comparison['tax_new_regime'],
            "best_regime": comparison['best_regime'],
            "selected_regime": selected_regime
        }
    }
    return render_template(
        'results.html',
        session_id=session_id,
        reviewed=reviewed_data,
        comparison=comparison,
        selected_regime=selected_regime
    )

@app.route('/advisor', methods=['GET', 'POST'])
def advisor():
    session_id = request.args.get('session_id') or request.form.get('session_id')
    if not session_id:
        return "Session ID missing.", 400
    session_data = get_session_data(session_id)
    if not session_data or not session_data['user']:
        return "Session not found.", 404
    if request.method == 'GET':
        # Generate a smart follow-up question using Gemini
        user = session_data['user']
        tax = session_data['tax']
        prompt = (
            f"""
            You are a proactive, friendly Indian tax advisor. Based on the following user data and tax comparison, ask ONE smart, contextual follow-up question to help the user optimize their taxes or investments. Be concise and relevant.\n\nUser Data: {json.dumps(user)}\nTax Comparison: {json.dumps(tax)}\n\nOnly output the question, no extra text.
            """
        )
        api_key = os.getenv('GEMINI_API_KEY')
        question = ""
        if api_key:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                question = response.text.strip()
            except Exception as e:
                question = "(Could not generate question: " + str(e) + ")"
        else:
            question = "(Gemini API key missing)"
        log_ai_conversation(session_id, "ai", question)
        return render_template('ask.html', session_id=session_id, question=question, suggestions=None, suggestion_cards=None)
    else:
        # POST: user answered the question, get suggestions from Gemini
        user_answer = request.form.get('user_answer', '')
        log_ai_conversation(session_id, "user", user_answer)
        user = session_data['user']
        tax = session_data['tax']
        prompt = (
            f"""
            You are a top Indian tax advisor. Given the user's data, tax comparison, and their answer to your follow-up question, provide 3-5 personalized, actionable investment and tax-saving suggestions.\n\nUser Data: {json.dumps(user)}\nTax Comparison: {json.dumps(tax)}\nUser's Answer: {user_answer}\n\nRespond in a clear, modern, readable card format (use short titles and 1-2 line explanations for each suggestion).\n\nOnly output the suggestions, no extra text.
            """
        )
        api_key = os.getenv('GEMINI_API_KEY')
        suggestions = ""
        suggestion_cards = []
        if api_key:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                suggestions = response.text.strip()
                suggestion_cards = parse_gemini_suggestions(suggestions)
            except Exception as e:
                suggestions = "(Could not generate suggestions: " + str(e) + ")"
        else:
            suggestions = "(Gemini API key missing)"
        log_ai_conversation(session_id, "ai", suggestions)
        return render_template('ask.html', session_id=session_id, question=None, suggestions=suggestions, suggestion_cards=suggestion_cards)

@app.route('/advisor-info', methods=['GET'])
def advisor_info():
    return render_template('advisor_info.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 