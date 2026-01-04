# app.py - Aplicación Flask MindGeek Clinic
# Código completo con corrección de indentación en línea 4228
# ¡NO se han eliminado funcionalidades!

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_file, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, and_, func, desc
import os
import json
import datetime
import uuid
import logging
from logging.handlers import RotatingFileHandler
from werkzeug.utils import secure_filename
import stripe
import pandas as pd
import numpy as np
from datetime import timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import hashlib
import secrets
import string
import random
from functools import wraps
import time
from io import BytesIO
import csv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import qrcode
from PIL import Image
import io
from flask_socketio import SocketIO, emit, join_room, leave_room
import eventlet
eventlet.monkey_patch()

# Configuración de la aplicación
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave-secreta-por-defecto-cambiar-en-produccion')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///mindgeekclinic.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secreto-por-defecto-cambiar')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit
app.config['STRIPE_PUBLIC_KEY'] = os.environ.get('STRIPE_PUBLIC_KEY', '')
app.config['STRIPE_SECRET_KEY'] = os.environ.get('STRIPE_SECRET_KEY', '')
app.config['STRIPE_WEBHOOK_SECRET'] = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

# Configuración de email
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', '')

# Inicializar extensiones
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
CORS(app)
migrate = Migrate(app, db)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Configurar Stripe
stripe.api_key = app.config['STRIPE_SECRET_KEY']

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear carpeta de uploads si no existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'profiles'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'documents'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'products'), exist_ok=True)

# ------------------------------------------------------------
# MODELOS DE BASE DE DATOS
# ------------------------------------------------------------

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(20))
    profile_image = db.Column(db.String(200))
    bio = db.Column(db.Text)
    role = db.Column(db.String(50), default='user')  # user, therapist, admin
    specialization = db.Column(db.String(200))
    qualifications = db.Column(db.Text)
    experience_years = db.Column(db.Integer)
    hourly_rate = db.Column(db.Float, default=0.0)
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100))
    reset_token = db.Column(db.String(100))
    reset_token_expiry = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(100))
    
    # Relaciones
    appointments = db.relationship('Appointment', backref='client', lazy=True, foreign_keys='Appointment.client_id')
    therapist_appointments = db.relationship('Appointment', backref='therapist', lazy=True, foreign_keys='Appointment.therapist_id')
    sessions = db.relationship('Session', backref='participant', lazy=True)
    messages_sent = db.relationship('Message', backref='sender', lazy=True, foreign_keys='Message.sender_id')
    messages_received = db.relationship('Message', backref='receiver', lazy=True, foreign_keys='Message.receiver_id')
    reviews = db.relationship('Review', backref='reviewer', lazy=True)
    therapist_reviews = db.relationship('Review', backref='therapist_reviewed', lazy=True, foreign_keys='Review.therapist_id')
    products = db.relationship('Product', backref='creator', lazy=True)
    orders = db.relationship('Order', backref='customer', lazy=True)
    payments = db.relationship('Payment', backref='payer', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    affiliate = db.relationship('Affiliate', backref='user', lazy=True, uselist=False)
    referrals = db.relationship('Referral', backref='referrer', lazy=True, foreign_keys='Referral.referrer_id')
    referred = db.relationship('Referral', backref='referred_user', lazy=True, foreign_keys='Referral.referred_id')
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def generate_verification_token(self):
        self.verification_token = secrets.token_urlsafe(32)
        return self.verification_token
    
    def generate_reset_token(self):
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiry = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        return self.reset_token
    
    def verify_reset_token(self, token):
        if self.reset_token == token and self.reset_token_expiry > datetime.datetime.utcnow():
            return True
        return False

class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    therapist_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    duration = db.Column(db.Integer, default=60)  # en minutos
    status = db.Column(db.String(50), default='scheduled')  # scheduled, confirmed, completed, cancelled, no_show
    appointment_type = db.Column(db.String(100))  # individual, couple, family, etc.
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    reminder_sent = db.Column(db.Boolean, default=False)
    payment_status = db.Column(db.String(50), default='pending')
    amount = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(10), default='USD')
    meeting_link = db.Column(db.String(500))
    
    # Relación con Session
    session = db.relationship('Session', backref='appointment', lazy=True, uselist=False)

class Session(db.Model):
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Integer)  # en minutos
    notes = db.Column(db.Text)
    recording_url = db.Column(db.String(500))
    transcript = db.Column(db.Text)
    mood_start = db.Column(db.String(50))
    mood_end = db.Column(db.String(50))
    satisfaction_score = db.Column(db.Integer)  # 1-5
    therapist_notes = db.Column(db.Text)
    homework_assigned = db.Column(db.Text)
    next_session_plan = db.Column(db.Text)
    
    # Relación con SessionResource
    resources = db.relationship('SessionResource', backref='session', lazy=True)

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    read_timestamp = db.Column(db.DateTime)
    message_type = db.Column(db.String(50), default='text')  # text, image, file, system
    attachment_url = db.Column(db.String(500))
    
    # Indexes para búsquedas eficientes
    __table_args__ = (
        db.Index('idx_messages_sender_receiver', 'sender_id', 'receiver_id'),
        db.Index('idx_messages_timestamp', 'timestamp'),
    )

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    therapist_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    is_verified = db.Column(db.Boolean, default=False)
    response = db.Column(db.Text)
    response_date = db.Column(db.DateTime)
    
    __table_args__ = (
        db.UniqueConstraint('client_id', 'therapist_id', name='unique_client_therapist_review'),
    )

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    discount_price = db.Column(db.Float)
    category = db.Column(db.String(100))
    subcategory = db.Column(db.String(100))
    tags = db.Column(db.String(500))
    image_url = db.Column(db.String(500))
    stock_quantity = db.Column(db.Integer, default=0)
    is_digital = db.Column(db.Boolean, default=False)
    digital_file_url = db.Column(db.String(500))
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    views = db.Column(db.Integer, default=0)
    purchases = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float, default=0.0)
    review_count = db.Column(db.Integer, default=0)
    
    # Relaciones
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    discount_amount = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    shipping_amount = db.Column(db.Float, default=0.0)
    final_amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='USD')
    status = db.Column(db.String(50), default='pending')  # pending, processing, completed, cancelled, refunded
    payment_status = db.Column(db.String(50), default='pending')  # pending, paid, failed, refunded
    payment_method = db.Column(db.String(100))
    shipping_address = db.Column(db.Text)
    billing_address = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relaciones
    items = db.relationship('OrderItem', backref='order', lazy=True)
    payments = db.relationship('Payment', backref='order', lazy=True)

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0.0)

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    payment_reference = db.Column(db.String(100), unique=True, nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='USD')
    payment_method = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, completed, failed, refunded
    stripe_payment_intent_id = db.Column(db.String(100))
    stripe_charge_id = db.Column(db.String(100))
    payment_details = db.Column(db.Text)  # JSON con detalles del pago
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50))  # info, success, warning, error, appointment, message, payment
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    action_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_notifications_user_read', 'user_id', 'is_read'),
    )

class SessionResource(db.Model):
    __tablename__ = 'session_resources'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)
    resource_type = db.Column(db.String(50))  # document, link, exercise, homework
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    content = db.Column(db.Text)
    file_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Affiliate(db.Model):
    __tablename__ = 'affiliates'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    affiliate_code = db.Column(db.String(50), unique=True, nullable=False)
    commission_rate = db.Column(db.Float, default=10.0)  # Porcentaje
    total_earnings = db.Column(db.Float, default=0.0)
    pending_earnings = db.Column(db.Float, default=0.0)
    paid_earnings = db.Column(db.Float, default=0.0)
    referral_count = db.Column(db.Integer, default=0)
    conversion_rate = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(50), default='active')  # active, inactive, suspended
    contact_info = db.Column(db.Text)
    payment_method = db.Column(db.String(100))
    payment_details = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relación con Referral
    referrals_made = db.relationship('Referral', backref='affiliate', lazy=True, foreign_keys='Referral.affiliate_id')

