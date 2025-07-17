import math

def calculate_old_regime(data):
    # Extract values, default to 0 if missing
    gross_salary = float(data.get('gross_salary', 0) or 0)
    basic_salary = float(data.get('basic_salary', 0) or 0)
    hra_received = float(data.get('hra_received', 0) or 0)
    rent_paid = float(data.get('rent_paid', 0) or 0)
    deduction_80c = float(data.get('deduction_80c', 0) or 0)
    deduction_80d = float(data.get('deduction_80d', 0) or 0)
    standard_deduction = float(data.get('standard_deduction', 50000) or 50000)
    professional_tax = float(data.get('professional_tax', 0) or 0)
    tds = float(data.get('tds', 0) or 0)

    # HRA Exemption (simplified):
    # Least of: (i) Actual HRA received, (ii) 50% of basic (metro) or 40% (non-metro), (iii) Rent paid - 10% of basic
    basic = basic_salary
    hra_exempt = min(
        hra_received,
        0.5 * basic,  # Assume metro for simplicity
        max(0, rent_paid - 0.1 * basic)
    )

    # Taxable income
    taxable_income = gross_salary - standard_deduction - hra_exempt - professional_tax - deduction_80c - deduction_80d
    taxable_income = max(0, taxable_income)

    # Old regime slabs (FY 2024-25)
    slabs = [
        (250000, 0.0),
        (250000, 0.05),
        (500000, 0.2),
        (math.inf, 0.3)
    ]
    tax = 0
    income_left = taxable_income
    for slab_amt, rate in slabs:
        if income_left > 0:
            amt = min(slab_amt, income_left)
            tax += amt * rate
            income_left -= amt
    # Rebate under 87A if taxable income <= 5L
    if taxable_income <= 500000:
        tax = 0
    # Add 4% cess
    tax = tax * 1.04
    return round(tax, 2)

def calculate_new_regime(data):
    gross_salary = float(data.get('gross_salary', 0) or 0)
    standard_deduction = float(data.get('standard_deduction', 50000) or 50000)
    tds = float(data.get('tds', 0) or 0)
    # Only standard deduction allowed
    taxable_income = gross_salary - standard_deduction
    taxable_income = max(0, taxable_income)
    # New regime slabs (FY 2024-25)
    slabs = [
        (300000, 0.0),
        (300000, 0.05),
        (300000, 0.1),
        (300000, 0.15),
        (300000, 0.2),
        (math.inf, 0.3)
    ]
    tax = 0
    income_left = taxable_income
    for slab_amt, rate in slabs:
        if income_left > 0:
            amt = min(slab_amt, income_left)
            tax += amt * rate
            income_left -= amt
    # Rebate under 87A if taxable income <= 7L
    if taxable_income <= 700000:
        tax = 0
    # Add 4% cess
    tax = tax * 1.04
    return round(tax, 2)

def compare_regimes(data):
    tax_old = calculate_old_regime(data)
    tax_new = calculate_new_regime(data)
    best = 'old' if tax_old < tax_new else 'new'
    return {
        'tax_old_regime': tax_old,
        'tax_new_regime': tax_new,
        'best_regime': best
    } 