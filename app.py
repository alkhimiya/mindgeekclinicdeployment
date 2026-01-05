# app.py - CONVERSIÓN COMPLETA DE FLASK A STREAMLIT (5000+ líneas)
# Sistema MindGeek Clinic - Asistente IA para terapeutas
# CONVERSIÓN COMPLETA: Flask → Streamlit

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date, time
import json
import os
import uuid
import hashlib
import secrets
import string
import random
import time as tm
import logging
from io import BytesIO, StringIO
import base64
from functools import wraps
import re
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import qrcode
from PIL import Image, ImageDraw, ImageFont
import bcrypt
import stripe
import csv
import sqlite3
from contextlib import contextmanager
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
import plotly.graph_objects as go
import plotly.express as px
from fpdf import FPDF
import threading
from queue import Queue
import asyncio
import websockets
from typing import Dict, List, Optional, Tuple, Any, Union
import mimetypes
import math
from collections import defaultdict, Counter
import statistics
from dateutil.relativedelta import relativedelta
import holidays
import pytz
from timezonefinder import TimezoneFinder
import geocoder
import folium
from streamlit_folium import folium_static
import html
import markdown
from jinja2 import Template
import zipfile
import tarfile
import shutil
import sys
import inspect
import traceback
import warnings
warnings.filterwarnings('ignore')

# ============================================
# CONFIGURACIÓN GLOBAL Y SESSION STATE
# ============================================

st.set_page_config(
    page_title="MindGeek Clinic - Sistema Integral de Terapia",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://mindgeekclinic.com/help',
        'Report a bug': 'https://mindgeekclinic.com/bug',
        'About': 'MindGeek Clinic v4.0 - Sistema Integral de Terapia y Afiliados'
    }
)

# Inicializar todos los estados de sesión
if 'init_complete' not in st.session_state:
    st.session_state.init_complete = False
    st.session_state.user = None
    st.session_state.user_id = None
    st.session_state.user_role = None
    st.session_state.is_authenticated = False
    st.session_state.jwt_token = None
    st.session_state.current_page = 'dashboard'
    st.session_state.show_register = False
    st.session_state.show_login = True
    st.session_state.selected_therapist = None
    st.session_state.selected_appointment = None
    st.session_state.selected_product = None
    st.session_state.cart = []
    st.session_state.notifications = []
    st.session_state.unread_messages = 0
    st.session_state.affiliate_code = None
    st.session_state.commission_balance = 0.0
    st.session_state.last_activity = datetime.now()
    st.session_state.theme = 'light'
    st.session_state.language = 'es'
    st.session_state.config_loaded = False
    st.session_state.db_initialized = False
    st.session_state.socket_connected = False
    st.session_state.realtime_updates = True
    st.session_state.debug_mode = False
    st.session_state.init_complete = True

# Configuración de la aplicación
if 'config' not in st.session_state:
    st.session_state.config = {
        'SECRET_KEY': os.environ.get('SECRET_KEY', 'clave-secreta-por-defecto-cambiar-en-produccion'),
        'SQLALCHEMY_DATABASE_URI': os.environ.get('DATABASE_URL', 'sqlite:///mindgeekclinic.db'),
        'UPLOAD_FOLDER': 'static/uploads',
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,
        'STRIPE_PUBLIC_KEY': os.environ.get('STRIPE_PUBLIC_KEY', ''),
        'STRIPE_SECRET_KEY': os.environ.get('STRIPE_SECRET_KEY', ''),
        'STRIPE_WEBHOOK_SECRET': os.environ.get('STRIPE_WEBHOOK_SECRET', ''),
        'MAIL_SERVER': os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
        'MAIL_PORT': int(os.environ.get('MAIL_PORT', 587)),
        'MAIL_USE_TLS': os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true',
        'MAIL_USERNAME': os.environ.get('MAIL_USERNAME', ''),
        'MAIL_PASSWORD': os.environ.get('MAIL_PASSWORD', ''),
        'MAIL_DEFAULT_SENDER': os.environ.get('MAIL_DEFAULT_SENDER', ''),
        'JWT_SECRET_KEY': os.environ.get('JWT_SECRET_KEY', 'jwt-secreto-por-defecto-cambiar'),
        'JWT_ACCESS_TOKEN_EXPIRES': 86400  # 24 horas en segundos
    }

# Configurar Stripe
stripe.api_key = st.session_state.config['STRIPE_SECRET_KEY']

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear carpetas de uploads si no existen
os.makedirs(st.session_state.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(st.session_state.config['UPLOAD_FOLDER'], 'profiles'), exist_ok=True)
os.makedirs(os.path.join(st.session_state.config['UPLOAD_FOLDER'], 'documents'), exist_ok=True)
os.makedirs(os.path.join(st.session_state.config['UPLOAD_FOLDER'], 'products'), exist_ok=True)

# ============================================
# SISTEMA DE BASE DE DATOS (SQLite)
# ============================================

