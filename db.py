# Database Configuration Module
# Healthcare Management System (MedTrack)
# Copyright (c) 2026 Mallikarjun
# Licensed under the MIT License

import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==================== DATABASE CONFIGURATION ====================

"""
This module provides database configuration for the Healthcare Management System.

Supported Database Options:
1. In-Memory Storage (Default) - Using Python dictionaries
2. AWS DynamoDB - For production deployments
3. SQLite - For local testing with persistence
4. PostgreSQL - For production deployments

To switch databases, update the DATABASE_TYPE environment variable.
"""

DATABASE_TYPE = os.getenv("DATABASE_TYPE", "memory")

# ==================== AWS DYNAMODB CONFIGURATION ====================
# Uncomment and configure below for AWS DynamoDB integration

"""
if DATABASE_TYPE == "dynamodb":
    import boto3
    
    dynamodb = boto3.resource(
        'dynamodb',
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )
    
    # DynamoDB table connections
    users_table = dynamodb.Table(os.getenv("USERS_TABLE", "MedTrack_Users"))
    appointments_table = dynamodb.Table(os.getenv("APPOINTMENTS_TABLE", "MedTrack_Appointments"))
    notifications_table = dynamodb.Table(os.getenv("NOTIFICATIONS_TABLE", "MedTrack_Notifications"))
    
    logging.info("DynamoDB database configured successfully")
"""

# ==================== SQLITE CONFIGURATION ====================
# Uncomment and configure below for SQLite database

"""
if DATABASE_TYPE == "sqlite":
    import sqlite3
    
    DATABASE_PATH = os.getenv("DATABASE_PATH", "medtrack.db")
    
    def get_db_connection():
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    
    def initialize_database():
        '''Initialize SQLite database with required tables'''
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                address TEXT,
                phone TEXT,
                specialization TEXT,
                experience TEXT,
                medical_history TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create appointments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                appointment_id TEXT PRIMARY KEY,
                doctor_id TEXT NOT NULL,
                patient_id TEXT NOT NULL,
                appointment_date TEXT NOT NULL,
                appointment_time TEXT NOT NULL,
                symptoms TEXT,
                status TEXT NOT NULL,
                diagnosis TEXT,
                treatment_plan TEXT,
                prescription TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doctor_id) REFERENCES users(user_id),
                FOREIGN KEY (patient_id) REFERENCES users(user_id)
            )
        ''')
        
        # Create notifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                message TEXT NOT NULL,
                is_read BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logging.info("SQLite database initialized successfully")
    
    initialize_database()
"""

# ==================== POSTGRESQL CONFIGURATION ====================
# Uncomment and configure below for PostgreSQL database

"""
if DATABASE_TYPE == "postgresql":
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/medtrack")
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    
    logging.info("PostgreSQL database configured successfully")
"""

# ==================== DEFAULT IN-MEMORY CONFIGURATION ====================

if DATABASE_TYPE == "memory":
    logging.info("Using in-memory database storage")
    # Data is stored in app.py using Python dictionaries
    # No additional configuration needed here

# ==================== LOGGING ====================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info(f"Database initialized with type: {DATABASE_TYPE}")
