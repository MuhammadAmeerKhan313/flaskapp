import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import numpy as np
from fpdf import FPDF  # For generating PDF reports
from config import get_db
from functools import wraps
from model import predict_performance

# ---------------------------
# Flask App Initialization
# ---------------------------
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')

# ---------------------------
# Database Connection
# ---------------------------
db = get_db()  # Make sure get_db() is properly defined in config.py

# ---------------------------
# Login Required Decorator
# ---------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# ---------------------------
# Routes
# ---------------------------
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/prediction')
def prediction():
    return render_template('prediction.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/documentation')
def documentation():
    return render_template('documentation.html')

# ---------------------------
# User Registration
# ---------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = db.users
        username = request.form['username']
        existing_user = users.find_one({"username": username})
        if existing_user is None:
            hashed_password = generate_password_hash(request.form['password'])
            user = {
                "username": username,
                "email": request.form['email'],
                "password": hashed_password
            }
            users.insert_one(user)
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username already exists!', 'danger')
    return render_template('register.html')

# ---------------------------
# User Login
# ---------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = db.users
        username = request.form.get('username')
        password = request.form.get('password')
        if username and password:
            user = users.find_one({"username": username})
            if user and check_password_hash(user['password'], password):
                session['username'] = username
                session['email'] = user['email']
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid credentials, please try again.', 'danger')
    return render_template('login.html')

# ---------------------------
# User Logout
# ---------------------------
@app.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    session.pop('email', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ---------------------------
# Prediction Route
# ---------------------------
@app.route('/predict', methods=['POST'])
@login_required
def predict():
    try:
        name = request.form['name']
        student_id = request.form['student_id']
        email = request.form['email']
        attendance = float(request.form['attendance'])
        homework_completion = float(request.form['homework_completion'])
        test_scores = float(request.form['test_scores'])

        percentage = (test_scores * 0.5) + (attendance * 0.3) + (homework_completion * 0.2)
        prediction = 1 if percentage > 60 else 0
        probability = round(percentage, 2)

        student_data = {
            'name': name,
            'student_id': student_id,
            'email': email,
            'attendance': attendance,
            'homework_completion': homework_completion,
            'test_scores': test_scores,
            'prediction': prediction,
            'probability': probability,
        }
        session['student_data'] = student_data

        prediction_message = "Good Result! The student is likely to perform well." if prediction == 1 else "Bad Result! The student may not succeed based on current indicators."

        return render_template('result.html', prediction=prediction, probability=probability, prediction_message=prediction_message, student=student_data)
    
    except Exception as e:
        flash(f"Error during prediction: {e}", 'danger')
        return redirect(url_for('index'))

# ---------------------------
# PDF Report Generation
# ---------------------------
@app.route('/report/<student_id>', methods=['GET'])
@login_required
def report(student_id):
    student = session.get('student_data')
    if student and student['student_id'] == student_id:
        try:
            prediction_text = 'Good Student' if student['prediction'] == 1 else 'Needs Improvement'
            probability = student['probability']
            percentage = round((student['test_scores'] * 0.5) + (student['attendance'] * 0.3) + (student['homework_completion'] * 0.2), 2)

            pdf = FPDF()
            pdf.add_page()

            # Background and Title
            pdf.set_fill_color(12, 18, 40)
            pdf.rect(0, 0, 210, 297, 'F')
            pdf.set_font("Arial", 'B', 20)
            pdf.set_text_color(245, 164, 37)
            pdf.cell(200, 10, txt="STUDENT APPRAISAL REPORT", ln=True, align='C')

            current_month_year = datetime.now().strftime("MONTH OF %B %Y").upper()
            pdf.set_font("Arial", '', 12)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(200, 10, txt=current_month_year, ln=True, align='C')
            pdf.ln(10)

            # Student Details Table
            pdf.set_font("Arial", 'B', 18)
            pdf.set_text_color(245, 164, 37)
            pdf.cell(200, 10, txt="Student Details:", ln=True)
            pdf.ln(5)

            col_widths = [60, 130]
            pdf.set_font("Arial", 'B', 14)
            pdf.set_text_color(245, 164, 37)
            pdf.cell(col_widths[0], 10, 'Field', 1, 0, 'C')
            pdf.cell(col_widths[1], 10, 'Details', 1, 1, 'C')

            pdf.set_font("Arial", '', 12)
            pdf.set_text_color(255, 255, 255)

            details = [
                ("Student Name", student['name']),
                ("Enrollment", f"Student {student['student_id']}"),
                ("Email", student['email']),
                ("Attendance", f"{student['attendance']}%"),
                ("Homework Completion", f"{student['homework_completion']}%"),
                ("Test Scores", f"{student['test_scores']}"),
                ("Overall Percentage", f"{percentage}%"),
                ("Faculty", "John Doe"),
                ("Coordinator", "Elia")
            ]
            for label, value in details:
                pdf.cell(col_widths[0], 10, label, 1, 0, 'C')
                pdf.cell(col_widths[1], 10, value, 1, 1, 'C')

            pdf.ln(5)
            pdf.set_font("Arial", 'BU', 12)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(200, 10, txt="Remarks: " + prediction_text, ln=True)
            pdf.cell(200, 10, txt=f"Confidence: {probability}%", ln=True)
            pdf.ln(10)

            pdf.set_font("Arial", 'I', 11)
            footer_info = [
                "(92-21) 36630102-3",
                "infoexample@aptechnn.com",
                "SD-1 BLOCK A NORTH NAZIMABAD KARACHI-PAKISTAN"
            ]
            for line in footer_info:
                pdf.cell(200, 10, txt=line, ln=True, align='L')

            pdf_file = f"report_{student['student_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
            pdf.output(pdf_file)

            if os.path.exists(pdf_file):
                return send_file(pdf_file, as_attachment=True)
            else:
                flash('Error generating the PDF report', 'danger')
                return redirect(url_for('index'))

        except Exception as e:
            flash(f"Error generating PDF: {e}", 'danger')
            return redirect(url_for('index'))
    else:
        flash('Student not found!', 'danger')
        return redirect(url_for('index'))

# ---------------------------
# Run App (Deploy-ready for Railway)
# ---------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
