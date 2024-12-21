import re
from datetime import datetime
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
import json
import os

# Load ATS rules
def load_ats_rules():
    with open("ats_rules.json", "r") as f:
        return json.load(f)

# Load OCR Model
model = ocr_predictor(pretrained=True)

# Extract text from PDF
def extract_text_from_pdf(pdf_path):
    doc = DocumentFile.from_pdf(pdf_path)
    result = model(doc)
    
    all_text = []
    for page in result.pages:
        for block in page.blocks:
            for line in block.lines:
                all_text.append(" ".join(word.value for word in line.words))
    return " ".join(all_text)

def extract_dates(text):
    date_patterns = [
        r"\b\d{1,2}/\d{1,2}/\d{4}\b",  # DD/MM/YYYY
        r"\b\d{4}-\d{2}-\d{2}\b",      # YYYY-MM-DD
        r"\b\d{4}/\d{2}\b",            # YYYY/MM
        r"\b[A-Za-z]{3}\s?\d{4}\b"     # Month YYYY
    ]
    dates = []
    for pattern in date_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                dates.append(parse_date(match))
            except ValueError:
                continue
    return dates

def parse_date(date_str):
    date_formats = [
        "%d/%m/%Y",  # DD/MM/YYYY
        "%Y-%m-%d",  # YYYY-MM-DD
        "%Y/%m",     # YYYY/MM
        "%b %Y"      # Month Year
    ]
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unknown date format: {date_str}")


# Match keywords
def match_keywords(text, keywords):
    matched = {}
    for keyword in keywords:
        count = text.lower().count(keyword.lower())
        if count > 0:
            matched[keyword] = count
    return matched

# Calculate experience
def calculate_experience(employment_text, keywords):
    experience = {keyword: 0 for keyword in keywords}
    dates = extract_dates(employment_text)
    if len(dates) >= 2:
        for i in range(0, len(dates) - 1, 2):
            start, end = dates[i], dates[i + 1]
            duration_months = (end.year - start.year) * 12 + end.month - start.month
            for keyword in keywords:
                if keyword in employment_text.lower():
                    experience[keyword] += duration_months
    return experience

# Check ATS compliance
def check_ats_compliance(text, ats_rules):
    """
    Evaluate the resume text against ATS compliance rules.
    
    Args:
        text (str): Extracted text from the resume.
        ats_rules (dict): Dictionary containing ATS compliance rules.
    
    Returns:
        float: ATS compliance score as a percentage.
    """
    score = 0
    total_criteria = 0

    # Check for mandatory labels (e.g., name, email, phone, LinkedIn)
    required_labels = ats_rules.get("required_labels", [])
    for label in required_labels:
        total_criteria += 1
        if label.lower() in text.lower():
            score += 1

    # Check for mandatory sections
    mandatory_sections = ats_rules.get("mandatory_sections", [])
    for section in mandatory_sections:
        total_criteria += 1
        if section.lower() in text.lower():
            score += 1

    # Check for accepted date formats
    date_pattern = ats_rules.get("date_pattern", r"\b(0[1-9]|1[0-2])\s?\d{4}\b")  # Default MM YYYY
    if re.search(date_pattern, text):
        total_criteria += 1
        score += 1

    # Calculate ATS compliance score as a percentage
    ats_score = (score / total_criteria) * 100 if total_criteria > 0 else 0
    return ats_score