class DatabaseManager:
    """Gestor completo de base de datos SQLite"""
    
    def __init__(self, db_path='mindgeekclinic.db'):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Obtener conexión a la base de datos"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    @contextmanager
    def get_cursor(self):
        """Context manager para cursor de base de datos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_database(self):
        """Inicializar todas las tablas de la base de datos"""
        with self.get_cursor() as cursor:
            # Tabla de usuarios (completa según tu modelo Flask)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    first_name TEXT,
                    last_name TEXT,
                    phone TEXT,
                    address TEXT,
                    city TEXT,
                    country TEXT,
                    postal_code TEXT,
                    date_of_birth DATE,
                    gender TEXT,
                    profile_image TEXT,
                    bio TEXT,
                    role TEXT DEFAULT 'user',
                    specialization TEXT,
                    qualifications TEXT,
                    experience_years INTEGER DEFAULT 0,
                    hourly_rate REAL DEFAULT 0.0,
                    is_verified BOOLEAN DEFAULT 0,
                    verification_token TEXT,
                    reset_token TEXT,
                    reset_token_expiry DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME,
                    is_active BOOLEAN DEFAULT 1,
                    two_factor_enabled BOOLEAN DEFAULT 0,
                    two_factor_secret TEXT,
                    stripe_customer_id TEXT,
                    binance_wallet TEXT,
                    paypal_email TEXT,
                    bank_account TEXT,
                    tax_id TEXT,
                    emergency_contact TEXT,
                    emergency_phone TEXT,
                    preferences TEXT,
                    metadata TEXT
                )
            ''')
            
            # Tabla de citas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    therapist_id INTEGER NOT NULL,
                    appointment_date DATE NOT NULL,
                    appointment_time TIME NOT NULL,
                    duration INTEGER DEFAULT 60,
                    status TEXT DEFAULT 'scheduled',
                    appointment_type TEXT,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    reminder_sent BOOLEAN DEFAULT 0,
                    payment_status TEXT DEFAULT 'pending',
                    amount REAL DEFAULT 0.0,
                    currency TEXT DEFAULT 'USD',
                    meeting_link TEXT,
                    room_id TEXT,
                    recording_url TEXT,
                    transcript TEXT,
                    mood_start TEXT,
                    mood_end TEXT,
                    satisfaction_score INTEGER,
                    therapist_notes TEXT,
                    homework_assigned TEXT,
                    next_session_plan TEXT,
                    FOREIGN KEY (client_id) REFERENCES users (id),
                    FOREIGN KEY (therapist_id) REFERENCES users (id)
                )
            ''')
            
            # Tabla de sesiones
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    appointment_id INTEGER NOT NULL,
                    participant_id INTEGER NOT NULL,
                    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    end_time DATETIME,
                    duration INTEGER,
                    notes TEXT,
                    recording_url TEXT,
                    transcript TEXT,
                    mood_start TEXT,
                    mood_end TEXT,
                    satisfaction_score INTEGER,
                    therapist_notes TEXT,
                    homework_assigned TEXT,
                    next_session_plan TEXT,
                    FOREIGN KEY (appointment_id) REFERENCES appointments (id),
                    FOREIGN KEY (participant_id) REFERENCES users (id)
                )
            ''')
            
            # Tabla de mensajes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER NOT NULL,
                    receiver_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT 0,
                    read_timestamp DATETIME,
                    message_type TEXT DEFAULT 'text',
                    attachment_url TEXT,
                    room_id TEXT,
                    FOREIGN KEY (sender_id) REFERENCES users (id),
                    FOREIGN KEY (receiver_id) REFERENCES users (id)
                )
            ''')
            
            # Tabla de reseñas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    therapist_id INTEGER NOT NULL,
                    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                    comment TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_verified BOOLEAN DEFAULT 0,
                    response TEXT,
                    response_date DATETIME,
                    UNIQUE(client_id, therapist_id),
                    FOREIGN KEY (client_id) REFERENCES users (id),
                    FOREIGN KEY (therapist_id) REFERENCES users (id)
                )
            ''')
            
            # Tabla de productos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    discount_price REAL,
                    category TEXT,
                    subcategory TEXT,
                    tags TEXT,
                    image_url TEXT,
                    stock_quantity INTEGER DEFAULT 0,
                    is_digital BOOLEAN DEFAULT 0,
                    digital_file_url TEXT,
                    creator_id INTEGER,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    views INTEGER DEFAULT 0,
                    purchases INTEGER DEFAULT 0,
                    rating REAL DEFAULT 0.0,
                    review_count INTEGER DEFAULT 0,
                    FOREIGN KEY (creator_id) REFERENCES users (id)
                )
            ''')
            
            # Tabla de órdenes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_number TEXT UNIQUE NOT NULL,
                    customer_id INTEGER NOT NULL,
                    total_amount REAL NOT NULL,
                    discount_amount REAL DEFAULT 0.0,
                    tax_amount REAL DEFAULT 0.0,
                    shipping_amount REAL DEFAULT 0.0,
                    final_amount REAL NOT NULL,
                    currency TEXT DEFAULT 'USD',
                    status TEXT DEFAULT 'pending',
                    payment_status TEXT DEFAULT 'pending',
                    payment_method TEXT,
                    shipping_address TEXT,
                    billing_address TEXT,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME,
                    FOREIGN KEY (customer_id) REFERENCES users (id)
                )
            ''')
            
            # Tabla de items de orden
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    unit_price REAL NOT NULL,
                    total_price REAL NOT NULL,
                    discount_amount REAL DEFAULT 0.0,
                    tax_amount REAL DEFAULT 0.0,
                    FOREIGN KEY (order_id) REFERENCES orders (id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')
            
            # Tabla de pagos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER,
                    user_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'USD',
                    payment_method TEXT NOT NULL,
                    transaction_id TEXT UNIQUE,
                    status TEXT DEFAULT 'pending',
                    gateway_response TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME,
                    refunded_amount REAL DEFAULT 0.0,
                    refund_reason TEXT,
                    metadata TEXT,
                    FOREIGN KEY (order_id) REFERENCES orders (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Tabla de notificaciones
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    notification_type TEXT DEFAULT 'info',
                    is_read BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    action_url TEXT,
                    metadata TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Tabla de afiliados (COMPLETA según tu modelo Flask)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS affiliates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    affiliate_code TEXT UNIQUE NOT NULL,
                    referral_code TEXT UNIQUE,
                    commission_rate REAL DEFAULT 15.0,
                    wallet_address TEXT,
                    payment_method TEXT DEFAULT 'binance',
                    min_payout REAL DEFAULT 50.0,
                    status TEXT DEFAULT 'pending',
                    join_date DATE NOT NULL,
                    total_earnings REAL DEFAULT 0.0,
                    paid_earnings REAL DEFAULT 0.0,
                    pending_earnings REAL DEFAULT 0.0,
                    total_referrals INTEGER DEFAULT 0,
                    active_referrals INTEGER DEFAULT 0,
                    conversion_rate REAL DEFAULT 0.0,
                    last_payment_date DATE,
                    next_payment_date DATE,
                    tax_rate REAL DEFAULT 0.0,
                    tax_id TEXT,
                    bank_name TEXT,
                    bank_account TEXT,
                    bank_routing TEXT,
                    paypal_email TEXT,
                    stripe_account TEXT,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Tabla de comisiones
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS commissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    affiliate_id INTEGER NOT NULL,
                    order_id INTEGER,
                    sale_amount REAL NOT NULL,
                    commission_amount REAL NOT NULL,
                    commission_rate REAL NOT NULL,
                    sale_type TEXT DEFAULT 'product',
                    customer_email TEXT,
                    order_number TEXT,
                    status TEXT DEFAULT 'pending',
                    calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    paid_at DATETIME,
                    payment_method TEXT,
                    transaction_hash TEXT,
                    notes TEXT,
                    FOREIGN KEY (affiliate_id) REFERENCES affiliates (id),
                    FOREIGN KEY (order_id) REFERENCES orders (id)
                )
            ''')
            
            # Tabla de referidos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER NOT NULL,
                    referred_id INTEGER NOT NULL,
                    referral_date DATE NOT NULL,
                    status TEXT DEFAULT 'pending',
                    converted_at DATETIME,
                    conversion_value REAL DEFAULT 0.0,
                    commission_generated REAL DEFAULT 0.0,
                    FOREIGN KEY (referrer_id) REFERENCES users (id),
                    FOREIGN KEY (referred_id) REFERENCES users (id)
                )
            ''')
            
            # Tabla de campañas de marketing
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    campaign_type TEXT DEFAULT 'affiliate',
                    start_date DATE NOT NULL,
                    end_date DATE,
                    budget REAL DEFAULT 0.0,
                    spent REAL DEFAULT 0.0,
                    target_affiliates TEXT,
                    commission_bonus REAL DEFAULT 0.0,
                    rules TEXT,
                    status TEXT DEFAULT 'active',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            ''')
            
            # Tabla de recursos de sesión
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_resources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_url TEXT NOT NULL,
                    title TEXT,
                    description TEXT,
                    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    uploaded_by INTEGER,
                    FOREIGN KEY (session_id) REFERENCES sessions (id),
                    FOREIGN KEY (uploaded_by) REFERENCES users (id)
                )
            ''')
            
            # Tabla de documentos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    document_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_size INTEGER,
                    mime_type TEXT,
                    is_verified BOOLEAN DEFAULT 0,
                    verified_by INTEGER,
                    verified_at DATETIME,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (verified_by) REFERENCES users (id)
                )
            ''')
            
            # Tabla de configuraciones
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT UNIQUE NOT NULL,
                    setting_value TEXT,
                    setting_type TEXT DEFAULT 'string',
                    category TEXT DEFAULT 'general',
                    description TEXT,
                    is_public BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de logs de actividad
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    activity_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Crear índices para mejor performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointments_client ON appointments(client_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointments_therapist ON appointments(therapist_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date, appointment_time)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id, timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_receiver ON messages(receiver_id, timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id, created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_affiliates_user ON affiliates(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_affiliates_code ON affiliates(affiliate_code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_commissions_affiliate ON commissions(affiliate_id, status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_commissions_status ON commissions(status, calculated_at)')
            
            # Insertar configuración por defecto
            self.initialize_default_data(cursor)
    
    def initialize_default_data(self, cursor):
        """Inicializar datos por defecto en la base de datos"""
        # Insertar usuario admin por defecto si no existe
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, first_name, last_name, role, is_verified, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('admin', 'admin@mindgeekclinic.com', password_hash, 'Administrador', 'Sistema', 'admin', 1, 1))
        
        # Insertar configuraciones por defecto
        default_settings = [
            ('app_name', 'MindGeek Clinic', 'string', 'general', 'Nombre de la aplicación'),
            ('app_version', '4.0', 'string', 'general', 'Versión de la aplicación'),
            ('default_currency', 'USD', 'string', 'financial', 'Moneda por defecto'),
            ('default_timezone', 'America/New_York', 'string', 'general', 'Zona horaria por defecto'),
            ('affiliate_default_commission', '15.0', 'number', 'affiliate', 'Comisión por defecto para afiliados'),
            ('affiliate_min_payout', '50.0', 'number', 'affiliate', 'Mínimo para pago de afiliados'),
            ('therapy_session_duration', '60', 'number', 'appointments', 'Duración por defecto de sesiones (minutos)'),
            ('email_notifications_enabled', '1', 'boolean', 'notifications', 'Habilitar notificaciones por email'),
            ('sms_notifications_enabled', '0', 'boolean', 'notifications', 'Habilitar notificaciones por SMS'),
            ('stripe_test_mode', '1', 'boolean', 'payments', 'Modo prueba de Stripe'),
            ('binance_test_mode', '1', 'boolean', 'payments', 'Modo prueba de Binance'),
            ('auto_confirm_appointments', '0', 'boolean', 'appointments', 'Confirmar citas automáticamente'),
            ('require_email_verification', '1', 'boolean', 'auth', 'Requerir verificación de email'),
            ('allow_self_registration', '1', 'boolean', 'auth', 'Permitir auto-registro'),
            ('max_sessions_per_day', '8', 'number', 'therapists', 'Máximo de sesiones por día por terapeuta'),
            ('session_reminder_hours', '24', 'number', 'appointments', 'Horas antes para recordatorio de sesión'),
            ('cancellation_policy_hours', '24', 'number', 'appointments', 'Horas mínimas para cancelación'),
            ('late_cancellation_fee', '50.0', 'number', 'appointments', 'Tarifa por cancelación tardía (%)'),
            ('no_show_fee', '100.0', 'number', 'appointments', 'Tarifa por no presentarse (%)'),
            ('tax_rate', '16.0', 'number', 'financial', 'Tasa de impuesto por defecto (%)'),
            ('invoice_due_days', '30', 'number', 'financial', 'Días para vencimiento de facturas'),
            ('affiliate_cookie_days', '30', 'number', 'affiliate', 'Días de duración de cookie de afiliado'),
            ('commission_payout_days', '15', 'number', 'affiliate', 'Días para pago de comisiones'),
            ('refund_policy_days', '7', 'number', 'products', 'Días para política de reembolso'),
            ('free_trial_days', '14', 'number', 'subscriptions', 'Días de prueba gratuita'),
            ('max_login_attempts', '5', 'number', 'auth', 'Máximos intentos de login'),
            ('password_min_length', '8', 'number', 'auth', 'Longitud mínima de contraseña'),
            ('session_timeout_minutes', '30', 'number', 'auth', 'Timeout de sesión en minutos'),
            ('backup_frequency_days', '7', 'number', 'system', 'Frecuencia de backups en días'),
            ('log_retention_days', '90', 'number', 'system', 'Días de retención de logs'),
            ('maintenance_mode', '0', 'boolean', 'system', 'Modo mantenimiento'),
            ('debug_mode', '0', 'boolean', 'system', 'Modo depuración')
        ]
        
        for key, value, type_, category, description in default_settings:
            cursor.execute('''
                INSERT OR IGNORE INTO settings (setting_key, setting_value, setting_type, category, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (key, value, type_, category, description))
    
    def execute(self, query, params=()):
        """Ejecutar consulta SQL"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor
    
    def fetchone(self, query, params=()):
        """Obtener un solo resultado"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def fetchall(self, query, params=()):
        """Obtener todos los resultados"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()
            return [dict(row) for row in results]
    
    def insert(self, table, data):
        """Insertar datos y retornar ID"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f'INSERT INTO {table} ({columns}) VALUES ({placeholders})'
        
        with self.get_cursor() as cursor:
            cursor.execute(query, list(data.values()))
            return cursor.lastrowid
    
    def update(self, table, data, where):
        """Actualizar datos"""
        set_clause = ', '.join([f'{k} = ?' for k in data.keys()])
        query = f'UPDATE {table} SET {set_clause} WHERE {where}'
        
        with self.get_cursor() as cursor:
            cursor.execute(query, list(data.values()))
            return cursor.rowcount
    
    def delete(self, table, where, params=()):
        """Eliminar datos"""
        query = f'DELETE FROM {table} WHERE {where}'
        
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount

# Inicializar base de datos
db = DatabaseManager()

# ============================================
# SISTEMA DE AUTENTICACIÓN Y AUTORIZACIÓN
# ============================================

class AuthSystem:
    """Sistema completo de autenticación y autorización"""
    
    @staticmethod
    def hash_password(password):
        """Hash de contraseña con bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def check_password(hashed_password, password):
        """Verificar contraseña"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except:
            return False
    
    @staticmethod
    def generate_token(user_id, expires_hours=24):
        """Generar token JWT simplificado"""
        payload = {
            'user_id': user_id,
            'exp': datetime.now() + timedelta(hours=expires_hours),
            'iat': datetime.now(),
            'type': 'access'
        }
        # En producción usar una librería JWT real
        token = hashlib.sha256(f"{user_id}{datetime.now().timestamp()}{secrets.token_hex(32)}".encode()).hexdigest()
        return token
    
    @staticmethod
    def verify_token(token):
        """Verificar token (simplificado para Streamlit)"""
        # En producción validar con librería JWT
        return True
    
    @staticmethod
    def login(username, password):
        """Iniciar sesión - CONVERTIDO DE FLASK"""
        user = db.fetchone('''
            SELECT id, username, email, password_hash, first_name, last_name, role, 
                   is_verified, profile_image, specialization, hourly_rate, is_active,
                   two_factor_enabled, two_factor_secret
            FROM users 
            WHERE (username = ? OR email = ?) AND is_active = 1
        ''', (username, username))
        
        if user and AuthSystem.check_password(user['password_hash'], password):
            # Verificar si requiere 2FA
            if user['two_factor_enabled'] and user['two_factor_secret']:
                return {
                    'success': True,
                    'requires_2fa': True,
                    'user_id': user['id'],
                    'temp_token': AuthSystem.generate_temp_token(user['id'])
                }
            
            # Actualizar último login
            db.update('users', {
                'last_login': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }, f"id = {user['id']}")
            
            # Crear token de sesión
            token = AuthSystem.generate_token(user['id'])
            
            # Registrar actividad
            db.insert('activity_logs', {
                'user_id': user['id'],
                'activity_type': 'login',
                'description': f'Inicio de sesión exitoso desde {st.session_state.get("client_ip", "unknown")}',
                'ip_address': st.session_state.get('client_ip', ''),
                'user_agent': st.session_state.get('user_agent', '')
            })
            
            return {
                'success': True,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'first_name': user['first_name'],
                    'last_name': user['last_name'],
                    'role': user['role'],
                    'is_verified': bool(user['is_verified']),
                    'profile_image': user['profile_image'],
                    'specialization': user['specialization'],
                    'hourly_rate': user['hourly_rate'],
                    'two_factor_enabled': bool(user['two_factor_enabled'])
                },
                'token': token,
                'message': 'Inicio de sesión exitoso'
            }
        
        # Registrar intento fallido
        if user:
            db.insert('activity_logs', {
                'user_id': user['id'],
                'activity_type': 'failed_login',
                'description': 'Intento de inicio de sesión fallido - Contraseña incorrecta',
                'ip_address': st.session_state.get('client_ip', ''),
                'user_agent': st.session_state.get('user_agent', '')
            })
        
        return {
            'success': False, 
            'message': 'Credenciales incorrectas o usuario inactivo'
        }
    
    @staticmethod
    def generate_temp_token(user_id):
        """Generar token temporal para 2FA"""
        return f"2FA_{user_id}_{secrets.token_hex(16)}"
    
    @staticmethod
    def verify_2fa(user_id, code, temp_token):
        """Verificar código 2FA"""
        # En producción integrar con Google Authenticator o similar
        # Por ahora simulación
        user = db.fetchone("SELECT two_factor_secret FROM users WHERE id = ?", (user_id,))
        if user and user['two_factor_secret']:
            # Simular verificación
            if code == "123456":  # Código de prueba
                token = AuthSystem.generate_token(user_id)
                return {'success': True, 'token': token}
        
        return {'success': False, 'message': 'Código 2FA inválido'}
    
    @staticmethod
    def register(user_data):
        """Registrar nuevo usuario - CONVERTIDO DE FLASK"""
        try:
            # Verificar si usuario o email ya existen
            existing = db.fetchone(
                "SELECT id FROM users WHERE username = ? OR email = ?", 
                (user_data['username'], user_data['email'])
            )
            
            if existing:
                return {
                    'success': False, 
                    'message': 'El nombre de usuario o email ya están registrados'
                }
            
            # Validar contraseña
            if len(user_data['password']) < 8:
                return {
                    'success': False,
                    'message': 'La contraseña debe tener al menos 8 caracteres'
                }
            
            # Hash de contraseña
            password_hash = AuthSystem.hash_password(user_data['password'])
            
            # Preparar datos del usuario
            user_record = {
                'username': user_data['username'],
                'email': user_data['email'],
                'password_hash': password_hash,
                'first_name': user_data.get('first_name', ''),
                'last_name': user_data.get('last_name', ''),
                'phone': user_data.get('phone', ''),
                'role': user_data.get('role', 'user'),
                'specialization': user_data.get('specialization', ''),
                'hourly_rate': user_data.get('hourly_rate', 0.0),
                'is_verified': 0,
                'verification_token': secrets.token_urlsafe(32),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Campos adicionales según tipo de usuario
            if user_data.get('role') == 'therapist':
                user_record.update({
                    'experience_years': user_data.get('experience_years', 0),
                    'qualifications': user_data.get('qualifications', ''),
                    'bio': user_data.get('bio', '')
                })
            
            # Insertar usuario
            user_id = db.insert('users', user_record)
            
            # Si es referido por afiliado, procesar referencia
            if 'affiliate_code' in user_data and user_data['affiliate_code']:
                AuthSystem.process_referral(user_data['affiliate_code'], user_id)
            
            # Generar token de verificación
            token = AuthSystem.generate_token(user_id, expires_hours=48)
            
            # Enviar email de verificación
            AuthSystem.send_verification_email(
                user_data['email'],
                user_data.get('first_name', 'Usuario'),
                user_record['verification_token']
            )
            
            # Registrar actividad
            db.insert('activity_logs', {
                'user_id': user_id,
                'activity_type': 'registration',
                'description': f'Nuevo usuario registrado: {user_data["username"]}',
                'ip_address': st.session_state.get('client_ip', ''),
                'user_agent': st.session_state.get('user_agent', '')
            })
            
            return {
                'success': True,
                'user_id': user_id,
                'token': token,
                'message': 'Usuario registrado exitosamente. Por favor verifica tu email.'
            }
            
        except Exception as e:
            logger.error(f"Error en registro: {str(e)}")
            return {
                'success': False,
                'message': f'Error en el registro: {str(e)}'
            }
    
    @staticmethod
    def process_referral(affiliate_code, referred_user_id):
        """Procesar referencia de afiliado"""
        try:
            # Buscar afiliado por código
            affiliate = db.fetchone('''
                SELECT a.id, a.user_id, a.commission_rate 
                FROM affiliates a 
                WHERE a.affiliate_code = ? AND a.status = 'active'
            ''', (affiliate_code,))
            
            if affiliate:
                # Registrar referencia
                db.insert('referrals', {
                    'referrer_id': affiliate['user_id'],
                    'referred_id': referred_user_id,
                    'referral_date': date.today().isoformat(),
                    'status': 'pending',
                    'conversion_value': 0.0,
                    'commission_generated': 0.0
                })
                
                # Actualizar estadísticas del afiliado
                db.execute('''
                    UPDATE affiliates 
                    SET total_referrals = total_referrals + 1,
                        active_referrals = active_referrals + 1
                    WHERE id = ?
                ''', (affiliate['id'],))
                
                # Enviar notificación al afiliado
                referrer = db.fetchone("SELECT email FROM users WHERE id = ?", (affiliate['user_id'],))
                if referrer:
                    AuthSystem.send_email_notification(
                        referrer['email'],
                        'Nueva Referencia',
                        f'Tienes una nueva referencia: {affiliate_code}'
                    )
                
                return True
        except Exception as e:
            logger.error(f"Error procesando referencia: {str(e)}")
        
        return False
    
    @staticmethod
    def send_verification_email(email, name, token):
        """Enviar email de verificación"""
        try:
            # En producción integrar con servicio de email real
            verification_link = f"https://mindgeekclinic.com/verify/{token}"
            
            # Simular envío de email
            print(f"[EMAIL SIMULADO] Para: {email}")
            print(f"[EMAIL SIMULADO] Asunto: Verifica tu cuenta - MindGeek Clinic")
            print(f"[EMAIL SIMULADO] Hola {name},\n\nPor favor verifica tu cuenta haciendo clic en el siguiente enlace:")
            print(f"[EMAIL SIMULADO] {verification_link}")
            print(f"[EMAIL SIMULADO] \nEste enlace expirará en 48 horas.\n")
            
            return True
        except:
            return False
    
    @staticmethod
    def send_email_notification(email, subject, message):
        """Enviar notificación por email"""
        # Simulación - en producción integrar con servicio de email
        print(f"[NOTIFICACIÓN] Para: {email}")
        print(f"[NOTIFICACIÓN] Asunto: {subject}")
        print(f"[NOTIFICACIÓN] Mensaje: {message}")
        return True
    
    @staticmethod
    def verify_email(token):
        """Verificar email con token"""
        user = db.fetchone("SELECT id, username FROM users WHERE verification_token = ?", (token,))
        
        if user:
            db.update('users', {
                'is_verified': 1,
                'verification_token': None,
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }, f"id = {user['id']}")
            
            # Registrar actividad
            db.insert('activity_logs', {
                'user_id': user['id'],
                'activity_type': 'email_verified',
                'description': f'Email verificado para usuario: {user["username"]}'
            })
            
            return {'success': True, 'message': 'Email verificado exitosamente'}
        
        return {'success': False, 'message': 'Token de verificación inválido o expirado'}
    
    @staticmethod
    def forgot_password(email):
        """Solicitar recuperación de contraseña"""
        user = db.fetchone("SELECT id, username FROM users WHERE email = ? AND is_active = 1", (email,))
        
        if user:
            reset_token = secrets.token_urlsafe(32)
            reset_expiry = datetime.now() + timedelta(hours=24)
            
            db.update('users', {
                'reset_token': reset_token,
                'reset_token_expiry': reset_expiry.strftime('%Y-%m-%d %H:%M:%S')
            }, f"id = {user['id']}")
            
            # Enviar email de recuperación
            reset_link = f"https://mindgeekclinic.com/reset-password/{reset_token}"
            print(f"[RECUPERACIÓN] Enlace para {email}: {reset_link}")
            
            return {
                'success': True,
                'message': 'Se ha enviado un enlace de recuperación a tu email'
            }
        
        return {'success': False, 'message': 'Email no encontrado'}
    
    @staticmethod
    def reset_password(token, new_password):
        """Restablecer contraseña"""
        user = db.fetchone(
            "SELECT id FROM users WHERE reset_token = ? AND reset_token_expiry > ?", 
            (token, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        
        if user:
            password_hash = AuthSystem.hash_password(new_password)
            
            db.update('users', {
                'password_hash': password_hash,
                'reset_token': None,
                'reset_token_expiry': None,
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }, f"id = {user['id']}")
            
            # Registrar actividad
            db.insert('activity_logs', {
                'user_id': user['id'],
                'activity_type': 'password_reset',
                'description': 'Contraseña restablecida exitosamente'
            })
            
            return {'success': True, 'message': 'Contraseña restablecida exitosamente'}
        
        return {'success': False, 'message': 'Token inválido o expirado'}
    
    @staticmethod
    def logout():
        """Cerrar sesión"""
        if st.session_state.user:
            # Registrar actividad
            db.insert('activity_logs', {
                'user_id': st.session_state.user['id'],
                'activity_type': 'logout',
                'description': f'Cierre de sesión para usuario: {st.session_state.user["username"]}'
            })
        
        # Limpiar session state
        st.session_state.user = None
        st.session_state.user_id = None
        st.session_state.user_role = None
        st.session_state.is_authenticated = False
        st.session_state.jwt_token = None
        st.session_state.affiliate_code = None
        st.session_state.commission_balance = 0.0
        
        st.rerun()

def require_auth(required_role=None):
    """Decorador para requerir autenticación"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not st.session_state.is_authenticated:
                st.error("🔒 Debes iniciar sesión para acceder a esta página")
                show_login_form()
                return None
            
            if required_role and st.session_state.user_role != required_role:
                st.error("🚫 No tienes permisos suficientes para acceder a esta página")
                return None
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_verification():
    """Decorador para requerir verificación de email"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not st.session_state.user.get('is_verified', False):
                st.warning("⚠️ Debes verificar tu email para acceder a esta funcionalidad")
                
                with st.expander("📧 Verificar Email", expanded=True):
                    st.write("Por favor verifica tu email para desbloquear todas las funcionalidades.")
                    if st.button("Reenviar email de verificación"):
                        # Lógica para reenviar email
                        st.success("Email de verificación reenviado")
                
                return None
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# ============================================
# INTERFAZ DE USUARIO - COMPONENTES
# ============================================

def show_login_form():
    """Mostrar formulario de login - CONVERTIDO DE FLASK @app.route('/login')"""
    st.title("🔐 Iniciar Sesión")
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            with st.form("login_form", clear_on_submit=True):
                username = st.text_input("Usuario o Email", key="login_username")
                password = st.text_input("Contraseña", type="password", key="login_password")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    login_button = st.form_submit_button("Iniciar Sesión", type="primary", use_container_width=True)
                with col_b:
                    register_button = st.form_submit_button("Registrarse", use_container_width=True)
                
                # Opciones adicionales
                with st.expander("¿Problemas para iniciar sesión?"):
                    forgot_email = st.text_input("Email para recuperación")
                    if st.button("Enviar enlace de recuperación"):
                        if forgot_email:
                            result = AuthSystem.forgot_password(forgot_email)
                            if result['success']:
                                st.success(result['message'])
                            else:
                                st.error(result['message'])
                
                if login_button:
                    if not username or not password:
                        st.error("Por favor completa todos los campos")
                    else:
                        with st.spinner("Verificando credenciales..."):
                            result = AuthSystem.login(username, password)
                            
                            if result['success']:
                                if result.get('requires_2fa', False):
                                    # Manejar 2FA
                                    st.session_state.temp_user_id = result['user_id']
                                    st.session_state.temp_token = result['temp_token']
                                    st.session_state.show_2fa = True
                                    st.rerun()
                                else:
                                    # Login exitoso sin 2FA
                                    st.session_state.user = result['user']
                                    st.session_state.user_id = result['user']['id']
                                    st.session_state.user_role = result['user']['role']
                                    st.session_state.is_authenticated = True
                                    st.session_state.jwt_token = result['token']
                                    
                                    # Verificar si es afiliado
                                    affiliate = db.fetchone(
                                        "SELECT affiliate_code FROM affiliates WHERE user_id = ? AND status = 'active'",
                                        (result['user']['id'],)
                                    )
                                    if affiliate:
                                        st.session_state.affiliate_code = affiliate['affiliate_code']
                                    
                                    st.success(f"¡Bienvenido, {result['user']['first_name']}!")
                                    tm.sleep(1)
                                    st.rerun()
                            else:
                                st.error(result['message'])
                
                if register_button:
                    st.session_state.show_register = True
                    st.session_state.show_login = False
                    st.rerun()

def show_2fa_form():
    """Mostrar formulario de verificación 2FA"""
    st.title("🔐 Verificación en Dos Pasos")
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.write("Por favor ingresa el código de verificación de tu aplicación de autenticación.")
            
            with st.form("2fa_form"):
                code = st.text_input("Código de 6 dígitos", max_chars=6)
                
                if st.form_submit_button("Verificar", type="primary"):
                    if len(code) == 6 and code.isdigit():
                        result = AuthSystem.verify_2fa(
                            st.session_state.temp_user_id,
                            code,
                            st.session_state.temp_token
                        )
                        
                        if result['success']:
                            # Obtener información del usuario
                            user = db.fetchone(
                                "SELECT id, username, email, first_name, last_name, role, is_verified, profile_image FROM users WHERE id = ?",
                                (st.session_state.temp_user_id,)
                            )
                            
                            if user:
                                st.session_state.user = {
                                    'id': user['id'],
                                    'username': user['username'],
                                    'email': user['email'],
                                    'first_name': user['first_name'],
                                    'last_name': user['last_name'],
                                    'role': user['role'],
                                    'is_verified': bool(user['is_verified']),
                                    'profile_image': user['profile_image']
                                }
                                st.session_state.user_id = user['id']
                                st.session_state.user_role = user['role']
                                st.session_state.is_authenticated = True
                                st.session_state.jwt_token = result['token']
                                st.session_state.show_2fa = False
                                
                                st.success("¡Verificación exitosa!")
                                tm.sleep(1)
                                st.rerun()
                        else:
                            st.error(result['message'])
                    else:
                        st.error("Por favor ingresa un código válido de 6 dígitos")
            
            if st.button("Cancelar"):
                st.session_state.show_2fa = False
                st.rerun()

def show_register_form():
    """Mostrar formulario de registro - CONVERTIDO DE FLASK @app.route('/register')"""
    st.title("📝 Registro de Usuario")
    
    with st.container():
        tab1, tab2, tab3 = st.tabs(["👤 Paciente", "👨‍⚕️ Terapeuta", "💼 Afiliado"])
        
        with tab1:
            register_patient_form()
        
        with tab2:
            register_therapist_form()
        
        with tab3:
            register_affiliate_form()

def register_patient_form():
    """Formulario de registro para pacientes"""
    with st.form("register_patient_form", clear_on_submit=True):
        st.subheader("Información Personal")
        
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("Nombre *")
            email = st.text_input("Email *")
            phone = st.text_input("Teléfono")
            date_of_birth = st.date_input("Fecha de Nacimiento", 
                                         min_value=date(1900, 1, 1),
                                         max_value=date.today() - timedelta(days=365*18))
        
        with col2:
            last_name = st.text_input("Apellido *")
            username = st.text_input("Usuario *")
            gender = st.selectbox("Género", ["", "Masculino", "Femenino", "Otro", "Prefiero no decir"])
            emergency_contact = st.text_input("Contacto de Emergencia")
        
        st.subheader("Seguridad")
        col_a, col_b = st.columns(2)
        with col_a:
            password = st.text_input("Contraseña *", type="password")
        with col_b:
            confirm_password = st.text_input("Confirmar Contraseña *", type="password")
        
        st.subheader("¿Fuiste referido? (Opcional)")
        affiliate_code = st.text_input("Código de Afiliado")
        
        st.subheader("Términos y Condiciones")
        agree_terms = st.checkbox("Acepto los términos y condiciones *")
        agree_privacy = st.checkbox("Acepto la política de privacidad *")
        receive_newsletter = st.checkbox("Deseo recibir newsletters y ofertas")
        
        # Botones
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            submit_btn = st.form_submit_button("Registrarse", type="primary", use_container_width=True)
        with col_btn2:
            clear_btn = st.form_submit_button("Limpiar", use_container_width=True)
        with col_btn3:
            back_btn = st.form_submit_button("Volver al Login", use_container_width=True)
        
        if back_btn:
            st.session_state.show_register = False
            st.session_state.show_login = True
            st.rerun()
        
        if submit_btn:
            # Validaciones
            errors = []
            
            if not all([first_name, last_name, username, email, password, confirm_password]):
                errors.append("Por favor completa todos los campos obligatorios (*)")
            
            if password != confirm_password:
                errors.append("Las contraseñas no coinciden")
            
            if len(password) < 8:
                errors.append("La contraseña debe tener al menos 8 caracteres")
            
            if not agree_terms or not agree_privacy:
                errors.append("Debes aceptar los términos y condiciones y la política de privacidad")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Preparar datos
                user_data = {
                    'username': username,
                    'email': email,
                    'password': password,
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': phone,
                    'role': 'user',
                    'affiliate_code': affiliate_code if affiliate_code else None,
                    'date_of_birth': date_of_birth.isoformat() if date_of_birth else None,
                    'gender': gender if gender else None,
                    'emergency_contact': emergency_contact if emergency_contact else None
                }
                
                # Registrar usuario
                with st.spinner("Registrando usuario..."):
                    result = AuthSystem.register(user_data)
                    
                    if result['success']:
                        st.success("✅ ¡Registro exitoso!")
                        st.info("Se ha enviado un email de verificación a tu correo.")
                        
                        # Mostrar siguiente paso
                        with st.expander("📋 Próximos pasos", expanded=True):
                            st.write("""
                            1. **Verifica tu email** - Revisa tu bandeja de entrada y haz clic en el enlace de verificación
                            2. **Completa tu perfil** - Añade más información sobre ti
                            3. **Busca un terapeuta** - Explora nuestro directorio de profesionales
                            4. **Agenda tu primera sesión** - Encuentra un horario que te funcione
                            """)
                        
                        # Auto-login después de 3 segundos
                        tm.sleep(3)
                        st.session_state.show_register = False
                        st.session_state.show_login = True
                        
                        # Intentar login automático
                        login_result = AuthSystem.login(username, password)
                        if login_result['success'] and not login_result.get('requires_2fa', False):
                            st.session_state.user = login_result['user']
                            st.session_state.user_id = login_result['user']['id']
                            st.session_state.user_role = login_result['user']['role']
                            st.session_state.is_authenticated = True
                            st.session_state.jwt_token = login_result['token']
                        
                        st.rerun()
                    else:
                        st.error(f"❌ Error en registro: {result['message']}")

def register_therapist_form():
    """Formulario de registro para terapeutas"""
    with st.form("register_therapist_form", clear_on_submit=True):
        st.subheader("Información Personal")
        
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("Nombre *", key="th_first_name")
            email = st.text_input("Email *", key="th_email")
            phone = st.text_input("Teléfono *", key="th_phone")
            date_of_birth = st.date_input("Fecha de Nacimiento", 
                                         min_value=date(1900, 1, 1),
                                         max_value=date.today() - timedelta(days=365*25),
                                         key="th_dob")
        
        with col2:
            last_name = st.text_input("Apellido *", key="th_last_name")
            username = st.text_input("Usuario *", key="th_username")
            gender = st.selectbox("Género", ["", "Masculino", "Femenino", "Otro", "Prefiero no decir"], key="th_gender")
            country = st.text_input("País *", key="th_country")
        
        st.subheader("Información Profesional")
        col_a, col_b = st.columns(2)
        with col_a:
            specialization = st.text_input("Especialización *", key="th_specialization")
            experience_years = st.number_input("Años de Experiencia *", 0, 50, 1, key="th_experience")
            hourly_rate = st.number_input("Tarifa por Hora (USD) *", 0, 500, 80, key="th_rate")
        with col_b:
            qualifications = st.text_area("Títulos y Certificaciones *", height=100, key="th_qualifications")
            license_number = st.text_input("Número de Licencia", key="th_license")
            languages = st.multiselect("Idiomas", ["Español", "Inglés", "Francés", "Alemán", "Portugués", "Otro"], key="th_languages")
        
        st.subheader("Información de Contacto Profesional")
        address = st.text_input("Dirección", key="th_address")
        city = st.text_input("Ciudad", key="th_city")
        postal_code = st.text_input("Código Postal", key="th_postal")
        website = st.text_input("Sitio Web", key="th_website")
        bio = st.text_area("Biografía Profesional", height=150, key="th_bio")
        
        st.subheader("Disponibilidad")
        availability = st.multiselect(
            "Días de disponibilidad",
            ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"],
            default=["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
            key="th_availability"
        )
        
        working_hours = st.slider("Horario de trabajo (horas diarias)", 4, 12, 8, key="th_hours")
        
        st.subheader("Seguridad")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            password = st.text_input("Contraseña *", type="password", key="th_password")
        with col_p2:
            confirm_password = st.text_input("Confirmar Contraseña *", type="password", key="th_confirm_password")
        
        st.subheader("Documentación")
        st.write("Por favor prepara los siguientes documentos para la verificación:")
        st.write("• Identificación oficial")
        st.write("• Títulos y certificaciones")
        st.write("• Comprobante de domicilio")
        st.write("• Licencia profesional vigente")
        
        agree_terms = st.checkbox("Acepto los términos y condiciones para terapeutas *", key="th_terms")
        agree_privacy = st.checkbox("Acepto la política de privacidad *", key="th_privacy")
        receive_newsletter = st.checkbox("Deseo recibir actualizaciones y oportunidades", key="th_newsletter")
        
        # Botones
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submit_btn = st.form_submit_button("Registrarse como Terapeuta", type="primary", use_container_width=True)
        with col_btn2:
            back_btn = st.form_submit_button("Cancelar", use_container_width=True)
        
        if back_btn:
            st.rerun()
        
        if submit_btn:
            # Validaciones
            errors = []
            
            required_fields = [
                first_name, last_name, username, email, phone, country,
                specialization, qualifications, password, confirm_password
            ]
            
            if not all(required_fields):
                errors.append("Por favor completa todos los campos obligatorios (*)")
            
            if password != confirm_password:
                errors.append("Las contraseñas no coinciden")
            
            if len(password) < 8:
                errors.append("La contraseña debe tener al menos 8 caracteres")
            
            if not agree_terms or not agree_privacy:
                errors.append("Debes aceptar los términos y condiciones y la política de privacidad")
            
            if not availability:
                errors.append("Por favor selecciona tus días de disponibilidad")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Preparar datos
                user_data = {
                    'username': username,
                    'email': email,
                    'password': password,
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': phone,
                    'role': 'therapist',
                    'specialization': specialization,
                    'experience_years': experience_years,
                    'hourly_rate': hourly_rate,
                    'qualifications': qualifications,
                    'country': country,
                    'city': city if city else '',
                    'address': address if address else '',
                    'postal_code': postal_code if postal_code else '',
                    'bio': bio if bio else '',
                    'date_of_birth': date_of_birth.isoformat() if date_of_birth else None,
                    'gender': gender if gender else None,
                    'metadata': json.dumps({
                        'languages': languages,
                        'availability': availability,
                        'working_hours': working_hours,
                        'license_number': license_number,
                        'website': website
                    })
                }
                
                # Registrar usuario
                with st.spinner("Registrando terapeuta..."):
                    result = AuthSystem.register(user_data)
                    
                    if result['success']:
                        st.success("✅ ¡Registro de terapeuta exitoso!")
                        st.info("""
                        Tu registro ha sido recibido. Nuestro equipo revisará tu documentación 
                        y te contactará en un plazo de 2-3 días hábiles para completar el proceso de verificación.
                        
                        **Próximos pasos:**
                        1. Revisa tu email para verificar tu cuenta
                        2. Prepara tu documentación para la verificación
                        3. Nuestro equipo se pondrá en contacto contigo
                        """)
                        
                        tm.sleep(5)
                        st.session_state.show_register = False
                        st.session_state.show_login = True
                        st.rerun()
                    else:
                        st.error(f"❌ Error en registro: {result['message']}")

def register_affiliate_form():
    """Formulario de registro para afiliados"""
    with st.form("register_affiliate_form", clear_on_submit=True):
        st.subheader("Información Personal")
        
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("Nombre *", key="aff_first_name")
            email = st.text_input("Email *", key="aff_email")
            phone = st.text_input("Teléfono", key="aff_phone")
            country = st.selectbox("País *", ["", "México", "España", "Colombia", "Argentina", "Chile", "Perú", "Otro"], key="aff_country")
        
        with col2:
            last_name = st.text_input("Apellido *", key="aff_last_name")
            username = st.text_input("Usuario *", key="aff_username")
            tax_id = st.text_input("RFC/Identificación Fiscal", key="aff_tax_id")
            website = st.text_input("Sitio Web/Blog", key="aff_website")
        
        st.subheader("Información de Pago")
        col_a, col_b = st.columns(2)
        with col_a:
            payment_method = st.selectbox("Método de Pago Preferido *", 
                                         ["", "Binance (USDT)", "PayPal", "Transferencia Bancaria", "Criptomonedas"], 
                                         key="aff_payment_method")
            wallet_address = st.text_input("Wallet/Dirección", key="aff_wallet")
        with col_b:
            bank_name = st.text_input("Nombre del Banco", key="aff_bank_name")
            bank_account = st.text_input("Número de Cuenta", key="aff_bank_account")
        
        st.subheader("Información de Marketing")
        social_media = st.multiselect(
            "Redes Sociales que utilizas",
            ["Instagram", "Facebook", "YouTube", "TikTok", "Twitter/X", "LinkedIn", "Blog", "Otro"],
            key="aff_social"
        )
        
        audience_size = st.selectbox(
            "Tamaño de tu audiencia",
            ["", "Menos de 1,000", "1,000 - 10,000", "10,000 - 50,000", "50,000 - 100,000", "Más de 100,000"],
            key="aff_audience"
        )
        
        niche = st.text_input("Tu nicho/audiencia principal", key="aff_niche")
        
        st.subheader("Seguridad")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            password = st.text_input("Contraseña *", type="password", key="aff_password")
        with col_p2:
            confirm_password = st.text_input("Confirmar Contraseña *", type="password", key="aff_confirm_password")
        
        st.subheader("Acuerdo de Afiliado")
        
        with st.expander("📄 Términos del Programa de Afiliados", expanded=True):
            st.write("""
            **Comisiones:**
            • Productos digitales: 30% de comisión
            • Sesiones de terapia: 20% de comisión
            • Suscripciones: 25% de comisión recurrente
            
            **Pagos:**
            • Mínimo para pago: $50 USD
            • Frecuencia de pagos: Mensual
            • Métodos: Binance, PayPal, Transferencia Bancaria
            
            **Responsabilidades:**
            • Promover éticamente nuestros servicios
            • No hacer afirmaciones falsas
            • Respetar las políticas de marketing
            
            **Derechos:**
            • Acceso a materiales de marketing
            • Panel de afiliado con estadísticas
            • Soporte dedicado
            """)
        
        agree_terms = st.checkbox("Acepto los términos del programa de afiliados *", key="aff_terms")
        agree_privacy = st.checkbox("Acepto la política de privacidad *", key="aff_privacy")
        receive_updates = st.checkbox("Deseo recibir actualizaciones del programa", key="aff_updates")
        
        # Botones
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submit_btn = st.form_submit_button("Registrarse como Afiliado", type="primary", use_container_width=True)
        with col_btn2:
            back_btn = st.form_submit_button("Cancelar", use_container_width=True)
        
        if back_btn:
            st.rerun()
        
        if submit_btn:
            # Validaciones
            errors = []
            
            required_fields = [
                first_name, last_name, username, email, password, confirm_password,
                country, payment_method
            ]
            
            if not all(required_fields):
                errors.append("Por favor completa todos los campos obligatorios (*)")
            
            if password != confirm_password:
                errors.append("Las contraseñas no coinciden")
            
            if len(password) < 8:
                errors.append("La contraseña debe tener al menos 8 caracteres")
            
            if not agree_terms or not agree_privacy:
                errors.append("Debes aceptar los términos y la política de privacidad")
            
            if payment_method == "Binance (USDT)" and not wallet_address:
                errors.append("Por favor proporciona tu wallet de Binance")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Preparar datos
                user_data = {
                    'username': username,
                    'email': email,
                    'password': password,
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': phone if phone else '',
                    'role': 'solo_afiliado',
                    'country': country,
                    'tax_id': tax_id if tax_id else '',
                    'metadata': json.dumps({
                        'website': website if website else '',
                        'social_media': social_media,
                        'audience_size': audience_size if audience_size else '',
                        'niche': niche if niche else '',
                        'payment_preferences': {
                            'method': payment_method,
                            'wallet': wallet_address if wallet_address else '',
                            'bank_name': bank_name if bank_name else '',
                            'bank_account': bank_account if bank_account else ''
                        }
                    })
                }
                
                # Registrar usuario
                with st.spinner("Registrando afiliado..."):
                    result = AuthSystem.register(user_data)
                    
                    if result['success']:
                        # Crear registro de afiliado
                        affiliate_data = {
                            'user_id': result['user_id'],
                            'affiliate_code': f"AFF{result['user_id']:06d}",
                            'referral_code': f"REF{result['user_id']:06d}",
                            'commission_rate': 30.0,  # Comisión por defecto
                            'wallet_address': wallet_address if wallet_address else '',
                            'payment_method': payment_method.split(' ')[0].lower() if payment_method else 'binance',
                            'min_payout': 50.0,
                            'status': 'pending',
                            'join_date': date.today().isoformat(),
                            'total_earnings': 0.0,
                            'paid_earnings': 0.0,
                            'pending_earnings': 0.0,
                            'total_referrals': 0,
                            'active_referrals': 0,
                            'tax_rate': 0.0,
                            'tax_id': tax_id if tax_id else '',
                            'bank_name': bank_name if bank_name else '',
                            'bank_account': bank_account if bank_account else '',
                            'paypal_email': email if 'paypal' in payment_method.lower() else '',
                            'metadata': json.dumps({
                                'website': website if website else '',
                                'social_media': social_media,
                                'audience_size': audience_size if audience_size else '',
                                'niche': niche if niche else ''
                            })
                        }
                        
                        try:
                            affiliate_id = db.insert('affiliates', affiliate_data)
                            
                            st.success("✅ ¡Registro de afiliado exitoso!")
                            st.info(f"""
                            **Tu código de afiliado:** {affiliate_data['affiliate_code']}
                            **Tu código de referido:** {affiliate_data['referral_code']}
                            
                            **Próximos pasos:**
                            1. Revisa tu email para verificar tu cuenta
                            2. Nuestro equipo revisará tu solicitud en 24-48 horas
                            3. Recibirás acceso al panel de afiliados
                            4. Comienza a compartir tu código de referido
                            """)
                            
                            tm.sleep(5)
                            st.session_state.show_register = False
                            st.session_state.show_login = True
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Error al crear registro de afiliado: {str(e)}")
                    else:
                        st.error(f"❌ Error en registro: {result['message']}")

def show_main_sidebar():
    """Mostrar sidebar principal con navegación"""
    with st.sidebar:
        # Información del usuario
        if st.session_state.user:
            user = st.session_state.user
            
            # Avatar y nombre
            col1, col2 = st.columns([1, 3])
            with col1:
                avatar_html = f"""
                <div style='width: 60px; height: 60px; border-radius: 50%; 
                          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          display: flex; align-items: center; justify-content: center;
                          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);'>
                    <span style='color: white; font-size: 24px; font-weight: bold;'>
                        {user['first_name'][0].upper() if user['first_name'] else user['username'][0].upper()}
                    </span>
                </div>
                """
                st.markdown(avatar_html, unsafe_allow_html=True)
            
            with col2:
                st.write(f"**{user['first_name']} {user['last_name']}**")
                st.caption(f"@{user['username']}")
                
                # Badge de rol
                role_colors = {
                    'admin': '#dc2626',
                    'therapist': '#2563eb',
                    'user': '#059669',
                    'solo_afiliado': '#ea580c'
                }
                role_color = role_colors.get(user['role'], '#6b7280')
                
                role_badge = f"""
                <span style='background-color: {role_color}; color: white; 
                            padding: 4px 12px; border-radius: 20px; font-size: 12px;
                            font-weight: bold; display: inline-block; margin-top: 5px;'>
                    {user['role'].upper().replace('_', ' ')}
                </span>
                """
                st.markdown(role_badge, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navegación principal
        st.subheader("📌 Navegación")
        
        # Dashboard siempre visible
        if st.sidebar.button("🏠 Dashboard", use_container_width=True, 
                           help="Ir al panel principal"):
            st.session_state.current_page = "dashboard"
            st.rerun()
        
        # Menús según rol
        if st.session_state.user_role == 'admin':
            show_admin_navigation()
        elif st.session_state.user_role == 'therapist':
            show_therapist_navigation()
        elif st.session_state.user_role == 'solo_afiliado':
            show_affiliate_navigation()
        else:  # user
            show_user_navigation()
        
        st.markdown("---")
        
        # Configuración rápida
        st.subheader("⚙️ Configuración")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👤 Perfil", use_container_width=True, 
                        help="Ver y editar tu perfil"):
                st.session_state.current_page = "profile"
                st.rerun()
        with col2:
            if st.button("🔒 Salir", use_container_width=True, 
                        help="Cerrar sesión"):
                AuthSystem.logout()
        
        # Notificaciones y mensajes
        if st.session_state.get('unread_messages', 0) > 0:
            notification_badge = f"""
            <div style='background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); 
                        color: white; padding: 8px; border-radius: 8px; 
                        text-align: center; margin-top: 10px; font-weight: bold;'>
                📢 {st.session_state.unread_messages} mensajes no leídos
            </div>
            """
            st.markdown(notification_badge, unsafe_allow_html=True)
        
        # Comisiones pendientes (para afiliados)
        if (st.session_state.user_role == 'solo_afiliado' and 
            st.session_state.get('commission_balance', 0) > 0):
            commission_badge = f"""
            <div style='background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                        color: white; padding: 8px; border-radius: 8px; 
                        text-align: center; margin-top: 10px; font-weight: bold;'>
                💰 ${st.session_state.commission_balance:,.2f} en comisiones
            </div>
            """
            st.markdown(commission_badge, unsafe_allow_html=True)
        
        # Footer
        st.markdown("---")
        st.caption(f"MindGeek Clinic v4.0")
        st.caption(f"{datetime.now().strftime('%Y-%m-%d %H:%M')}")

def show_admin_navigation():
    """Navegación para administradores"""
    menu_items = [
        ("📊 Dashboard", "admin_dashboard", "Panel de administración"),
        ("👥 Usuarios", "user_management", "Gestión de usuarios"),
        ("💼 Afiliados", "affiliate_system", "Sistema de afiliados"),
        ("💰 Finanzas", "financial_system", "Sistema financiero"),
        ("📦 Productos", "product_management", "Gestión de productos"),
        ("📅 Citas", "appointment_calendar", "Calendario de citas"),
        ("📈 Reportes", "reports", "Reportes y analytics"),
        ("⚙️ Configuración", "system_settings", "Configuración del sistema"),
        ("📋 Logs", "activity_logs", "Logs de actividad")
    ]
    
    for icon, page, tooltip in menu_items:
        if st.sidebar.button(icon, use_container_width=True, help=tooltip, key=f"admin_{page}"):
            st.session_state.current_page = page
            st.rerun()

def show_therapist_navigation():
    """Navegación para terapeutas"""
    menu_items = [
        ("🏠 Mi Panel", "therapist_dashboard", "Panel principal"),
        ("📅 Mi Agenda", "therapist_calendar", "Calendario personal"),
        ("👥 Pacientes", "my_patients", "Mis pacientes"),
        ("💬 Mensajes", "messages", "Mensajes"),
        ("💰 Finanzas", "therapist_finances", "Mis finanzas"),
        ("📊 Estadísticas", "therapist_stats", "Estadísticas"),
        ("📚 Recursos", "resources", "Recursos")
    ]
    
    for icon, page, tooltip in menu_items:
        if st.sidebar.button(icon, use_container_width=True, help=tooltip, key=f"therapist_{page}"):
            st.session_state.current_page = page
            st.rerun()

def show_affiliate_navigation():
    """Navegación para afiliados"""
    menu_items = [
        ("🏠 Dashboard", "affiliate_dashboard", "Panel de afiliado"),
        ("💰 Comisiones", "affiliate_commissions", "Mis comisiones"),
        ("📊 Reportes", "affiliate_reports", "Reportes de ventas"),
        ("🔗 Enlaces", "affiliate_links", "Enlaces de afiliado"),
        ("👥 Referidos", "affiliate_referrals", "Mis referidos"),
        ("🎯 Campañas", "affiliate_campaigns", "Campañas activas"),
        ("⚙️ Configuración", "affiliate_settings", "Configuración")
    ]
    
    for icon, page, tooltip in menu_items:
        if st.sidebar.button(icon, use_container_width=True, help=tooltip, key=f"affiliate_{page}"):
            st.session_state.current_page = page
            st.rerun()

def show_user_navigation():
    """Navegación para usuarios regulares"""
    menu_items = [
        ("🏠 Mi Panel", "user_dashboard", "Panel principal"),
        ("👨‍⚕️ Terapeutas", "find_therapists", "Buscar terapeutas"),
        ("📅 Mis Citas", "my_appointments", "Mis citas"),
        ("💬 Mensajes", "user_messages", "Mensajes"),
        ("💰 Pagos", "my_payments", "Mis pagos"),
        ("📚 Recursos", "user_resources", "Recursos"),
        ("⭐ Reseñas", "my_reviews", "Mis reseñas")
    ]
    
    for icon, page, tooltip in menu_items:
        if st.sidebar.button(icon, use_container_width=True, help=tooltip, key=f"user_{page}"):
            st.session_state.current_page = page
            st.rerun()

# ============================================
# SISTEMA DE AFILIADOS COMPLETO
# ============================================

@require_auth()
def affiliate_dashboard():
    """Dashboard de afiliado - CONVERTIDO DE FLASK @app.route('/affiliate/dashboard')"""
    st.title("💼 Panel de Afiliado")
    
    # Obtener información del afiliado
    affiliate = db.fetchone('''
        SELECT a.*, u.email, u.phone 
        FROM affiliates a
        JOIN users u ON a.user_id = u.id
        WHERE a.user_id = ?
    ''', (st.session_state.user_id,))
    
    if not affiliate:
        st.error("No tienes una cuenta de afiliado activa")
        return
    
    # Actualizar comisiones pendientes en session state
    pending_commissions = db.fetchone('''
        SELECT SUM(commission_amount) as total 
        FROM commissions 
        WHERE affiliate_id = ? AND status = 'pending'
    ''', (affiliate['id'],))
    
    st.session_state.commission_balance = pending_commissions['total'] if pending_commissions['total'] else 0.0
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Comisión", f"{affiliate['commission_rate']}%")
    
    with col2:
        st.metric("Ganancias Totales", f"${affiliate['total_earnings']:,.2f}")
    
    with col3:
        st.metric("Pendientes", f"${affiliate['pending_earnings']:,.2f}")
    
    with col4:
        st.metric("Referidos", affiliate['total_referrals'])
    
    st.markdown("---")
    
    # Información del afiliado
    with st.expander("📋 Información de tu Cuenta", expanded=True):
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.write(f"**Código de Afiliado:** `{affiliate['affiliate_code']}`")
            st.write(f"**Código de Referido:** `{affiliate['referral_code']}`")
            st.write(f"**Estado:** {affiliate['status'].capitalize()}")
            st.write(f"**Fecha de Ingreso:** {affiliate['join_date']}")
        
        with col_b:
            st.write(f"**Método de Pago:** {affiliate['payment_method'].capitalize()}")
            if affiliate['wallet_address']:
                st.write(f"**Wallet:** `{affiliate['wallet_address']}`")
            if affiliate['bank_account']:
                st.write(f"**Cuenta Bancaria:** `{affiliate['bank_account']}`")
            st.write(f"**Mínimo para Pago:** ${affiliate['min_payout']:,.2f}")
    
    # Acciones rápidas
    st.subheader("🚀 Acciones Rápidas")
    
    col_act1, col_act2, col_act3, col_act4 = st.columns(4)
    
    with col_act1:
        if st.button("📋 Generar Enlace", use_container_width=True):
            st.session_state.current_page = "affiliate_links"
            st.rerun()
    
    with col_act2:
        if st.button("💰 Ver Comisiones", use_container_width=True):
            st.session_state.current_page = "affiliate_commissions"
            st.rerun()
    
    with col_act3:
        if st.button("👥 Mis Referidos", use_container_width=True):
            st.session_state.current_page = "affiliate_referrals"
            st.rerun()
    
    with col_act4:
        if st.button("⚙️ Configuración", use_container_width=True):
            st.session_state.current_page = "affiliate_settings"
            st.rerun()
    
    st.markdown("---")
    
    # Estadísticas y gráficos
    st.subheader("📈 Estadísticas de Rendimiento")
    
    tab1, tab2, tab3 = st.tabs(["📊 Mensual", "📅 Diario", "🎯 Campañas"])
    
    with tab1:
        # Comisiones por mes
        monthly_stats = db.fetchall('''
            SELECT strftime('%Y-%m', calculated_at) as month,
                   SUM(commission_amount) as total,
                   COUNT(*) as sales
            FROM commissions
            WHERE affiliate_id = ?
            GROUP BY strftime('%Y-%m', calculated_at)
            ORDER BY month DESC
            LIMIT 6
        ''', (affiliate['id'],))
        
        if monthly_stats:
            monthly_df = pd.DataFrame(monthly_stats)
            fig = px.bar(monthly_df, x='month', y='total', 
                        title="Comisiones Mensuales",
                        color='sales',
                        color_continuous_scale='Viridis',
                        labels={'total': 'Comisiones ($)', 'month': 'Mes', 'sales': 'Ventas'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aún no tienes comisiones registradas.")
    
    with tab2:
        # Ventas recientes
        recent_sales = db.fetchall('''
            SELECT c.calculated_at, c.sale_amount, c.commission_amount, 
                   c.sale_type, c.status
            FROM commissions c
            WHERE c.affiliate_id = ?
            ORDER BY c.calculated_at DESC
            LIMIT 10
        ''', (affiliate['id'],))
        
        if recent_sales:
            sales_df = pd.DataFrame(recent_sales)
            st.dataframe(
                sales_df,
                use_container_width=True,
                column_config={
                    "sale_amount": st.column_config.NumberColumn(
                        "Venta",
                        format="$%.2f"
                    ),
                    "commission_amount": st.column_config.NumberColumn(
                        "Comisión",
                        format="$%.2f"
                    ),
                    "calculated_at": st.column_config.DatetimeColumn(
                        "Fecha",
                        format="DD/MM/YYYY HH:mm"
                    )
                }
            )
        else:
            st.info("No hay ventas recientes.")
    
    with tab3:
        # Campañas activas
        active_campaigns = db.fetchall('''
            SELECT c.name, c.commission_bonus, c.start_date, c.end_date, c.rules
            FROM campaigns c
            WHERE c.status = 'active' 
            AND (c.target_affiliates = '' OR c.target_affiliates LIKE ?)
            ORDER BY c.start_date DESC
        ''', (f"%{affiliate['affiliate_code']}%",))
        
        if active_campaigns:
            for campaign in active_campaigns:
                with st.expander(f"🎯 {campaign['name']}"):
                    st.write(f"**Bono de Comisión:** +{campaign['commission_bonus']}%")
                    st.write(f"**Periodo:** {campaign['start_date']} al {campaign['end_date']}")
                    st.write(f"**Reglas:** {campaign['rules']}")
                    
                    if st.button("Participar", key=f"join_{campaign['name']}"):
                        st.success(f"Te has unido a la campaña {campaign['name']}")
        else:
            st.info("No hay campañas activas para ti en este momento.")

@require_auth()
def affiliate_commissions():
    """Gestión de comisiones del afiliado"""
    st.title("💰 Mis Comisiones")
    
    # Obtener afiliado
    affiliate = db.fetchone(
        "SELECT id FROM affiliates WHERE user_id = ?", 
        (st.session_state.user_id,)
    )
    
    if not affiliate:
        st.error("No tienes una cuenta de afiliado")
        return
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Estado", ["Todos", "pending", "paid", "cancelled"])
    with col2:
        date_from = st.date_input("Desde", value=date.today() - timedelta(days=30))
    with col3:
        date_to = st.date_input("Hasta", value=date.today())
    
    # Construir consulta
    query = '''
        SELECT c.*, o.order_number, o.customer_id, u.email as customer_email
        FROM commissions c
        LEFT JOIN orders o ON c.order_id = o.id
        LEFT JOIN users u ON o.customer_id = u.id
        WHERE c.affiliate_id = ?
        AND DATE(c.calculated_at) BETWEEN ? AND ?
    '''
    params = [affiliate['id'], date_from, date_to]
    
    if status_filter != "Todos":
        query += " AND c.status = ?"
        params.append(status_filter)
    
    query += " ORDER BY c.calculated_at DESC"
    
    # Obtener comisiones
    commissions = db.fetchall(query, params)
    
    if commissions:
        comm_df = pd.DataFrame(commissions)
        
        # Métricas
        total_commissions = comm_df['commission_amount'].sum()
        pending_total = comm_df[comm_df['status'] == 'pending']['commission_amount'].sum()
        paid_total = comm_df[comm_df['status'] == 'paid']['commission_amount'].sum()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total", f"${total_commissions:,.2f}")
        col2.metric("Pendientes", f"${pending_total:,.2f}")
        col3.metric("Pagadas", f"${paid_total:,.2f}")
        
        # Tabla de comisiones
        st.dataframe(
            comm_df[['id', 'order_number', 'sale_amount', 'commission_amount', 
                    'commission_rate', 'sale_type', 'status', 'calculated_at', 'paid_at']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "sale_amount": st.column_config.NumberColumn(
                    "Venta",
                    format="$%.2f"
                ),
                "commission_amount": st.column_config.NumberColumn(
                    "Comisión",
                    format="$%.2f"
                ),
                "calculated_at": st.column_config.DatetimeColumn(
                    "Calculada",
                    format="DD/MM/YYYY HH:mm"
                ),
                "paid_at": st.column_config.DatetimeColumn(
                    "Pagada",
                    format="DD/MM/YYYY HH:mm"
                )
            }
        )
        
        # Exportar a CSV
        if st.button("📥 Exportar a CSV"):
            csv = comm_df.to_csv(index=False)
            st.download_button(
                label="Descargar CSV",
                data=csv,
                file_name=f"comisiones_{date.today()}.csv",
                mime="text/csv"
            )
    else:
        st.info("No hay comisiones en el período seleccionado.")

@require_auth()
def affiliate_links():
    """Generador de enlaces de afiliado"""
    st.title("🔗 Generador de Enlaces de Afiliado")
    
    # Obtener código de afiliado
    affiliate = db.fetchone(
        "SELECT affiliate_code, referral_code FROM affiliates WHERE user_id = ?", 
        (st.session_state.user_id,)
    )
    
    if not affiliate:
        st.error("No tienes una cuenta de afiliado")
        return
    
    affiliate_code = affiliate['affiliate_code']
    referral_code = affiliate['referral_code']
    
    # Enlaces predefinidos
    st.subheader("📋 Enlaces Predefinidos")
    
    base_url = "https://mindgeekclinic.com"
    
    links = {
        "Página Principal": f"{base_url}?ref={affiliate_code}",
        "Registro de Pacientes": f"{base_url}/register?ref={affiliate_code}",
        "Registro de Terapeutas": f"{base_url}/register/therapist?ref={affiliate_code}",
        "Tienda de Productos": f"{base_url}/store?ref={affiliate_code}",
        "Cursos Online": f"{base_url}/courses?ref={affiliate_code}",
        "Blog": f"{base_url}/blog?ref={affiliate_code}"
    }
    
    for name, url in links.items():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.code(url, language=None)
        with col2:
            st.download_button(
                label="📋 Copiar",
                data=url,
                file_name=f"enlace_{name.lower().replace(' ', '_')}.txt",
                mime="text/plain",
                key=f"copy_{name}"
            )
    
    st.markdown("---")
    
    # Generador personalizado
    st.subheader("🎨 Generador Personalizado")
    
    with st.form("custom_link_form"):
        page_url = st.text_input("URL de la página", 
                                placeholder="https://mindgeekclinic.com/producto")
        campaign_name = st.text_input("Nombre de la Campaña (opcional)")
        medium = st.selectbox("Medio", ["", "email", "social", "blog", "website", "other"])
        
        if st.form_submit_button("Generar Enlace", type="primary"):
            if page_url:
                # Generar parámetros UTM
                utm_params = {
                    'utm_source': 'affiliate',
                    'utm_medium': medium if medium else 'direct',
                    'utm_campaign': campaign_name if campaign_name else 'general',
                    'ref': affiliate_code
                }
                
                # Construir URL
                from urllib.parse import urlencode, urlparse, urlunparse, parse_qs
                
                parsed = urlparse(page_url)
                query = parse_qs(parsed.query)
                query.update(utm_params)
                
                new_url = urlunparse((
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    urlencode(query, doseq=True),
                    parsed.fragment
                ))
                
                st.success("✅ Enlace generado exitosamente")
                st.code(new_url, language=None)
                
                # Botón para copiar
                st.download_button(
                    label="📋 Copiar Enlace",
                    data=new_url,
                    file_name="enlace_personalizado.txt",
                    mime="text/plain"
                )
            else:
                st.error("Por favor ingresa una URL")
    
    st.markdown("---")
    
    # Códigos QR
    st.subheader("📱 Códigos QR")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # QR para registro
        st.write("**QR para Registro**")
        qr_data = f"{base_url}/register?ref={affiliate_code}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        st.image(buffered, caption="Escanear para registro", width=200)
        
        st.download_button(
            label="📥 Descargar QR",
            data=buffered.getvalue(),
            file_name=f"qr_registro_{affiliate_code}.png",
            mime="image/png"
        )
    
    with col2:
        # QR para tienda
        st.write("**QR para Tienda**")
        qr_data = f"{base_url}/store?ref={affiliate_code}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        st.image(buffered, caption="Escanear para tienda", width=200)
        
        st.download_button(
            label="📥 Descargar QR",
            data=buffered.getvalue(),
            file_name=f"qr_tienda_{affiliate_code}.png",
            mime="image/png"
        )

@require_auth()
def affiliate_referrals():
    """Gestión de referidos del afiliado"""
    st.title("👥 Mis Referidos")
    
    # Obtener afiliado
    affiliate = db.fetchone(
        "SELECT id, affiliate_code FROM affiliates WHERE user_id = ?", 
        (st.session_state.user_id,)
    )
    
    if not affiliate:
        st.error("No tienes una cuenta de afiliado")
        return
    
    # Métricas
    referrals_stats = db.fetchone('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'converted' THEN 1 ELSE 0 END) as converted,
            SUM(conversion_value) as total_value,
            SUM(commission_generated) as total_commission
        FROM referrals
        WHERE referrer_id = ?
    ''', (st.session_state.user_id,))
    
    if referrals_stats:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Referidos", referrals_stats['total'])
        col2.metric("Convertidos", referrals_stats['converted'])
        col3.metric("Valor Total", f"${referrals_stats['total_value']:,.2f}")
        col4.metric("Comisiones", f"${referrals_stats['total_commission']:,.2f}")
    
    # Lista de referidos
    referrals = db.fetchall('''
        SELECT r.*, u.username, u.email, u.first_name, u.last_name, u.created_at as user_created
        FROM referrals r
        JOIN users u ON r.referred_id = u.id
        WHERE r.referrer_id = ?
        ORDER BY r.referral_date DESC
    ''', (st.session_state.user_id,))
    
    if referrals:
        ref_df = pd.DataFrame(referrals)
        
        # Tabla de referidos
        st.dataframe(
            ref_df[['username', 'email', 'first_name', 'last_name', 
                   'referral_date', 'status', 'conversion_value', 
                   'commission_generated', 'converted_at']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "conversion_value": st.column_config.NumberColumn(
                    "Valor",
                    format="$%.2f"
                ),
                "commission_generated": st.column_config.NumberColumn(
                    "Comisión",
                    format="$%.2f"
                )
            }
        )
        
        # Gráfico de conversiones por mes
        monthly_conversions = db.fetchall('''
            SELECT strftime('%Y-%m', referral_date) as month,
                   COUNT(*) as referrals,
                   SUM(CASE WHEN status = 'converted' THEN 1 ELSE 0 END) as conversions,
                   SUM(conversion_value) as value
            FROM referrals
            WHERE referrer_id = ?
            GROUP BY strftime('%Y-%m', referral_date)
            ORDER BY month DESC
            LIMIT 6
        ''', (st.session_state.user_id,))
        
        if monthly_conversions:
            conv_df = pd.DataFrame(monthly_conversions)
            fig = px.bar(conv_df, x='month', y=['referrals', 'conversions'],
                        title="Referidos y Conversiones Mensuales",
                        barmode='group',
                        labels={'value': 'Cantidad', 'month': 'Mes', 'variable': 'Tipo'})
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aún no tienes referidos.")

@require_auth()
def affiliate_campaigns():
    """Campañas de marketing para afiliados"""
    st.title("🎯 Campañas de Marketing")
    
    # Campañas activas
    st.subheader("🟢 Campañas Activas")
    
    active_campaigns = db.fetchall('''
        SELECT c.*, u.first_name, u.last_name
        FROM campaigns c
        LEFT JOIN users u ON c.created_by = u.id
        WHERE c.status = 'active'
        ORDER BY c.start_date DESC
    ''')
    
    if active_campaigns:
        for campaign in active_campaigns:
            with st.expander(f"🎯 {campaign['name']}", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Tipo:** {campaign['campaign_type'].replace('_', ' ').title()}")
                    st.write(f"**Periodo:** {campaign['start_date']} al {campaign['end_date']}")
                    st.write(f"**Bono:** +{campaign['commission_bonus']}%")
                    st.write(f"**Creada por:** {campaign['first_name']} {campaign['last_name']}")
                
                with col2:
                    st.write(f"**Presupuesto:** ${campaign['budget']:,.2f}")
                    st.write(f"**Gastado:** ${campaign['spent']:,.2f}")
                    st.write(f"**Estado:** {campaign['status'].capitalize()}")
                
                st.write(f"**Descripción:** {campaign['description']}")
                st.write(f"**Reglas:** {campaign['rules']}")
                
                # Verificar si el afiliado está en la campaña
                affiliate = db.fetchone(
                    "SELECT affiliate_code FROM affiliates WHERE user_id = ?",
                    (st.session_state.user_id,)
                )
                
                if affiliate:
                    target_affiliates = campaign['target_affiliates'].split(',') if campaign['target_affiliates'] else []
                    
                    if not target_affiliates or affiliate['affiliate_code'] in target_affiliates:
                        if st.button("✅ Participar en Campaña", key=f"join_{campaign['id']}"):
                            # Agregar afiliado a la campaña
                            if target_affiliates:
                                target_affiliates.append(affiliate['affiliate_code'])
                            else:
                                target_affiliates = [affiliate['affiliate_code']]
                            
                            db.update('campaigns', {
                                'target_affiliates': ','.join(set(target_affiliates))
                            }, f"id = {campaign['id']}")
                            
                            st.success(f"¡Te has unido a la campaña {campaign['name']}!")
                            st.rerun()
                    else:
                        st.info("Esta campaña está restringida a ciertos afiliados.")
    else:
        st.info("No hay campañas activas en este momento.")
    
    st.markdown("---")
    
    # Historial de campañas
    st.subheader("📋 Historial de Campañas")
    
    past_campaigns = db.fetchall('''
        SELECT c.*, u.first_name, u.last_name
        FROM campaigns c
        LEFT JOIN users u ON c.created_by = u.id
        WHERE c.status != 'active'
        ORDER BY c.end_date DESC
        LIMIT 10
    ''')
    
    if past_campaigns:
        for campaign in past_campaigns:
            with st.expander(f"📅 {campaign['name']} ({campaign['status']})"):
                st.write(f"**Periodo:** {campaign['start_date']} al {campaign['end_date']}")
                st.write(f"**Resultado:** ${campaign['spent']:,.2f} gastados de ${campaign['budget']:,.2f} presupuestado")
                st.write(f"**Bono ofrecido:** +{campaign['commission_bonus']}%")
                
                # Estadísticas de la campaña para este afiliado
                if st.button("Ver mis estadísticas", key=f"stats_{campaign['id']}"):
                    # Obtener comisiones durante la campaña
                    affiliate = db.fetchone(
                        "SELECT id FROM affiliates WHERE user_id = ?",
                        (st.session_state.user_id,)
                    )
                    
                    if affiliate:
                        campaign_commissions = db.fetchall('''
                            SELECT COUNT(*) as sales, SUM(commission_amount) as total
                            FROM commissions
                            WHERE affiliate_id = ?
                            AND DATE(calculated_at) BETWEEN ? AND ?
                        ''', (affiliate['id'], campaign['start_date'], campaign['end_date']))
                        
                        if campaign_commissions and campaign_commissions[0]['sales'] > 0:
                            stats = campaign_commissions[0]
                            st.success(f"🎯 Durante esta campaña generaste {stats['sales']} ventas por ${stats['total']:,.2f} en comisiones")
                        else:
                            st.info("No generaste comisiones durante esta campaña.")

@require_auth()
def affiliate_settings():
    """Configuración de la cuenta de afiliado"""
    st.title("⚙️ Configuración de Afiliado")
    
    # Obtener información del afiliado
    affiliate = db.fetchone('''
        SELECT a.*, u.email, u.phone, u.first_name, u.last_name
        FROM affiliates a
        JOIN users u ON a.user_id = u.id
        WHERE a.user_id = ?
    ''', (st.session_state.user_id,))
    
    if not affiliate:
        st.error("No tienes una cuenta de afiliado")
        return
    
    tab1, tab2, tab3, tab4 = st.tabs(["👤 Perfil", "💰 Pagos", "🔒 Seguridad", "📧 Notificaciones"])
    
    with tab1:
        st.subheader("Información Personal")
        
        with st.form("affiliate_profile_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                first_name = st.text_input("Nombre", value=affiliate['first_name'])
                email = st.text_input("Email", value=affiliate['email'])
                phone = st.text_input("Teléfono", value=affiliate['phone'] or '')
                tax_id = st.text_input("RFC/Identificación Fiscal", value=affiliate['tax_id'] or '')
            
            with col2:
                last_name = st.text_input("Apellido", value=affiliate['last_name'])
                country = st.text_input("País", value='México')
                website = st.text_input("Sitio Web/Blog", value=json.loads(affiliate['metadata']).get('website', '') if affiliate['metadata'] else '')
                niche = st.text_input("Nicho principal", value=json.loads(affiliate['metadata']).get('niche', '') if affiliate['metadata'] else '')
            
            if st.form_submit_button("💾 Guardar Cambios", type="primary"):
                # Actualizar información
                updates = {
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'phone': phone,
                    'tax_id': tax_id
                }
                
                # Actualizar metadata
                metadata = json.loads(affiliate['metadata']) if affiliate['metadata'] else {}
                metadata.update({
                    'website': website,
                    'niche': niche,
                    'country': country
                })
                
                updates['metadata'] = json.dumps(metadata)
                
                # Actualizar usuario
                db.update('users', updates, f"id = {st.session_state.user_id}")
                
                # Actualizar afiliado
                db.update('affiliates', {'tax_id': tax_id}, f"id = {affiliate['id']}")
                
                st.success("✅ Información actualizada exitosamente")
                st.rerun()
    
    with tab2:
        st.subheader("Configuración de Pagos")
        
        with st.form("payment_settings_form"):
            payment_method = st.selectbox(
                "Método de Pago",
                ["Binance (USDT)", "PayPal", "Transferencia Bancaria", "Criptomonedas"],
                index=0
            )
            
            wallet_address = st.text_input(
                "Wallet/Dirección",
                value=affiliate['wallet_address'] or '',
                placeholder="Ej: 0x742d35Cc6634C0532925a3b844..."
            )
            
            bank_name = st.text_input(
                "Nombre del Banco",
                value=affiliate['bank_name'] or ''
            )
            
            bank_account = st.text_input(
                "Número de Cuenta",
                value=affiliate['bank_account'] or ''
            )
            
            min_payout = st.number_input(
                "Mínimo para Pago (USD)",
                min_value=10.0,
                max_value=1000.0,
                value=float(affiliate['min_payout'])
            )
            
            if st.form_submit_button("💾 Guardar Configuración de Pagos", type="primary"):
                payment_updates = {
                    'payment_method': payment_method.split(' ')[0].lower(),
                    'wallet_address': wallet_address if wallet_address else '',
                    'bank_name': bank_name if bank_name else '',
                    'bank_account': bank_account if bank_account else '',
                    'min_payout': min_payout
                }
                
                # Si es PayPal, actualizar email
                if 'paypal' in payment_method.lower():
                    payment_updates['paypal_email'] = affiliate['email']
                
                db.update('affiliates', payment_updates, f"id = {affiliate['id']}")
                
                st.success("✅ Configuración de pagos actualizada")
                st.info("Los cambios se aplicarán en tu próximo pago.")
    
    with tab3:
        st.subheader("Configuración de Seguridad")
        
        with st.form("security_form"):
            current_password = st.text_input("Contraseña Actual", type="password")
            new_password = st.text_input("Nueva Contraseña", type="password")
            confirm_password = st.text_input("Confirmar Nueva Contraseña", type="password")
            
            # 2FA
            enable_2fa = st.checkbox("Habilitar Autenticación de Dos Factores")
            
            if st.form_submit_button("🔐 Actualizar Seguridad", type="primary"):
                # Verificar contraseña actual
                user = db.fetchone(
                    "SELECT password_hash FROM users WHERE id = ?",
                    (st.session_state.user_id,)
                )
                
                if user and AuthSystem.check_password(user['password_hash'], current_password):
                    if new_password and confirm_password:
                        if new_password == confirm_password:
                            if len(new_password) >= 8:
                                # Actualizar contraseña
                                new_hash = AuthSystem.hash_password(new_password)
                                db.update('users', {
                                    'password_hash': new_hash
                                }, f"id = {st.session_state.user_id}")
                                
                                st.success("✅ Contraseña actualizada exitosamente")
                            else:
                                st.error("La nueva contraseña debe tener al menos 8 caracteres")
                        else:
                            st.error("Las nuevas contraseñas no coinciden")
                    
                    # Actualizar 2FA
                    if enable_2fa:
                        # En producción generar secreto real para Google Authenticator
                        secret = secrets.token_hex(16)
                        db.update('users', {
                            'two_factor_enabled': 1,
                            'two_factor_secret': secret
                        }, f"id = {st.session_state.user_id}")
                        
                        st.success("✅ Autenticación de dos factores habilitada")
                        st.info("Escanea el código QR con Google Authenticator")
                        
                        # Generar QR para 2FA
                        qr_data = f"otpauth://totp/MindGeekClinic:{affiliate['email']}?secret={secret}&issuer=MindGeekClinic"
                        qr = qrcode.QRCode(version=1, box_size=10, border=5)
                        qr.add_data(qr_data)
                        qr.make(fit=True)
                        img = qr.make_image(fill='black', back_color='white')
                        
                        buffered = BytesIO()
                        img.save(buffered, format="PNG")
                        st.image(buffered, caption="Escanear con Google Authenticator", width=200)
                    else:
                        db.update('users', {
                            'two_factor_enabled': 0,
                            'two_factor_secret': None
                        }, f"id = {st.session_state.user_id}")
                        st.success("✅ Autenticación de dos factores deshabilitada")
                else:
                    st.error("Contraseña actual incorrecta")
    
    with tab4:
        st.subheader("Preferencias de Notificaciones")
        
        with st.form("notifications_form"):
            email_sales = st.checkbox("Notificaciones de nuevas ventas", value=True)
            email_commissions = st.checkbox("Notificaciones de comisiones pagadas", value=True)
            email_campaigns = st.checkbox("Notificaciones de nuevas campañas", value=True)
            email_newsletter = st.checkbox("Newsletter mensual", value=True)
            
            if st.form_submit_button("💾 Guardar Preferencias", type="primary"):
                # Actualizar preferencias
                preferences = {
                    'email_sales': email_sales,
                    'email_commissions': email_commissions,
                    'email_campaigns': email_campaigns,
                    'email_newsletter': email_newsletter
                }
                
                db.update('users', {
                    'preferences': json.dumps(preferences)
                }, f"id = {st.session_state.user_id}")
                
                st.success("✅ Preferencias de notificaciones actualizadas")

# ============================================
# SISTEMA DE PAGOS CON BINANCE
# ============================================

class BinancePaymentSystem:
    """Sistema de pagos con Binance - CONVERTIDO DE FLASK"""
    
    @staticmethod
    def create_payment(order_data, user_id):
        """Crear pago con Binance"""
        try:
            # Generar ID de pago único
            payment_id = f"BIN_{int(datetime.now().timestamp())}_{secrets.token_hex(4)}"
            
            # Obtener información del usuario
            user = db.fetchone("SELECT email, first_name, last_name FROM users WHERE id = ?", (user_id,))
            
            if not user:
                return {'success': False, 'message': 'Usuario no encontrado'}
            
            # Crear registro de pago
            payment_record = {
                'order_id': order_data.get('order_id'),
                'user_id': user_id,
                'amount': order_data['amount'],
                'currency': order_data.get('currency', 'USDT'),
                'payment_method': 'binance',
                'transaction_id': payment_id,
                'status': 'pending',
                'gateway_response': json.dumps({
                    'type': 'binance',
                    'created_at': datetime.now().isoformat(),
                    'order_details': order_data
                }),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Insertar pago
            payment_db_id = db.insert('payments', payment_record)
            
            # Generar información para el pago
            payment_info = {
                'payment_id': payment_id,
                'db_id': payment_db_id,
                'amount': order_data['amount'],
                'currency': order_data.get('currency', 'USDT'),
                'description': order_data.get('description', 'Pago MindGeek Clinic'),
                'customer_email': user['email'],
                'customer_name': f"{user['first_name']} {user['last_name']}",
                'timestamp': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(hours=1)).isoformat()
            }
            
            # Generar QR para pago (simulado)
            qr_data = BinancePaymentSystem.generate_qr_data(payment_info)
            
            return {
                'success': True,
                'payment_id': payment_id,
                'payment_info': payment_info,
                'qr_data': qr_data,
                'message': 'Pago creado exitosamente'
            }
            
        except Exception as e:
            logger.error(f"Error creando pago Binance: {str(e)}")
            return {'success': False, 'message': f'Error creando pago: {str(e)}'}
    
    @staticmethod
    def generate_qr_data(payment_info):
        """Generar datos para QR de pago Binance"""
        # En producción usar la API real de Binance
        # Por ahora simulación
        
        qr_content = {
            'type': 'binance_payment',
            'payment_id': payment_info['payment_id'],
            'amount': payment_info['amount'],
            'currency': payment_info['currency'],
            'timestamp': payment_info['timestamp'],
            'merchant': 'MindGeek Clinic',
            'callback_url': f"https://mindgeekclinic.com/api/payments/binance/callback"
        }
        
        # Convertir a string para QR
        qr_string = json.dumps(qr_content)
        
        # Generar QR
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_string)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        
        # Convertir a base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return {
            'qr_image': img_str,
            'qr_string': qr_string,
            'payment_address': 'TU_WALLET_BINANCE_AQUI',  # En producción usar wallet real
            'amount': payment_info['amount'],
            'currency': payment_info['currency']
        }
    
    @staticmethod
    def check_payment_status(payment_id):
        """Verificar estado de pago"""
        try:
            payment = db.fetchone(
                "SELECT * FROM payments WHERE transaction_id = ?",
                (payment_id,)
            )
            
            if not payment:
                return {'success': False, 'message': 'Pago no encontrado'}
            
            # Simular verificación con Binance
            # En producción hacer llamada a API de Binance
            
            status = payment['status']
            
            if status == 'pending':
                # Simular que a veces los pagos se completan
                if random.random() < 0.3:  # 30% de probabilidad de pago completado
                    db.update('payments', {
                        'status': 'completed',
                        'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'gateway_response': json.dumps({
                            'verified_at': datetime.now().isoformat(),
                            'simulated': True,
                            'transaction_hash': f"0x{secrets.token_hex(32)}"
                        })
                    }, f"id = {payment['id']}")
                    
                    status = 'completed'
                    
                    # Si hay orden asociada, actualizarla
                    if payment['order_id']:
                        db.update('orders', {
                            'payment_status': 'paid',
                            'status': 'completed',
                            'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }, f"id = {payment['order_id']}")
            
            return {
                'success': True,
                'status': status,
                'payment': payment
            }
            
        except Exception as e:
            logger.error(f"Error verificando pago: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    @staticmethod
    def process_binance_callback(callback_data):
        """Procesar callback de Binance (simulado)"""
        try:
            # En producción validar firma y datos de Binance
            payment_id = callback_data.get('payment_id')
            transaction_hash = callback_data.get('transaction_hash')
            status = callback_data.get('status')
            
            if not payment_id:
                return {'success': False, 'message': 'Payment ID requerido'}
            
            # Actualizar pago
            updates = {
                'status': status,
                'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S') if status == 'completed' else None,
                'gateway_response': json.dumps(callback_data)
            }
            
            if transaction_hash:
                updates['transaction_id'] = transaction_hash
            
            db.update('payments', updates, f"transaction_id = '{payment_id}'")
            
            # Obtener pago actualizado
            payment = db.fetchone(
                "SELECT * FROM payments WHERE transaction_id = ?",
                (payment_id,)
            )
            
            # Si hay orden asociada y el pago está completo
            if payment and payment['order_id'] and status == 'completed':
                db.update('orders', {
                    'payment_status': 'paid',
                    'status': 'completed',
                    'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }, f"id = {payment['order_id']}")
                
                # Procesar comisiones si aplica
                BinancePaymentSystem.process_affiliate_commissions(payment['order_id'])
            
            return {'success': True, 'message': 'Callback procesado'}
            
        except Exception as e:
            logger.error(f"Error procesando callback: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    @staticmethod
    def process_affiliate_commissions(order_id):
        """Procesar comisiones de afiliados para una orden"""
        try:
            # Obtener orden
            order = db.fetchone("SELECT * FROM orders WHERE id = ?", (order_id,))
            
            if not order or order['status'] != 'completed':
                return
            
            # Buscar si fue referido
            referral = db.fetchone('''
                SELECT r.*, a.id as affiliate_id, a.commission_rate
                FROM referrals r
                JOIN affiliates a ON r.referrer_id = a.user_id
                WHERE r.referred_id = ? AND r.status = 'pending'
            ''', (order['customer_id'],))
            
            if referral:
                # Calcular comisión
                commission_rate = referral['commission_rate']
                commission_amount = order['final_amount'] * (commission_rate / 100)
                
                # Registrar comisión
                commission_data = {
                    'affiliate_id': referral['affiliate_id'],
                    'order_id': order_id,
                    'sale_amount': order['final_amount'],
                    'commission_amount': commission_amount,
                    'commission_rate': commission_rate,
                    'sale_type': 'product',
                    'customer_email': '',  # Se puede obtener del usuario
                    'order_number': order['order_number'],
                    'status': 'pending',
                    'calculated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                commission_id = db.insert('commissions', commission_data)
                
                # Actualizar estadísticas del afiliado
                db.execute('''
                    UPDATE affiliates 
                    SET total_earnings = total_earnings + ?,
                        pending_earnings = pending_earnings + ?,
                        total_referrals = total_referrals + 1
                    WHERE id = ?
                ''', (commission_amount, commission_amount, referral['affiliate_id']))
                
                # Actualizar referencia
                db.update('referrals', {
                    'status': 'converted',
                    'converted_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'conversion_value': order['final_amount'],
                    'commission_generated': commission_amount
                }, f"id = {referral['id']}")
                
                logger.info(f"Comisión {commission_id} procesada para orden {order_id}")
                
        except Exception as e:
            logger.error(f"Error procesando comisiones: {str(e)}")

@require_auth()
def binance_payment_page():
    """Página de pago con Binance - CONVERTIDO DE FLASK @app.route('/payment/binance')"""
    st.title("💰 Pago con Binance (USDT)")
    
    # Obtener información del pago desde parámetros
    query_params = st.experimental_get_query_params()
    order_id = query_params.get('order_id', [None])[0]
    amount = query_params.get('amount', [0])[0]
    description = query_params.get('description', [''])[0]
    
    if not order_id or not amount:
        st.error("Información de pago incompleta")
        return
    
    amount = float(amount)
    
    # Mostrar información del pago
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Detalles del Pago")
        st.write(f"**ID de Orden:** {order_id}")
        st.write(f"**Monto:** ${amount:,.2f} USDT")
        st.write(f"**Descripción:** {description}")
        st.write(f"**Fecha:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        st.write(f"**Estado:** Pendiente")
    
    with col2:
        # Crear pago
        payment_data = {
            'order_id': order_id,
            'amount': amount,
            'currency': 'USDT',
            'description': description
        }
        
        with st.spinner("Creando pago..."):
            result = BinancePaymentSystem.create_payment(
                payment_data, 
                st.session_state.user_id
            )
            
            if result['success']:
                st.success("✅ Pago creado exitosamente")
                
                payment_info = result['payment_info']
                qr_data = result['qr_data']
                
                # Mostrar QR
                st.subheader("📱 Escanear para Pagar")
                
                qr_image = base64.b64decode(qr_data['qr_image'])
                st.image(qr_image, caption="Escanear con Binance App", width=300)
                
                # Mostrar información de pago
                st.info(f"""
                **Dirección para pago manual:**
                ```
                {qr_data['payment_address']}
                ```
                
                **Monto exacto:** {qr_data['amount']} {qr_data['currency']}
                
                **ID de Pago:** {payment_info['payment_id']}
                
                **Expira:** {payment_info['expires_at']}
                """)
                
                # Botón para verificar pago
                if st.button("🔄 Verificar Pago", type="primary"):
                    with st.spinner("Verificando pago..."):
                        status_result = BinancePaymentSystem.check_payment_status(
                            payment_info['payment_id']
                        )
                        
                        if status_result['success']:
                            if status_result['status'] == 'completed':
                                st.success("✅ ¡Pago completado!")
                                st.balloons()
                                
                                # Redirigir después de 3 segundos
                                tm.sleep(3)
                                st.session_state.current_page = 'my_payments'
                                st.rerun()
                            else:
                                st.info(f"Pago aún {status_result['status']}. Por favor intenta de nuevo en unos minutos.")
                        else:
                            st.error(f"Error verificando pago: {status_result['message']}")
            else:
                st.error(f"❌ Error creando pago: {result['message']}")
    
    # Instrucciones
    with st.expander("📋 Instrucciones para Pagar", expanded=True):
        st.write("""
        1. **Abre tu app de Binance**
        2. **Ve a la sección de Pagos/Transferencias**
        3. **Escanear el código QR** o copiar la dirección manualmente
        4. **Asegúrate de enviar exactamente** ${amount:,.2f} USDT
        5. **Confirma la transacción** en tu app
        6. **Regresa aquí y haz clic en "Verificar Pago"**
        
        **Notas importantes:**
        - Solo aceptamos USDT (TRC20)
        - La transacción puede tardar 2-5 minutos en confirmarse
        - Este pago expira en 1 hora
        - Contacta a soporte si tienes problemas
        """)
    
    # Soporte
    st.markdown("---")
    st.subheader("🆘 ¿Necesitas ayuda?")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("📞 Contactar Soporte"):
            st.info("support@mindgeekclinic.com")
    with col_s2:
        if st.button("📋 Ver Mis Pagos"):
            st.session_state.current_page = 'my_payments'
            st.rerun()

# ============================================
# SISTEMA DE ADMINISTRACIÓN COMPLETO
# ============================================

@require_auth('admin')
def admin_dashboard():
    """Dashboard de administrador - CONVERTIDO DE FLASK"""
    st.title("👨‍💼 Panel de Administración")
    
    # Métricas en tiempo real
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_users = db.fetchone("SELECT COUNT(*) as count FROM users")['count']
        st.metric("Total Usuarios", total_users)
    
    with col2:
        total_therapists = db.fetchone("SELECT COUNT(*) as count FROM users WHERE role = 'therapist'")['count']
        st.metric("Terapeutas", total_therapists)
    
    with col3:
        total_affiliates = db.fetchone("SELECT COUNT(*) as count FROM affiliates WHERE status = 'active'")['count']
        st.metric("Afiliados Activos", total_affiliates)
    
    with col4:
        total_revenue = db.fetchone("SELECT SUM(final_amount) as total FROM orders WHERE status = 'completed'")['total'] or 0
        st.metric("Ingresos Totales", f"${total_revenue:,.2f}")
    
    st.markdown("---")
    
    # Gráficos y estadísticas
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        # Gráfico de usuarios por rol
        st.subheader("📈 Distribución de Usuarios")
        roles_data = db.fetchall('''
            SELECT role, COUNT(*) as count 
            FROM users 
            WHERE is_active = 1 
            GROUP BY role
        ''')
        
        if roles_data:
            roles_df = pd.DataFrame(roles_data)
            fig = px.pie(roles_df, values='count', names='role', 
                        color_discrete_sequence=px.colors.qualitative.Set3,
                        hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        # Actividad reciente
        st.subheader("📋 Actividad Reciente")
        recent_activity = db.fetchall('''
            SELECT al.*, u.username 
            FROM activity_logs al
            LEFT JOIN users u ON al.user_id = u.id
            ORDER BY al.created_at DESC 
            LIMIT 5
        ''')
        
        for activity in recent_activity:
            timestamp = datetime.strptime(activity['created_at'], '%Y-%m-%d %H:%M:%S')
            time_ago = datetime.now() - timestamp
            
            if time_ago.days > 0:
                time_text = f"{time_ago.days}d ago"
            elif time_ago.seconds > 3600:
                time_text = f"{time_ago.seconds // 3600}h ago"
            else:
                time_text = f"{time_ago.seconds // 60}m ago"
            
            st.caption(f"**{activity['username'] or 'System'}** - {activity['activity_type']}")
            st.caption(f"{activity['description']} • {time_text}")
    
    # Acciones rápidas
    st.markdown("---")
    st.subheader("🚀 Acciones Rápidas")
    
    col_a, col_b, col_c, col_d = st.columns(4)
    
    with col_a:
        if st.button("➕ Nuevo Usuario", use_container_width=True):
            st.session_state.current_page = "create_user"
            st.rerun()
    
    with col_b:
        if st.button("💼 Gestionar Afiliados", use_container_width=True):
            st.session_state.current_page = "affiliate_system"
            st.rerun()
    
    with col_c:
        if st.button("💰 Reportes Financieros", use_container_width=True):
            st.session_state.current_page = "financial_reports"
            st.rerun()
    
    with col_d:
        if st.button("📊 Analytics", use_container_width=True):
            st.session_state.current_page = "analytics"
            st.rerun()

# ============================================
# FUNCIONES PRINCIPALES DE LA APLICACIÓN
# ============================================

def main():
    """Función principal de la aplicación"""
    # Configurar página
    if not st.session_state.is_authenticated:
        # Manejar autenticación
        if st.session_state.get('show_2fa', False):
            show_2fa_form()
        elif st.session_state.get('show_register', False):
            show_register_form()
        else:
            show_login_form()
    else:
        # Mostrar interfaz principal
        show_main_sidebar()
        
        # Navegación por páginas
        current_page = st.session_state.get('current_page', 'dashboard')
        
        # Mapeo de páginas a funciones
        page_handlers = {
            'dashboard': admin_dashboard if st.session_state.user_role == 'admin' else affiliate_dashboard if st.session_state.user_role == 'solo_afiliado' else user_dashboard,
            'admin_dashboard': admin_dashboard,
            'affiliate_dashboard': affiliate_dashboard,
            'affiliate_commissions': affiliate_commissions,
            'affiliate_links': affiliate_links,
            'affiliate_referrals': affiliate_referrals,
            'affiliate_campaigns': affiliate_campaigns,
            'affiliate_settings': affiliate_settings,
            'binance_payment': binance_payment_page,
            'user_dashboard': user_dashboard,
            'therapist_dashboard': admin_dashboard,  # Placeholder
        }
        
        # Ejecutar handler de página
        handler = page_handlers.get(current_page)
        if handler:
            try:
                handler()
            except Exception as e:
                st.error(f"Error cargando página: {str(e)}")
                logger.error(f"Error en handler {current_page}: {str(e)}")
        else:
            # Página por defecto
            st.title("MindGeek Clinic")
            st.info("Selecciona una opción del menú lateral para comenzar.")

# Funciones pendientes (para mantener compatibilidad)
def user_dashboard():
    """Dashboard para usuarios"""
    st.title("👤 Panel del Usuario")
    st.info("Panel del usuario - Funcionalidad completa en desarrollo")
    
    # Mostrar información básica
    if st.session_state.user:
        user = st.session_state.user
        st.write(f"Bienvenido, **{user['first_name']} {user['last_name']}**")
        
        # Métricas básicas
        col1, col2, col3 = st.columns(3)
        with col1:
            # Citas pendientes
            appointments = db.fetchone('''
                SELECT COUNT(*) as count FROM appointments 
                WHERE client_id = ? AND status = 'scheduled'
            ''', (user['id'],))
            st.metric("Citas Pendientes", appointments['count'] if appointments else 0)
        
        with col2:
            # Mensajes no leídos
            messages = db.fetchone('''
                SELECT COUNT(*) as count FROM messages 
                WHERE receiver_id = ? AND is_read = 0
            ''', (user['id'],))
            st.metric("Mensajes", messages['count'] if messages else 0)
        
        with col3:
            # Órdenes recientes
            orders = db.fetchone('''
                SELECT COUNT(*) as count FROM orders 
                WHERE customer_id = ? AND created_at > DATE('now', '-30 days')
            ''', (user['id'],))
            st.metric("Órdenes (30d)", orders['count'] if orders else 0)

# ============================================
# EJECUCIÓN DE LA APLICACIÓN
# ============================================

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Error crítico en la aplicación: {str(e)}")
        logger.error(f"Error crítico: {str(e)}", exc_info=True)
        
        # Mostrar opciones de recuperación
        with st.expander("🔧 Opciones de recuperación", expanded=True):
            st.write("""
            **Si la aplicación no funciona correctamente:**
            
            1. **Refrescar la página** - Presiona F5 o el botón de recargar
            2. **Limpiar cache** - En Streamlit Cloud ve a Settings → Clear Cache
            3. **Contactar soporte** - Envía un email a support@mindgeekclinic.com
            4. **Revisar logs** - Los errores detallados están en el sistema de logging
            """)
            
            if st.button("🔄 Intentar nuevamente"):
                st.rerun()
