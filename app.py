# Healthcare Management System (MedTrack)
# Copyright (c) 2026 Mallikarjun
# Licensed under the MIT License
# For inquiries: suremallikarjun2@gmail.com

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import logging
import os
import uuid
from functools import wraps
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from aws_services import (
    load_runtime_data,
    persist_appointment,
    persist_notification,
    persist_user,
    publish_sns_notification,
)

# Load environment variables from .env file
load_dotenv()

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "medtrack_default_key_2026")

# ==================== LOGGING CONFIGURATION ====================
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# ==================== CONTEXT PROCESSOR ====================
@app.context_processor
def inject_datetime():
    """Inject current datetime into all templates"""
    return {'now': datetime.now()}

# ==================== IN-MEMORY DATA STORAGE ====================
# Initialize data dictionaries
users_database = {}
appointments_database = {}
notifications_list = []

# Sample Users for Testing
users_database = {
    'DOC1': {
        'user_id': 'DOC1',
        'name': 'Rajesh Kumar',
        'email': 'rajesh.kumar@medtrack.com',
        'password': generate_password_hash('password123'),
        'role': 'doctor',
        'specialization': 'Cardiology',
        'experience': '12 years',
        'age': 45,
        'gender': 'Male',
        'address': 'Medical Plaza, Downtown',
        'phone': '9876543210'
    },
    'DOC2': {
        'user_id': 'DOC2',
        'name': 'Nandini Sure',
        'email': 'nandini.sure@medtrack.com',
        'password': generate_password_hash('password123'),
        'role': 'doctor',
        'specialization': 'Pediatrics',
        'experience': '8 years',
        'age': 38,
        'gender': 'Female',
        'address': 'Shiva Nagar Hospital, Bidar',
        'phone': '9876543211'
    },
    'PAT1': {
        'user_id': 'PAT1',
        'name': 'Arjun Singh',
        'email': 'arjun.singh@email.com',
        'password': generate_password_hash('password123'),
        'role': 'patient',
        'age': 35,
        'gender': 'Male',
        'address': 'Residential Area, Sector 5',
        'medical_history': 'Hypertension, Allergies',
        'phone': '9123456789'
    },
    'PAT2': {
        'user_id': 'PAT2',
        'name': 'Anaya Patel',
        'email': 'anaya.patel@email.com',
        'password': generate_password_hash('password123'),
        'role': 'patient',
        'age': 28,
        'gender': 'Female',
        'address': 'Modern Society, West Wing',
        'medical_history': 'Asthma',
        'phone': '9123456790'
    }
}

# Sample Appointments for Testing
appointments_database = {
    'APT001': {
        'appointment_id': 'APT001',
        'doctor_id': 'DOC1',
        'patient_id': 'PAT1',
        'appointment_date': (date.today() + timedelta(days=2)).strftime('%Y-%m-%d'),
        'appointment_time': '10:00 AM',
        'symptoms': 'Chest pain and shortness of breath',
        'status': 'Pending',
        'created_at': datetime.now(),
        'diagnosis': None,
        'treatment_plan': None,
        'prescription': None
    },
    'APT002': {
        'appointment_id': 'APT002',
        'doctor_id': 'DOC2',
        'patient_id': 'PAT2',
        'appointment_date': (date.today() + timedelta(days=1)).strftime('%Y-%m-%d'),
        'appointment_time': '02:00 PM',
        'symptoms': 'Difficulty breathing and cough',
        'status': 'Completed',
        'created_at': datetime.now(),
        'diagnosis': 'Asthma exacerbation',
        'treatment_plan': 'Increase inhaler usage and avoid triggers',
        'prescription': 'Albuterol inhaler, Fluticasone propionate'
    },
    'APT003': {
        'appointment_id': 'APT003',
        'doctor_id': 'DOC1',
        'patient_id': 'PAT2',
        'appointment_date': (date.today() + timedelta(days=3)).strftime('%Y-%m-%d'),
        'appointment_time': '03:30 PM',
        'symptoms': 'Follow-up checkup',
        'status': 'Pending',
        'created_at': datetime.now(),
        'diagnosis': None,
        'treatment_plan': None,
        'prescription': None
    }
}

