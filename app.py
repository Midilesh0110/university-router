from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from email.message import EmailMessage
import smtplib
from pymongo import MongoClient
import os

app = Flask(__name__)
CORS(app)

# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------
SENDER_EMAIL = "nihalvarma4687@gmail.com"
APP_PASSWORD = "OOd5ibqJJvGjtk0U" # Replace with your 16-letter App Password

# MongoDB Connection
MONGO_URI = "mongodb+srv://midilesh0330_db_user:O0d5ibqJJvgjtk0U@cluster0.fulm0s5.mongodb.net/?appName=Cluster0&tlsAllowInvalidCertificates=true"
try:
    client = MongoClient(MONGO_URI)
    db = client['university_system']
    requests_collection = db['student_requests']
    print("MongoDB Connected Successfully!")
except Exception as e:
    print(f"MongoDB Connection Error: {e}")

# -------------------------------------------------
# TRAIN MODEL
# -------------------------------------------------
print("Training AI Model...")
requests_data = [
    "leave permission","medical leave","attendance shortage","bonafide certificate",
    "study certificate","transfer certificate","migration certificate",
    "course completion certificate","internship permission letter",
    "project approval academic","elective subject change",
    "semester registration issue","section change request",
    "academic calendar clarification","id card issue",
    "tuition fee payment issue","fee receipt not generated","refund request",
    "caution deposit refund","excess fee paid","fine payment issue",
    "payment gateway failure","fee structure clarification",
    "installment request","scholarship adjustment in fees",
    "hall ticket not generated","wrong subject in hall ticket","exam fee issue",
    "revaluation request","photocopy of answer script",
    "supplementary exam registration","improvement exam",
    "internal marks correction","grade card correction",
    "backlog registration issue",
    "scholarship not credited","nsp portal issue","minority scholarship",
    "post matric scholarship","upload document correction",
    "income certificate issue","bank account update",
    "aadhaar mismatch","scholarship renewal problem",
    "room allocation issue","room change request","water problem hostel",
    "electricity issue hostel","wifi issue hostel",
    "mess quality complaint","mess fee payment issue",
    "furniture damage","cleaning issue hostel",
    "security complaint hostel","gate pass permission",
    "project topic approval","internship approval","lab permission",
    "attendance condonation","faculty complaint",
    "internal marks discussion","subject doubt clarification",
    "research paper submission","recommendation letter",
    "department event permission",
    "serious grievance","faculty misconduct","harassment complaint",
    "policy complaint","disciplinary issue",
    "appeal against suspension","overall college complaint",
    "placement registration issue","resume submission","internship opportunity",
    "company drive details","offer letter issue",
    "training program enrollment","aptitude training request",
    "mock interview request","noc for internship",
    "sports certificate","tournament participation",
    "sports equipment issue","ground booking",
    "sports quota certificate","attendance for sports",
    "sports scholarship",
    "library fine issue","book not available","lost book",
    "library id issue","digital library access","thesis submission",
    "bus pass issue","route change transport","bus timing issue",
    "transport fee payment","new transport request",
    "erp login issue","portal password reset",
    "wifi campus issue","email id problem","software lab issue",
    "ragging complaint","discrimination complaint",
    "academic bias complaint"
]

departments_labels = [
    "Academic","Academic","Academic","Academic","Academic","Academic",
    "Academic","Academic","Academic","Academic","Academic","Academic",
    "Academic","Academic","Academic",
    "Accounts","Accounts","Accounts","Accounts","Accounts",
    "Accounts","Accounts","Accounts","Accounts","Accounts",
    "Examination","Examination","Examination","Examination",
    "Examination","Examination","Examination","Examination",
    "Examination","Examination",
    "Scholarship","Scholarship","Scholarship","Scholarship",
    "Scholarship","Scholarship","Scholarship","Scholarship","Scholarship",
    "Hostel","Hostel","Hostel","Hostel","Hostel",
    "Hostel","Hostel","Hostel","Hostel","Hostel","Hostel",
    "HOD","HOD","HOD","HOD","HOD",
    "HOD","HOD","HOD","HOD","HOD",
    "Principal","Principal","Principal","Principal",
    "Principal","Principal","Principal",
    "TPO","TPO","TPO","TPO","TPO",
    "TPO","TPO","TPO","TPO",
    "Sports","Sports","Sports","Sports",
    "Sports","Sports","Sports",
    "Library","Library","Library","Library","Library","Library",
    "Transport","Transport","Transport","Transport","Transport",
    "IT","IT","IT","IT","IT",
    "Grievance","Grievance","Grievance"
]

vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1,2))
X = vectorizer.fit_transform(requests_data)
model = MultinomialNB()
model.fit(X, departments_labels)
print("Model Trained Successfully.")

def send_email_func(to_email, subject, body):
    try:
        msg = EmailMessage()
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False

# -------------------------------------------------
# WEB ROUTES
# -------------------------------------------------

@app.route('/')
def home():
    # Serves your HTML frontend
    return render_template('index.html')

@app.route('/submit_request', methods=['POST'])
def submit_request():
    data = request.json
    
    r_name = data.get('name')
    r_id = data.get('studentId')
    r_email = data.get('email')
    r_dept = data.get('department')
    r_year = data.get('classYear')
    r_desc = data.get('description')

    if not r_desc:
        return jsonify({"status": "error", "message": "Description required"}), 400

    # Predict Department
    vector = vectorizer.transform([r_desc.lower()])
    probabilities = model.predict_proba(vector)[0]
    
    threshold = 0.15
    matched_departments = [model.classes_[i] for i, prob in enumerate(probabilities) if prob > threshold]
    
    if not matched_departments:
        matched_departments = [model.predict(vector)[0]]

    primary_dept = matched_departments[0]

    # Save to MongoDB
    db_record = {
        "name": r_name,
        "student_id": r_id,
        "email": r_email,
        "department": r_dept,
        "class_year": r_year,
        "description": r_desc,
        "assigned_to": primary_dept
    }
    try:
        requests_collection.insert_one(db_record)
        print("Record saved to MongoDB!")
    except Exception as e:
        print(f"Failed to save to MongoDB: {e}")

    # Send Email to Student
    student_body = f"Dear {r_name},\n\nYour request '{r_desc}' has been successfully received.\nIt has been routed to the {primary_dept} department.\n\nReference ID: {r_id}"
    send_email_func(r_email, "Request Received - University System", student_body)

    return jsonify({
        "status": "success", 
        "routed_to": matched_departments
    })

# Render uses Gunicorn in production, but this is for local testing
if __name__ == '__main__':

    app.run(debug=True, port=5000)
