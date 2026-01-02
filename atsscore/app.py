from flask import Flask, request, jsonify, render_template
import PyPDF2
import re

app = Flask(__name__)

# ----------------------------
# ATS CONFIG
# ----------------------------
POWER_WORDS = [
    "achieved", "managed", "developed", "led", "created", "improved",
    "implemented", "optimized", "designed", "engineered", "collaborated"
]

STANDARD_KEYWORDS = [
    "communication", "leadership", "teamwork", "project",
    "management", "analysis", "development", "problem solving"
]

SECTIONS = ["experience", "education", "skills", "projects", "summary"]

# ----------------------------
# ROUTES
# ----------------------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze_resume():
    data = request.json
    resume_text = data.get("resume_text", "").lower()

    if not resume_text:
        return jsonify({"error": "Resume text is required"}), 400

    # --- Keyword Match ---
    matched = [kw for kw in STANDARD_KEYWORDS if kw in resume_text]
    missing = [kw for kw in STANDARD_KEYWORDS if kw not in resume_text]

    keyword_score = min(int((len(matched) / len(STANDARD_KEYWORDS)) * 100), 100)

    # --- Formatting Score ---
    format_score = 10
    issues = []

    if not re.search(r"@", resume_text):
        format_score -= 2
        issues.append("Missing email")

    if not re.search(r"\d{10}", resume_text):
        format_score -= 2
        issues.append("Missing phone number")

    section_count = sum(1 for s in SECTIONS if s in resume_text)
    if section_count < 3:
        format_score -= 2
        issues.append("Missing standard sections")

    word_count = len(resume_text.split())
    if word_count < 150:
        format_score -= 2
        issues.append("Resume too short")

    if format_score < 0:
        format_score = 0

    # --- Power Words ---
    power_count = sum(1 for pw in POWER_WORDS if pw in resume_text)
    power_score = min(power_count * 10, 100)

    # --- Final Score ---
    total_score = int(
        (keyword_score * 0.4) +
        (format_score * 10 * 0.4) +
        (power_score * 0.2)
    )

    verdict = (
        "Poor" if total_score <= 40 else
        "Average" if total_score <= 70 else
        "Good"
    )

    return jsonify({
        "total_score": total_score,
        "verdict": verdict,
        "keyword_score": keyword_score,
        "format_score": format_score,
        "power_word_score": power_score,
        "missing_keywords": missing,
        "format_issues": issues
    })

@app.route("/upload-pdf", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    reader = PyPDF2.PdfReader(file)

    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted

    return jsonify({"text": text})

# ----------------------------
# RUN APP
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)