# Load persisted data when DynamoDB backend is enabled.
users_database, appointments_database, notifications_list = load_runtime_data(
    users_database,
    appointments_database,
)

# ==================== UTILITY FUNCTIONS ====================

def role_required(required_role):
    """Decorator to check if user has required role"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please log in to access this page.", "danger")
                return redirect(url_for('login'))
            
            if session.get('role') != required_role:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for('index'))
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def send_email_notification(recipient_email, subject, message_body):
    """Send email notification to user"""
    try:
        smtp_email = os.getenv("SMTP_EMAIL")
        smtp_password = os.getenv("SMTP_PASSWORD")
        
        if not smtp_email or not smtp_password:
            logging.warning(f"SMTP credentials not configured, skipping email to {recipient_email}")
            return False
        
        msg = MIMEMultipart()
        msg['From'] = smtp_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message_body, 'html'))
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_email, smtp_password)
            server.send_message(msg)
        
        logging.info(f"Email sent to {recipient_email}: {subject}")
        return True
    except Exception as e:
        logging.error(f"Failed to send email to {recipient_email}: {str(e)}")
        return False


def send_sns_notification(subject, message_body):
    """Publish notification message to configured SNS topic"""
    return publish_sns_notification(subject, message_body)


def record_notification(user_id, message, event_type="general"):
    """Store notification in local runtime and DynamoDB when configured"""
    notification = {
        'notification_id': str(uuid.uuid4()),
        'user_id': user_id,
        'event_type': event_type,
        'message': message,
        'is_read': False,
        'created_at': datetime.now().isoformat()
    }
    notifications_list.append(notification)
    persist_notification(notification)


def get_user_by_email(email):
    """Search for user by email address"""
    for user_id, user_data in users_database.items():
        if user_data['email'].lower() == email.lower():
            return user_id, user_data
    return None, None


def calculate_appointment_stats(appointments_list):
    """Calculate appointment statistics"""
    total = len(appointments_list)
    pending = sum(1 for apt in appointments_list if apt['status'] == 'Pending')
    completed = sum(1 for apt in appointments_list if apt['status'] == 'Completed')
    
    return {
        'total': total,
        'pending': pending,
        'completed': completed
    }


# ==================== ROUTES ====================

@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route"""
    if request.method == 'POST':
        # Get form data
        full_name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        user_role = request.form.get('role', '').strip()
        
        # Validation checks
        if not all([full_name, email, password, user_role]):
            flash("All fields are required.", "danger")
            return redirect(url_for('register'))
        
        # Check if email already exists
        existing_user_id, _ = get_user_by_email(email)
        if existing_user_id:
            flash("An account with this email already exists.", "danger")
            return redirect(url_for('register'))
        
        # Check password match
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('register'))
        
        # Check password length
        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return redirect(url_for('register'))
        
        # Create new user
        user_id = f"{user_role.upper()[:3]}{str(uuid.uuid4())[:6].upper()}"
        
        new_user = {
            'user_id': user_id,
            'name': full_name,
            'email': email,
            'password': generate_password_hash(password),
            'role': user_role.lower(),
            'age': request.form.get('age'),
            'gender': request.form.get('gender'),
            'address': request.form.get('address'),
            'phone': request.form.get('phone'),
            'specialization': request.form.get('specialization') if user_role.lower() == 'doctor' else None,
            'experience': request.form.get('experience') if user_role.lower() == 'doctor' else None,
            'medical_history': request.form.get('medical_history') if user_role.lower() == 'patient' else None
        }
        
        users_database[user_id] = new_user
        persist_user(new_user)
        logging.info(f"New user registered: {user_id} ({email})")
        
        flash(f"Registration successful! Your User ID: {user_id}. Please log in.", "success")
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        selected_role = request.form.get('role', '').strip().lower()
        
        # Find user by email
        user_id, user_data = get_user_by_email(email)
        
        # Verify credentials
        if not user_id or not check_password_hash(user_data['password'], password):
            flash("Invalid email or password.", "danger")
            logging.warning(f"Failed login attempt for email: {email}")
            return redirect(url_for('login'))
        
        # Verify role matches
        if user_data['role'] != selected_role:
            flash(f"Role mismatch! Your account is registered as a {user_data['role'].upper()}.", "danger")
            logging.warning(f"Role mismatch for {email}: selected {selected_role}, actual {user_data['role']}")
            return redirect(url_for('login'))
        
        # Set session and redirect
        session['user_id'] = user_id
        session['role'] = user_data['role']
        session['name'] = user_data['name']
        logging.info(f"User logged in: {user_id} ({email})")
        
        if user_data['role'] == 'doctor':
            return redirect(url_for('doctor_dashboard'))
        else:
            return redirect(url_for('patient_dashboard'))
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """User logout route"""
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))