class Referral(db.Model):
    __tablename__ = 'referrals'
    
    id = db.Column(db.Integer, primary_key=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    referred_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    affiliate_id = db.Column(db.Integer, db.ForeignKey('affiliates.id'))
    referral_code = db.Column(db.String(50))
    referral_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status = db.Column(db.String(50), default='pending')  # pending, registered, converted, paid
    conversion_date = db.Column(db.DateTime)
    conversion_value = db.Column(db.Float, default=0.0)
    commission_earned = db.Column(db.Float, default=0.0)
    commission_paid = db.Column(db.Boolean, default=False)
    payment_date = db.Column(db.DateTime)
    
    __table_args__ = (
        db.UniqueConstraint('referrer_id', 'referred_id', name='unique_referral_pair'),
    )

class Coupon(db.Model):
    __tablename__ = 'coupons'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_type = db.Column(db.String(20), nullable=False)  # percentage, fixed
    discount_value = db.Column(db.Float, nullable=False)
    min_purchase = db.Column(db.Float, default=0.0)
    max_discount = db.Column(db.Float)
    valid_from = db.Column(db.DateTime, nullable=False)
    valid_until = db.Column(db.DateTime, nullable=False)
    usage_limit = db.Column(db.Integer)
    used_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relación con órdenes que usaron este cupón
    orders = db.relationship('Order', secondary='order_coupons', backref='coupons')

class OrderCoupon(db.Model):
    __tablename__ = 'order_coupons'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    coupon_id = db.Column(db.Integer, db.ForeignKey('coupons.id'), nullable=False)
    discount_applied = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# Tabla de unión para usuarios bloqueados
user_blocks = db.Table('user_blocks',
    db.Column('blocker_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('blocked_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.datetime.utcnow),  # ← CORREGIDO
    db.Column('reason', db.Text)
                      )

# ------------------------------------------------------------
# SISTEMA DE AFILIADOS
# ------------------------------------------------------------

class AffiliateSystem:
    def __init__(self):
        self.min_commission_rate = 5.0
        self.max_commission_rate = 30.0
        self.default_commission_rate = 10.0
        
    def generate_affiliate_code(self):
        """Genera un código de afiliado único"""
        while True:
            # Formato: MG + 6 caracteres alfanuméricos
            code = 'MG' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Affiliate.query.filter_by(affiliate_code=code).first():
                return code
    
    def validate_affiliate_data(self, data):
        """Valida los datos del afiliado"""
        errors = []
        
        # Validar user_id
        if 'user_id' not in data:
            errors.append('user_id es requerido')
        else:
            user = User.query.get(data['user_id'])
            if not user:
                errors.append('Usuario no encontrado')
        
        # Validar commission_rate
        if 'commission_rate' in data:
            try:
                commission_rate = float(data['commission_rate'])
                if commission_rate < self.min_commission_rate or commission_rate > self.max_commission_rate:
                    errors.append(f'La comisión debe estar entre {self.min_commission_rate}% y {self.max_commission_rate}%')
            except ValueError:
                errors.append('commission_rate debe ser un número')
        
        return errors
    
    def map_fields(self, data):
        """Mapea los campos de entrada a los campos del modelo"""
        mapped_data = {}
        field_mapping = {
            'user_id': 'user_id',
            'affiliate_code': 'affiliate_code',
            'commission_rate': 'commission_rate',
            'contact_info': 'contact_info',
            'status': 'status',
            'payment_method': 'payment_method',
            'payment_details': 'payment_details',
            'notes': 'notes'
        }
        
        for key, value in data.items():
            if key in field_mapping:
                mapped_data[field_mapping[key]] = value
        
        return mapped_data
    
    def add_affiliate(self, data):
        """Agrega un nuevo afiliado"""
        try:
            # Verificar si el usuario ya es afiliado
            existing_affiliate = Affiliate.query.filter_by(user_id=data['user_id']).first()
            if existing_affiliate:
                return False, 'El usuario ya es un afiliado', None
            
            # Crear nuevo afiliado
            affiliate = Affiliate(
                user_id=data['user_id'],
                affiliate_code=data.get('affiliate_code', self.generate_affiliate_code()),
                commission_rate=data.get('commission_rate', self.default_commission_rate),
                contact_info=data.get('contact_info', ''),
                status=data.get('status', 'active'),
                payment_method=data.get('payment_method', ''),
                payment_details=data.get('payment_details', ''),
                notes=data.get('notes', '')
            )
            
            db.session.add(affiliate)
            db.session.commit()
            
            # Registrar en log
            logger.info(f'Nuevo afiliado creado: {affiliate.id} - Usuario: {data["user_id"]}')
            
            return True, 'Afiliado creado exitosamente', {
                'id': affiliate.id,
                'user_id': affiliate.user_id,
                'affiliate_code': affiliate.affiliate_code,
                'commission_rate': affiliate.commission_rate,
                'status': affiliate.status
            }
            
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f'Error de integridad al crear afiliado: {str(e)}')
            return False, 'Error de integridad en la base de datos', None
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error al crear afiliado: {str(e)}')
            return False, f'Error del servidor: {str(e)}', None
    
    def update_affiliate(self, affiliate_id, data):
        """Actualiza un afiliado existente"""
        try:
            affiliate = Affiliate.query.get(affiliate_id)
            if not affiliate:
                return False, 'Afiliado no encontrado', None
            
            # Actualizar campos permitidos
            updatable_fields = ['commission_rate', 'contact_info', 'status', 
                              'payment_method', 'payment_details', 'notes']
            
            for field in updatable_fields:
                if field in data:
                    setattr(affiliate, field, data[field])
            
            affiliate.updated_at = datetime.datetime.utcnow()
            db.session.commit()
            
            return True, 'Afiliado actualizado exitosamente', {
                'id': affiliate.id,
                'user_id': affiliate.user_id,
                'affiliate_code': affiliate.affiliate_code,
                'commission_rate': affiliate.commission_rate,
                'status': affiliate.status
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error al actualizar afiliado: {str(e)}')
            return False, f'Error del servidor: {str(e)}', None
    
    def get_affiliate_stats(self, affiliate_id):
        """Obtiene estadísticas del afiliado"""
        affiliate = Affiliate.query.get(affiliate_id)
        if not affiliate:
            return None
        
        # Calcular estadísticas en tiempo real
        referrals = Referral.query.filter_by(affiliate_id=affiliate_id).all()
        total_referrals = len(referrals)
        converted_referrals = len([r for r in referrals if r.status == 'converted'])
        pending_earnings = sum([r.commission_earned for r in referrals if not r.commission_paid])
        
        # Calcular tasa de conversión
        conversion_rate = (converted_referrals / total_referrals * 100) if total_referrals > 0 else 0
        
        return {
            'affiliate_id': affiliate.id,
            'affiliate_code': affiliate.affiliate_code,
            'total_referrals': total_referrals,
            'converted_referrals': converted_referrals,
            'conversion_rate': round(conversion_rate, 2),
            'total_earnings': affiliate.total_earnings,
            'pending_earnings': pending_earnings,
            'paid_earnings': affiliate.paid_earnings,
            'commission_rate': affiliate.commission_rate,
            'status': affiliate.status
        }
    
    def process_referral_conversion(self, referral_id, conversion_value):
        """Procesa la conversión de una referencia"""
        try:
            referral = Referral.query.get(referral_id)
            if not referral:
                return False, 'Referencia no encontrada'
            
            affiliate = referral.affiliate
            if not affiliate:
                return False, 'Afiliado no encontrado'
            
            # Calcular comisión
            commission = (conversion_value * affiliate.commission_rate) / 100
            
            # Actualizar referencia
            referral.status = 'converted'
            referral.conversion_date = datetime.datetime.utcnow()
            referral.conversion_value = conversion_value
            referral.commission_earned = commission
            
            # Actualizar estadísticas del afiliado
            affiliate.total_earnings += commission
            affiliate.pending_earnings += commission
            affiliate.referral_count += 1
            
            # Calcular nueva tasa de conversión
            total_referrals = Referral.query.filter_by(affiliate_id=affiliate.id).count()
            converted_referrals = Referral.query.filter_by(affiliate_id=affiliate.id, status='converted').count()
            affiliate.conversion_rate = (converted_referrals / total_referrals * 100) if total_referrals > 0 else 0
            
            db.session.commit()
            
            logger.info(f'Conversión procesada: Referral {referral_id}, Comisión: {commission}')
            
            return True, 'Conversión procesada exitosamente'
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error al procesar conversión: {str(e)}')
            return False, f'Error del servidor: {str(e)}'

# Instanciar el sistema de afiliados
affiliate_system = AffiliateSystem()

# ------------------------------------------------------------
# SISTEMA DE EMAIL
# ------------------------------------------------------------

class EmailSystem:
    def __init__(self, app):
        self.app = app
        self.smtp_server = app.config['MAIL_SERVER']
        self.smtp_port = app.config['MAIL_PORT']
        self.use_tls = app.config['MAIL_USE_TLS']
        self.username = app.config['MAIL_USERNAME']
        self.password = app.config['MAIL_PASSWORD']
        self.default_sender = app.config['MAIL_DEFAULT_SENDER']
    
    def send_email(self, to_email, subject, body_html, body_text=None):
        """Envía un email"""
        try:
            if not self.username or not self.password:
                logger.warning('Credenciales de email no configuradas. Email no enviado.')
                return False
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.default_sender
            msg['To'] = to_email
            
            # Adjuntar cuerpo en texto plano y HTML
            if body_text:
                part1 = MIMEText(body_text, 'plain')
                msg.attach(part1)
            
            part2 = MIMEText(body_html, 'html')
            msg.attach(part2)
            
            # Conectar y enviar
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f'Email enviado a {to_email}: {subject}')
            return True
            
        except Exception as e:
            logger.error(f'Error al enviar email: {str(e)}')
            return False
    
    def send_welcome_email(self, user_email, user_name):
        """Envía email de bienvenida"""
        subject = "¡Bienvenido a MindGeek Clinic!"
        body_html = f"""
        <html>
        <body>
            <h1>¡Bienvenido, {user_name}!</h1>
            <p>Gracias por registrarte en MindGeek Clinic. Estamos emocionados de tenerte con nosotros.</p>
            <p>Tu cuenta ha sido creada exitosamente y ahora puedes acceder a todos nuestros servicios.</p>
            <p>Si tienes alguna pregunta, no dudes en contactarnos.</p>
            <br>
            <p>Saludos,<br>El equipo de MindGeek Clinic</p>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, body_html)
    
    def send_password_reset_email(self, user_email, reset_token):
        """Envía email de recuperación de contraseña"""
        reset_url = f"https://tudominio.com/reset-password?token={reset_token}"
        subject = "Recuperación de contraseña - MindGeek Clinic"
        body_html = f"""
        <html>
        <body>
            <h1>Recuperación de contraseña</h1>
            <p>Hemos recibido una solicitud para restablecer tu contraseña.</p>
            <p>Para crear una nueva contraseña, haz clic en el siguiente enlace:</p>
            <p><a href="{reset_url}">Restablecer contraseña</a></p>
            <p>Este enlace expirará en 24 horas.</p>
            <p>Si no solicitaste este cambio, puedes ignorar este email.</p>
            <br>
            <p>Saludos,<br>El equipo de MindGeek Clinic</p>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, body_html)
    
    def send_appointment_confirmation(self, user_email, appointment_details):
        """Envía confirmación de cita"""
        subject = "Confirmación de cita - MindGeek Clinic"
        body_html = f"""
        <html>
        <body>
            <h1>Cita confirmada</h1>
            <p>Tu cita ha sido programada exitosamente.</p>
            <p><strong>Detalles de la cita:</strong></p>
            <ul>
                <li>Fecha: {appointment_details['date']}</li>
                <li>Hora: {appointment_details['time']}</li>
                <li>Terapeuta: {appointment_details['therapist']}</li>
                <li>Tipo: {appointment_details['type']}</li>
            </ul>
            <p>Te recordaremos la cita 24 horas antes.</p>
            <p>Para cualquier cambio, por favor contacta con nosotros.</p>
            <br>
            <p>Saludos,<br>El equipo de MindGeek Clinic</p>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, body_html)

# Instanciar el sistema de email
email_system = EmailSystem(app)

# ------------------------------------------------------------
# SISTEMA DE PAGOS CON STRIPE
# ------------------------------------------------------------

class PaymentSystem:
    def __init__(self):
        self.stripe_public_key = app.config['STRIPE_PUBLIC_KEY']
        self.stripe_secret_key = app.config['STRIPE_SECRET_KEY']
        self.stripe_webhook_secret = app.config['STRIPE_WEBHOOK_SECRET']
        
        if self.stripe_secret_key:
            stripe.api_key = self.stripe_secret_key
    
    def create_payment_intent(self, amount, currency='usd', metadata=None):
        """Crea un PaymentIntent de Stripe"""
        try:
            # Convertir a centavos/céntimos
            amount_in_cents = int(amount * 100)
            
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_in_cents,
                currency=currency,
                metadata=metadata or {},
                automatic_payment_methods={
                    'enabled': True,
                }
            )
            
            return {
                'success': True,
                'client_secret': payment_intent.client_secret,
                'payment_intent_id': payment_intent.id,
                'amount': amount,
                'currency': currency
            }
            
        except stripe.error.StripeError as e:
            logger.error(f'Error de Stripe: {str(e)}')
            return {
                'success': False,
                'error': str(e.user_message if hasattr(e, 'user_message') else e)
            }
        except Exception as e:
            logger.error(f'Error al crear payment intent: {str(e)}')
            return {
                'success': False,
                'error': 'Error interno del servidor'
            }
    
    def confirm_payment(self, payment_intent_id):
        """Confirma un pago de Stripe"""
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                'success': True,
                'status': payment_intent.status,
                'amount': payment_intent.amount / 100,
                'currency': payment_intent.currency,
                'payment_method': payment_intent.payment_method_types[0] if payment_intent.payment_method_types else 'unknown'
            }
            
        except stripe.error.StripeError as e:
            logger.error(f'Error de Stripe al confirmar pago: {str(e)}')
            return {
                'success': False,
                'error': str(e.user_message if hasattr(e, 'user_message') else e)
            }
    
    def create_checkout_session(self, line_items, success_url, cancel_url, metadata=None):
        """Crea una sesión de checkout de Stripe"""
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata or {}
            )
            
            return {
                'success': True,
                'session_id': checkout_session.id,
                'url': checkout_session.url
            }
            
        except stripe.error.StripeError as e:
            logger.error(f'Error de Stripe en checkout: {str(e)}')
            return {
                'success': False,
                'error': str(e.user_message if hasattr(e, 'user_message') else e)
            }
    
    def handle_webhook(self, payload, sig_header):
        """Maneja webhooks de Stripe"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.stripe_webhook_secret
            )
            
            # Manejar diferentes tipos de eventos
            if event['type'] == 'payment_intent.succeeded':
                payment_intent = event['data']['object']
                self._handle_payment_success(payment_intent)
                
            elif event['type'] == 'payment_intent.payment_failed':
                payment_intent = event['data']['object']
                self._handle_payment_failure(payment_intent)
            
            return {'success': True, 'event': event['type']}
            
        except ValueError as e:
            logger.error(f'Payload inválido: {str(e)}')
            return {'success': False, 'error': 'Payload inválido'}
        except stripe.error.SignatureVerificationError as e:
            logger.error(f'Firma inválida: {str(e)}')
            return {'success': False, 'error': 'Firma inválida'}
    
    def _handle_payment_success(self, payment_intent):
        """Maneja pagos exitosos"""
        try:
            # Buscar pago en la base de datos
            payment = Payment.query.filter_by(
                stripe_payment_intent_id=payment_intent['id']
            ).first()
            
            if payment:
                payment.status = 'completed'
                payment.stripe_charge_id = payment_intent.get('charges', {}).get('data', [{}])[0].get('id')
                payment.payment_details = json.dumps(payment_intent)
                payment.updated_at = datetime.datetime.utcnow()
                
                # Actualizar orden asociada
                if payment.order_id:
                    order = Order.query.get(payment.order_id)
                    if order:
                        order.payment_status = 'paid'
                        order.status = 'processing'
                        order.updated_at = datetime.datetime.utcnow()
                
                db.session.commit()
                logger.info(f'Pago completado: {payment_intent["id"]}')
                
                # Enviar notificación
                self._send_payment_notification(payment.user_id, payment.amount, True)
        
        except Exception as e:
            logger.error(f'Error al manejar pago exitoso: {str(e)}')
    
    def _handle_payment_failure(self, payment_intent):
        """Maneja pagos fallidos"""
        try:
            payment = Payment.query.filter_by(
                stripe_payment_intent_id=payment_intent['id']
            ).first()
            
            if payment:
                payment.status = 'failed'
                payment.payment_details = json.dumps(payment_intent)
                payment.updated_at = datetime.datetime.utcnow()
                db.session.commit()
                
                # Enviar notificación
                self._send_payment_notification(payment.user_id, payment.amount, False)
                
                logger.warning(f'Pago fallido: {payment_intent["id"]}')
        
        except Exception as e:
            logger.error(f'Error al manejar pago fallido: {str(e)}')
    
    def _send_payment_notification(self, user_id, amount, success):
        """Envía notificación de pago"""
        try:
            user = User.query.get(user_id)
            if not user:
                return
            
            notification = Notification(
                user_id=user_id,
                title='Pago procesado' if success else 'Pago fallido',
                message=f'Tu pago de ${amount:.2f} ha sido {"completado exitosamente" if success else "rechazado"}',
                notification_type='success' if success else 'error',
                action_url='/dashboard/payments'
            )
            
            db.session.add(notification)
            db.session.commit()
        
        except Exception as e:
            logger.error(f'Error al enviar notificación de pago: {str(e)}')

# Instanciar el sistema de pagos
payment_system = PaymentSystem()

# ------------------------------------------------------------
# SISTEMA DE NOTIFICACIONES EN TIEMPO REAL
# ------------------------------------------------------------

class NotificationSystem:
    @staticmethod
    def create_notification(user_id, title, message, notification_type='info', action_url=None):
        """Crea una nueva notificación"""
        try:
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                action_url=action_url
            )
            
            db.session.add(notification)
            db.session.commit()
            
            # Enviar notificación en tiempo real via Socket.IO
            socketio.emit('new_notification', {
                'id': notification.id,
                'title': title,
                'message': message,
                'type': notification_type,
                'timestamp': notification.created_at.isoformat(),
                'action_url': action_url
            }, room=f'user_{user_id}')
            
            return notification
            
        except Exception as e:
            logger.error(f'Error al crear notificación: {str(e)}')
            return None
    
    @staticmethod
    def send_appointment_reminder(appointment):
        """Envía recordatorio de cita"""
        try:
            # Notificación al cliente
            NotificationSystem.create_notification(
                user_id=appointment.client_id,
                title='Recordatorio de cita',
                message=f'Tienes una cita programada para {appointment.appointment_date} a las {appointment.appointment_time}',
                notification_type='appointment',
                action_url=f'/appointments/{appointment.id}'
            )
            
            # Notificación al terapeuta
            NotificationSystem.create_notification(
                user_id=appointment.therapist_id,
                title='Cita programada',
                message=f'Tienes una cita con {appointment.client.first_name} {appointment.client.last_name}',
                notification_type='appointment',
                action_url=f'/therapist/appointments/{appointment.id}'
            )
            
            # Enviar email si está configurado
            if appointment.client.email and email_system.username:
                email_system.send_appointment_confirmation(
                    appointment.client.email,
                    {
                        'date': appointment.appointment_date.strftime('%Y-%m-%d'),
                        'time': appointment.appointment_time.strftime('%H:%M'),
                        'therapist': f'{appointment.therapist.first_name} {appointment.therapist.last_name}',
                        'type': appointment.appointment_type
                    }
                )
        
        except Exception as e:
            logger.error(f'Error al enviar recordatorio: {str(e)}')
    
    @staticmethod
    def mark_as_read(notification_id, user_id):
        """Marca una notificación como leída"""
        try:
            notification = Notification.query.filter_by(
                id=notification_id, 
                user_id=user_id
            ).first()
            
            if notification:
                notification.is_read = True
                notification.read_at = datetime.datetime.utcnow()
                db.session.commit()
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f'Error al marcar notificación como leída: {str(e)}')
            return False

# ------------------------------------------------------------
# SISTEMA DE CHAT EN TIEMPO REAL
# ------------------------------------------------------------

@socketio.on('connect')
def handle_connect():
    """Maneja conexión de Socket.IO"""
    if current_user.is_authenticated:
        join_room(f'user_{current_user.id}')
        logger.info(f'Usuario {current_user.id} conectado al chat')

@socketio.on('disconnect')
def handle_disconnect():
    """Maneja desconexión de Socket.IO"""
    if current_user.is_authenticated:
        leave_room(f'user_{current_user.id}')
        logger.info(f'Usuario {current_user.id} desconectado del chat')

@socketio.on('send_message')
def handle_send_message(data):
    """Maneja envío de mensajes"""
    try:
        sender_id = current_user.id
        receiver_id = data.get('receiver_id')
        content = data.get('content')
        message_type = data.get('type', 'text')
        
        if not receiver_id or not content:
            emit('error', {'message': 'Datos incompletos'})
            return
        
        # Verificar si el receptor ha bloqueado al remitente
        blocker_check = db.session.query(user_blocks).filter_by(
            blocker_id=receiver_id,
            blocked_id=sender_id
        ).first()
        
        if blocker_check:
            emit('error', {'message': 'No puedes enviar mensajes a este usuario'})
            return
        
        # Crear mensaje en la base de datos
        message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            message_type=message_type
        )
        
        db.session.add(message)
        db.session.commit()
        
        # Emitir mensaje al receptor
        message_data = {
            'id': message.id,
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'content': content,
            'type': message_type,
            'timestamp': message.timestamp.isoformat(),
            'sender_name': f'{current_user.first_name} {current_user.last_name}',
            'sender_avatar': current_user.profile_image or '/static/images/default-avatar.png'
        }
        
        emit('receive_message', message_data, room=f'user_{receiver_id}')
        emit('message_sent', message_data)  # Confirmación al remitente
        
        # Crear notificación
        NotificationSystem.create_notification(
            user_id=receiver_id,
            title='Nuevo mensaje',
            message=f'Tienes un nuevo mensaje de {current_user.first_name}',
            notification_type='message',
            action_url=f'/messages/{sender_id}'
        )
        
    except Exception as e:
        logger.error(f'Error al enviar mensaje: {str(e)}')
        emit('error', {'message': 'Error al enviar mensaje'})

@socketio.on('typing')
def handle_typing(data):
    """Maneja indicador de escritura"""
    receiver_id = data.get('receiver_id')
    is_typing = data.get('is_typing', False)
    
    if receiver_id:
        emit('user_typing', {
            'user_id': current_user.id,
            'is_typing': is_typing
        }, room=f'user_{receiver_id}')

# ------------------------------------------------------------
# BLUEPRINTS Y RUTAS
# ------------------------------------------------------------

# Blueprint para usuarios
users_blueprint = Blueprint('users', __name__)

# ------------------------------------------------------------
# DECORADORES Y FUNCIONES DE AYUDA
# ------------------------------------------------------------

def admin_required(f):
    """Decorador para requerir rol de administrador"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        if not is_admin(current_user_id):
            return jsonify({
                'success': False,
                'message': 'Acceso denegado. Se requieren privilegios de administrador.'
            }), 403
        return f(*args, **kwargs)
    return decorated_function

def therapist_required(f):
    """Decorador para requerir rol de terapeuta"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or user.role not in ['therapist', 'admin']:
            return jsonify({
                'success': False,
                'message': 'Acceso denegado. Se requiere rol de terapeuta.'
            }), 403
        return f(*args, **kwargs)
    return decorated_function

