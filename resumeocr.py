from doctr.io import DocumentFile
from doctr.models import ocr_predictor
import warnings
import re
from datetime import datetime

warnings.filterwarnings("ignore", category=UserWarning)

# Load the OCR model
model = ocr_predictor(pretrained=True)

# Load and process the PDF file
doc = DocumentFile.from_pdf("ExcelHRS.pdf")
result = model(doc)

# Extract text and confidence scores
all_text = []
confidence_scores = []

for page in result.pages:
    for block in page.blocks:
        for line in block.lines:
            line_text = " ".join(word.value for word in line.words)
            all_text.append(line_text)
            confidence_scores.extend(word.confidence for word in line.words)

# Join all text lines into a single paragraph
paragraph_text = " ".join(all_text)

# Define technical keywords and initialize experience dictionary
tech_keywords = ["React.js", "React Js", "Reactjs", "React framework", "JavaScript", "Redux", "TypeScript", "Next.js", "GraphQL", "CSS", "Bootstrap"]
experience = {key: 0 for key in tech_keywords}

# Find employment history section
employment_history_match = re.search(r"(EMPLOYMENT HISTORY)(.*?)(EDUCATION|SKILLS)", paragraph_text, re.DOTALL)
employment_history = employment_history_match.group(2) if employment_history_match else ""

# Comprehensive date pattern to capture a range of date formats
date_pattern = r"""
    (
        \b[A-Za-z]{3}\s\d{4}\b               |  # e.g., "Jan 2024"
        \b\d{1,2}\s[A-Za-z]{3,9}\s\d{4}\b    |  # e.g., "25 Jan 2024" or "25 January 2024"
        \b\d{4}-\d{2}-\d{2}\b                |  # e.g., "2024-01-25"
        \b\d{1,2}/\d{1,2}/\d{4}\b            |  # e.g., "01/25/2024" or "25/01/2024"
        \b\d{4}/\d{2}/\d{2}\b                  # e.g., "2024/01/25"
    )
"""

# Compile regex with VERBOSE flag for readability
date_regex = re.compile(date_pattern, re.VERBOSE)

# Split employment history into jobs based on job titles
jobs = re.split(r"(SOFTWARE DEVELOPER|FRONTEND DEVELOPER)", employment_history)

for job in jobs:
    # Find start and end dates
    dates = date_regex.findall(job)
    if len(dates) >= 2:
        try:
            # Try parsing using different possible date formats
            start_date = datetime.strptime(dates[0], "%b %Y")
            end_date = datetime.strptime(dates[1], "%b %Y")
            
            # Calculate the months difference excluding the start month
            months_diff = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) - 1

        except ValueError:
            # Handle different date formats if needed
            continue

        # Check for keywords in job description
        for keyword in tech_keywords:
            if keyword.lower() in job.lower():
                experience[keyword] += max(months_diff, 0)  # Only add positive experience

# Display extracted experience
print("Extracted Text:\n", paragraph_text)
print("\nExperience in months for each technical keyword:")
for tech, months in experience.items():
    print(f"{tech}: {months} months")

# Calculate and display overall confidence score
overall_confidence = (sum(confidence_scores) / len(confidence_scores) * 100) if confidence_scores else 0
print("\nOverall Confidence Score: {:.2f}%".format(overall_confidence))