@app.route('/patient/dashboard')
@role_required('patient')
def patient_dashboard():
    """Patient dashboard"""
    user_id = session.get('user_id')
    user_data = users_database.get(user_id)
    
    # Get user's appointments
    user_appointments = [
        apt for apt in appointments_database.values() 
        if apt['patient_id'] == user_id
    ]
    
    # Handle search
    search_query = request.args.get('search', '').strip().lower()
    if search_query:
        user_appointments = [
            apt for apt in user_appointments
            if (search_query in users_database[apt['doctor_id']]['name'].lower() or
                search_query in apt['status'].lower())
        ]
    
    # Calculate stats
    stats = calculate_appointment_stats(user_appointments)
    
    # Get available doctors
    doctors_list = {
        uid: data for uid, data in users_database.items()
        if data['role'] == 'doctor'
    }
    
    return render_template(
        'patient_dashboard.html',
        user=user_data,
        appointments=user_appointments,
        stats=stats,
        doctors=doctors_list,
        users=users_database
    )


@app.route('/doctor/dashboard')
@role_required('doctor')
def doctor_dashboard():
    """Doctor dashboard"""
    user_id = session.get('user_id')
    user_data = users_database.get(user_id)
    
    # Get appointments for this doctor
    doctor_appointments = [
        apt for apt in appointments_database.values()
        if apt['doctor_id'] == user_id
    ]
    
    # Handle search
    search_query = request.args.get('search', '').strip().lower()
    if search_query:
        doctor_appointments = [
            apt for apt in doctor_appointments
            if search_query in users_database[apt['patient_id']]['name'].lower()
        ]
    
    # Calculate stats
    stats = calculate_appointment_stats(doctor_appointments)
    
    return render_template(
        'doctor_dashboard.html',
        user=user_data,
        appointments=doctor_appointments,
        stats=stats,
        users=users_database
    )