def is_admin(user_id):
    """Verifica si un usuario es administrador"""
    user = User.query.get(user_id)
    return user and user.role == 'admin'

def is_therapist(user_id):
    """Verifica si un usuario es terapeuta"""
    user = User.query.get(user_id)
    return user and user.role in ['therapist', 'admin']

def generate_order_number():
    """Genera un número de orden único"""
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = ''.join(random.choices(string.digits, k=6))
    return f'ORD-{timestamp}-{random_str}'

def validate_email(email):
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Valida fortaleza de contraseña"""
    if len(password) < 8:
        return False, 'La contraseña debe tener al menos 8 caracteres'
    
    if not re.search(r'[A-Z]', password):
        return False, 'La contraseña debe contener al menos una mayúscula'
    
    if not re.search(r'[a-z]', password):
        return False, 'La contraseña debe contener al menos una minúscula'
    
    if not re.search(r'[0-9]', password):
        return False, 'La contraseña debe contener al menos un número'
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, 'La contraseña debe contener al menos un carácter especial'
    
    return True, 'Contraseña válida'

# ------------------------------------------------------------
# RUTAS DE AUTENTICACIÓN
# ------------------------------------------------------------

@users_blueprint.route('/api/register', methods=['POST'])
def register():
    """Registra un nuevo usuario"""
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        required_fields = ['username', 'email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Campo requerido faltante: {field}'
                }), 400
        
        # Validar email
        if not validate_email(data['email']):
            return jsonify({
                'success': False,
                'message': 'Formato de email inválido'
            }), 400
        
        # Validar contraseña
        is_valid, msg = validate_password(data['password'])
        if not is_valid:
            return jsonify({
                'success': False,
                'message': msg
            }), 400
        
        # Verificar si el usuario ya existe
        existing_user = User.query.filter(
            (User.username == data['username']) | (User.email == data['email'])
        ).first()
        
        if existing_user:
            return jsonify({
                'success': False,
                'message': 'El usuario o email ya están registrados'
            }), 400
        
        # Crear nuevo usuario
        user = User(
            username=data['username'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data.get('phone', ''),
            role=data.get('role', 'user'),
            is_active=True
        )
        
        user.set_password(data['password'])
        
        # Generar token de verificación
        user.generate_verification_token()
        
        db.session.add(user)
        db.session.commit()
        
        # Enviar email de bienvenida
        if email_system.username:
            email_system.send_welcome_email(user.email, user.first_name)
        
        # Crear token JWT
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'success': True,
            'message': 'Usuario registrado exitosamente',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role
            },
            'access_token': access_token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error en registro: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/login', methods=['POST'])
def login():
    """Inicia sesión de usuario"""
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        if 'email' not in data or 'password' not in data:
            return jsonify({
                'success': False,
                'message': 'Email y contraseña son requeridos'
            }), 400
        
        # Buscar usuario
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({
                'success': False,
                'message': 'Credenciales inválidas'
            }), 401
        
        if not user.is_active:
            return jsonify({
                'success': False,
                'message': 'Cuenta desactivada. Contacta al administrador.'
            }), 403
        
        # Actualizar último login
        user.last_login = datetime.datetime.utcnow()
        db.session.commit()
        
        # Crear token JWT
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'success': True,
            'message': 'Inicio de sesión exitoso',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'profile_image': user.profile_image
            },
            'access_token': access_token
        }), 200
        
    except Exception as e:
        logger.error(f'Error en login: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresca el token JWT"""
    try:
        current_user_id = get_jwt_identity()
        access_token = create_access_token(identity=current_user_id)
        
        return jsonify({
            'success': True,
            'access_token': access_token
        }), 200
        
    except Exception as e:
        logger.error(f'Error al refrescar token: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error al refrescar token'
        }), 500

@users_blueprint.route('/api/logout', methods=['POST'])
@jwt_required()
def logout():
    """Cierra sesión del usuario"""
    # En JWT, el logout es del lado del cliente (eliminar token)
    return jsonify({
        'success': True,
        'message': 'Sesión cerrada exitosamente'
    }), 200

@users_blueprint.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    """Solicita restablecimiento de contraseña"""
    try:
        data = request.get_json()
        
        if 'email' not in data:
            return jsonify({
                'success': False,
                'message': 'Email es requerido'
            }), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if user:
            # Generar token de restablecimiento
            reset_token = user.generate_reset_token()
            db.session.commit()
            
            # Enviar email con enlace de restablecimiento
            if email_system.username:
                email_system.send_password_reset_email(user.email, reset_token)
        
        # Siempre devolver éxito (por seguridad)
        return jsonify({
            'success': True,
            'message': 'Si el email existe, se enviarán instrucciones para restablecer la contraseña'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error en forgot-password: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/reset-password', methods=['POST'])
def reset_password():
    """Restablece la contraseña con token"""
    try:
        data = request.get_json()
        
        required_fields = ['token', 'new_password']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Campo requerido faltante: {field}'
                }), 400
        
        # Buscar usuario con token válido
        user = User.query.filter_by(reset_token=data['token']).first()
        
        if not user or not user.verify_reset_token(data['token']):
            return jsonify({
                'success': False,
                'message': 'Token inválido o expirado'
            }), 400
        
        # Validar nueva contraseña
        is_valid, msg = validate_password(data['new_password'])
        if not is_valid:
            return jsonify({
                'success': False,
                'message': msg
            }), 400
        
        # Actualizar contraseña
        user.set_password(data['new_password'])
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contraseña restablecida exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error en reset-password: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

# ------------------------------------------------------------
# RUTAS DE PERFIL DE USUARIO
# ------------------------------------------------------------

