from flask import Flask, render_template, request, redirect, url_for
import os
import re
import pandas as pd
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

# Preload OCR Predictor (Global Initialization for Performance)
ocr_model = ocr_predictor(pretrained=True)

# Allowed File Check
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Extract Text from Resume
def extract_text_from_resume(filepath):
    document = DocumentFile.from_pdf(filepath)
    result = ocr_model(document)
    return "\n".join([page.get_text() for page in result.pages])

# Validate Date Format (MM YYYY)
def validate_date_format(text):
    dates = re.findall(r"\b\d{1,2}/\d{4}|\b\d{4}", text)
    valid_format = all(re.match(r"^\d{2}/\d{4}$", date) for date in dates)
    return valid_format

# Extract Candidate Name, Contact Info, and Sections
def extract_details(text):
    name = re.search(r"Name[:\s]+([A-Za-z\s]+)", text)
    contact = re.search(r"\b\d{10}\b", text)
    email = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    linkedin = re.search(r"linkedin\.com/\w+", text)

    name = name.group(1).strip() if name else "Unknown"
    contact = contact.group() if contact else "Not Found"
    email = email.group() if email else "Not Found"
    linkedin = linkedin.group() if linkedin else "Not Found"

    # Extracting Relevant Sections
    sections = {section: section in text.lower() for section in [
        "professional summary", "employment history", "education",
        "skills", "languages", "certifications", "work history", "projects"
    ]}
    return name, contact, email, linkedin, sections

# Analyze Resume
def analyze_resume(text, job_description, experience_required):
    # Extract Job Description Keywords
    job_skills = job_description.lower().split()
    resume_skills = re.findall(r"\b\w+\b", text.lower())

    # Match Skills
    matched_skills = set(job_skills) & set(resume_skills)
    skill_match_percentage = (len(matched_skills) / len(job_skills)) * 100

    # ATS Compliance Score
    required_sections = [
        "professional summary", "employment history", "education",
        "skills", "certifications", "work history"
    ]
    ats_score = sum(1 for section in required_sections if section in text.lower()) / len(required_sections) * 100

    # Shortlisting Criteria
    result = "Shortlisted" if skill_match_percentage >= 70 and ats_score >= 70 else "Not Shortlisted"
    return matched_skills, skill_match_percentage, ats_score, result

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get('resume')
        experience_required = request.form.get('experience')
        job_description = request.form.get('job_description')

        if file and allowed_file(file.filename) and experience_required:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)

            # Process Resume
            text = extract_text_from_resume(filepath)
            name, contact, email, linkedin, sections = extract_details(text)
            is_valid_date = validate_date_format(text)

            matched_skills, skill_match, ats_score, result = analyze_resume(
                text, job_description, experience_required
            )

            # Display Results
            results = {
                "Candidate Name": name,
                "Contact": contact,
                "Email": email,
                "LinkedIn": linkedin,
                "Core Skills": ", ".join(matched_skills),
                "Skill Match (%)": skill_match,
                "ATS Score (%)": ats_score,
                "Date Format Valid": "Yes" if is_valid_date else "No",
                "Result": result
            }
            return render_template("index.html", results=[results])

    return render_template("index.html", results=[])

if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
