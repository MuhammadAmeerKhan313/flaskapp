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


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for sessions

# Connect to MongoDB
db = get_db()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required  # Protect the home route
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


# User Registration
@app.route('/register', methods=['POST', 'GET'])
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

# User Login
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        users = db.users
        username = request.form.get('username')
        password = request.form.get('password')

        if username and password:
            user = users.find_one({"username": username})
            if user and check_password_hash(user['password'], password):
                session['username'] = username
                session['email'] = user['email']  # Add email to session
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid credentials, please try again.', 'danger')

    return render_template('login.html')

# User Logout
@app.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    session.pop('email', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Prediction Route
@app.route('/predict', methods=['POST'])
@login_required
def predict():
    # Collect the features for prediction
    name = request.form['name']
    student_id = request.form['student_id']
    email = request.form['email']
    attendance = float(request.form['attendance'])
    homework_completion = float(request.form['homework_completion'])
    test_scores = float(request.form['test_scores'])

    # Use formula to calculate percentage and prediction
    percentage = (test_scores * 0.5) + (attendance * 0.3) + (homework_completion * 0.2)
    prediction = 1 if percentage > 60 else 0
    probability = round(percentage, 2)

    # Store student and prediction details in the session
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

    # Prediction message
    prediction_message = "Good Result! The student is likely to perform well." if prediction == 1 else "Bad Result! The student may not succeed based on current indicators."

    return render_template('result.html', prediction=prediction, probability=probability, prediction_message=prediction_message, student=student_data)

# PDF Report Generation
@app.route('/report/<student_id>', methods=['GET'])
@login_required
def report(student_id):
    # Retrieve student data from session
    student = session.get('student_data')

    # Validate student session and match the requested student_id
    if student and student['student_id'] == student_id:
        try:
            # Define prediction and probability
            prediction = 'Good Student' if student['prediction'] == 1 else 'Needs Improvement'
            probability = student['probability']

            # Calculate overall performance percentage
            percentage = round((student['test_scores'] * 0.5) + (student['attendance'] * 0.3) + (student['homework_completion'] * 0.2), 2)

            # Initialize FPDF instance for creating PDF
            pdf = FPDF()
            pdf.add_page()

            # Set background color (RGB) to #0c1228 (Dark Blue)
            pdf.set_fill_color(12, 18, 40)  # Dark Blue RGB color
            pdf.rect(0, 0, 210, 297, 'F')  # Full page rectangle (A4 size: 210mm x 297mm)

            # Title Section: Set title font and color to #f5a425 (Golden color)
            pdf.set_font("Arial", 'B', 20)
            pdf.set_text_color(245, 164, 37)  # Golden color
            pdf.cell(200, 10, txt="STUDENT APPRAISAL REPORT", ln=True, align='C')

            from datetime import datetime
            # Get current month and year (e.g., "May 2025")
            current_month_year = datetime.now().strftime("MONTH OF %B %Y").upper()

            # Subtitle with current month/year in white
            pdf.set_font("Arial", '', 12)
            pdf.set_text_color(255, 255, 255)  # White color
            pdf.cell(200, 10, txt=current_month_year, ln=True, align='C')

            # Reset text color for next sections (white for general content)
            pdf.set_text_color(255, 255, 255)
            pdf.ln(10)

            # Student Details Section (Table format) in #f5a425 (Golden)
            pdf.set_font("Arial", 'B', 18)
            pdf.set_text_color(245, 164, 37)  # Golden color
            pdf.cell(200, 10, txt="Student Details:", ln=True)
            pdf.ln(5)

            # Set table column widths, adjusted for right margin
            col_widths = [60, 130]  # Decreased the second column width for margin
            
            # Table Header Row
            pdf.set_font("Arial", 'B', 14)
            pdf.set_text_color(245, 164, 37)  # Golden color
            pdf.cell(col_widths[0], 10, 'Field', 1, 0, 'C')
            pdf.cell(col_widths[1], 10, 'Details', 1, 1, 'C')

            # Set content font and color
            pdf.set_font("Arial", '', 12)
            pdf.set_text_color(255, 255, 255)  # White color

            # Table rows for student details
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

           # Prediction and Remarks Section in white
            pdf.ln(5)
# Set font to bold, size 12, and underline for Prediction
            pdf.set_font("Arial", 'BU', 12)  # 'BU' stands for Bold and Underline
            pdf.set_text_color(255, 255, 255)  # White color

# Add underlined prediction text
            pdf.cell(200, 10, txt="Remarks: " + prediction, ln=True)

# Add underlined confidence text
            pdf.cell(200, 10, txt=f"Confidence: {probability}%", ln=True)

            pdf.ln(10)


            # Footer Section with company info in white
            pdf.set_font("Arial", 'I', 11)
            footer_info = [
                "(92-21) 36630102-3",
                "infoexample@aptechnn.com",
                "SD-1 BLOCK A NORTH NAZIMABAD KARACHI-PAKISTAN"
            ]
            for line in footer_info:
                pdf.cell(200, 10, txt=line, ln=True, align='L')

            # Generate the PDF file with timestamp to avoid filename collisions
            pdf_file = f"report_{student['student_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
            pdf.output(pdf_file)

            # Ensure the PDF file exists before attempting to send it
            if os.path.exists(pdf_file):
                return send_file(pdf_file, as_attachment=True)

            else:
                flash('Error generating the PDF report', 'danger')
                return redirect(url_for('index'))

        except Exception as e:
            # Handle errors gracefully with a flash message
            flash(f"Error generating PDF: {e}", 'danger')
            return redirect(url_for('index'))
    
    else:
        # If the student session is invalid or mismatched
        flash('Student not found!', 'danger')
        return redirect(url_for('index'))





if __name__ == '__main__':
    app.run(debug=True)