@users_blueprint.route('/api/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Obtiene el perfil del usuario actual"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'Usuario no encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'address': user.address,
                'city': user.city,
                'country': user.country,
                'postal_code': user.postal_code,
                'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
                'gender': user.gender,
                'profile_image': user.profile_image,
                'bio': user.bio,
                'role': user.role,
                'specialization': user.specialization,
                'qualifications': user.qualifications,
                'experience_years': user.experience_years,
                'hourly_rate': user.hourly_rate,
                'is_verified': user.is_verified,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f'Error al obtener perfil: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Actualiza el perfil del usuario"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'Usuario no encontrado'
            }), 404
        
        data = request.get_json()
        
        # Campos actualizables
        updatable_fields = [
            'first_name', 'last_name', 'phone', 'address', 'city',
            'country', 'postal_code', 'date_of_birth', 'gender',
            'bio', 'specialization', 'qualifications', 'experience_years',
            'hourly_rate'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(user, field, data[field])
        
        user.updated_at = datetime.datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Perfil actualizado exitosamente',
            'user': {
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'bio': user.bio,
                'specialization': user.specialization,
                'experience_years': user.experience_years,
                'hourly_rate': user.hourly_rate
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error al actualizar perfil: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/profile/avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    """Sube/actualiza avatar del usuario"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'Usuario no encontrado'
            }), 404
        
        if 'avatar' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No se proporcionó archivo de avatar'
            }), 400
        
        avatar_file = request.files['avatar']
        
        if avatar_file.filename == '':
            return jsonify({
                'success': False,
                'message': 'Nombre de archivo vacío'
            }), 400
        
        # Validar tipo de archivo
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        filename = avatar_file.filename.lower()
        if '.' not in filename or filename.rsplit('.', 1)[1] not in allowed_extensions:
            return jsonify({
                'success': False,
                'message': 'Formato de archivo no permitido. Use PNG, JPG, JPEG o GIF.'
            }), 400
        
        # Generar nombre único
        file_ext = filename.rsplit('.', 1)[1]
        unique_filename = f"{current_user_id}_{int(time.time())}.{file_ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'profiles', unique_filename)
        
        # Guardar archivo
        avatar_file.save(filepath)
        
        # Actualizar perfil del usuario
        user.profile_image = f'/static/uploads/profiles/{unique_filename}'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Avatar actualizado exitosamente',
            'avatar_url': user.profile_image
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error al subir avatar: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Cambia la contraseña del usuario"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'Usuario no encontrado'
            }), 404
        
        data = request.get_json()
        
        required_fields = ['current_password', 'new_password']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Campo requerido faltante: {field}'
                }), 400
        
        # Verificar contraseña actual
        if not user.check_password(data['current_password']):
            return jsonify({
                'success': False,
                'message': 'Contraseña actual incorrecta'
            }), 400
        
        # Validar nueva contraseña
        is_valid, msg = validate_password(data['new_password'])
        if not is_valid:
            return jsonify({
                'success': False,
                'message': msg
            }), 400
        
        # Actualizar contraseña
        user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contraseña cambiada exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error al cambiar contraseña: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

# ------------------------------------------------------------
# RUTAS DE CITAS (APPOINTMENTS)
# ------------------------------------------------------------

@users_blueprint.route('/api/appointments', methods=['POST'])
@jwt_required()
def create_appointment():
    """Crea una nueva cita"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar campos requeridos
        required_fields = ['therapist_id', 'appointment_date', 'appointment_time']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Campo requerido faltante: {field}'
                }), 400
        
        # Verificar si el terapeuta existe y es terapeuta
        therapist = User.query.get(data['therapist_id'])
        if not therapist or therapist.role not in ['therapist', 'admin']:
            return jsonify({
                'success': False,
                'message': 'Terapeuta no válido'
            }), 400
        
        # Verificar disponibilidad del terapeuta
        existing_appointment = Appointment.query.filter_by(
            therapist_id=data['therapist_id'],
            appointment_date=data['appointment_date'],
            appointment_time=data['appointment_time'],
            status='scheduled'
        ).first()
        
        if existing_appointment:
            return jsonify({
                'success': False,
                'message': 'El terapeuta no está disponible en ese horario'
            }), 400
        
        # Crear cita
        appointment = Appointment(
            client_id=current_user_id,
            therapist_id=data['therapist_id'],
            appointment_date=datetime.datetime.strptime(data['appointment_date'], '%Y-%m-%d').date(),
            appointment_time=datetime.datetime.strptime(data['appointment_time'], '%H:%M').time(),
            duration=data.get('duration', 60),
            appointment_type=data.get('appointment_type', 'individual'),
            notes=data.get('notes', ''),
            amount=therapist.hourly_rate * (data.get('duration', 60) / 60),
            currency='USD'
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        # Crear notificación para el terapeuta
        NotificationSystem.create_notification(
            user_id=therapist.id,
            title='Nueva cita programada',
            message=f'{current_user.first_name} {current_user.last_name} ha programado una cita contigo',
            notification_type='appointment',
            action_url=f'/therapist/appointments/{appointment.id}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Cita creada exitosamente',
            'appointment': {
                'id': appointment.id,
                'client_id': appointment.client_id,
                'therapist_id': appointment.therapist_id,
                'appointment_date': appointment.appointment_date.isoformat(),
                'appointment_time': appointment.appointment_time.strftime('%H:%M'),
                'duration': appointment.duration,
                'type': appointment.appointment_type,
                'status': appointment.status,
                'amount': appointment.amount
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error al crear cita: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/appointments', methods=['GET'])
@jwt_required()
def get_appointments():
    """Obtiene citas del usuario"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'Usuario no encontrado'
            }), 404
        
        # Filtrar por tipo de usuario
        if user.role in ['therapist', 'admin']:
            appointments = Appointment.query.filter_by(therapist_id=current_user_id)
        else:
            appointments = Appointment.query.filter_by(client_id=current_user_id)
        
        # Filtrar por estado si se proporciona
        status = request.args.get('status')
        if status:
            appointments = appointments.filter_by(status=status)
        
        # Filtrar por fecha si se proporciona
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        if date_from:
            appointments = appointments.filter(Appointment.appointment_date >= date_from)
        if date_to:
            appointments = appointments.filter(Appointment.appointment_date <= date_to)
        
        # Ordenar por fecha
        appointments = appointments.order_by(
            Appointment.appointment_date.desc(),
            Appointment.appointment_time.desc()
        ).all()
        
        appointments_data = []
        for appt in appointments:
            if user.role in ['therapist', 'admin']:
                other_user = appt.client
            else:
                other_user = appt.therapist
            
            appointments_data.append({
                'id': appt.id,
                'other_user': {
                    'id': other_user.id,
                    'name': f'{other_user.first_name} {other_user.last_name}',
                    'profile_image': other_user.profile_image
                },
                'appointment_date': appt.appointment_date.isoformat(),
                'appointment_time': appt.appointment_time.strftime('%H:%M'),
                'duration': appt.duration,
                'type': appt.appointment_type,
                'status': appt.status,
                'amount': appt.amount,
                'payment_status': appt.payment_status,
                'created_at': appt.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'appointments': appointments_data,
            'count': len(appointments_data)
        }), 200
        
    except Exception as e:
        logger.error(f'Error al obtener citas: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/appointments/<int:appointment_id>', methods=['GET'])
@jwt_required()
def get_appointment(appointment_id):
    """Obtiene detalles de una cita específica"""
    try:
        current_user_id = get_jwt_identity()
        
        appointment = Appointment.query.get(appointment_id)
        
        if not appointment:
            return jsonify({
                'success': False,
                'message': 'Cita no encontrada'
            }), 404
        
        # Verificar permisos
        if appointment.client_id != current_user_id and appointment.therapist_id != current_user_id:
            user = User.query.get(current_user_id)
            if user.role != 'admin':
                return jsonify({
                    'success': False,
                    'message': 'No tienes permisos para ver esta cita'
                }), 403
        
        # Obtener detalles del cliente y terapeuta
        client = User.query.get(appointment.client_id)
        therapist = User.query.get(appointment.therapist_id)
        
        appointment_data = {
            'id': appointment.id,
            'client': {
                'id': client.id,
                'name': f'{client.first_name} {client.last_name}',
                'email': client.email,
                'phone': client.phone,
                'profile_image': client.profile_image
            },
            'therapist': {
                'id': therapist.id,
                'name': f'{therapist.first_name} {therapist.last_name}',
                'email': therapist.email,
                'phone': therapist.phone,
                'profile_image': therapist.profile_image,
                'specialization': therapist.specialization,
                'hourly_rate': therapist.hourly_rate
            },
            'appointment_date': appointment.appointment_date.isoformat(),
            'appointment_time': appointment.appointment_time.strftime('%H:%M'),
            'duration': appointment.duration,
            'type': appointment.appointment_type,
            'status': appointment.status,
            'notes': appointment.notes,
            'amount': appointment.amount,
            'currency': appointment.currency,
            'payment_status': appointment.payment_status,
            'meeting_link': appointment.meeting_link,
            'created_at': appointment.created_at.isoformat(),
            'updated_at': appointment.updated_at.isoformat() if appointment.updated_at else None
        }
        
        # Incluir información de sesión si existe
        if appointment.session:
            session_data = {
                'id': appointment.session.id,
                'start_time': appointment.session.start_time.isoformat() if appointment.session.start_time else None,
                'end_time': appointment.session.end_time.isoformat() if appointment.session.end_time else None,
                'duration': appointment.session.duration,
                'notes': appointment.session.notes,
                'mood_start': appointment.session.mood_start,
                'mood_end': appointment.session.mood_end,
                'satisfaction_score': appointment.session.satisfaction_score
            }
            appointment_data['session'] = session_data
        
        return jsonify({
            'success': True,
            'appointment': appointment_data
        }), 200
        
    except Exception as e:
        logger.error(f'Error al obtener cita: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/appointments/<int:appointment_id>', methods=['PUT'])
@jwt_required()
def update_appointment(appointment_id):
    """Actualiza una cita"""
    try:
        current_user_id = get_jwt_identity()
        
        appointment = Appointment.query.get(appointment_id)
        
        if not appointment:
            return jsonify({
                'success': False,
                'message': 'Cita no encontrada'
            }), 404
        
        # Verificar permisos
        if appointment.client_id != current_user_id and appointment.therapist_id != current_user_id:
            user = User.query.get(current_user_id)
            if user.role != 'admin':
                return jsonify({
                    'success': False,
                    'message': 'No tienes permisos para actualizar esta cita'
                }), 403
        
        data = request.get_json()
        
        # Campos actualizables
        updatable_fields = ['notes', 'status', 'payment_status', 'meeting_link']
        
        for field in updatable_fields:
            if field in data:
                setattr(appointment, field, data[field])
        
        appointment.updated_at = datetime.datetime.utcnow()
        db.session.commit()
        
        # Notificar al otro usuario sobre el cambio
        if current_user_id == appointment.client_id:
            notify_user_id = appointment.therapist_id
        else:
            notify_user_id = appointment.client_id
        
        NotificationSystem.create_notification(
            user_id=notify_user_id,
            title='Cita actualizada',
            message=f'La cita ha sido actualizada',
            notification_type='appointment',
            action_url=f'/appointments/{appointment.id}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Cita actualizada exitosamente',
            'appointment': {
                'id': appointment.id,
                'status': appointment.status,
                'payment_status': appointment.payment_status,
                'notes': appointment.notes
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error al actualizar cita: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/appointments/<int:appointment_id>', methods=['DELETE'])
@jwt_required()
def cancel_appointment(appointment_id):
    """Cancela una cita"""
    try:
        current_user_id = get_jwt_identity()
        
        appointment = Appointment.query.get(appointment_id)
        
        if not appointment:
            return jsonify({
                'success': False,
                'message': 'Cita no encontrada'
            }), 404
        
        # Verificar permisos
        if appointment.client_id != current_user_id and appointment.therapist_id != current_user_id:
            user = User.query.get(current_user_id)
            if user.role != 'admin':
                return jsonify({
                    'success': False,
                    'message': 'No tienes permisos para cancelar esta cita'
                }), 403
        
        # Solo permitir cancelar citas programadas o confirmadas
        if appointment.status not in ['scheduled', 'confirmed']:
            return jsonify({
                'success': False,
                'message': f'No se puede cancelar una cita con estado {appointment.status}'
            }), 400
        
        # Cancelar cita
        old_status = appointment.status
        appointment.status = 'cancelled'
        appointment.updated_at = datetime.datetime.utcnow()
        
        # Reembolsar si ya estaba pagada
        if appointment.payment_status == 'paid':
            # Aquí se implementaría la lógica de reembolso con Stripe
            appointment.payment_status = 'refunded'
        
        db.session.commit()
        
        # Notificar al otro usuario sobre la cancelación
        if current_user_id == appointment.client_id:
            notify_user_id = appointment.therapist_id
            cancelled_by = 'cliente'
        else:
            notify_user_id = appointment.client_id
            cancelled_by = 'terapeuta'
        
        NotificationSystem.create_notification(
            user_id=notify_user_id,
            title='Cita cancelada',
            message=f'La cita ha sido cancelada por el {cancelled_by}',
            notification_type='appointment',
            action_url=f'/appointments/{appointment.id}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Cita cancelada exitosamente',
            'appointment': {
                'id': appointment.id,
                'status': appointment.status,
                'previous_status': old_status
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error al cancelar cita: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

# ------------------------------------------------------------
# RUTAS DE SESIONES
# ------------------------------------------------------------

@users_blueprint.route('/api/sessions', methods=['POST'])
@jwt_required()
@therapist_required
def create_session():
    """Crea una sesión para una cita (solo terapeutas)"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar campos requeridos
        required_fields = ['appointment_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Campo requerido faltante: {field}'
                }), 400
        
        # Verificar si la cita existe y pertenece al terapeuta
        appointment = Appointment.query.get(data['appointment_id'])
        
        if not appointment:
            return jsonify({
                'success': False,
                'message': 'Cita no encontrada'
            }), 404
        
        if appointment.therapist_id != current_user_id:
            return jsonify({
                'success': False,
                'message': 'No tienes permisos para crear una sesión para esta cita'
            }), 403
        
        # Verificar si ya existe una sesión para esta cita
        existing_session = Session.query.filter_by(appointment_id=data['appointment_id']).first()
        if existing_session:
            return jsonify({
                'success': False,
                'message': 'Ya existe una sesión para esta cita'
            }), 400
        
        # Verificar que la cita esté confirmada
        if appointment.status != 'confirmed':
            return jsonify({
                'success': False,
                'message': 'La cita debe estar confirmada para crear una sesión'
            }), 400
        
        # Crear sesión
        session = Session(
            appointment_id=data['appointment_id'],
            participant_id=appointment.client_id,
            notes=data.get('notes', ''),
            mood_start=data.get('mood_start'),
            therapist_notes=data.get('therapist_notes', ''),
            homework_assigned=data.get('homework_assigned', ''),
            next_session_plan=data.get('next_session_plan', '')
        )
        
        db.session.add(session)
        
        # Actualizar estado de la cita
        appointment.status = 'in_session'
        appointment.updated_at = datetime.datetime.utcnow()
        
        db.session.commit()
        
        # Notificar al cliente
        NotificationSystem.create_notification(
            user_id=appointment.client_id,
            title='Sesión iniciada',
            message=f'Tu terapeuta ha iniciado la sesión',
            notification_type='session',
            action_url=f'/sessions/{session.id}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Sesión creada exitosamente',
            'session': {
                'id': session.id,
                'appointment_id': session.appointment_id,
                'start_time': session.start_time.isoformat() if session.start_time else None,
                'notes': session.notes,
                'mood_start': session.mood_start
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error al crear sesión: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/sessions/<int:session_id>', methods=['PUT'])
@jwt_required()
def update_session(session_id):
    """Actualiza una sesión (termina sesión, agrega notas, etc.)"""
    try:
        current_user_id = get_jwt_identity()
        
        session = Session.query.get(session_id)
        
        if not session:
            return jsonify({
                'success': False,
                'message': 'Sesión no encontrada'
            }), 404
        
        # Verificar permisos
        appointment = session.appointment
        if appointment.therapist_id != current_user_id and appointment.client_id != current_user_id:
            user = User.query.get(current_user_id)
            if user.role != 'admin':
                return jsonify({
                    'success': False,
                    'message': 'No tienes permisos para actualizar esta sesión'
                }), 403
        
        data = request.get_json()
        
        # Manejar finalización de sesión
        if data.get('end_session'):
            if not session.end_time:
                session.end_time = datetime.datetime.utcnow()
                
                # Calcular duración en minutos
                if session.start_time:
                    duration = (session.end_time - session.start_time).total_seconds() / 60
                    session.duration = int(duration)
                
                # Actualizar estado de la cita
                appointment.status = 'completed'
                appointment.updated_at = datetime.datetime.utcnow()
        
        # Actualizar campos
        updatable_fields = [
            'notes', 'mood_end', 'satisfaction_score',
            'therapist_notes', 'homework_assigned', 'next_session_plan',
            'recording_url', 'transcript'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(session, field, data[field])
        
        db.session.commit()
        
        # Notificar al otro usuario sobre la actualización
        if current_user_id == appointment.client_id:
            notify_user_id = appointment.therapist_id
        else:
            notify_user_id = appointment.client_id
        
        NotificationSystem.create_notification(
            user_id=notify_user_id,
            title='Sesión actualizada',
            message=f'La sesión ha sido actualizada',
            notification_type='session',
            action_url=f'/sessions/{session.id}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Sesión actualizada exitosamente',
            'session': {
                'id': session.id,
                'end_time': session.end_time.isoformat() if session.end_time else None,
                'duration': session.duration,
                'mood_end': session.mood_end,
                'satisfaction_score': session.satisfaction_score
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error al actualizar sesión: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/sessions/<int:session_id>', methods=['GET'])
@jwt_required()
def get_session(session_id):
    """Obtiene detalles de una sesión"""
    try:
        current_user_id = get_jwt_identity()
        
        session = Session.query.get(session_id)
        
        if not session:
            return jsonify({
                'success': False,
                'message': 'Sesión no encontrada'
            }), 404
        
        # Verificar permisos
        appointment = session.appointment
        if appointment.therapist_id != current_user_id and appointment.client_id != current_user_id:
            user = User.query.get(current_user_id)
            if user.role != 'admin':
                return jsonify({
                    'success': False,
                    'message': 'No tienes permisos para ver esta sesión'
                }), 403
        
        # Obtener información de la cita
        appointment_data = {
            'id': appointment.id,
            'date': appointment.appointment_date.isoformat(),
            'time': appointment.appointment_time.strftime('%H:%M'),
            'type': appointment.appointment_type
        }
        
        # Obtener información del cliente y terapeuta
        client = appointment.client
        therapist = appointment.therapist
        
        session_data = {
            'id': session.id,
            'appointment': appointment_data,
            'client': {
                'id': client.id,
                'name': f'{client.first_name} {client.last_name}'
            },
            'therapist': {
                'id': therapist.id,
                'name': f'{therapist.first_name} {therapist.last_name}'
            },
            'start_time': session.start_time.isoformat() if session.start_time else None,
            'end_time': session.end_time.isoformat() if session.end_time else None,
            'duration': session.duration,
            'notes': session.notes,
            'mood_start': session.mood_start,
            'mood_end': session.mood_end,
            'satisfaction_score': session.satisfaction_score,
            'therapist_notes': session.therapist_notes if current_user_id == therapist.id or user.role == 'admin' else None,
            'homework_assigned': session.homework_assigned,
            'next_session_plan': session.next_session_plan,
            'recording_url': session.recording_url,
            'transcript': session.transcript,
            'created_at': session.created_at.isoformat()
        }
        
        return jsonify({
            'success': True,
            'session': session_data
        }), 200
        
    except Exception as e:
        logger.error(f'Error al obtener sesión: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

# ------------------------------------------------------------
# RUTAS DE MENSAJES
# ------------------------------------------------------------

@users_blueprint.route('/api/messages', methods=['GET'])
@jwt_required()
def get_messages():
    """Obtiene mensajes del usuario"""
    try:
        current_user_id = get_jwt_identity()
        
        # Obtener ID del otro usuario (si se proporciona)
        other_user_id = request.args.get('user_id')
        
        if other_user_id:
            # Obtener conversación específica
            messages = Message.query.filter(
                ((Message.sender_id == current_user_id) & (Message.receiver_id == other_user_id)) |
                ((Message.sender_id == other_user_id) & (Message.receiver_id == current_user_id))
            ).order_by(Message.timestamp.asc()).all()
            
            # Marcar mensajes como leídos
            unread_messages = Message.query.filter_by(
                sender_id=other_user_id,
                receiver_id=current_user_id,
                is_read=False
            ).all()
            
            for msg in unread_messages:
                msg.is_read = True
                msg.read_timestamp = datetime.datetime.utcnow()
            
            db.session.commit()
            
            messages_data = []
            for msg in messages:
                sender = User.query.get(msg.sender_id)
                messages_data.append({
                    'id': msg.id,
                    'sender_id': msg.sender_id,
                    'sender_name': f'{sender.first_name} {sender.last_name}',
                    'sender_avatar': sender.profile_image,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'is_read': msg.is_read,
                    'type': msg.message_type,
                    'attachment_url': msg.attachment_url
                })
            
            return jsonify({
                'success': True,
                'messages': messages_data
            }), 200
        
        else:
            # Obtener lista de conversaciones
            # Obtener todos los usuarios con los que ha intercambiado mensajes
            subquery_sent = db.session.query(
                Message.receiver_id.label('user_id'),
                func.max(Message.timestamp).label('last_message')
            ).filter(Message.sender_id == current_user_id).group_by(Message.receiver_id).subquery()
            
            subquery_received = db.session.query(
                Message.sender_id.label('user_id'),
                func.max(Message.timestamp).label('last_message')
            ).filter(Message.receiver_id == current_user_id).group_by(Message.sender_id).subquery()
            
            # Combinar resultados
            conversations = db.session.query(
                func.coalesce(subquery_sent.c.user_id, subquery_received.c.user_id).label('user_id'),
                func.greatest(
                    func.coalesce(subquery_sent.c.last_message, datetime.datetime.min),
                    func.coalesce(subquery_received.c.last_message, datetime.datetime.min)
                ).label('last_message_time')
            ).outerjoin(
                subquery_received,
                subquery_sent.c.user_id == subquery_received.c.user_id
            ).union(
                db.session.query(
                    subquery_received.c.user_id,
                    subquery_received.c.last_message
                ).filter(~subquery_received.c.user_id.in_(
                    db.session.query(subquery_sent.c.user_id)
                ))
            ).subquery()
            
            # Obtener detalles de conversaciones
            conv_query = db.session.query(
                User.id,
                User.first_name,
                User.last_name,
                User.profile_image,
                User.role,
                conversations.c.last_message_time,
                func.count(Message.id).filter(Message.is_read == False).label('unread_count')
            ).join(
                conversations, User.id == conversations.c.user_id
            ).outerjoin(
                Message,
                (Message.sender_id == User.id) & (Message.receiver_id == current_user_id) & (Message.is_read == False)
            ).group_by(
                User.id, conversations.c.last_message_time
            ).order_by(conversations.c.last_message_time.desc()).all()
            
            conversations_data = []
            for conv in conv_query:
                conversations_data.append({
                    'user_id': conv.id,
                    'user_name': f'{conv.first_name} {conv.last_name}',
                    'user_avatar': conv.profile_image,
                    'user_role': conv.role,
                    'last_message_time': conv.last_message_time.isoformat() if conv.last_message_time else None,
                    'unread_count': conv.unread_count or 0
                })
            
            return jsonify({
                'success': True,
                'conversations': conversations_data
            }), 200
            
    except Exception as e:
        logger.error(f'Error al obtener mensajes: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/messages/unread', methods=['GET'])
@jwt_required()
def get_unread_count():
    """Obtiene el número de mensajes no leídos"""
    try:
        current_user_id = get_jwt_identity()
        
        unread_count = Message.query.filter_by(
            receiver_id=current_user_id,
            is_read=False
        ).count()
        
        return jsonify({
            'success': True,
            'unread_count': unread_count
        }), 200
        
    except Exception as e:
        logger.error(f'Error al obtener conteo de no leídos: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/messages', methods=['POST'])
@jwt_required()
def send_message():
    """Envía un mensaje"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar campos requeridos
        required_fields = ['receiver_id', 'content']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Campo requerido faltante: {field}'
                }), 400
        
        # Verificar si el receptor existe
        receiver = User.query.get(data['receiver_id'])
        if not receiver:
            return jsonify({
                'success': False,
                'message': 'Usuario receptor no encontrado'
            }), 404
        
        # Verificar si el receptor ha bloqueado al remitente
        blocker_check = db.session.query(user_blocks).filter_by(
            blocker_id=data['receiver_id'],
            blocked_id=current_user_id
        ).first()
        
        if blocker_check:
            return jsonify({
                'success': False,
                'message': 'No puedes enviar mensajes a este usuario'
            }), 403
        
        # Crear mensaje
        message = Message(
            sender_id=current_user_id,
            receiver_id=data['receiver_id'],
            content=data['content'],
            message_type=data.get('type', 'text'),
            attachment_url=data.get('attachment_url')
        )
        
        db.session.add(message)
        db.session.commit()
        
        # Notificar al receptor via Socket.IO (si está conectado)
        socketio.emit('new_message', {
            'id': message.id,
            'sender_id': current_user_id,
            'sender_name': f'{current_user.first_name} {current_user.last_name}',
            'sender_avatar': current_user.profile_image or '/static/images/default-avatar.png',
            'content': data['content'],
            'timestamp': message.timestamp.isoformat(),
            'type': data.get('type', 'text')
        }, room=f'user_{data["receiver_id"]}')
        
        # Crear notificación para el receptor
        NotificationSystem.create_notification(
            user_id=data['receiver_id'],
            title='Nuevo mensaje',
            message=f'Tienes un nuevo mensaje de {current_user.first_name}',
            notification_type='message',
            action_url=f'/messages/{current_user_id}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Mensaje enviado exitosamente',
            'message_id': message.id,
            'timestamp': message.timestamp.isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error al enviar mensaje: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

# ------------------------------------------------------------
# RUTAS DE TERAPEUTAS
# ------------------------------------------------------------

@users_blueprint.route('/api/therapists', methods=['GET'])
def get_therapists():
    """Obtiene lista de terapeutas"""
    try:
        # Filtrar usuarios con rol de terapeuta
        therapists = User.query.filter(User.role.in_(['therapist', 'admin'])).filter_by(is_active=True).all()
        
        therapists_data = []
        for therapist in therapists:
            # Obtener estadísticas del terapeuta
            total_appointments = Appointment.query.filter_by(therapist_id=therapist.id).count()
            completed_appointments = Appointment.query.filter_by(therapist_id=therapist.id, status='completed').count()
            
            # Obtener calificación promedio
            avg_rating_result = db.session.query(func.avg(Review.rating)).filter_by(therapist_id=therapist.id).first()
            avg_rating = avg_rating_result[0] if avg_rating_result[0] else 0.0
            
            therapists_data.append({
                'id': therapist.id,
                'name': f'{therapist.first_name} {therapist.last_name}',
                'profile_image': therapist.profile_image,
                'specialization': therapist.specialization,
                'qualifications': therapist.qualifications,
                'experience_years': therapist.experience_years,
                'hourly_rate': therapist.hourly_rate,
                'bio': therapist.bio,
                'avg_rating': round(avg_rating, 1),
                'total_appointments': total_appointments,
                'completed_appointments': completed_appointments,
                'is_verified': therapist.is_verified
            })
        
        return jsonify({
            'success': True,
            'therapists': therapists_data,
            'count': len(therapists_data)
        }), 200
        
    except Exception as e:
        logger.error(f'Error al obtener terapeutas: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/therapists/<int:therapist_id>', methods=['GET'])
def get_therapist_detail(therapist_id):
    """Obtiene detalles de un terapeuta específico"""
    try:
        therapist = User.query.get(therapist_id)
        
        if not therapist or therapist.role not in ['therapist', 'admin']:
            return jsonify({
                'success': False,
                'message': 'Terapeuta no encontrado'
            }), 404
        
        # Obtener estadísticas
        total_appointments = Appointment.query.filter_by(therapist_id=therapist.id).count()
        completed_appointments = Appointment.query.filter_by(therapist_id=therapist.id, status='completed').count()
        
        # Obtener calificación promedio y reseñas
        reviews = Review.query.filter_by(therapist_id=therapist.id).order_by(Review.created_at.desc()).limit(10).all()
        
        avg_rating_result = db.session.query(func.avg(Review.rating)).filter_by(therapist_id=therapist.id).first()
        avg_rating = avg_rating_result[0] if avg_rating_result[0] else 0.0
        
        reviews_data = []
        for review in reviews:
            client = review.reviewer
            reviews_data.append({
                'id': review.id,
                'client_name': f'{client.first_name} {client.last_name}',
                'client_avatar': client.profile_image,
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at.isoformat(),
                'response': review.response,
                'response_date': review.response_date.isoformat() if review.response_date else None
            })
        
        # Obtener disponibilidad (esto sería más complejo en producción)
        # Por ahora, devolvemos horarios de trabajo básicos
        availability = {
            'monday': {'start': '09:00', 'end': '18:00'},
            'tuesday': {'start': '09:00', 'end': '18:00'},
            'wednesday': {'start': '09:00', 'end': '18:00'},
            'thursday': {'start': '09:00', 'end': '18:00'},
            'friday': {'start': '09:00', 'end': '18:00'},
            'saturday': {'start': '10:00', 'end': '14:00'},
            'sunday': {'start': '10:00', 'end': '14:00'}
        }
        
        therapist_data = {
            'id': therapist.id,
            'name': f'{therapist.first_name} {therapist.last_name}',
            'email': therapist.email,
            'phone': therapist.phone,
            'profile_image': therapist.profile_image,
            'bio': therapist.bio,
            'specialization': therapist.specialization,
            'qualifications': therapist.qualifications,
            'experience_years': therapist.experience_years,
            'hourly_rate': therapist.hourly_rate,
            'avg_rating': round(avg_rating, 1),
            'total_reviews': len(reviews),
            'total_appointments': total_appointments,
            'completed_appointments': completed_appointments,
            'is_verified': therapist.is_verified,
            'availability': availability,
            'reviews': reviews_data
        }
        
        return jsonify({
            'success': True,
            'therapist': therapist_data
        }), 200
        
    except Exception as e:
        logger.error(f'Error al obtener detalle de terapeuta: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/therapists/<int:therapist_id>/availability', methods=['GET'])
def get_therapist_availability(therapist_id):
    """Obtiene disponibilidad de un terapeuta"""
    try:
        therapist = User.query.get(therapist_id)
        
        if not therapist or therapist.role not in ['therapist', 'admin']:
            return jsonify({
                'success': False,
                'message': 'Terapeuta no encontrado'
            }), 404
        
        # Obtener fecha específica si se proporciona
        date_str = request.args.get('date')
        if date_str:
            try:
                target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Formato de fecha inválido. Use YYYY-MM-DD.'
                }), 400
        else:
            # Por defecto, hoy
            target_date = datetime.date.today()
        
        # Obtener citas existentes para esa fecha
        appointments = Appointment.query.filter_by(
            therapist_id=therapist_id,
            appointment_date=target_date,
            status='scheduled'
        ).all()
        
        # Horarios ocupados
        busy_slots = []
        for appt in appointments:
            busy_slots.append({
                'start': appt.appointment_time.strftime('%H:%M'),
                'end': (datetime.datetime.combine(target_date, appt.appointment_time) + 
                       datetime.timedelta(minutes=appt.duration)).strftime('%H:%M')
            })
        
        # Generar horarios disponibles (ejemplo básico)
        # En producción, esto dependería de las preferencias del terapeuta
        available_slots = []
        start_hour = 9
        end_hour = 18
        
        for hour in range(start_hour, end_hour):
            for minute in [0, 30]:
                slot_time = f'{hour:02d}:{minute:02d}'
                
                # Verificar si el horario está ocupado
                is_busy = False
                for busy in busy_slots:
                    busy_start = datetime.datetime.strptime(busy['start'], '%H:%M').time()
                    busy_end = datetime.datetime.strptime(busy['end'], '%H:%M').time()
                    slot_time_obj = datetime.datetime.strptime(slot_time, '%H:%M').time()
                    
                    if busy_start <= slot_time_obj < busy_end:
                        is_busy = True
                        break
                
                if not is_busy:
                    available_slots.append(slot_time)
        
        return jsonify({
            'success': True,
            'date': target_date.isoformat(),
            'therapist_id': therapist_id,
            'available_slots': available_slots,
            'busy_slots': busy_slots
        }), 200
        
    except Exception as e:
        logger.error(f'Error al obtener disponibilidad: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

# ------------------------------------------------------------
# RUTAS DE RESEÑAS
# ------------------------------------------------------------

@users_blueprint.route('/api/reviews', methods=['POST'])
@jwt_required()
def create_review():
    """Crea una reseña para un terapeuta"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar campos requeridos
        required_fields = ['therapist_id', 'rating']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Campo requerido faltante: {field}'
                }), 400
        
        # Verificar si el terapeuta existe
        therapist = User.query.get(data['therapist_id'])
        if not therapist or therapist.role not in ['therapist', 'admin']:
            return jsonify({
                'success': False,
                'message': 'Terapeuta no encontrado'
            }), 404
        
        # Verificar si ya existe una reseña del cliente para este terapeuta
        existing_review = Review.query.filter_by(
            client_id=current_user_id,
            therapist_id=data['therapist_id']
        ).first()
        
        if existing_review:
            return jsonify({
                'success': False,
                'message': 'Ya has escrito una reseña para este terapeuta'
            }), 400
        
        # Verificar que el cliente haya tenido al menos una cita completada con el terapeuta
        completed_appointment = Appointment.query.filter_by(
            client_id=current_user_id,
            therapist_id=data['therapist_id'],
            status='completed'
        ).first()
        
        if not completed_appointment:
            return jsonify({
                'success': False,
                'message': 'Debes haber completado al menos una cita con el terapeuta para escribir una reseña'
            }), 400
        
        # Validar rating (1-5)
        rating = int(data['rating'])
        if rating < 1 or rating > 5:
            return jsonify({
                'success': False,
                'message': 'El rating debe estar entre 1 y 5'
            }), 400
        
        # Crear reseña
        review = Review(
            client_id=current_user_id,
            therapist_id=data['therapist_id'],
            rating=rating,
            comment=data.get('comment', '')
        )
        
        db.session.add(review)
        db.session.commit()
        
        # Notificar al terapeuta
        NotificationSystem.create_notification(
            user_id=therapist.id,
            title='Nueva reseña',
            message=f'Tienes una nueva reseña de {current_user.first_name}',
            notification_type='review',
            action_url=f'/reviews/{review.id}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Reseña creada exitosamente',
            'review': {
                'id': review.id,
                'therapist_id': review.therapist_id,
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error al crear reseña: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/reviews/<int:review_id>', methods=['PUT'])
@jwt_required()
def update_review(review_id):
    """Actualiza una reseña (solo el autor o administrador)"""
    try:
        current_user_id = get_jwt_identity()
        
        review = Review.query.get(review_id)
        
        if not review:
            return jsonify({
                'success': False,
                'message': 'Reseña no encontrada'
            }), 404
        
        # Verificar permisos
        user = User.query.get(current_user_id)
        if review.client_id != current_user_id and user.role != 'admin':
            return jsonify({
                'success': False,
                'message': 'No tienes permisos para actualizar esta reseña'
            }), 403
        
        data = request.get_json()
        
        # Actualizar campos permitidos
        if 'rating' in data:
            rating = int(data['rating'])
            if rating < 1 or rating > 5:
                return jsonify({
                    'success': False,
                    'message': 'El rating debe estar entre 1 y 5'
                }), 400
            review.rating = rating
        
        if 'comment' in data:
            review.comment = data['comment']
        
        review.updated_at = datetime.datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Reseña actualizada exitosamente',
            'review': {
                'id': review.id,
                'rating': review.rating,
                'comment': review.comment,
                'updated_at': review.updated_at.isoformat()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error al actualizar reseña: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/reviews/<int:review_id>/response', methods=['POST'])
@jwt_required()
@therapist_required
def add_review_response(review_id):
    """Agrega una respuesta a una reseña (solo el terapeuta)"""
    try:
        current_user_id = get_jwt_identity()
        
        review = Review.query.get(review_id)
        
        if not review:
            return jsonify({
                'success': False,
                'message': 'Reseña no encontrada'
            }), 404
        
        # Verificar que el terapeuta sea el dueño de la reseña
        if review.therapist_id != current_user_id:
            return jsonify({
                'success': False,
                'message': 'No tienes permisos para responder a esta reseña'
            }), 403
        
        data = request.get_json()
        
        if 'response' not in data:
            return jsonify({
                'success': False,
                'message': 'El campo response es requerido'
            }), 400
        
        # Agregar respuesta
        review.response = data['response']
        review.response_date = datetime.datetime.utcnow()
        db.session.commit()
        
        # Notificar al cliente
        NotificationSystem.create_notification(
            user_id=review.client_id,
            title='Respuesta a tu reseña',
            message=f'El terapeuta ha respondido a tu reseña',
            notification_type='review',
            action_url=f'/reviews/{review.id}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Respuesta agregada exitosamente',
            'review': {
                'id': review.id,
                'response': review.response,
                'response_date': review.response_date.isoformat()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error al agregar respuesta: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

# ------------------------------------------------------------
# RUTAS DE PRODUCTOS
# ------------------------------------------------------------

@users_blueprint.route('/api/products', methods=['GET'])
def get_products():
    """Obtiene lista de productos"""
    try:
        # Filtros
        category = request.args.get('category')
        min_price = request.args.get('min_price')
        max_price = request.args.get('max_price')
        search = request.args.get('search')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        query = Product.query.filter_by(is_active=True)
        
        # Aplicar filtros
        if category:
            query = query.filter_by(category=category)
        
        if min_price:
            query = query.filter(Product.price >= float(min_price))
        
        if max_price:
            query = query.filter(Product.price <= float(max_price))
        
        if search:
            search_term = f'%{search}%'
            query = query.filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.description.ilike(search_term),
                    Product.tags.ilike(search_term)
                )
            )
        
        # Ordenar
        if sort_by == 'price':
            if sort_order == 'asc':
                query = query.order_by(Product.price.asc())
            else:
                query = query.order_by(Product.price.desc())
        elif sort_by == 'rating':
            if sort_order == 'asc':
                query = query.order_by(Product.rating.asc())
            else:
                query = query.order_by(Product.rating.desc())
        else:  # created_at
            if sort_order == 'asc':
                query = query.order_by(Product.created_at.asc())
            else:
                query = query.order_by(Product.created_at.desc())
        
        products = query.all()
        
        products_data = []
        for product in products:
            creator = product.creator
            products_data.append({
                'id': product.id,
                'name': product.name,
                'description': product.description[:200] + '...' if len(product.description) > 200 else product.description,
                'price': product.price,
                'discount_price': product.discount_price,
                'category': product.category,
                'image_url': product.image_url,
                'rating': product.rating,
                'review_count': product.review_count,
                'creator': {
                    'id': creator.id if creator else None,
                    'name': f'{creator.first_name} {creator.last_name}' if creator else 'Administrador'
                },
                'is_digital': product.is_digital,
                'created_at': product.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'products': products_data,
            'count': len(products_data)
        }), 200
        
    except Exception as e:
        logger.error(f'Error al obtener productos: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/products', methods=['POST'])
@jwt_required()
@admin_required
def create_product():
    """Crea un nuevo producto (solo administrador)"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar campos requeridos
        required_fields = ['name', 'price', 'category']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Campo requerido faltante: {field}'
                }), 400
        
        # Crear producto
        product = Product(
            name=data['name'],
            description=data.get('description', ''),
            price=float(data['price']),
            discount_price=float(data['discount_price']) if 'discount_price' in data else None,
            category=data['category'],
            subcategory=data.get('subcategory'),
            tags=data.get('tags', ''),
            is_digital=data.get('is_digital', False),
            digital_file_url=data.get('digital_file_url'),
            creator_id=current_user_id,
            stock_quantity=data.get('stock_quantity', 0)
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Producto creado exitosamente',
            'product': {
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'category': product.category,
                'is_digital': product.is_digital
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error al crear producto: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Obtiene detalles de un producto específico"""
    try:
        product = Product.query.get(product_id)
        
        if not product or not product.is_active:
            return jsonify({
                'success': False,
                'message': 'Producto no encontrado'
            }), 404
        
        # Incrementar contador de vistas
        product.views += 1
        db.session.commit()
        
        creator = product.creator
        product_data = {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'discount_price': product.discount_price,
            'category': product.category,
            'subcategory': product.subcategory,
            'tags': product.tags.split(',') if product.tags else [],
            'image_url': product.image_url,
            'stock_quantity': product.stock_quantity,
            'is_digital': product.is_digital,
            'digital_file_url': product.digital_file_url,
            'rating': product.rating,
            'review_count': product.review_count,
            'views': product.views,
            'purchases': product.purchases,
            'creator': {
                'id': creator.id if creator else None,
                'name': f'{creator.first_name} {creator.last_name}' if creator else 'Administrador',
                'profile_image': creator.profile_image if creator else None
            },
            'created_at': product.created_at.isoformat(),
            'updated_at': product.updated_at.isoformat() if product.updated_at else None
        }
        
        return jsonify({
            'success': True,
            'product': product_data
        }), 200
        
    except Exception as e:
        logger.error(f'Error al obtener producto: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

# ------------------------------------------------------------
# RUTAS DE CARRITO DE COMPRAS Y ÓRDENES
# ------------------------------------------------------------

@users_blueprint.route('/api/cart', methods=['GET'])
@jwt_required()
def get_cart():
    """Obtiene el carrito del usuario (sesión basada)"""
    try:
        cart = session.get('cart', {})
        
        # Obtener detalles de productos en el carrito
        cart_items = []
        total = 0
        
        for product_id_str, item_data in cart.items():
            try:
                product_id = int(product_id_str)
                product = Product.query.get(product_id)
                
                if product and product.is_active:
                    quantity = item_data.get('quantity', 1)
                    price = product.discount_price or product.price
                    subtotal = price * quantity
                    
                    cart_items.append({
                        'product_id': product.id,
                        'name': product.name,
                        'price': price,
                        'quantity': quantity,
                        'subtotal': subtotal,
                        'image_url': product.image_url,
                        'is_digital': product.is_digital
                    })
                    
                    total += subtotal
            
            except (ValueError, TypeError):
                continue
        
        return jsonify({
            'success': True,
            'cart': {
                'items': cart_items,
                'total': total,
                'item_count': len(cart_items)
            }
        }), 200
        
    except Exception as e:
        logger.error(f'Error al obtener carrito: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/cart', methods=['POST'])
@jwt_required()
def add_to_cart():
    """Agrega un producto al carrito"""
    try:
        data = request.get_json()
        
        required_fields = ['product_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Campo requerido faltante: {field}'
                }), 400
        
        product_id = data['product_id']
        quantity = data.get('quantity', 1)
        
        # Verificar si el producto existe y está activo
        product = Product.query.get(product_id)
        if not product or not product.is_active:
            return jsonify({
                'success': False,
                'message': 'Producto no encontrado'
            }), 404
        
        # Verificar stock si no es digital
        if not product.is_digital and product.stock_quantity < quantity:
            return jsonify({
                'success': False,
                'message': 'Stock insuficiente'
            }), 400
        
        # Inicializar carrito si no existe
        if 'cart' not in session:
            session['cart'] = {}
        
        cart = session['cart']
        
        # Agregar o actualizar producto en el carrito
        if str(product_id) in cart:
            cart[str(product_id)]['quantity'] += quantity
        else:
            cart[str(product_id)] = {
                'quantity': quantity,
                'added_at': datetime.datetime.utcnow().isoformat()
            }
        
        session['cart'] = cart
        session.modified = True
        
        return jsonify({
            'success': True,
            'message': 'Producto agregado al carrito',
            'cart_item_count': len(cart)
        }), 200
        
    except Exception as e:
        logger.error(f'Error al agregar al carrito: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/cart/<int:product_id>', methods=['DELETE'])
@jwt_required()
def remove_from_cart(product_id):
    """Elimina un producto del carrito"""
    try:
        if 'cart' not in session:
            return jsonify({
                'success': False,
                'message': 'El carrito está vacío'
            }), 400
        
        cart = session['cart']
        
        if str(product_id) not in cart:
            return jsonify({
                'success': False,
                'message': 'Producto no encontrado en el carrito'
            }), 404
        
        # Eliminar producto
        del cart[str(product_id)]
        session['cart'] = cart
        session.modified = True
        
        return jsonify({
            'success': True,
            'message': 'Producto eliminado del carrito',
            'cart_item_count': len(cart)
        }), 200
        
    except Exception as e:
        logger.error(f'Error al eliminar del carrito: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/cart/clear', methods=['POST'])
@jwt_required()
def clear_cart():
    """Vacía el carrito"""
    try:
        session.pop('cart', None)
        session.modified = True
        
        return jsonify({
            'success': True,
            'message': 'Carrito vaciado exitosamente'
        }), 200
        
    except Exception as e:
        logger.error(f'Error al vaciar carrito: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/orders', methods=['POST'])
@jwt_required()
def create_order():
    """Crea una orden a partir del carrito"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'Usuario no encontrado'
            }), 404
        
        # Obtener carrito de la sesión
        cart = session.get('cart', {})
        
        if not cart:
            return jsonify({
                'success': False,
                'message': 'El carrito está vacío'
            }), 400
        
        # Verificar y preparar items
        order_items = []
        total_amount = 0
        
        for product_id_str, item_data in cart.items():
            try:
                product_id = int(product_id_str)
                product = Product.query.get(product_id)
                
                if not product or not product.is_active:
                    continue
                
                quantity = item_data.get('quantity', 1)
                
                # Verificar stock si no es digital
                if not product.is_digital and product.stock_quantity < quantity:
                    return jsonify({
                        'success': False,
                        'message': f'Stock insuficiente para: {product.name}'
                    }), 400
                
                # Calcular precio (usar precio con descuento si existe)
                price = product.discount_price or product.price
                subtotal = price * quantity
                
                order_items.append({
                    'product': product,
                    'quantity': quantity,
                    'price': price,
                    'subtotal': subtotal
                })
                
                total_amount += subtotal
            
            except (ValueError, TypeError):
                continue
        
        if not order_items:
            return jsonify({
                'success': False,
                'message': 'No hay productos válidos en el carrito'
            }), 400
        
        # Crear número de orden único
        order_number = generate_order_number()
        
        # Crear orden
        order = Order(
            order_number=order_number,
            customer_id=current_user_id,
            total_amount=total_amount,
            final_amount=total_amount,
            shipping_address=user.address,
            billing_address=user.address
        )
        
        db.session.add(order)
        db.session.flush()  # Para obtener el ID de la orden
        
        # Crear items de orden
        for item in order_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item['product'].id,
                quantity=item['quantity'],
                unit_price=item['price'],
                subtotal=item['subtotal']
            )
            
            db.session.add(order_item)
            
            # Actualizar stock y contador de compras
            if not item['product'].is_digital:
                item['product'].stock_quantity -= item['quantity']
            item['product'].purchases += item['quantity']
        
        db.session.commit()
        
        # Vaciar carrito
        session.pop('cart', None)
        session.modified = True
        
        # Crear notificación
        NotificationSystem.create_notification(
            user_id=current_user_id,
            title='Orden creada',
            message=f'Tu orden #{order_number} ha sido creada exitosamente',
            notification_type='order',
            action_url=f'/orders/{order.id}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Orden creada exitosamente',
            'order': {
                'id': order.id,
                'order_number': order.order_number,
                'total_amount': order.total_amount,
                'status': order.status,
                'created_at': order.created_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error al crear orden: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/orders', methods=['GET'])
@jwt_required()
def get_orders():
    """Obtiene las órdenes del usuario"""
    try:
        current_user_id = get_jwt_identity()
        
        # Filtrar órdenes del usuario
        orders = Order.query.filter_by(customer_id=current_user_id).order_by(Order.created_at.desc()).all()
        
        orders_data = []
        for order in orders:
            # Obtener items de la orden
            items_data = []
            for item in order.items:
                product = item.product
                items_data.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'quantity': item.quantity,
                    'unit_price': item.unit_price,
                    'subtotal': item.subtotal
                })
            
            orders_data.append({
                'id': order.id,
                'order_number': order.order_number,
                'total_amount': order.total_amount,
                'final_amount': order.final_amount,
                'status': order.status,
                'payment_status': order.payment_status,
                'created_at': order.created_at.isoformat(),
                'items': items_data
            })
        
        return jsonify({
            'success': True,
            'orders': orders_data,
            'count': len(orders_data)
        }), 200
        
    except Exception as e:
        logger.error(f'Error al obtener órdenes: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/orders/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    """Obtiene detalles de una orden específica"""
    try:
        current_user_id = get_jwt_identity()
        
        order = Order.query.get(order_id)
        
        if not order:
            return jsonify({
                'success': False,
                'message': 'Orden no encontrada'
            }), 404
        
        # Verificar permisos
        if order.customer_id != current_user_id:
            user = User.query.get(current_user_id)
            if user.role != 'admin':
                return jsonify({
                    'success': False,
                    'message': 'No tienes permisos para ver esta orden'
                }), 403
        
        # Obtener items de la orden
        items_data = []
        for item in order.items:
            product = item.product
            items_data.append({
                'product_id': product.id,
                'product_name': product.name,
                'product_image': product.image_url,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'subtotal': item.subtotal
            })
        
        # Obtener información del cliente
        customer = order.customer
        
        order_data = {
            'id': order.id,
            'order_number': order.order_number,
            'customer': {
                'id': customer.id,
                'name': f'{customer.first_name} {customer.last_name}',
                'email': customer.email,
                'phone': customer.phone
            },
            'total_amount': order.total_amount,
            'discount_amount': order.discount_amount,
            'tax_amount': order.tax_amount,
            'shipping_amount': order.shipping_amount,
            'final_amount': order.final_amount,
            'status': order.status,
            'payment_status': order.payment_status,
            'payment_method': order.payment_method,
            'shipping_address': order.shipping_address,
            'billing_address': order.billing_address,
            'notes': order.notes,
            'created_at': order.created_at.isoformat(),
            'updated_at': order.updated_at.isoformat() if order.updated_at else None,
            'completed_at': order.completed_at.isoformat() if order.completed_at else None,
            'items': items_data
        }
        
        return jsonify({
            'success': True,
            'order': order_data
        }), 200
        
    except Exception as e:
        logger.error(f'Error al obtener orden: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

# ------------------------------------------------------------
# RUTAS DE PAGOS
# ------------------------------------------------------------

@users_blueprint.route('/api/payments/create-intent', methods=['POST'])
@jwt_required()
def create_payment_intent():
    """Crea un PaymentIntent de Stripe"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        required_fields = ['amount', 'order_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Campo requerido faltante: {field}'
                }), 400
        
        # Verificar si la orden existe y pertenece al usuario
        order = Order.query.get(data['order_id'])
        if not order or order.customer_id != current_user_id:
            return jsonify({
                'success': False,
                'message': 'Orden no válida'
            }), 404
        
        amount = float(data['amount'])
        
        # Crear payment intent con Stripe
        result = payment_system.create_payment_intent(
            amount=amount,
            currency='usd',
            metadata={
                'order_id': order.id,
                'user_id': current_user_id,
                'order_number': order.order_number
            }
        )
        
        if not result['success']:
            return jsonify({
                'success': False,
                'message': result['error']
            }), 400
        
        # Crear registro de pago en la base de datos
        payment = Payment(
            payment_reference=f"PAY-{int(time.time())}-{random.randint(1000, 9999)}",
            order_id=order.id,
            user_id=current_user_id,
            amount=amount,
            payment_method='stripe',
            stripe_payment_intent_id=result['payment_intent_id']
        )
        
        db.session.add(payment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'client_secret': result['client_secret'],
            'payment_intent_id': result['payment_intent_id'],
            'payment_id': payment.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error al crear payment intent: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/payments/confirm', methods=['POST'])
@jwt_required()
def confirm_payment():
    """Confirma un pago de Stripe"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        required_fields = ['payment_intent_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Campo requerido faltante: {field}'
                }), 400
        
        # Confirmar pago con Stripe
        result = payment_system.confirm_payment(data['payment_intent_id'])
        
        if not result['success']:
            return jsonify({
                'success': False,
                'message': result['error']
            }), 400
        
        # Actualizar pago en la base de datos
        payment = Payment.query.filter_by(
            stripe_payment_intent_id=data['payment_intent_id']
        ).first()
        
        if payment:
            payment.status = 'completed' if result['status'] == 'succeeded' else 'failed'
            payment.stripe_charge_id = result.get('charge_id')
            payment.updated_at = datetime.datetime.utcnow()
            
            # Actualizar orden
            if payment.order_id:
                order = Order.query.get(payment.order_id)
                if order:
                    order.payment_status = 'paid' if result['status'] == 'succeeded' else 'failed'
                    order.status = 'completed' if result['status'] == 'succeeded' else 'processing'
                    order.updated_at = datetime.datetime.utcnow()
            
            db.session.commit()
            
            # Notificar al usuario
            if result['status'] == 'succeeded':
                NotificationSystem.create_notification(
                    user_id=current_user_id,
                    title='Pago completado',
                    message=f'Tu pago de ${payment.amount:.2f} ha sido procesado exitosamente',
                    notification_type='payment',
                    action_url=f'/orders/{payment.order_id}'
                )
        
        return jsonify({
            'success': True,
            'status': result['status'],
            'message': 'Pago confirmado exitosamente' if result['status'] == 'succeeded' else 'Pago fallido'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error al confirmar pago: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/payments', methods=['GET'])
@jwt_required()
def get_payments():
    """Obtiene los pagos del usuario"""
    try:
        current_user_id = get_jwt_identity()
        
        payments = Payment.query.filter_by(user_id=current_user_id).order_by(Payment.created_at.desc()).all()
        
        payments_data = []
        for payment in payments:
            order = payment.order
            payments_data.append({
                'id': payment.id,
                'payment_reference': payment.payment_reference,
                'amount': payment.amount,
                'currency': payment.currency,
                'status': payment.status,
                'payment_method': payment.payment_method,
                'order': {
                    'id': order.id if order else None,
                    'order_number': order.order_number if order else None
                },
                'created_at': payment.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'payments': payments_data,
            'count': len(payments_data)
        }), 200
        
    except Exception as e:
        logger.error(f'Error al obtener pagos: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

# ------------------------------------------------------------
# RUTAS DE NOTIFICACIONES
# ------------------------------------------------------------

@users_blueprint.route('/api/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """Obtiene las notificaciones del usuario"""
    try:
        current_user_id = get_jwt_identity()
        
        # Parámetros de paginación
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        # Construir query
        query = Notification.query.filter_by(user_id=current_user_id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        # Ordenar por fecha de creación (más recientes primero)
        query = query.order_by(Notification.created_at.desc())
        
        # Paginar
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        notifications = pagination.items
        
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.notification_type,
                'is_read': notification.is_read,
                'read_at': notification.read_at.isoformat() if notification.read_at else None,
                'action_url': notification.action_url,
                'created_at': notification.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'notifications': notifications_data,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages
            },
            'unread_count': Notification.query.filter_by(user_id=current_user_id, is_read=False).count()
        }), 200
        
    except Exception as e:
        logger.error(f'Error al obtener notificaciones: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@jwt_required()
def mark_notification_as_read(notification_id):
    """Marca una notificación como leída"""
    try:
        current_user_id = get_jwt_identity()
        
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=current_user_id
        ).first()
        
        if not notification:
            return jsonify({
                'success': False,
                'message': 'Notificación no encontrada'
            }), 404
        
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.datetime.utcnow()
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Notificación marcada como leída'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error al marcar notificación como leída: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/notifications/read-all', methods=['POST'])
@jwt_required()
def mark_all_notifications_as_read():
    """Marca todas las notificaciones como leídas"""
    try:
        current_user_id = get_jwt_identity()
        
        # Marcar todas las notificaciones no leídas como leídas
        Notification.query.filter_by(
            user_id=current_user_id,
            is_read=False
        ).update({
            'is_read': True,
            'read_at': datetime.datetime.utcnow()
        })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Todas las notificaciones marcadas como leídas'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error al marcar todas las notificaciones como leídas: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

# ------------------------------------------------------------
# RUTAS DE ADMINISTRACIÓN
# ------------------------------------------------------------

@users_blueprint.route('/api/admin/users', methods=['GET'])
@admin_required
def admin_get_users():
    """Obtiene todos los usuarios (solo administrador)"""
    try:
        # Parámetros de filtro
        role = request.args.get('role')
        search = request.args.get('search')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = User.query
        
        # Aplicar filtros
        if role:
            query = query.filter_by(role=role)
        
        if search:
            search_term = f'%{search}%'
            query = query.filter(
                or_(
                    User.username.ilike(search_term),
                    User.email.ilike(search_term),
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term)
                )
            )
        
        # Ordenar por fecha de creación
        query = query.order_by(User.created_at.desc())
        
        # Paginar
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        users = pagination.items
        
        users_data = []
        for user in users:
            # Obtener estadísticas del usuario
            appointment_count = Appointment.query.filter_by(client_id=user.id).count()
            order_count = Order.query.filter_by(customer_id=user.id).count()
            
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'is_active': user.is_active,
                'is_verified': user.is_verified,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'appointment_count': appointment_count,
                'order_count': order_count
            })
        
        return jsonify({
            'success': True,
            'users': users_data,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }), 200
        
    except Exception as e:
        logger.error(f'Error al obtener usuarios: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@admin_required
def admin_update_user(user_id):
    """Actualiza un usuario (solo administrador)"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'Usuario no encontrado'
            }), 404
        
        data = request.get_json()
        
        # Campos actualizables por administrador
        updatable_fields = [
            'first_name', 'last_name', 'role', 'is_active', 
            'is_verified', 'specialization', 'qualifications',
            'experience_years', 'hourly_rate'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(user, field, data[field])
        
        user.updated_at = datetime.datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Usuario actualizado exitosamente',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'is_active': user.is_active,
                'is_verified': user.is_verified
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error al actualizar usuario: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/admin/stats', methods=['GET'])
@admin_required
def admin_get_stats():
    """Obtiene estadísticas del sistema (solo administrador)"""
    try:
        # Estadísticas de usuarios
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        therapists_count = User.query.filter_by(role='therapist').count()
        new_users_today = User.query.filter(
            User.created_at >= datetime.datetime.utcnow().date()
        ).count()
        
        # Estadísticas de citas
        total_appointments = Appointment.query.count()
        completed_appointments = Appointment.query.filter_by(status='completed').count()
        pending_appointments = Appointment.query.filter_by(status='scheduled').count()
        
        # Estadísticas de órdenes
        total_orders = Order.query.count()
        total_revenue = db.session.query(func.sum(Order.final_amount)).scalar() or 0
        today_revenue = db.session.query(func.sum(Order.final_amount)).filter(
            Order.created_at >= datetime.datetime.utcnow().date()
        ).scalar() or 0
        
        # Estadísticas de productos
        total_products = Product.query.count()
        active_products = Product.query.filter_by(is_active=True).count()
        digital_products = Product.query.filter_by(is_digital=True).count()
        
        # Ingresos por mes (últimos 6 meses)
        revenue_by_month = []
        for i in range(5, -1, -1):
            month_start = datetime.datetime.utcnow().replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            ) - datetime.timedelta(days=30*i)
            
            month_end = month_start + datetime.timedelta(days=30)
            
            month_revenue = db.session.query(func.sum(Order.final_amount)).filter(
                Order.created_at >= month_start,
                Order.created_at < month_end
            ).scalar() or 0
            
            revenue_by_month.append({
                'month': month_start.strftime('%Y-%m'),
                'revenue': float(month_revenue)
            })
        
        return jsonify({
            'success': True,
            'stats': {
                'users': {
                    'total': total_users,
                    'active': active_users,
                    'therapists': therapists_count,
                    'new_today': new_users_today
                },
                'appointments': {
                    'total': total_appointments,
                    'completed': completed_appointments,
                    'pending': pending_appointments
                },
                'orders': {
                    'total': total_orders,
                    'total_revenue': float(total_revenue),
                    'today_revenue': float(today_revenue)
                },
                'products': {
                    'total': total_products,
                    'active': active_products,
                    'digital': digital_products
                },
                'revenue_by_month': revenue_by_month
            }
        }), 200
        
    except Exception as e:
        logger.error(f'Error al obtener estadísticas: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

# ------------------------------------------------------------
# RUTAS DEL SISTEMA DE AFILIADOS
# ------------------------------------------------------------

@users_blueprint.route('/api/affiliates', methods=['POST'])
@jwt_required()
def create_affiliate():
    try:
        current_user_id = get_jwt_identity()
        
        # Verificar permisos de administrador
        if not is_admin(current_user_id):
            return jsonify({
                'success': False,
                'message': 'No tienes permisos para realizar esta acción'
            }), 403
        
        data = request.get_json()
        
        # Validaciones básicas
        required_fields = ['user_id', 'commission_rate', 'contact_info']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Campo requerido faltante: {field}'
                }), 400
        
        # Verificar si el usuario existe
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({
                'success': False,
                'message': 'Usuario no encontrado'
            }), 404
        
        # Verificar si ya es afiliado
        existing_affiliate = Affiliate.query.filter_by(user_id=data['user_id']).first()
        if existing_affiliate:
            return jsonify({
                'success': False,
                'message': 'Este usuario ya es un afiliado'
            }), 400
        
        # Preparar datos para el sistema de afiliados
        affiliate_data = {
            'user_id': data['user_id'],
            'commission_rate': float(data['commission_rate']),
            'contact_info': data['contact_info'],
            'status': data.get('status', 'active'),
            'notes': data.get('notes', '')
        }
        
        # Mapear campos adicionales
        affiliate_data_mapped = affiliate_system.map_fields(affiliate_data)
        
        # Asignar affiliate_code generado si no se proporcionó
        affiliate_code = data.get('affiliate_code')
        if not affiliate_code:
            affiliate_code = affiliate_system.generate_affiliate_code()
            affiliate_data['affiliate_code'] = affiliate_code
        
        success, message, affiliate_record = affiliate_system.add_affiliate(affiliate_data_mapped)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Afiliado creado exitosamente',
                'affiliate': affiliate_record
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
            
    except Exception as e:
        logger.error(f"Error creating affiliate: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error del servidor: {str(e)}'
        }), 500

@users_blueprint.route('/api/affiliates', methods=['GET'])
@jwt_required()
def get_affiliates():
    """Obtiene la lista de afiliados (solo administrador)"""
    try:
        current_user_id = get_jwt_identity()
        
        # Verificar permisos de administrador
        if not is_admin(current_user_id):
            return jsonify({
                'success': False,
                'message': 'No tienes permisos para realizar esta acción'
            }), 403
        
        # Obtener parámetros de filtro
        status = request.args.get('status')
        search = request.args.get('search')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = Affiliate.query.join(User)
        
        # Aplicar filtros
        if status:
            query = query.filter(Affiliate.status == status)
        
        if search:
            search_term = f'%{search}%'
            query = query.filter(
                or_(
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    User.email.ilike(search_term),
                    Affiliate.affiliate_code.ilike(search_term)
                )
            )
        
        # Ordenar por fecha de creación
        query = query.order_by(Affiliate.created_at.desc())
        
        # Paginar
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        affiliates = pagination.items
        
        affiliates_data = []
        for affiliate in affiliates:
            user = affiliate.user
            stats = affiliate_system.get_affiliate_stats(affiliate.id) or {}
            
            affiliates_data.append({
                'id': affiliate.id,
                'user': {
                    'id': user.id,
                    'name': f'{user.first_name} {user.last_name}',
                    'email': user.email
                },
                'affiliate_code': affiliate.affiliate_code,
                'commission_rate': affiliate.commission_rate,
                'total_earnings': affiliate.total_earnings,
                'pending_earnings': affiliate.pending_earnings,
                'referral_count': affiliate.referral_count,
                'conversion_rate': affiliate.conversion_rate,
                'status': affiliate.status,
                'created_at': affiliate.created_at.isoformat(),
                'stats': stats
            })
        
        return jsonify({
            'success': True,
            'affiliates': affiliates_data,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }), 200
        
    except Exception as e:
        logger.error(f'Error al obtener afiliados: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/affiliates/<int:affiliate_id>', methods=['GET'])
@jwt_required()
def get_affiliate(affiliate_id):
    """Obtiene detalles de un afiliado específico"""
    try:
        current_user_id = get_jwt_identity()
        
        affiliate = Affiliate.query.get(affiliate_id)
        
        if not affiliate:
            return jsonify({
                'success': False,
                'message': 'Afiliado no encontrado'
            }), 404
        
        # Verificar permisos
        if affiliate.user_id != current_user_id:
            if not is_admin(current_user_id):
                return jsonify({
                    'success': False,
                    'message': 'No tienes permisos para ver este afiliado'
                }), 403
        
        user = affiliate.user
        stats = affiliate_system.get_affiliate_stats(affiliate.id) or {}
        
        # Obtener referencias del afiliado
        referrals = Referral.query.filter_by(affiliate_id=affiliate.id).order_by(Referral.referral_date.desc()).limit(50).all()
        
        referrals_data = []
        for referral in referrals:
            referrer = referral.referrer
            referred = referral.referred_user
            
            referrals_data.append({
                'id': referral.id,
                'referrer': {
                    'id': referrer.id,
                    'name': f'{referrer.first_name} {referrer.last_name}'
                },
                'referred': {
                    'id': referred.id,
                    'name': f'{referred.first_name} {referred.last_name}'
                },
                'referral_date': referral.referral_date.isoformat(),
                'status': referral.status,
                'conversion_value': referral.conversion_value,
                'commission_earned': referral.commission_earned,
                'commission_paid': referral.commission_paid
            })
        
        affiliate_data = {
            'id': affiliate.id,
            'user': {
                'id': user.id,
                'name': f'{user.first_name} {user.last_name}',
                'email': user.email,
                'phone': user.phone,
                'profile_image': user.profile_image
            },
            'affiliate_code': affiliate.affiliate_code,
            'commission_rate': affiliate.commission_rate,
            'total_earnings': affiliate.total_earnings,
            'pending_earnings': affiliate.pending_earnings,
            'paid_earnings': affiliate.paid_earnings,
            'referral_count': affiliate.referral_count,
            'conversion_rate': affiliate.conversion_rate,
            'status': affiliate.status,
            'contact_info': affiliate.contact_info,
            'payment_method': affiliate.payment_method,
            'notes': affiliate.notes,
            'created_at': affiliate.created_at.isoformat(),
            'updated_at': affiliate.updated_at.isoformat() if affiliate.updated_at else None,
            'stats': stats,
            'referrals': referrals_data
        }
        
        return jsonify({
            'success': True,
            'affiliate': affiliate_data
        }), 200
        
    except Exception as e:
        logger.error(f'Error al obtener afiliado: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/affiliates/<int:affiliate_id>', methods=['PUT'])
@jwt_required()
def update_affiliate(affiliate_id):
    """Actualiza un afiliado"""
    try:
        current_user_id = get_jwt_identity()
        
        affiliate = Affiliate.query.get(affiliate_id)
        
        if not affiliate:
            return jsonify({
                'success': False,
                'message': 'Afiliado no encontrado'
            }), 404
        
        # Verificar permisos
        if affiliate.user_id != current_user_id:
            if not is_admin(current_user_id):
                return jsonify({
                    'success': False,
                    'message': 'No tienes permisos para actualizar este afiliado'
                }), 403
        
        data = request.get_json()
        
        # Validar datos según quién está actualizando
        if affiliate.user_id == current_user_id:
            # El afiliado solo puede actualizar ciertos campos
            allowed_fields = ['contact_info', 'payment_method', 'payment_details']
        else:
            # El administrador puede actualizar más campos
            allowed_fields = ['commission_rate', 'contact_info', 'status', 
                            'payment_method', 'payment_details', 'notes']
        
        affiliate_data = {}
        for field in allowed_fields:
            if field in data:
                affiliate_data[field] = data[field]
        
        # Actualizar afiliado
        success, message, updated_affiliate = affiliate_system.update_affiliate(affiliate_id, affiliate_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'affiliate': updated_affiliate
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
            
    except Exception as e:
        logger.error(f'Error al actualizar afiliado: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/affiliates/my-stats', methods=['GET'])
@jwt_required()
def get_my_affiliate_stats():
    """Obtiene las estadísticas del afiliado actual"""
    try:
        current_user_id = get_jwt_identity()
        
        # Verificar si el usuario es afiliado
        affiliate = Affiliate.query.filter_by(user_id=current_user_id).first()
        
        if not affiliate:
            return jsonify({
                'success': False,
                'message': 'No eres un afiliado'
            }), 404
        
        # Obtener estadísticas
        stats = affiliate_system.get_affiliate_stats(affiliate.id)
        
        if not stats:
            return jsonify({
                'success': False,
                'message': 'Error al obtener estadísticas'
            }), 500
        
        # Obtener referencias recientes
        recent_referrals = Referral.query.filter_by(
            affiliate_id=affiliate.id
        ).order_by(Referral.referral_date.desc()).limit(10).all()
        
        referrals_data = []
        for referral in recent_referrals:
            referred = referral.referred_user
            referrals_data.append({
                'id': referral.id,
                'referred_user': {
                    'id': referred.id,
                    'name': f'{referred.first_name} {referred.last_name}'
                },
                'referral_date': referral.referral_date.isoformat(),
                'status': referral.status,
                'conversion_value': referral.conversion_value,
                'commission_earned': referral.commission_earned
            })
        
        # Obtear ingresos por mes (últimos 6 meses)
        earnings_by_month = []
        for i in range(5, -1, -1):
            month_start = datetime.datetime.utcnow().replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            ) - datetime.timedelta(days=30*i)
            
            month_end = month_start + datetime.timedelta(days=30)
            
            month_earnings = db.session.query(func.sum(Referral.commission_earned)).filter(
                Referral.affiliate_id == affiliate.id,
                Referral.conversion_date >= month_start,
                Referral.conversion_date < month_end
            ).scalar() or 0
            
            earnings_by_month.append({
                'month': month_start.strftime('%Y-%m'),
                'earnings': float(month_earnings)
            })
        
        return jsonify({
            'success': True,
            'stats': {
                **stats,
                'recent_referrals': referrals_data,
                'earnings_by_month': earnings_by_month
            }
        }), 200
        
    except Exception as e:
        logger.error(f'Error al obtener estadísticas de afiliado: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/affiliates/refer', methods=['POST'])
@jwt_required()
def create_referral():
    """Crea una nueva referencia"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        required_fields = ['referred_email']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Campo requerido faltante: {field}'
                }), 400
        
        # Verificar si el usuario es afiliado
        affiliate = Affiliate.query.filter_by(user_id=current_user_id).first()
        
        if not affiliate:
            return jsonify({
                'success': False,
                'message': 'No eres un afiliado'
            }), 400
        
        # Verificar si el correo ya está registrado
        existing_user = User.query.filter_by(email=data['referred_email']).first()
        
        if existing_user:
            return jsonify({
                'success': False,
                'message': 'Este correo ya está registrado'
            }), 400
        
        # Verificar si ya existe una referencia para este correo
        existing_referral = Referral.query.join(User, Referral.referred_id == User.id).filter(
            User.email == data['referred_email'],
            Referral.referrer_id == current_user_id
        ).first()
        
        if existing_referral:
            return jsonify({
                'success': False,
                'message': 'Ya has referido a este correo'
            }), 400
        
        # Crear usuario temporal para la referencia
        # En producción, esto enviaría un email de invitación
        temp_user = User(
            email=data['referred_email'],
            first_name=data.get('referred_first_name', ''),
            last_name=data.get('referred_last_name', ''),
            is_active=False
        )
        
        db.session.add(temp_user)
        db.session.flush()  # Para obtener el ID
        
        # Crear referencia
        referral = Referral(
            referrer_id=current_user_id,
            referred_id=temp_user.id,
            affiliate_id=affiliate.id,
            referral_code=affiliate.affiliate_code,
            status='pending'
        )
        
        db.session.add(referral)
        db.session.commit()
        
        # Enviar email de invitación
        referral_link = f"https://tudominio.com/register?ref={affiliate.affiliate_code}"
        
        if email_system.username:
            email_system.send_email(
                to_email=data['referred_email'],
                subject=f'Invitación de {current_user.first_name} {current_user.last_name}',
                body_html=f"""
                <html>
                <body>
                    <h1>¡Te han invitado a unirte a MindGeek Clinic!</h1>
                    <p>{current_user.first_name} {current_user.last_name} te ha invitado a unirte a nuestra plataforma.</p>
                    <p>MindGeek Clinic ofrece servicios de terapia en línea, productos de bienestar y más.</p>
                    <p>Para registrarte, haz clic en el siguiente enlace:</p>
                    <p><a href="{referral_link}">Unirse a MindGeek Clinic</a></p>
                    <p>Al registrarte a través de este enlace, {current_user.first_name} recibirá una comisión por tus compras.</p>
                    <br>
                    <p>Saludos,<br>El equipo de MindGeek Clinic</p>
                </body>
                </html>
                """
            )
        
        return jsonify({
            'success': True,
            'message': 'Invitación enviada exitosamente',
            'referral': {
                'id': referral.id,
                'referred_email': data['referred_email'],
                'status': referral.status,
                'referral_date': referral.referral_date.isoformat()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error al crear referencia: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/affiliates/register-with-referral', methods=['POST'])
def register_with_referral():
    """Registra un usuario con código de referencia"""
    try:
        data = request.get_json()
        
        required_fields = ['username', 'email', 'password', 'first_name', 'last_name', 'referral_code']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Campo requerido faltante: {field}'
                }), 400
        
        # Primero, registrar al usuario normalmente
        registration_response = register()
        
        if registration_response.status_code != 201:
            return registration_response
        
        registration_data = json.loads(registration_response.get_data(as_text=True))
        
        if not registration_data['success']:
            return registration_response
        
        # Buscar afiliado por código
        affiliate = Affiliate.query.filter_by(affiliate_code=data['referral_code']).first()
        
        if not affiliate:
            return jsonify({
                'success': True,  # Aún éxito porque el usuario se registró
                'message': 'Usuario registrado exitosamente, pero el código de referencia no es válido',
                'user': registration_data['user'],
                'access_token': registration_data['access_token']
            }), 201
        
        # Crear referencia
        new_user_id = registration_data['user']['id']
        
        referral = Referral(
            referrer_id=affiliate.user_id,
            referred_id=new_user_id,
            affiliate_id=affiliate.id,
            referral_code=data['referral_code'],
            status='registered'
        )
        
        db.session.add(referral)
        
        # Actualizar contador de referencias del afiliado
        affiliate.referral_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Usuario registrado exitosamente con código de referencia',
            'user': registration_data['user'],
            'access_token': registration_data['access_token'],
            'referral': {
                'affiliate_code': data['referral_code'],
                'status': 'registered'
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error en registro con referencia: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

# ------------------------------------------------------------
# RUTAS DE CUPONES
# ------------------------------------------------------------

@users_blueprint.route('/api/coupons/validate', methods=['POST'])
@jwt_required()
def validate_coupon():
    """Valida un cupón de descuento"""
    try:
        data = request.get_json()
        
        if 'code' not in data:
            return jsonify({
                'success': False,
                'message': 'Código de cupón es requerido'
            }), 400
        
        coupon = Coupon.query.filter_by(code=data['code'], is_active=True).first()
        
        if not coupon:
            return jsonify({
                'success': False,
                'message': 'Cupón no válido'
            }), 400
        
        # Verificar fecha de validez
        now = datetime.datetime.utcnow()
        if now < coupon.valid_from or now > coupon.valid_until:
            return jsonify({
                'success': False,
                'message': 'Cupón expirado'
            }), 400
        
        # Verificar límite de uso
        if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
            return jsonify({
                'success': False,
                'message': 'Cupón agotado'
            }), 400
        
        return jsonify({
            'success': True,
            'coupon': {
                'id': coupon.id,
                'code': coupon.code,
                'discount_type': coupon.discount_type,
                'discount_value': coupon.discount_value,
                'min_purchase': coupon.min_purchase,
                'max_discount': coupon.max_discount,
                'valid_until': coupon.valid_until.isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f'Error al validar cupón: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

# ------------------------------------------------------------
# RUTAS DE BLOQUEO DE USUARIOS
# ------------------------------------------------------------

@users_blueprint.route('/api/users/block', methods=['POST'])
@jwt_required()
def block_user():
    """Bloquea a un usuario"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if 'user_id' not in data:
            return jsonify({
                'success': False,
                'message': 'ID de usuario es requerido'
            }), 400
        
        user_to_block_id = data['user_id']
        
        # Verificar que no sea el mismo usuario
        if user_to_block_id == current_user_id:
            return jsonify({
                'success': False,
                'message': 'No puedes bloquearte a ti mismo'
            }), 400
        
        # Verificar si el usuario existe
        user_to_block = User.query.get(user_to_block_id)
        if not user_to_block:
            return jsonify({
                'success': False,
                'message': 'Usuario no encontrado'
            }), 404
        
        # Verificar si ya está bloqueado
        existing_block = db.session.query(user_blocks).filter_by(
            blocker_id=current_user_id,
            blocked_id=user_to_block_id
        ).first()
        
        if existing_block:
            return jsonify({
                'success': False,
                'message': 'Usuario ya bloqueado'
            }), 400
        
        # Bloquear usuario
        db.session.execute(
            user_blocks.insert().values(
                blocker_id=current_user_id,
                blocked_id=user_to_block_id,
                reason=data.get('reason', ''),
                created_at=datetime.datetime.utcnow()
            )
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Usuario bloqueado exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error al bloquear usuario: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/users/unblock', methods=['POST'])
@jwt_required()
def unblock_user():
    """Desbloquea a un usuario"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if 'user_id' not in data:
            return jsonify({
                'success': False,
                'message': 'ID de usuario es requerido'
            }), 400
        
        user_to_unblock_id = data['user_id']
        
        # Verificar si existe el bloqueo
        existing_block = db.session.query(user_blocks).filter_by(
            blocker_id=current_user_id,
            blocked_id=user_to_unblock_id
        ).first()
        
        if not existing_block:
            return jsonify({
                'success': False,
                'message': 'Usuario no está bloqueado'
            }), 400
        
        # Desbloquear usuario
        db.session.execute(
            user_blocks.delete().where(
                (user_blocks.c.blocker_id == current_user_id) &
                (user_blocks.c.blocked_id == user_to_unblock_id)
            )
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Usuario desbloqueado exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error al desbloquear usuario: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@users_blueprint.route('/api/users/blocked', methods=['GET'])
@jwt_required()
def get_blocked_users():
    """Obtiene la lista de usuarios bloqueados"""
    try:
        current_user_id = get_jwt_identity()
        
        # Obtener usuarios bloqueados
        blocked_records = db.session.query(user_blocks).filter_by(
            blocker_id=current_user_id
        ).all()
        
        blocked_users = []
        for record in blocked_records:
            user = User.query.get(record.blocked_id)
            if user:
                blocked_users.append({
                    'user_id': user.id,
                    'name': f'{user.first_name} {user.last_name}',
                    'profile_image': user.profile_image,
                    'reason': record.reason,
                    'blocked_at': record.created_at.isoformat() if record.created_at else None
                })
        
        return jsonify({
            'success': True,
            'blocked_users': blocked_users,
            'count': len(blocked_users)
        }), 200
        
    except Exception as e:
        logger.error(f'Error al obtener usuarios bloqueados: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

# ------------------------------------------------------------
# RUTAS DE REPORTES Y EXPORTACIÓN
# ------------------------------------------------------------

@users_blueprint.route('/api/reports/appointments', methods=['GET'])
@jwt_required()
@admin_required
def generate_appointments_report():
    """Genera reporte de citas"""
    try:
        # Parámetros de filtro
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        therapist_id = request.args.get('therapist_id')
        status = request.args.get('status')
        format_type = request.args.get('format', 'json')  # json, csv, pdf
        
        # Construir query
        query = Appointment.query
        
        if start_date:
            query = query.filter(Appointment.appointment_date >= start_date)
        
        if end_date:
            query = query.filter(Appointment.appointment_date <= end_date)
        
        if therapist_id:
            query = query.filter_by(therapist_id=therapist_id)
        
        if status:
            query = query.filter_by(status=status)
        
        appointments = query.order_by(Appointment.appointment_date.desc()).all()
        
        if format_type == 'csv':
            # Generar CSV
            output = BytesIO()
            writer = csv.writer(output)
            
            # Escribir encabezados
            writer.writerow([
                'ID', 'Cliente', 'Terapeuta', 'Fecha', 'Hora', 'Duración',
                'Tipo', 'Estado', 'Monto', 'Estado de Pago', 'Creado'
            ])
            
            # Escribir datos
            for appt in appointments:
                client = appt.client
                therapist = appt.therapist
                
                writer.writerow([
                    appt.id,
                    f'{client.first_name} {client.last_name}',
                    f'{therapist.first_name} {therapist.last_name}',
                    appt.appointment_date.isoformat(),
                    appt.appointment_time.strftime('%H:%M'),
                    appt.duration,
                    appt.appointment_type,
                    appt.status,
                    appt.amount,
                    appt.payment_status,
                    appt.created_at.isoformat()
                ])
            
            output.seek(0)
            
            return send_file(
                output,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'appointments_report_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )
        
        elif format_type == 'pdf':
            # Generar PDF (implementación básica)
            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            
            # Encabezado
            p.setFont("Helvetica-Bold", 16)
            p.drawString(100, 750, "Reporte de Citas - MindGeek Clinic")
            p.setFont("Helvetica", 10)
            p.drawString(100, 735, f"Generado: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Tabla
            y = 700
            p.setFont("Helvetica-Bold", 10)
            p.drawString(50, y, "ID")
            p.drawString(100, y, "Cliente")
            p.drawString(250, y, "Terapeuta")
            p.drawString(400, y, "Fecha")
            p.drawString(470, y, "Estado")
            
            p.setFont("Helvetica", 8)
            y -= 20
            
            for appt in appointments[:30]:  # Limitar para una página
                client = appt.client
                therapist = appt.therapist
                
                p.drawString(50, y, str(appt.id))
                p.drawString(100, y, f'{client.first_name} {client.last_name}'[:15])
                p.drawString(250, y, f'{therapist.first_name} {therapist.last_name}'[:15])
                p.drawString(400, y, appt.appointment_date.strftime('%Y-%m-%d'))
                p.drawString(470, y, appt.status)
                
                y -= 15
                if y < 50:
                    p.showPage()
                    y = 750
            
            p.save()
            buffer.seek(0)
            
            return send_file(
                buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'appointments_report_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            )
        
        else:
            # Formato JSON (por defecto)
            appointments_data = []
            for appt in appointments:
                client = appt.client
                therapist = appt.therapist
                
                appointments_data.append({
                    'id': appt.id,
                    'client': {
                        'id': client.id,
                        'name': f'{client.first_name} {client.last_name}'
                    },
                    'therapist': {
                        'id': therapist.id,
                        'name': f'{therapist.first_name} {therapist.last_name}'
                    },
                    'appointment_date': appt.appointment_date.isoformat(),
                    'appointment_time': appt.appointment_time.strftime('%H:%M'),
                    'duration': appt.duration,
                    'type': appt.appointment_type,
                    'status': appt.status,
                    'amount': appt.amount,
                    'payment_status': appt.payment_status,
                    'created_at': appt.created_at.isoformat()
                })
            
            return jsonify({
                'success': True,
                'report': {
                    'type': 'appointments',
                    'filters': {
                        'start_date': start_date,
                        'end_date': end_date,
                        'therapist_id': therapist_id,
                        'status': status
                    },
                    'generated_at': datetime.datetime.utcnow().isoformat(),
                    'data': appointments_data,
                    'count': len(appointments_data)
                }
            }), 200
        
    except Exception as e:
        logger.error(f'Error al generar reporte de citas: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

# ------------------------------------------------------------
# RUTAS DE SALUD Y MONITOREO
# ------------------------------------------------------------

@users_blueprint.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de salud de la aplicación"""
    try:
        # Verificar conexión a la base de datos
        db.session.execute('SELECT 1')
        
        # Verificar que las tablas principales existan
        tables = ['users', 'appointments', 'products', 'orders']
        for table in tables:
            db.session.execute(f'SELECT 1 FROM {table} LIMIT 1')
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'database': 'connected',
            'version': '1.0.0'
        }), 200
        
    except Exception as e:
        logger.error(f'Health check failed: {str(e)}')
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500

@users_blueprint.route('/api/metrics', methods=['GET'])
@admin_required
def get_metrics():
    """Obtiene métricas del sistema (solo administrador)"""
    try:
        # Métricas en tiempo real
        active_sessions = len(socketio.server.manager.rooms.get('/', {}))
        active_users = User.query.filter(
            User.last_login >= datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        ).count()
        
        # Métricas de rendimiento
        memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        return jsonify({
            'success': True,
            'metrics': {
                'active_sessions': active_sessions,
                'active_users_last_hour': active_users,
                'memory_usage_mb': round(memory_usage, 2),
                'timestamp': datetime.datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f'Error al obtener métricas: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

# ------------------------------------------------------------
# WEBHOOKS
# ------------------------------------------------------------

@users_blueprint.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Webhook para recibir eventos de Stripe"""
    try:
        payload = request.get_data(as_text=True)
        sig_header = request.headers.get('Stripe-Signature')
        
        if not sig_header:
            return jsonify({'error': 'No signature header'}), 400
        
        result = payment_system.handle_webhook(payload, sig_header)
        
        if result['success']:
            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f'Error en webhook de Stripe: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

# ------------------------------------------------------------
# RUTAS DE VISTAS HTML
# ------------------------------------------------------------

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard del usuario"""
    return render_template('dashboard.html')

@app.route('/therapist/dashboard')
@login_required
def therapist_dashboard():
    """Dashboard del terapeuta"""
    if current_user.role not in ['therapist', 'admin']:
        return redirect(url_for('dashboard'))
    return render_template('therapist_dashboard.html')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Dashboard del administrador"""
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))
    return render_template('admin_dashboard.html')

@app.route('/appointments')
@login_required
def appointments_page():
    """Página de citas"""
    return render_template('appointments.html')

@app.route('/messages')
@login_required
def messages_page():
    """Página de mensajes"""
    return render_template('messages.html')

@app.route('/marketplace')
def marketplace():
    """Marketplace de productos"""
    return render_template('marketplace.html')

@app.route('/affiliate')
@login_required
def affiliate_portal():
    """Portal de afiliados"""
    return render_template('affiliate.html')

# ------------------------------------------------------------
# MANEJO DE ERRORES
# ------------------------------------------------------------

@app.errorhandler(404)
def not_found_error(error):
    """Maneja errores 404"""
    return jsonify({
        'success': False,
        'message': 'Recurso no encontrado'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Maneja errores 500"""
    db.session.rollback()
    logger.error(f'Error interno del servidor: {str(error)}')
    return jsonify({
        'success': False,
        'message': 'Error interno del servidor'
    }), 500

@app.errorhandler(401)
def unauthorized_error(error):
    """Maneja errores 401"""
    return jsonify({
        'success': False,
        'message': 'No autorizado. Por favor inicia sesión.'
    }), 401

@app.errorhandler(403)
def forbidden_error(error):
    """Maneja errores 403"""
    return jsonify({
        'success': False,
        'message': 'Acceso prohibido. No tienes los permisos necesarios.'
    }), 403

# ------------------------------------------------------------
# INICIALIZACIÓN DE LA APLICACIÓN
# ------------------------------------------------------------

# Registrar blueprints
app.register_blueprint(users_blueprint)

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Crear tablas si no existen
@app.before_first_request
def create_tables():
    db.create_all()
    
    # Crear usuario administrador por defecto si no existe
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@mindgeekclinic.com',
            first_name='Administrador',
            last_name='Sistema',
            role='admin',
            is_active=True,
            is_verified=True
        )
        admin.set_password('Admin123!')  # Cambiar en producción
        db.session.add(admin)
        db.session.commit()
        logger.info('Usuario administrador creado por defecto')

# ------------------------------------------------------------
# EJECUCIÓN DE LA APLICACIÓN
# ------------------------------------------------------------

if __name__ == '__main__':
    # En producción, usar: socketio.run(app, host='0.0.0.0', port=5000)
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