@app.route('/appointment/book', methods=['GET', 'POST'])
@role_required('patient')
def book_appointment():
    """Book a new appointment"""
    if request.method == 'POST':
        doctor_id = request.form.get('doctor_id')
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        symptoms = request.form.get('symptoms', '').strip()
        
        # Validation
        if not all([doctor_id, appointment_date, appointment_time, symptoms]):
            flash("All fields are required.", "danger")
            return redirect(url_for('book_appointment'))
        
        # Verify doctor exists
        if doctor_id not in users_database or users_database[doctor_id]['role'] != 'doctor':
            flash("Selected doctor does not exist.", "danger")
            return redirect(url_for('book_appointment'))
        
        # Create appointment
        appointment_id = f"APT{str(uuid.uuid4())[:6].upper()}"
        
        new_appointment = {
            'appointment_id': appointment_id,
            'doctor_id': doctor_id,
            'patient_id': session.get('user_id'),
            'appointment_date': appointment_date,
            'appointment_time': appointment_time,
            'symptoms': symptoms,
            'status': 'Pending',
            'created_at': datetime.now(),
            'diagnosis': None,
            'treatment_plan': None,
            'prescription': None
        }
        
        appointments_database[appointment_id] = new_appointment
        persist_appointment(new_appointment)
        
        # Send notification email to doctor
        doctor_data = users_database[doctor_id]
        patient_data = users_database[session.get('user_id')]
        
        email_subject = f"New Appointment Request - {patient_data['name']}"
        email_body = f"""
        <h2>New Appointment Booking</h2>
        <p><strong>Patient:</strong> {patient_data['name']}</p>
        <p><strong>Date:</strong> {appointment_date}</p>
        <p><strong>Time:</strong> {appointment_time}</p>
        <p><strong>Symptoms:</strong> {symptoms}</p>
        <p>Please log in to your dashboard to manage this appointment.</p>
        """
        
        send_email_notification(doctor_data['email'], email_subject, email_body)
        send_sns_notification(
            "MedTrack: New Appointment Request",
            f"New appointment request from {patient_data['name']} with {doctor_data['name']} on {appointment_date} at {appointment_time}."
        )
        record_notification(
            doctor_id,
            f"New appointment request from {patient_data['name']} on {appointment_date} at {appointment_time}.",
            "appointment_booked"
        )
        
        logging.info(f"Appointment booked: {appointment_id} (Patient: {patient_data['name']}, Doctor: {doctor_data['name']})")
        flash("Appointment booked successfully!", "success")
        return redirect(url_for('patient_dashboard'))
    
    # Get list of doctors
    doctors_list = {
        uid: data for uid, data in users_database.items()
        if data['role'] == 'doctor'
    }
    
    return render_template('book_appointment.html', doctors=doctors_list)


@app.route('/appointment/<appointment_id>/view')
@role_required('doctor')
def view_appointment_doctor(appointment_id):
    """View appointment details (doctor view)"""
    appointment = appointments_database.get(appointment_id)
    
    if not appointment:
        flash("Appointment not found.", "danger")
        return redirect(url_for('doctor_dashboard'))
    
    if appointment['doctor_id'] != session.get('user_id'):
        flash("You do not have permission to view this appointment.", "danger")
        return redirect(url_for('doctor_dashboard'))
    
    patient_data = users_database.get(appointment['patient_id'])
    
    return render_template(
        'view_appointment_doctor.html',
        appointment=appointment,
        patient=patient_data
    )


@app.route('/appointment/<appointment_id>/submit-diagnosis', methods=['POST'])
@role_required('doctor')
def submit_diagnosis(appointment_id):
    """Submit diagnosis for an appointment"""
    appointment = appointments_database.get(appointment_id)
    
    if not appointment:
        flash("Appointment not found.", "danger")
        return redirect(url_for('doctor_dashboard'))
    
    if appointment['doctor_id'] != session.get('user_id'):
        flash("You do not have permission to modify this appointment.", "danger")
        return redirect(url_for('doctor_dashboard'))
    
    # Update appointment with diagnosis
    appointment['diagnosis'] = request.form.get('diagnosis', '').strip()
    appointment['treatment_plan'] = request.form.get('treatment_plan', '').strip()
    appointment['prescription'] = request.form.get('prescription', '').strip()
    appointment['status'] = 'Completed'
    persist_appointment(appointment)
    
    # Send email to patient
    patient_data = users_database[appointment['patient_id']]
    doctor_data = users_database[session.get('user_id')]
    
    email_subject = f"Appointment Completed - {doctor_data['name']}"
    email_body = f"""
    <h2>Your Appointment Consultation Summary</h2>
    <p><strong>Doctor:</strong> {doctor_data['name']}</p>
    <p><strong>Date:</strong> {appointment['appointment_date']}</p>
    <p><strong>Diagnosis:</strong> {appointment['diagnosis']}</p>
    <p><strong>Treatment Plan:</strong> {appointment['treatment_plan']}</p>
    <p><strong>Prescription:</strong> {appointment['prescription']}</p>
    """
    
    send_email_notification(patient_data['email'], email_subject, email_body)
    send_sns_notification(
        "MedTrack: Consultation Completed",
        f"Consultation completed for {patient_data['name']} by {doctor_data['name']} on {appointment['appointment_date']}."
    )
    record_notification(
        appointment['patient_id'],
        f"Your consultation with {doctor_data['name']} has been marked completed.",
        "appointment_completed"
    )
    
    logging.info(f"Diagnosis submitted for appointment {appointment_id}")
    flash("Diagnosis submitted successfully!", "success")
    return redirect(url_for('doctor_dashboard'))


