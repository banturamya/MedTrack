# 🏥 MedTrack - Healthcare Management System

A comprehensive web-based healthcare management application built with **Flask** and **Python**. This system enables patients to schedule appointments with doctors, manage their medical records, and allows healthcare providers to efficiently manage patient appointments and medical consultations.

---

## ✨ Features

### 👨‍⚕️ **Doctor Features**
- Secure doctor authentication and profile management
- Dashboard with appointment overview and statistics
- View detailed patient information and medical history
- Submit diagnoses, treatment plans, and prescriptions
- Search and filter patient appointments
- Receive appointment notifications via email

### 👤 **Patient Features**
- User registration and secure login
- Personalized patient dashboard
- Browse and book appointments with available doctors
- View appointment history and status
- Access consultation reports and diagnoses
- Manage personal medical profile and history
- Search doctor availability

### 🛠️ **Additional Features**
- Role-based access control (Doctor/Patient)
- Email notification system
- Comprehensive activity logging
- Search functionality
- Responsive user interface
- Session management
- Data validation and security

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Installation Steps

#### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/MedTrack.git
cd HealthCare
```

#### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Configure Environment Variables
Create a `.env` file in the project root:
```env
FLASK_SECRET_KEY=your_secret_key_here
FLASK_ENV=development
FLASK_DEBUG=1

# Email Configuration (Optional)
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_email_password

# Database Configuration
DATABASE_TYPE=memory  # Options: memory, sqlite, postgresql, dynamodb

# AWS Configuration (if using DynamoDB)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
USERS_TABLE=MedTrack_Users
APPOINTMENTS_TABLE=MedTrack_Appointments
NOTIFICATIONS_TABLE=MedTrack_Notifications

# SNS Configuration (optional)
ENABLE_SNS_NOTIFICATIONS=false
SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:medtrack-notifications
```

#### 5. Run the Application
```bash
python app.py
```

#### 6. Access the Application
Open your web browser and navigate to:
```
http://localhost:5000
```

---

## 🔐 Default Test Credentials

### Doctor Accounts
- **Email:** rajesh.kumar@medtrack.com | **Password:** password123 | **ID:** DOC1
- **Email:** nandini.sure@medtrack.com | **Password:** password123 | **ID:** DOC2

### Patient Accounts
- **Email:** arjun.singh@email.com | **Password:** password123 | **ID:** PAT1
- **Email:** anaya.patel@email.com | **Password:** password123 | **ID:** PAT2

---

## 📁 Project Structure

```
MedTrack/
│
├── app.py                          # Main Flask application
├── db.py                           # Database configuration
├── aws_services.py                 # DynamoDB + SNS integration helpers
├── requirements.txt                # Project dependencies
├── .env.example                    # Environment variables template
├── DEPLOY_AWS_EC2_DYNAMODB_SNS.md  # Full AWS deployment guide
├── LICENSE                         # MIT License
├── README.md                       # This file
│
├── templates/                      # HTML templates
│   ├── index.html                 # Landing page
│   ├── login.html                 # Login page
│   ├── register.html              # Registration page
│   ├── patient_dashboard.html     # Patient home
│   ├── doctor_dashboard.html      # Doctor home
│   ├── book_appointment.html      # Appointment booking
│   ├── view_appointment_doctor.html
│   ├── view_appointment_patient.html
│   ├── patient_profile.html       # Patient profile
│   ├── doctor_profile.html        # Doctor profile
│   ├── view_diagnoses.html        # Patient diagnoses
│   └── search_results.html        # Search results
```

---

## 🔧 Technology Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Flask (Python) |
| **Frontend** | HTML, CSS, Jinja2 |
| **Database** | In-Memory (Dictionary), SQLite, PostgreSQL, AWS DynamoDB |
| **Security** | Werkzeug (Password Hashing) |
| **Email** | SMTP (Gmail) |
| **Logging** | Python Logging Module |

---

## 📝 API Routes

### Authentication
- `GET/POST /login` - User login
- `GET/POST /register` - User registration
- `GET /logout` - User logout

### Patient Routes
- `GET /patient/dashboard` - Patient dashboard
- `GET/POST /appointment/book` - Book appointment
- `GET /appointment/<id>/patient-view` - View appointment
- `GET /diagnoses` - View all diagnoses
- `GET /profile/patient` - Patient profile

### Doctor Routes
- `GET /doctor/dashboard` - Doctor dashboard
- `GET /appointment/<id>/view` - View appointment
- `POST /appointment/<id>/submit-diagnosis` - Submit diagnosis
- `GET /profile/doctor` - Doctor profile

### Utility
- `GET /` - Home page
- `GET /search` - Search functionality

---

## 🔒 Security Features

1. **Password Security**
   - Passwords hashed using Werkzeug PBKDF2
   - Minimum 6 characters required

2. **Access Control**
   - Role-based decorators for protected routes
   - Session-based authentication
   - User ID validation

3. **Data Validation**
   - Form input validation
   - Email format validation
   - Data type checking

4. **Logging**
   - All authentication events logged
   - Failed login attempts tracked
   - User actions recorded

---

## 📧 Email Configuration

To enable email notifications:

1. Use a Gmail account or SMTP server
2. For Gmail: Enable "Less secure app access" or use App Password
3. Add credentials to `.env` file:
   ```env
   SMTP_EMAIL=your_email@gmail.com
   SMTP_PASSWORD=your_app_password
   ```

---

## 🗄️ Database Options

### In-Memory (Default)
- Perfect for development and testing
- Data persists during session
- No external dependencies

### SQLite
- Local persistent storage
- Good for small deployments
- Automatic schema creation

### PostgreSQL
- Enterprise-grade SQL database
- Scalable for large deployments
- Requires external database server

### AWS DynamoDB
- Cloud-based NoSQL database
- AWS integration included
- Scalable and serverless

### AWS SNS
- Topic-based notification fan-out
- Publishes booking and consultation completion events
- Controlled by `ENABLE_SNS_NOTIFICATIONS`

---

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Production with Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### AWS EC2 + DynamoDB + SNS
For complete production deployment on EC2 with DynamoDB persistence and SNS notifications, follow:

`DEPLOY_AWS_EC2_DYNAMODB_SNS.md`

### Docker Deployment
Create a `Dockerfile`:
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

---

## 📞 Contact & Support

- **Email:** suremallikarjun2@gmail.com
- **Website:** [Your Website]
- **Documentation:** [Link to docs]

---

## 🙏 Acknowledgments

- Flask framework for excellent web development tools
- Jinja2 for templating
- Python community for amazing libraries

---

## 📌 Roadmap

- [ ] SMS notifications for appointments
- [ ] Video consultation integration
- [ ] Mobile application
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Prescription management system
- [ ] Integration with healthcare APIs

---

## ⚖️ Legal Disclaimer

This application is designed for educational and demonstration purposes. For production healthcare use, ensure compliance with:
- HIPAA (Health Insurance Portability and Accountability Act)
- GDPR (General Data Protection Regulation)
- Local healthcare regulations
- Data privacy laws

---

**Last Updated:** March 5, 2026

**Version:** 1.0.0