@app.route('/appointment/<appointment_id>/patient-view')
@role_required('patient')
def view_appointment_patient(appointment_id):
    """View appointment details (patient view)"""
    appointment = appointments_database.get(appointment_id)
    
    if not appointment:
        flash("Appointment not found.", "danger")
        return redirect(url_for('patient_dashboard'))
    
    if appointment['patient_id'] != session.get('user_id'):
        flash("You do not have permission to view this appointment.", "danger")
        return redirect(url_for('patient_dashboard'))
    
    doctor_data = users_database.get(appointment['doctor_id'])
    
    return render_template(
        'view_appointment_patient.html',
        appointment=appointment,
        doctor=doctor_data
    )


@app.route('/profile/doctor')
@role_required('doctor')
def doctor_profile():
    """View/edit doctor profile"""
    user_id = session.get('user_id')
    user_data = users_database.get(user_id)
    
    return render_template('doctor_profile.html', user=user_data)


@app.route('/profile/patient')
@role_required('patient')
def patient_profile():
    """View/edit patient profile"""
    user_id = session.get('user_id')
    user_data = users_database.get(user_id)
    
    return render_template('patient_profile.html', user=user_data)


@app.route('/diagnoses')
@role_required('patient')
def view_diagnoses():
    """View all diagnoses for patient"""
    patient_id = session.get('user_id')
    
    patient_diagnoses = [
        apt for apt in appointments_database.values()
        if apt['patient_id'] == patient_id and apt.get('diagnosis')
    ]
    
    return render_template('view_diagnoses.html', diagnoses=patient_diagnoses, users=users_database)


@app.route('/search')
def search_results():
    """General search functionality"""
    query = request.args.get('q', '').strip().lower()
    
    if not query:
        return render_template('search_results.html', results=[], query='')
    
    results = {
        'doctors': [],
        'appointments': [],
        'diagnoses': []
    }
    
    # Search doctors
    if session.get('role') == 'patient':
        results['doctors'] = [
            doctor for doctor in users_database.values()
            if doctor['role'] == 'doctor' and query in doctor['name'].lower()
        ]
    
    # Search appointments
    if 'user_id' in session:
        if session.get('role') == 'patient':
            results['appointments'] = [
                apt for apt in appointments_database.values()
                if apt['patient_id'] == session.get('user_id') and
                (query in apt['appointment_date'] or query in apt['appointment_time'])
            ]
        elif session.get('role') == 'doctor':
            results['appointments'] = [
                apt for apt in appointments_database.values()
                if apt['doctor_id'] == session.get('user_id') and
                (query in apt['appointment_date'] or query in apt['appointment_time'] or
                 query in users_database[apt['patient_id']]['name'].lower())
            ]
    
    return render_template('search_results.html', results=results, query=query)


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def page_not_found(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logging.error(f"Internal server error: {str(error)}")
    return render_template('500.html'), 500


# ==================== MAIN ====================

if __name__ == '__main__':
    debug_mode = os.getenv("FLASK_DEBUG", "1").strip().lower() in {"1", "true", "yes"}
    app_host = os.getenv("FLASK_HOST", "0.0.0.0")
    app_port = int(os.getenv("FLASK_PORT", "5000"))
    app.run(debug=debug_mode, host=app_host, port=app_port)
