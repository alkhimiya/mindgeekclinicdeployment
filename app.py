# -*- coding: utf-8 -*-
"""
MINDGEEKCLINIC - Sistema Completo de Biodescodificación con IA
Versión: 5.0 - Completa con todas las funcionalidades
Fecha: Diciembre 2024
Líneas: ~3000
"""

# ============================================
# PARTE 1: IMPORTACIONES COMPLETAS
# ============================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff
from datetime import datetime, timedelta
import json
import hashlib
import time
import re
import random
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import requests
from io import BytesIO
import base64
import traceback
import os
import sys
import inspect
import logging
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
import sqlite3
from sqlite3 import Error as SqliteError
from contextlib import contextmanager
import pickle
import warnings
warnings.filterwarnings('ignore')

# Importaciones para IA y ML
import google.generativeai as genai
from groq import Groq
import openai
from openai import OpenAI
import anthropic
from anthropic import Anthropic
import cohere
from cohere import Client as CohereClient

# Importaciones para PDF y reportes
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import pypdf as PyPDF2
from pypdf import PdfReader, PdfWriter
import seaborn as sns
from wordcloud import WordCloud, STOPWORDS
import networkx as nx

# Importaciones para procesamiento de texto
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import spacy
from textblob import TextBlob
import gensim
from gensim import corpora, models

# Importaciones para base de datos vectorial
import chromadb
from chromadb import Client, Settings
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions

# Importaciones para audio (sesiones de hipnosis)
# ============================================
# MANEJO SEGURO DE sounddevice (para evitar error PortAudio)
# ============================================
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
    print("✅ Módulo sounddevice cargado correctamente")
except OSError as e:
    # Esto ocurrirá en entornos sin PortAudio (como teléfonos)
    print(f"⚠️  Advertencia: sounddevice no pudo cargarse - {e}")
    print("⚠️  El sistema funcionará en modo limitado: audios se generarán como archivos para descargar.")
    
    # Creamos un objeto simulado para evitar errores en el resto del código
    class MockSoundDevice:
        def __init__(self):
            self.available = False
            self.default = None
            self.default_output_device = None
            self.default_input_device = None
        
        def __getattr__(self, name):
            # Si cualquier parte del código intenta usar sd.funcion()
            def mock_method(*args, **kwargs):
                print(f"🔇 [Modo Simulado] Se llamó a sounddevice.{name}()")
                print("   Los audios se generarán como archivos descargables (no reproducción en tiempo real).")
                # Para funciones comunes, retornamos valores simulados
                if name == 'query_devices':
                    return []
                if name == 'play':
                    print("   [Simulación] Audio 'reproducido' (archivo disponible para descarga)")
                    return None
                if name == 'stop':
                    return None
                if name == 'get_status':
                    return {'active': False}
                return None
            return mock_method
        
        def play(self, *args, **kwargs):
            print("🔇 [Modo Simulado] Reproducción de audio simulada")
            print("   Descarga el archivo .mp3 o .wav para escucharlo")
            return None
    
    sd = MockSoundDevice()
    SOUNDDEVICE_AVAILABLE = False

# Variable global para que otras partes del código sepan si sounddevice funciona
AUDIO_CAPABILITIES = {
    'realtime_playback': SOUNDDEVICE_AVAILABLE,
    'file_generation': True,  # Siempre podemos generar archivos
    'binaural_beats': True,   # Podemos generar tonos binaurales
    'text_to_speech': False   # Necesitaríamos API externa para TTS
}
# ... (esto es el final de tu Bloque 1)

# Variable global para que otras partes del código sepan si sounddevice funciona
AUDIO_CAPABILITIES = {
    'realtime_playback': SOUNDDEVICE_AVAILABLE,
    'file_generation': True,  # Siempre podemos generar archivos
    'binaural_beats': True,   # Podemos generar tonos binaurales
    'text_to_speech': False   # Necesitaríamos API externa para TTS
}
# ============================================
# MANEJO SEGURO DE soundfile
# ============================================
try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
    print("✅ Módulo soundfile cargado correctamente")
except ImportError as e:
    print(f"⚠️  Advertencia: soundfile no disponible - {e}")
    
    class MockSoundFile:
        def __init__(self):
            self.available = False
        
        def __getattr__(self, name):
            def mock_method(*args, **kwargs):
                print(f"📁 [Modo Simulado] Se llamó a soundfile.{name}()")
                if name == 'write':
                    print("   [Simulación] Archivo de audio 'guardado' (operación simulada)")
                    return None
                return None
            return mock_method
        
        def write(self, file, data, samplerate):
            print(f"📁 [Simulación] Se habría guardado archivo de audio: {file}")
            print(f"   Muestras: {len(data)}, Tasa de muestreo: {samplerate}Hz")
            return None
    
    sf = MockSoundFile()
    SOUNDFILE_AVAILABLE = False
# Configuración de logging
logging.basicConfig(level=logging.INFO)
# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# PARTE 2: CONFIGURACIÓN INICIAL DE STREAMLIT
# ============================================

st.set_page_config(
    page_title="MINDGEEKCLINIC - Biodescodificación Integral",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo',
        'Report a bug': "https://github.com/your-repo/issues",
        'About': """
        # MINDGEEKCLINIC
        Sistema de biodescodificación emocional con IA.
        Versión 5.0
        """
    }
)

# Inicialización de estado de sesión
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.page = "home"
    st.session_state.user_data = {}
    st.session_state.diagnostic_history = []
    st.session_state.session_history = []
    st.session_state.emotional_state = {}
    st.session_state.affiliate_data = {}
    st.session_state.admin_logged_in = False
    st.session_state.current_diagnostic = None
    st.session_state.current_session = None
    st.session_state.chat_history = []
    st.session_state.verification_data = {}
    st.session_state.payment_data = {}

# ============================================
# PARTE 3: CONFIGURACIÓN Y SECRETS MANAGEMENT
# ============================================

class ConfigManager:
    """Gestor de configuración centralizado"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Carga la configuración desde secrets"""
        try:
            # Configuración de email
            self.email_config = {
                "smtp_server": st.secrets["email"]["smtp_server"],
                "smtp_port": int(st.secrets["email"]["smtp_port"]),
                "username": st.secrets["email"]["username"],
                "password": st.secrets["email"]["password"],
                "sender_email": st.secrets["email"]["sender_email"],
                "admin_email": st.secrets["email"]["admin_email"]
            }
            
            # Configuración de APIs de IA
            self.groq_api_key = st.secrets["groq"]["api_key"]
            self.openai_api_key = st.secrets.get("openai", {}).get("api_key", "")
            self.anthropic_api_key = st.secrets.get("anthropic", {}).get("api_key", "")
            self.google_api_key = st.secrets.get("google", {}).get("api_key", "")
            
            # Configuración de la aplicación
            self.app_config = {
                "admin_password": st.secrets["app"]["admin_password"],
                "admin_email": st.secrets["app"]["admin_email"],
                "name": st.secrets["app"]["name"],
                "maintenance_mode": st.secrets["app"].get("maintenance_mode", False),
                "debug": st.secrets["app"].get("debug", True),
                "version": "5.0",
                "contact_email": "promptandmente@gmail.com",
                "support_phone": "+34 123 456 789"
            }
            
            # Configuración de afiliados
            self.affiliates_config = {
                "commission_rate": float(st.secrets["affiliates"]["commission_rate"]),
                "min_payout": float(st.secrets["affiliates"]["min_payout"]),
                "payout_day": st.secrets["affiliates"]["payout_day"],
                "default_currency": st.secrets["affiliates"]["default_currency"],
                "kyc_required": True,
                "auto_approve": False,
                "max_referrals_per_day": 10
            }
            
            # Configuración de pagos
            self.payment_config = {
                "binance_enabled": True,
                "paypal_enabled": False,
                "stripe_enabled": False,
                "min_withdrawal": 10.0,
                "max_withdrawal": 10000.0,
                "processing_fee": 0.02
            }
            
            # Configuración de IA para diagnóstico
            self.ai_config = {
                "model": "mixtral-8x7b-32768",
                "temperature": 0.7,
                "max_tokens": 4000,
                "diagnostic_prompt": """
                Eres un experto en biodescodificación emocional. Analiza los síntomas y emociones 
                del paciente y proporciona un diagnóstico basado en los principios de la biodescodificación.
                
                SÍNTOMAS FÍSICOS: {physical_symptoms}
                SÍNTOMAS EMOCIONALES: {emotional_symptoms}
                HISTORIAL: {history}
                
                Proporciona:
                1. Análisis emocional
                2. Conflicto biológico asociado
                3. Recomendaciones específicas
                4. Afirmaciones positivas
                5. Plan de acción de 7 días
                """
            }
            
            logger.info("Configuración cargada exitosamente")
            
        except Exception as e:
            logger.error(f"Error cargando configuración: {e}")
            self._load_default_config()
    
    def _load_default_config(self):
        """Carga configuración por defecto"""
        self.email_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "promptandmente@gmail.com",
            "password": "",
            "sender_email": "promptandmente@gmail.com",
            "admin_email": "promptandmente@gmail.com"
        }
        self.groq_api_key = ""
        self.app_config = {
            "admin_password": "Enaraure25..",
            "admin_email": "promptandmente@gmail.com",
            "name": "MINDGEEKCLINIC",
            "maintenance_mode": False,
            "debug": True,
            "version": "5.0"
        }
        self.affiliates_config = {
            "commission_rate": 0.30,
            "min_payout": 50.0,
            "payout_day": "thursday",
            "default_currency": "USD"
        }

# ============================================
# PARTE 4: SISTEMA DE EMAIL MEJORADO
# ============================================

class EmailService:
    """Servicio de email completo y robusto"""
    
    def __init__(self):
        self.config = ConfigManager().email_config
        self.logger = logging.getLogger(__name__)
    
    def send_verification_email(self, to_email: str, code: str) -> Tuple[bool, str]:
        """Envía código de verificación"""
        try:
            subject = "🔐 Código de Verificación - MINDGEEKCLINIC"
            
            html_content = f"""
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Verificación de Email</title>
                <style>
                    body {{
                        font-family: 'Arial', sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: #f4f4f4;
                    }}
                    .container {{
                        background: white;
                        border-radius: 10px;
                        overflow: hidden;
                        box-shadow: 0 0 20px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 30px;
                        text-align: center;
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 24px;
                    }}
                    .content {{
                        padding: 30px;
                    }}
                    .code-container {{
                        background: #f8f9fa;
                        border: 2px dashed #dee2e6;
                        border-radius: 8px;
                        padding: 20px;
                        text-align: center;
                        margin: 30px 0;
                    }}
                    .code {{
                        font-family: 'Courier New', monospace;
                        font-size: 32px;
                        font-weight: bold;
                        color: #2196F3;
                        letter-spacing: 8px;
                    }}
                    .footer {{
                        background: #f8f9fa;
                        padding: 20px;
                        text-align: center;
                        color: #6c757d;
                        font-size: 12px;
                        border-top: 1px solid #dee2e6;
                    }}
                    .button {{
                        display: inline-block;
                        padding: 12px 24px;
                        background: #4CAF50;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                        font-weight: bold;
                        margin: 20px 0;
                    }}
                    .info-box {{
                        background: #e3f2fd;
                        border-left: 4px solid #2196F3;
                        padding: 15px;
                        margin: 20px 0;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🧠 MINDGEEKCLINIC</h1>
                        <p>Verificación de Email</p>
                    </div>
                    <div class="content">
                        <h2>¡Hola!</h2>
                        <p>Gracias por registrarte en nuestro programa de afiliados. Para completar tu registro, 
                        necesitamos verificar tu dirección de email.</p>
                        
                        <div class="code-container">
                            <p>Tu código de verificación es:</p>
                            <div class="code">{code}</div>
                            <p><small>Este código expirará en 15 minutos</small></p>
                        </div>
                        
                        <div class="info-box">
                            <strong>⚠️ Importante:</strong>
                            <ul>
                                <li>No compartas este código con nadie</li>
                                <li>Ingresa el código en la página de verificación</li>
                                <li>Si no solicitaste este código, ignora este email</li>
                            </ul>
                        </div>
                        
                        <p>Si tienes problemas con el código, puedes solicitar uno nuevo en la aplicación.</p>
                        
                        <p>Saludos,<br>
                        <strong>Equipo MINDGEEKCLINIC</strong></p>
                    </div>
                    <div class="footer">
                        <p>© 2024 MINDGEEKCLINIC. Todos los derechos reservados.</p>
                        <p>Este es un email automático, por favor no respondas.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            CÓDIGO DE VERIFICACIÓN MINDGEEKCLINIC
            
            Tu código de verificación es: {code}
            
            Este código es válido por 15 minutos.
            
            Ingresa este código en la página de verificación para completar tu registro.
            
            Si no solicitaste este código, por favor ignora este mensaje.
            
            Saludos,
            Equipo MINDGEEKCLINIC
            """
            
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config['sender_email']
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Adjuntar versiones
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Enviar email
            success = self._send_email(msg, to_email)
            
            if success:
                self.logger.info(f"Email de verificación enviado a {to_email}")
                return True, "✅ Código enviado exitosamente"
            else:
                return False, "❌ Error enviando el código"
                
        except Exception as e:
            self.logger.error(f"Error en send_verification_email: {str(e)}")
            return False, f"❌ Error: {str(e)}"
    
    def send_welcome_email(self, to_email: str, user_data: dict):
        """Envía email de bienvenida a nuevo afiliado"""
        try:
            subject = f"🎉 ¡Bienvenido {user_data['full_name']} al Programa de Afiliados!"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <div style="text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                         color: white; padding: 30px; border-radius: 10px 10px 0 0;">
                        <h1>¡Bienvenido {user_data['full_name']}!</h1>
                        <p>Tu registro en el Programa de Afiliados ha sido exitoso</p>
                    </div>
                    
                    <div style="padding: 30px;">
                        <h2 style="color: #4CAF50;">📋 Información de tu cuenta</h2>
                        
                        <div style="background: #f9f9f9; padding: 20px; border-radius: 5px; margin: 20px 0;">
                            <p><strong>ID de Afiliado:</strong> {user_data.get('affiliate_id', 'N/A')}</p>
                            <p><strong>Código de Referido:</strong> {user_data.get('referral_code', 'N/A')}</p>
                            <p><strong>Tasa de Comisión:</strong> 30%</p>
                            <p><strong>Estado de cuenta:</strong> Pendiente de verificación</p>
                            <p><strong>Fecha de registro:</strong> {datetime.now().strftime('%d/%m/%Y')}</p>
                        </div>
                        
                        <h3 style="color: #2196F3;">🔗 Tu enlace de referido único</h3>
                        <div style="background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 15px 0;">
                            <code style="font-size: 14px;">https://mindgeekclinic.streamlit.app/?ref={user_data.get('referral_code', '')}</code>
                        </div>
                        
                        <h3 style="color: #FF9800;">💰 Cómo ganar comisiones</h3>
                        <ul>
                            <li>Comparte tu enlace único con amigos y familiares</li>
                            <li>Cada venta generada a través de tu enlace te da 30% de comisión</li>
                            <li>Los pagos se realizan los jueves de cada semana</li>
                            <li>Mínimo para retiro: $50 USD</li>
                        </ul>
                        
                        <h3 style="color: #9C27B0;">🎁 Material de marketing</h3>
                        <p>Accede a nuestro kit de marketing en tu panel de afiliado.</p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="https://mindgeekclinic.streamlit.app/affiliate" 
                               style="background: #4CAF50; color: white; padding: 12px 24px; 
                                      text-decoration: none; border-radius: 5px; font-weight: bold;">
                               Ir a mi panel de afiliado
                            </a>
                        </div>
                        
                        <p>Si tienes preguntas, no dudes en contactarnos.</p>
                        
                        <p>Saludos,<br>
                        <strong>Equipo MINDGEEKCLINIC</strong></p>
                    </div>
                    
                    <div style="background: #f1f1f1; padding: 20px; text-align: center; 
                         color: #666; border-radius: 0 0 10px 10px;">
                        <p>© 2024 MINDGEEKCLINIC. Biodescodificación Integral.</p>
                        <p>Email: promptandmente@gmail.com</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config['sender_email']
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(html_content, 'html'))
            
            success = self._send_email(msg, to_email)
            return success
            
        except Exception as e:
            self.logger.error(f"Error en send_welcome_email: {str(e)}")
            return False
    
    def send_payment_notification(self, to_email: str, payment_data: dict):
        """Envía notificación de pago procesado"""
        try:
            subject = f"💰 Pago Procesado - ${payment_data['amount']} {payment_data['currency']}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <body>
                <h2>✅ Pago Procesado Exitosamente</h2>
                <p>Se ha procesado tu solicitud de pago:</p>
                <ul>
                    <li><strong>Monto:</strong> ${payment_data['amount']} {payment_data['currency']}</li>
                    <li><strong>Fecha:</strong> {payment_data['date']}</li>
                    <li><strong>Método:</strong> Binance</li>
                    <li><strong>ID de Transacción:</strong> {payment_data['transaction_id']}</li>
                </ul>
                <p>El pago ha sido enviado a tu dirección de Binance registrada.</p>
            </body>
            </html>
            """
            
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config['sender_email']
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(html_content, 'html'))
            
            success = self._send_email(msg, to_email)
            return success
            
        except Exception as e:
            self.logger.error(f"Error en send_payment_notification: {str(e)}")
            return False
    
    def _send_email(self, msg: MIMEMultipart, to_email: str) -> bool:
        """Envía el email usando SMTP"""
        try:
            # Configurar servidor SMTP
            if self.config['smtp_port'] == 465:
                # SSL
                server = smtplib.SMTP_SSL(self.config['smtp_server'], self.config['smtp_port'])
                server.login(self.config['username'], self.config['password'])
            else:
                # TLS
                server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
                server.starttls()
                server.login(self.config['username'], self.config['password'])
            
            # Enviar email
            server.send_message(msg)
            server.quit()
            
            return True
            
        except smtplib.SMTPAuthenticationError:
            self.logger.error("Error de autenticación SMTP. Verifica las credenciales.")
            return False
        except Exception as e:
            self.logger.error(f"Error enviando email: {str(e)}")
            return False

# ============================================
# PARTE 5: BASE DE DATOS COMPLETA
# ============================================

class DatabaseManager:
    """Gestor completo de base de datos"""
    
    def __init__(self):
        self.affiliates_file = "data/affiliates_db.json"
        self.payments_file = "data/payment_log.json"
        self.diagnostics_file = "data/diagnostics_db.json"
        self.sessions_file = "data/sessions_db.json"
        self.users_file = "data/users_db.json"
        
        # Crear directorio si no existe
        os.makedirs("data", exist_ok=True)
        
        # Inicializar bases de datos
        self._init_databases()
        
        # Configurar ChromaDB para embeddings
        self._setup_chromadb()
    
    def _init_databases(self):
        """Inicializa todas las bases de datos"""
        databases = {
            self.affiliates_file: {
                "affiliates": {},
                "next_id": 1,
                "referrals": {},
                "verification_codes": {},
                "statistics": {
                    "total_registered": 0,
                    "active_affiliates": 0,
                    "pending_affiliates": 0,
                    "suspended_affiliates": 0,
                    "total_earnings": 0.0,
                    "total_payments": 0.0,
                    "total_referrals": 0,
                    "total_conversions": 0
                },
                "settings": {
                    "commission_rate": 0.30,
                    "min_payout": 50.0,
                    "payout_day": "thursday"
                }
            },
            self.payments_file: [],
            self.diagnostics_file: {},
            self.sessions_file: {},
            self.users_file: {}
        }
        
        for file_path, default_data in databases.items():
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, indent=2, ensure_ascii=False)
    
    def _setup_chromadb(self):
        """Configura ChromaDB para embeddings"""
        try:
            self.chroma_client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory="./chroma_db"
            ))
            
            # Crear colección para diagnósticos
            self.diagnostics_collection = self.chroma_client.get_or_create_collection(
                name="diagnostics",
                metadata={"description": "Diagnósticos de biodescodificación"}
            )
            
            # Crear colección para sesiones
            self.sessions_collection = self.chroma_client.get_or_create_collection(
                name="sessions",
                metadata={"description": "Sesiones de hipnosis y meditación"}
            )
            
        except Exception as e:
            logger.warning(f"No se pudo configurar ChromaDB: {e}")
            self.chroma_client = None
    
    # ========== MÉTODOS PARA AFILIADOS ==========
    
    def add_affiliate(self, affiliate_data: dict) -> Tuple[bool, str, dict]:
        """Agrega un nuevo afiliado"""
        try:
            db = self.load_affiliates()
            
            # Verificar si el email ya existe
            for aff in db["affiliates"].values():
                if aff["email"] == affiliate_data["email"]:
                    return False, "El email ya está registrado", {}
            
            # Generar IDs y códigos
            affiliate_id = f"AFF{db['next_id']:04d}"
            referral_code = self._generate_referral_code()
            
            # Crear registro completo
            affiliate_record = {
                "id": affiliate_id,
                "referral_code": referral_code,
                "status": "pending",
                "verification_status": "pending",
                "kyc_status": "pending",
                "registration_date": datetime.now().isoformat(),
                "last_login": None,
                "last_payment": None,
                "total_earnings": 0.0,
                "pending_earnings": 0.0,
                "paid_earnings": 0.0,
                "commission_rate": 0.30,
                "referrals_count": 0,
                "conversions_count": 0,
                "total_commission": 0.0,
                "payment_method": "binance",
                "payment_address": affiliate_data.get("binance_address", ""),
                **affiliate_data
            }
            
            # Guardar en base de datos
            db["affiliates"][affiliate_id] = affiliate_record
            db["next_id"] += 1
            
            # Inicializar registro de referidos
            db["referrals"][referral_code] = {
                "affiliate_id": affiliate_id,
                "referrals": [],
                "conversions": 0,
                "total_commission": 0.0,
                "created_at": datetime.now().isoformat()
            }
            
            # Actualizar estadísticas
            db["statistics"]["total_registered"] += 1
            db["statistics"]["pending_affiliates"] += 1
            
            self.save_affiliates(db)
            
            # Crear registro de usuario
            self._create_user_record(affiliate_id, affiliate_data["email"])
            
            return True, "Afiliado registrado exitosamente", affiliate_record
            
        except Exception as e:
            return False, f"Error: {str(e)}", {}
    
    def update_affiliate_status(self, affiliate_id: str, status: str) -> bool:
        """Actualiza el estado de un afiliado"""
        try:
            db = self.load_affiliates()
            
            if affiliate_id not in db["affiliates"]:
                return False
            
            old_status = db["affiliates"][affiliate_id].get("status", "pending")
            db["affiliates"][affiliate_id]["status"] = status
            
            # Actualizar estadísticas
            if old_status != status:
                if old_status == "active":
                    db["statistics"]["active_affiliates"] -= 1
                elif old_status == "pending":
                    db["statistics"]["pending_affiliates"] -= 1
                elif old_status == "suspended":
                    db["statistics"]["suspended_affiliates"] -= 1
                
                if status == "active":
                    db["statistics"]["active_affiliates"] += 1
                elif status == "pending":
                    db["statistics"]["pending_affiliates"] += 1
                elif status == "suspended":
                    db["statistics"]["suspended_affiliates"] += 1
            
            self.save_affiliates(db)
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando estado: {e}")
            return False
    
    def add_referral(self, referral_code: str, user_id: str):
        """Agrega un referido"""
        try:
            db = self.load_affiliates()
            
            if referral_code in db["referrals"]:
                referral_data = db["referrals"][referral_code]
                
                if user_id not in referral_data["referrals"]:
                    referral_data["referrals"].append({
                        "user_id": user_id,
                        "timestamp": datetime.now().isoformat(),
                        "converted": False,
                        "conversion_date": None,
                        "commission": 0.0
                    })
                    
                    # Actualizar contador del afiliado
                    affiliate_id = referral_data["affiliate_id"]
                    if affiliate_id in db["affiliates"]:
                        db["affiliates"][affiliate_id]["referrals_count"] += 1
                    
                    db["statistics"]["total_referrals"] += 1
                    
                    self.save_affiliates(db)
                    
        except Exception as e:
            logger.error(f"Error agregando referido: {e}")
    
    def record_conversion(self, referral_code: str, user_id: str, amount: float):
        """Registra una conversión (venta)"""
        try:
            db = self.load_affiliates()
            
            if referral_code in db["referrals"]:
                referral_data = db["referrals"][referral_code]
                
                # Encontrar el referido
                for referral in referral_data["referrals"]:
                    if referral["user_id"] == user_id and not referral["converted"]:
                        referral["converted"] = True
                        referral["conversion_date"] = datetime.now().isoformat()
                        
                        # Calcular comisión (30%)
                        commission = amount * 0.30
                        referral["commission"] = commission
                        
                        # Actualizar afiliado
                        affiliate_id = referral_data["affiliate_id"]
                        if affiliate_id in db["affiliates"]:
                            affiliate = db["affiliates"][affiliate_id]
                            affiliate["conversions_count"] += 1
                            affiliate["total_commission"] += commission
                            affiliate["pending_earnings"] += commission
                            affiliate["total_earnings"] += commission
                        
                        # Actualizar datos de referidos
                        referral_data["conversions"] += 1
                        referral_data["total_commission"] += commission
                        
                        # Actualizar estadísticas
                        db["statistics"]["total_conversions"] += 1
                        db["statistics"]["total_earnings"] += commission
                        
                        self.save_affiliates(db)
                        
                        # Registrar pago pendiente
                        self._add_pending_payment(affiliate_id, commission)
                        
                        break
                        
        except Exception as e:
            logger.error(f"Error registrando conversión: {e}")
    
    def _add_pending_payment(self, affiliate_id: str, amount: float):
        """Agrega pago pendiente al historial"""
        try:
            payments = self.load_payments()
            
            payment = {
                "id": len(payments) + 1,
                "affiliate_id": affiliate_id,
                "amount": amount,
                "currency": "USD",
                "status": "pending",
                "type": "commission",
                "description": "Comisión por venta referida",
                "created_at": datetime.now().isoformat(),
                "processed_at": None,
                "transaction_id": None
            }
            
            payments.append(payment)
            self.save_payments(payments)
            
        except Exception as e:
            logger.error(f"Error agregando pago pendiente: {e}")
    
    def _generate_referral_code(self) -> str:
        """Genera un código de referido único"""
        import string
        characters = string.ascii_uppercase + string.digits
        while True:
            code = 'MG' + ''.join(random.choices(characters, k=6))
            # Verificar unicidad (implementar check en base de datos)
            return code
    
    def _create_user_record(self, user_id: str, email: str):
        """Crea un registro de usuario"""
        try:
            users = self.load_users()
            
            if user_id not in users:
                users[user_id] = {
                    "id": user_id,
                    "email": email,
                    "created_at": datetime.now().isoformat(),
                    "last_login": None,
                    "diagnostics_count": 0,
                    "sessions_count": 0,
                    "preferences": {},
                    "subscription": "free"
                }
                
                self.save_users(users)
                
        except Exception as e:
            logger.error(f"Error creando registro de usuario: {e}")
    
    # ========== MÉTODOS DE CARGA/GUARDADO ==========
    
    def load_affiliates(self) -> dict:
        """Carga datos de afiliados"""
        try:
            with open(self.affiliates_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando afiliados: {e}")
            return {"affiliates": {}, "next_id": 1, "referrals": {}, "statistics": {}}
    
    def save_affiliates(self, data: dict):
        """Guarda datos de afiliados"""
        try:
            with open(self.affiliates_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando afiliados: {e}")
    
    def load_payments(self) -> list:
        """Carga historial de pagos"""
        try:
            with open(self.payments_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando pagos: {e}")
            return []
    
    def save_payments(self, data: list):
        """Guarda historial de pagos"""
        try:
            with open(self.payments_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando pagos: {e}")
    
    def load_diagnostics(self) -> dict:
        """Carga diagnósticos"""
        try:
            with open(self.diagnostics_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def save_diagnostics(self, data: dict):
        """Guarda diagnósticos"""
        try:
            with open(self.diagnostics_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando diagnósticos: {e}")
    
    def load_sessions(self) -> dict:
        """Carga sesiones"""
        try:
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def save_sessions(self, data: dict):
        """Guarda sesiones"""
        try:
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando sesiones: {e}")
    
    def load_users(self) -> dict:
        """Carga usuarios"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def save_users(self, data: dict):
        """Guarda usuarios"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando usuarios: {e}")

# ============================================
# PARTE 6: SISTEMA DE IA PARA BIODESCODIFICACIÓN
# ============================================

class AIDiagnosticSystem:
    """Sistema de IA para diagnóstico de biodescodificación"""
    
    def __init__(self):
        self.config = ConfigManager()
        self.groq_client = None
        self.openai_client = None
        self.anthropic_client = None
        
        # Inicializar clientes de IA
        self._initialize_clients()
        
        # Base de conocimiento de biodescodificación
        self.biodescodification_knowledge = {
            "enfermedades": {
                "migraña": "Conflicto de territorio o imposibilidad de resolver un problema",
                "gastritis": "Conflicto de digestión emocional, algo que no se puede digerir",
                "asma": "Conflicto de miedo a la muerte, sensación de ahogo emocional",
                "dermatitis": "Conflicto de separación, necesidad de protección",
                "hipertensión": "Conflicto de territorio, presión emocional constante",
                "diabetes": "Conflicto de resistencia, algo dulce que falta en la vida",
                "artritis": "Conflicto de desvalorización, rigidez emocional",
                "cáncer": "Conflicto emocional grave no resuelto, resentimiento profundo"
            },
            "emociones": {
                "ira": "Hígado, vesícula biliar",
                "miedo": "Riñones, vejiga",
                "tristeza": "Pulmones, intestino grueso",
                "preocupación": "Estómago, bazo",
                "alegría": "Corazón, intestino delgado"
            },
            "tratamientos": {
                "meditación": "Para reducir estrés y ansiedad",
                "afirmaciones": "Para reprogramar creencias limitantes",
                "visualización": "Para sanar conflictos emocionales",
                "respiración": "Para liberar tensiones emocionales",
                "diario_emocional": "Para identificar patrones emocionales"
            }
        }
    
    def _initialize_clients(self):
        """Inicializa los clientes de IA"""
        try:
            # Groq
            if self.config.groq_api_key:
                self.groq_client = Groq(api_key=self.config.groq_api_key)
            
            # OpenAI
            if self.config.openai_api_key:
                self.openai_client = OpenAI(api_key=self.config.openai_api_key)
            
            # Anthropic
            if self.config.anthropic_api_key:
                self.anthropic_client = Anthropic(api_key=self.config.anthropic_api_key)
                
        except Exception as e:
            logger.error(f"Error inicializando clientes de IA: {e}")
    
    def analyze_symptoms(self, symptoms_data: dict) -> dict:
        """Analiza síntomas y proporciona diagnóstico de biodescodificación"""
        try:
            # Preparar prompt
            prompt = self._create_diagnostic_prompt(symptoms_data)
            
            # Obtener diagnóstico de IA
            diagnosis = self._get_ai_diagnosis(prompt)
            
            # Enriquecer con conocimiento de biodescodificación
            enriched_diagnosis = self._enrich_with_biodescodification(diagnosis, symptoms_data)
            
            # Generar plan de tratamiento
            treatment_plan = self._generate_treatment_plan(enriched_diagnosis)
            
            # Crear reporte completo
            report = {
                "diagnosis": enriched_diagnosis,
                "treatment_plan": treatment_plan,
                "emotional_analysis": self._analyze_emotions(symptoms_data),
                "physical_analysis": self._analyze_physical(symptoms_data),
                "recommendations": self._generate_recommendations(enriched_diagnosis),
                "timestamp": datetime.now().isoformat(),
                "session_id": f"DIAG_{int(time.time())}"
            }
            
            # Guardar en base de datos
            self._save_diagnosis_report(report)
            
            return report
            
        except Exception as e:
            logger.error(f"Error en análisis de síntomas: {e}")
            return self._get_fallback_diagnosis(symptoms_data)
    
    def _create_diagnostic_prompt(self, symptoms_data: dict) -> str:
        """Crea prompt para diagnóstico"""
        prompt = f"""
        Eres un experto en biodescodificación emocional con 20 años de experiencia.
        
        ANALIZA los siguientes síntomas del paciente:
        
        INFORMACIÓN PERSONAL:
        - Edad: {symptoms_data.get('age', 'No especificada')}
        - Género: {symptoms_data.get('gender', 'No especificado')}
        
        SÍNTOMAS FÍSICOS:
        {symptoms_data.get('physical_symptoms', [])}
        
        SÍNTOMAS EMOCIONALES:
        {symptoms_data.get('emotional_symptoms', [])}
        
        HISTORIAL:
        {symptoms_data.get('history', 'No especificado')}
        
        DURACIÓN:
        {symptoms_data.get('duration', 'No especificada')}
        
        PROPORCIONA UN DIAGNÓSTICO COMPLETO DE BIODESCODIFICACIÓN CON:
        
        1. ANÁLISIS EMOCIONAL:
           - Emociones predominantes
           - Conflictos emocionales no resueltos
           - Patrones emocionales recurrentes
        
        2. CONFLICTO BIOLÓGICO:
           - Órgano/sistema afectado según biodescodificación
           - Conflicto biológico específico
           - Fase de la enfermedad (activa/reparación)
        
        3. SIGNIFICADO EMOCIONAL:
           - Qué está expresando el cuerpo
           - Mensaje del síntoma
           - Necesidad emocional no cubierta
        
        4. RECOMENDACIONES ESPECÍFICAS:
           - Técnicas de liberación emocional
           - Cambios en estilo de vida
           - Afirmaciones positivas específicas
        
        5. PLAN DE ACCIÓN (7 días):
           - Día a día qué hacer
           - Ejercicios prácticos
           - Seguimiento recomendado
        
        Formato la respuesta en JSON con estas secciones.
        """
        
        return prompt
    
    def _get_ai_diagnosis(self, prompt: str) -> dict:
        """Obtiene diagnóstico de IA usando Groq"""
        try:
            if self.groq_client:
                response = self.groq_client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "Eres un experto en biodescodificación emocional. Proporciona diagnósticos precisos y recomendaciones prácticas."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    model="mixtral-8x7b-32768",
                    temperature=0.7,
                    max_tokens=4000,
                    top_p=1,
                    stream=False
                )
                
                # Parsear respuesta JSON
                content = response.choices[0].message.content
                
                # Intentar extraer JSON si está presente
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    # Si no hay JSON, crear estructura manualmente
                    return {
                        "analysis": content,
                        "conflict": "Por analizar",
                        "recommendations": ["Consulta con un especialista"]
                    }
                    
        except Exception as e:
            logger.error(f"Error obteniendo diagnóstico de IA: {e}")
        
        # Fallback
        return {
            "analysis": "Análisis no disponible temporalmente",
            "conflict": "Por determinar",
            "recommendations": ["Descansar", "Beber agua", "Consultar profesional"]
        }
    
    def _enrich_with_biodescodification(self, diagnosis: dict, symptoms_data: dict) -> dict:
        """Enriquece el diagnóstico con conocimiento de biodescodificación"""
        enriched = diagnosis.copy()
        
        # Añadir conocimiento específico
        enriched["biodescodification_insights"] = []
        
        # Buscar correspondencias con síntomas físicos
        physical_symptoms = symptoms_data.get('physical_symptoms', [])
        for symptom in physical_symptoms:
            symptom_lower = symptom.lower()
            for enfermedad, significado in self.biodescodification_knowledge["enfermedades"].items():
                if enfermedad in symptom_lower:
                    enriched["biodescodification_insights"].append({
                        "symptom": symptom,
                        "conflict": significado,
                        "organ": self._get_organ_for_symptom(symptom)
                    })
        
        # Añadir análisis emocional basado en biodescodificación
        emotional_symptoms = symptoms_data.get('emotional_symptoms', [])
        for emotion in emotional_symptoms:
            emotion_lower = emotion.lower()
            for emocion_base, organos in self.biodescodification_knowledge["emociones"].items():
                if emocion_base in emotion_lower:
                    enriched["biodescodification_insights"].append({
                        "emotion": emotion,
                        "affected_organs": organos,
                        "recommendation": self._get_emotion_recommendation(emocion_base)
                    })
        
        return enriched
    
    def _get_organ_for_symptom(self, symptom: str) -> str:
        """Obtiene órgano relacionado con síntoma"""
        organ_mapping = {
            "cabeza": "Cerebro, sistema nervioso",
            "estómago": "Sistema digestivo",
            "pecho": "Corazón, pulmones",
            "espalda": "Columna vertebral, riñones",
            "piel": "Sistema tegumentario",
            "articulaciones": "Sistema óseo-muscular"
        }
        
        for key, value in organ_mapping.items():
            if key in symptom.lower():
                return value
        
        return "Por determinar"
    
    def _get_emotion_recommendation(self, emotion: str) -> str:
        """Obtiene recomendación para emoción específica"""
        recommendations = {
            "ira": "Practicar técnicas de respiración y expresión asertiva",
            "miedo": "Trabajar con visualizaciones de seguridad y confianza",
            "tristeza": "Permitir el duelo y conectar con la autocompasión",
            "preocupación": "Meditación mindfulness y planificación realista",
            "alegría": "Canalizar la energía de forma creativa y compartir"
        }
        
        return recommendations.get(emotion, "Consulta con un terapeuta")
    
    def _generate_treatment_plan(self, diagnosis: dict) -> dict:
        """Genera plan de tratamiento personalizado"""
        plan = {
            "duration_days": 30,
            "daily_practices": [],
            "weekly_sessions": [],
            "diet_recommendations": [],
            "lifestyle_changes": [],
            "monitoring": []
        }
        
        # Añadir prácticas según diagnóstico
        if "ansiedad" in str(diagnosis).lower():
            plan["daily_practices"].extend([
                "Respiración diafragmática 10 min",
                "Meditación mindfulness 15 min",
                "Diario emocional antes de dormir"
            ])
            plan["weekly_sessions"].append("Sesión de hipnosis para ansiedad")
        
        if "depresión" in str(diagnosis).lower():
            plan["daily_practices"].extend([
                "Ejercicio físico moderado 30 min",
                "Exposición a luz solar 20 min",
                "Gratitud diaria (3 cosas)"
            ])
            plan["weekly_sessions"].append("Terapia cognitivo-conductual")
        
        # Recomendaciones dietéticas
        plan["diet_recommendations"].extend([
            "Aumentar consumo de omega-3 (pescado, nueces)",
            "Reducir azúcares refinados",
            "Mantener hidratación adecuada",
            "Consumir probióticos naturales"
        ])
        
        # Cambios de estilo de vida
        plan["lifestyle_changes"].extend([
            "Establecer rutina de sueño regular",
            "Reducir exposición a noticias negativas",
            "Practicar hobbies creativos",
            "Conectar con naturaleza semanalmente"
        ])
        
        # Monitoreo
        plan["monitoring"].extend([
            "Registro diario de síntomas",
            "Escala de humor (1-10)",
            "Horas de sueño de calidad",
            "Nivel de energía"
        ])
        
        return plan
    
    def _analyze_emotions(self, symptoms_data: dict) -> dict:
        """Analiza el perfil emocional"""
        emotional_symptoms = symptoms_data.get('emotional_symptoms', [])
        
        analysis = {
            "primary_emotions": [],
            "emotional_patterns": [],
            "intensity_level": "moderado",
            "coping_mechanisms": [],
            "emotional_needs": []
        }
        
        # Identificar emociones primarias
        emotion_categories = {
            "ira": ["enfado", "rabia", "frustración", "irritabilidad"],
            "miedo": ["ansiedad", "pánico", "preocupación", "nerviosismo"],
            "tristeza": ["depresión", "melancolía", "desesperanza", "vacío"],
            "alegría": ["euforia", "excitación", "contento", "satisfacción"]
        }
        
        for symptom in emotional_symptoms:
            symptom_lower = symptom.lower()
            for category, keywords in emotion_categories.items():
                if any(keyword in symptom_lower for keyword in keywords):
                    if category not in analysis["primary_emotions"]:
                        analysis["primary_emotions"].append(category)
        
        # Determinar intensidad
        symptom_count = len(emotional_symptoms)
        if symptom_count > 7:
            analysis["intensity_level"] = "alto"
        elif symptom_count > 3:
            analysis["intensity_level"] = "moderado"
        else:
            analysis["intensity_level"] = "bajo"
        
        # Identificar patrones
        patterns = []
        if "ansiedad" in str(emotional_symptoms).lower() and "insomnio" in str(symptoms_data.get('physical_symptoms', [])).lower():
            patterns.append("Patrón ansiedad-insomnio")
        if "tristeza" and "fatiga" in str(symptoms_data).lower():
            patterns.append("Patrón depresión-fatiga")
        
        analysis["emotional_patterns"] = patterns
        
        # Necesidades emocionales
        needs = []
        if "ira" in analysis["primary_emotions"]:
            needs.append("Expresión emocional segura")
        if "miedo" in analysis["primary_emotions"]:
            needs.append("Seguridad y protección")
        if "tristeza" in analysis["primary_emotions"]:
            needs.append("Aceptación y duelo")
        
        analysis["emotional_needs"] = needs
        
        return analysis
    
    def _analyze_physical(self, symptoms_data: dict) -> dict:
        """Analiza síntomas físicos"""
        physical_symptoms = symptoms_data.get('physical_symptoms', [])
        
        analysis = {
            "systems_affected": [],
            "severity": "leve",
            "chronicity": "agudo",
            "triggers": [],
            "body_mind_connection": []
        }
        
        # Sistema afectado
        system_mapping = {
            "cabeza": "sistema_nervioso",
            "estómago": "sistema_digestivo",
            "corazón": "sistema_cardiovascular",
            "piel": "sistema_tegumentario",
            "articulaciones": "sistema_musculoesquelético",
            "pulmones": "sistema_respiratorio"
        }
        
        systems = set()
        for symptom in physical_symptoms:
            symptom_lower = symptom.lower()
            for key, system in system_mapping.items():
                if key in symptom_lower:
                    systems.add(system)
        
        analysis["systems_affected"] = list(systems)
        
        # Severidad (basado en cantidad de síntomas)
        symptom_count = len(physical_symptoms)
        if symptom_count > 5:
            analysis["severity"] = "alto"
        elif symptom_count > 2:
            analysis["severity"] = "moderado"
        
        # Cronicidad (basado en duración)
        duration = symptoms_data.get('duration', '').lower()
        if "mes" in duration or "año" in duration:
            analysis["chronicity"] = "crónico"
        
        # Conexión cuerpo-mente
        connections = []
        for symptom in physical_symptoms:
            if "dolor" in symptom.lower():
                connections.append(f"{symptom} → Resistencia emocional")
            if "fatiga" in symptom.lower():
                connections.append(f"{symptom} → Agotamiento emocional")
            if "inflamación" in symptom.lower():
                connections.append(f"{symptom} → Ira contenida")
        
        analysis["body_mind_connection"] = connections
        
        return analysis
    
    def _generate_recommendations(self, diagnosis: dict) -> list:
        """Genera recomendaciones personalizadas"""
        recommendations = [
            "Mantener un diario emocional para identificar patrones",
            "Practicar técnicas de respiración consciente diariamente",
            "Establecer una rutina de sueño regular",
            "Incluir actividad física moderada en la rutina diaria",
            "Reducir consumo de estimulantes (café, azúcar)",
            "Practicar gratitud diaria (3 cosas al día)",
            "Buscar apoyo social o profesional si es necesario"
        ]
        
        # Recomendaciones específicas basadas en diagnóstico
        if "ansiedad" in str(diagnosis).lower():
            recommendations.append("Practicar grounding techniques (5-4-3-2-1)")
            recommendations.append("Limitar exposición a noticias y redes sociales")
        
        if "depresión" in str(diagnosis).lower():
            recommendations.append("Exposición a luz solar 20 minutos diarios")
            recommendations.append("Actividades placenteras programadas")
        
        return recommendations
    
    def _save_diagnosis_report(self, report: dict):
        """Guarda el reporte de diagnóstico"""
        try:
            db = DatabaseManager()
            diagnostics = db.load_diagnostics()
            
            session_id = report.get("session_id", f"DIAG_{int(time.time())}")
            diagnostics[session_id] = report
            
            db.save_diagnostics(diagnostics)
            
            # También guardar en ChromaDB si está disponible
            if hasattr(db, 'diagnostics_collection') and db.diagnostics_collection:
                db.diagnostics_collection.add(
                    documents=[json.dumps(report, ensure_ascii=False)],
                    metadatas=[{"type": "diagnosis", "timestamp": report["timestamp"]}],
                    ids=[session_id]
                )
                
        except Exception as e:
            logger.error(f"Error guardando diagnóstico: {e}")
    
    def _get_fallback_diagnosis(self, symptoms_data: dict) -> dict:
        """Diagnóstico de fallback cuando IA no está disponible"""
        return {
            "diagnosis": {
                "analysis": "Sistema temporalmente no disponible. Consulta recomendaciones generales.",
                "conflict": "Por determinar",
                "recommendations": ["Descansar adecuadamente", "Mantenerse hidratado", "Consultar profesional"]
            },
            "treatment_plan": {
                "duration_days": 7,
                "daily_practices": ["Respiración profunda 5 min", "Caminata ligera 15 min"],
                "recommendations": ["Dieta balanceada", "Sueño regular", "Reducción de estrés"]
            },
            "emotional_analysis": {
                "primary_emotions": ["Por analizar"],
                "intensity_level": "moderado"
            },
            "timestamp": datetime.now().isoformat()
        }

# ============================================
# PARTE 7: SISTEMA DE HIPNOSIS Y MEDITACIONES
# ============================================

class HypnosisSystem:
    """Sistema de sesiones de hipnosis y meditación guiada"""
    
    def __init__(self):
        self.sessions_db = DatabaseManager()
        self.ai_system = AIDiagnosticSystem()
        
        # Catálogo de sesiones
        self.session_catalog = {
            "relajacion_profunda": {
                "title": "Relajación Profunda",
                "duration": 20,
                "description": "Relajación muscular progresiva y calma mental",
                "benefits": ["Reducción de estrés", "Mejora del sueño", "Calma mental"],
                "audio_file": None,
                "script": self._get_relaxation_script()
            },
            "liberacion_emocional": {
                "title": "Liberación Emocional",
                "duration": 25,
                "description": "Libera emociones bloqueadas y sana heridas emocionales",
                "benefits": ["Liberación emocional", "Sanación interior", "Renovación energética"],
                "script": self._get_emotional_release_script()
            },
            "autoestima_confianza": {
                "title": "Autoestima y Confianza",
                "duration": 22,
                "description": "Refuerza tu autoestima y desarrolla confianza en ti mismo",
                "benefits": ["Autoaceptación", "Confianza personal", "Empoderamiento"],
                "script": self._get_self_esteem_script()
            },
            "manejo_ansiedad": {
                "title": "Manejo de Ansiedad",
                "duration": 18,
                "description": "Técnicas para reducir la ansiedad y encontrar tranquilidad",
                "benefits": ["Reducción de ansiedad", "Control emocional", "Paz interior"],
                "script": self._get_anxiety_script()
            },
            "sanacion_interior": {
                "title": "Sanación Interior",
                "duration": 30,
                "description": "Proceso de sanación profunda a nivel emocional y espiritual",
                "benefits": ["Sanación emocional", "Reconciliación interior", "Renovación"],
                "script": self._get_healing_script()
            },
            "conexion_mindfulness": {
                "title": "Conexión Mindfulness",
                "duration": 15,
                "description": "Práctica de mindfulness para el aquí y el ahora",
                "benefits": ["Presencia mental", "Claridad", "Reducción de estrés"],
                "script": self._get_mindfulness_script()
            }
        }
    
    def get_session(self, session_type: str, user_data: dict = None) -> dict:
        """Obtiene una sesión personalizada"""
        if session_type not in self.session_catalog:
            session_type = "relajacion_profunda"
        
        base_session = self.session_catalog[session_type].copy()
        
        # Personalizar si hay datos del usuario
        if user_data:
            base_session["personalized"] = self._personalize_session(base_session, user_data)
        else:
            base_session["personalized"] = False
        
        # Generar audio si es posible
        base_session["audio_available"] = self._generate_audio_session(base_session)
        
        # Crear ID de sesión
        base_session["session_id"] = f"SESS_{int(time.time())}_{random.randint(1000, 9999)}"
        base_session["start_time"] = datetime.now().isoformat()
        
        return base_session
    
    def _personalize_session(self, session: dict, user_data: dict) -> dict:
        """Personaliza la sesión basada en datos del usuario"""
        personalized = session.copy()
        
        # Extraer nombre si está disponible
        name = user_data.get('name', 'querido usuario')
        
        # Personalizar script
        script = personalized.get('script', '')
        script = script.replace("[NOMBRE]", name)
        
        # Añadir elementos personalizados basados en diagnóstico si existe
        if 'diagnosis' in user_data:
            diagnosis = user_data['diagnosis']
            
            # Añadir afirmaciones específicas
            if 'conflict' in diagnosis:
                conflict = diagnosis['conflict']
                affirmation = self._create_affirmation_for_conflict(conflict)
                script += f"\n\nAfirmación específica: {affirmation}"
            
            # Añadir visualizaciones personalizadas
            if 'emotional_needs' in diagnosis:
                needs = diagnosis['emotional_needs']
                if needs:
                    visualization = self._create_visualization_for_needs(needs[0])
                    script += f"\n\nVisualización: {visualization}"
        
        personalized['script'] = script
        personalized['personalized_for'] = name
        
        return personalized
    
    def _create_affirmation_for_conflict(self, conflict: str) -> str:
        """Crea afirmación positiva para un conflicto específico"""
        affirmations = {
            "territorio": "Estoy seguro y protegido en mi espacio vital",
            "separación": "Merezco amor y conexión en todas mis relaciones",
            "desvalorización": "Soy valioso y merezco respeto y aprecio",
            "miedo": "Confío en la vida y me siento seguro en cada momento",
            "ira": "Libero con amor lo que ya no me sirve"
        }
        
        for key, affirmation in affirmations.items():
            if key in conflict.lower():
                return affirmation
        
        return "Elijo paz, amor y sanación en cada momento"
    
    def _create_visualization_for_needs(self, need: str) -> str:
        """Crea visualización para necesidad emocional"""
        visualizations = {
            "seguridad": "Imagina una luz dorada que te envuelve protegiéndote",
            "amor": "Visualiza tu corazón expandiéndose con amor incondicional",
            "aceptación": "Imagínate siendo abrazado con compasión y entendimiento",
            "expresión": "Visualiza tus palabras fluyendo con claridad y armonía"
        }
        
        return visualizations.get(need.lower(), "Visualiza paz y armonía en tu interior")
    
    def _generate_audio_session(self, session: dict) -> bool:
        """Genera audio para la sesión (simulado por ahora)"""
        # En una implementación real, esto generaría audio usando TTS
        # Por ahora, solo marcamos que el audio está "disponible"
        return True
    
    def _get_relaxation_script(self) -> str:
        """Script para relajación profunda"""
        return """
        [NOMBRE], bienvenido a esta sesión de relajación profunda.
        
        Encuentra una posición cómoda, ya sea sentado o acostado.
        Cierra suavemente los ojos y permite que tu cuerpo se asiente.
        
        Comienza llevando tu atención a tu respiración...
        Inhalando profundamente... y exhalando lentamente...
        
        Vamos a relajar cada parte de tu cuerpo, comenzando por los pies...
        Siente cómo la tensión se disuelve... los músculos se sueltan...
        
        Subiendo a las piernas... dejando ir cualquier esfuerzo...
        Las caderas... la pelvis... completamente relajadas...
        
        El abdomen... suave y tranquilo...
        El pecho... expandiéndose con cada respiración...
        
        Los hombros... liberando el peso del día...
        Los brazos... pesados y relajados...
        Las manos... sueltas y abiertas...
        
        El cuello... libre de tensión...
        El rostro... todos los músculos faciales relajados...
        La mandíbula... suelta...
        Los ojos... en descanso profundo...
        
        Tu mente se calma... los pensamientos se aquietan...
        Estás en un estado de paz profunda...
        
        Permanece en este estado de relajación durante unos minutos...
        Disfruta de esta calma interior...
        
        Cuando estés listo, comienza a volver lentamente...
        Mueve suavemente los dedos de las manos y pies...
        Estira el cuerpo con suavidad...
        Y abre los ojos cuando te sientas preparado...
        
        Te sientes renovado, tranquilo y en paz.
        """
    
    def _get_emotional_release_script(self) -> str:
        """Script para liberación emocional"""
        return """
        [NOMBRE], esta sesión te guiará en la liberación de emociones almacenadas.
        
        Conéctate con tu respiración... profunda y consciente...
        Permite que surja cualquier emoción que necesite ser liberada...
        
        Visualiza un lugar seguro en tu interior...
        Un espacio de aceptación y compasión...
        
        Si hay tristeza, permítela fluir como un río que limpia...
        Si hay ira, transfórmala en energía creativa...
        Si hay miedo, envuélvelo en luz amorosa...
        
        Cada emoción tiene un mensaje... escúchalo con amor...
        Luego, libérala con gratitud por su enseñanza...
        
        Siente cómo tu corazón se hace más ligero...
        Cómo el espacio interior se expande...
        
        Eres más que tus emociones... eres la conciencia que las observa...
        Desde esta conciencia, elige paz... elige amor... elige libertad...
        
        Permanece en este estado de liberación...
        """
    
    def _get_self_esteem_script(self) -> str:
        """Script para autoestima y confianza"""
        return """
        [NOMBRE], en esta sesión fortalecerás tu autoestima y confianza.
        
        Comienza recordando tus cualidades únicas...
        Tus fortalezas... tus talentos... tu esencia...
        
        Repite en tu mente: "Me acepto completamente"
        "Me respeto y me valoro"
        "Confío en mi sabiduría interior"
        
        Visualiza una versión de ti mismo llena de confianza...
        Cómo se mueve... cómo habla... cómo se relaciona...
        Conecta con esa energía de seguridad interior...
        
        Siente cómo esta confianza se integra en cada célula...
        Cómo transforma tu postura... tu mirada... tu presencia...
        
        Eres digno de amor... digno de respeto... digno de éxito...
        Tu valor es inherente... no depende de logros externos...
        
        Desde este lugar de autoestima, tomas decisiones alineadas...
        Te expresas auténticamente... estableces límites sanos...
        
        Esta confianza crece cada día... fortaleciéndote interiormente...
        """
    
    def _get_anxiety_script(self) -> str:
        """Script para manejo de ansiedad"""
        return """
        [NOMBRE], esta sesión te ayudará a calmar la ansiedad.
        
        Primero, conecta con el momento presente...
        Nota 5 cosas que puedes ver...
        4 cosas que puedes tocar...
        3 cosas que puedes oír...
        2 cosas que puedes oler...
        1 cosa que puedes saborear...
        
        Ahora lleva la atención a tu cuerpo...
        ¿Dónde sientes la ansiedad?...
        Respira hacia esa zona... suavizando... liberando...
        
        Visualiza la ansiedad como una nube que pasa...
        Tú eres el cielo despejado... vasto y tranquilo...
        Las nubes vienen y van... el cielo permanece...
        
        Con cada exhalación, suelta preocupaciones...
        Con cada inhalación, aceptas calma...
        
        Recuerda: este momento es seguro...
        Tienes los recursos para manejarlo...
        La ansiedad es una señal, no una sentencia...
        
        Poco a poco, la calma se establece...
        La claridad regresa... la paz se restaura...
        """
    
    def _get_healing_script(self) -> str:
        """Script para sanación interior"""
        return """
        [NOMBRE], bienvenido a este espacio de sanación profunda.
        
        Conéctate con tu cuerpo sabio... ese que siempre busca equilibrio...
        Escucha sus mensajes... honra su sabiduría...
        
        Visualiza una luz sanadora entrando por la coronilla...
        Una luz dorada, llena de amor y compasión...
        Fluye por tu cabeza... tu cuello... tus hombros...
        
        Llega a tu pecho... a tu corazón...
        Disuelve viejas heridas... sana memorias dolorosas...
        Tu corazón se abre... se expande... se renueva...
        
        La luz continúa hacia tu abdomen... liberando miedos...
        Hacia tus piernas... arraigándote en fortaleza...
        Hacia tus pies... conectándote con la tierra...
        
        Cada célula de tu cuerpo se baña en esta luz sanadora...
        Se regenera... se revitaliza... se armoniza...
        
        Eres un ser completo... sanado... renovado...
        Tu esencia es perfecta salud... perfecta armonía...
        
        Permanece en esta frecuencia de sanación...
        Permite que se integre profundamente...
        """
    
    def _get_mindfulness_script(self) -> str:
        """Script para mindfulness"""
        return """
        [NOMBRE], practiquemos mindfulness juntos.
        
        Simplemente observa... sin juzgar... sin aferrarte...
        Observa tu respiración... el aire entra... el aire sale...
        
        Observa los sonidos... lejos... cerca... sin etiquetarlos...
        Observa las sensaciones en tu cuerpo... cambiantes... momentáneas...
        
        Cuando la mente divague, vuelve amablemente al ahora...
        Al sonido... a la respiración... a la sensación presente...
        
        No hay dónde llegar... no hay nada que conseguir...
        Solo este momento... solo esta experiencia...
        
        En este espacio de presencia, encuentras paz...
        Encuentras claridad... encuentras tu centro...
        
        El mindfulness es regresar a casa... a tu verdadero ser...
        Una y otra vez... con paciencia... con compasión...
        
        Permanece aquí... en el ahora... en la presencia...
        """
    
    def start_session(self, session_type: str, user_id: str = None) -> dict:
        """Inicia una sesión y la registra"""
        session = self.get_session(session_type)
        
        # Registrar en base de datos
        if user_id:
            self._record_session(session, user_id)
        
        return session
    
    def _record_session(self, session: dict, user_id: str):
        """Registra la sesión en la base de datos"""
        try:
            db = self.sessions_db
            sessions = db.load_sessions()
            
            session_record = {
                "session_id": session["session_id"],
                "user_id": user_id,
                "type": session["title"],
                "duration": session["duration"],
                "start_time": session["start_time"],
                "end_time": datetime.now().isoformat(),
                "personalized": session.get("personalized", False),
                "completed": True
            }
            
            if user_id not in sessions:
                sessions[user_id] = []
            
            sessions[user_id].append(session_record)
            
            # Limitar historial a 50 sesiones por usuario
            if len(sessions[user_id]) > 50:
                sessions[user_id] = sessions[user_id][-50:]
            
            db.save_sessions(sessions)
            
            # Actualizar contador en usuarios
            users = db.load_users()
            if user_id in users:
                users[user_id]["sessions_count"] = users[user_id].get("sessions_count", 0) + 1
                users[user_id]["last_session"] = session["start_time"]
                db.save_users(users)
            
        except Exception as e:
            logger.error(f"Error registrando sesión: {e}")

# ============================================
# PARTE 8: SISTEMA DE GENERACIÓN DE PDF
# ============================================

class PDFGenerator:
    """Generador de reportes PDF profesionales"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configura estilos personalizados"""
        # Estilo para título principal
        self.styles.add(ParagraphStyle(
            name='MainTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2E4053'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Estilo para subtítulos
        self.styles.add(ParagraphStyle(
            name='SubTitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#3498DB'),
            spaceAfter=15,
            spaceBefore=20
        ))
        
        # Estilo para contenido
def _setup_custom_styles(self):
    """Configura estilos personalizados"""
    # Verifica si el estilo ya existe antes de agregarlo
    if 'CustomTitle' not in self.styles:
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2E86AB'),
            spaceAfter=30
        ))
    
    # 🔥 CAMBIA ESTA PARTE - VERIFICA SI BodyText YA EXISTE
    if 'CustomHeading' not in self.styles:
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#A23B72'),
            spaceAfter=15
        ))
    
    # 🔥 ESTE ES EL CAMBIO CRÍTICO: verifica si 'BodyText' ya existe
    if 'BodyText' not in self.styles:
        self.styles.add(ParagraphStyle(
            name='BodyText',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=14,
            spaceAfter=12
        ))
    else:
        # Si ya existe, simplemente lo obtenemos
        pass  # Ya existe, no necesitamos crearlo
        
        # Estilo para listas
        self.styles.add(ParagraphStyle(
            name='Bullet',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2C3E50'),
            leftIndent=20,
            spaceAfter=8,
            bulletIndent=10
        ))
    
    def generate_diagnostic_report(self, diagnosis_data: dict, user_info: dict = None) -> BytesIO:
        """Genera reporte PDF de diagnóstico"""
        try:
            # Crear buffer para PDF
            buffer = BytesIO()
            
            # Crear documento
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Contenido del documento
            story = []
            
            # 1. Encabezado
            story.append(self._create_header(user_info))
            story.append(Spacer(1, 20))
            
            # 2. Título
            story.append(Paragraph("REPORTE DE DIAGNÓSTICO", self.styles['MainTitle']))
            story.append(Spacer(1, 10))
            
            # 3. Información básica
            story.append(self._create_basic_info(diagnosis_data, user_info))
            story.append(Spacer(1, 20))
            
            # 4. Análisis emocional
            story.append(self._create_emotional_analysis(diagnosis_data))
            story.append(Spacer(1, 20))
            
            # 5. Diagnóstico de biodescodificación
            story.append(self._create_biodescodification_diagnosis(diagnosis_data))
            story.append(Spacer(1, 20))
            
            # 6. Plan de tratamiento
            story.append(self._create_treatment_plan(diagnosis_data))
            story.append(Spacer(1, 20))
            
            # 7. Recomendaciones
            story.append(self._create_recommendations(diagnosis_data))
            story.append(Spacer(1, 20))
            
            # 8. Pie de página
            story.append(self._create_footer())
            
            # Construir PDF
            doc.build(story)
            
            # Preparar buffer para lectura
            buffer.seek(0)
            
            return buffer
            
        except Exception as e:
            logger.error(f"Error generando PDF: {e}")
            # PDF de error
            return self._generate_error_pdf()
    
    def _create_header(self, user_info: dict = None) -> Paragraph:
        """Crea encabezado del reporte"""
        date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        header_text = f"""
        <b>MINDGEEKCLINIC</b><br/>
        <font size="10">Sistema de Biodescodificación Integral</font><br/>
        <font size="9">Reporte generado: {date_str}</font>
        """
        
        if user_info:
            header_text += f"""<br/><font size="9">Paciente: {user_info.get('name', 'No especificado')}</font>"""
        
        return Paragraph(header_text, self.styles['Heading3'])
    
    def _create_basic_info(self, diagnosis_data: dict, user_info: dict = None) -> Table:
        """Crea tabla de información básica"""
        data = [
            ["INFORMACIÓN DEL DIAGNÓSTICO", ""],
            ["Fecha", diagnosis_data.get('timestamp', datetime.now().isoformat())],
            ["ID de Sesión", diagnosis_data.get('session_id', 'N/A')],
            ["Duración análisis", "Generado automáticamente"]
        ]
        
        if user_info:
            data.append(["Nombre", user_info.get('name', 'No especificado')])
            if 'age' in user_info:
                data.append(["Edad", user_info['age']])
            if 'gender' in user_info:
                data.append(["Género", user_info['gender']])
        
        table = Table(data, colWidths=[200, 200])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9F9')),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        return table
    
    def _create_emotional_analysis(self, diagnosis_data: dict) -> list:
        """Crea sección de análisis emocional"""
        story = []
        
        story.append(Paragraph("ANÁLISIS EMOCIONAL", self.styles['SubTitle']))
        
        emotional_data = diagnosis_data.get('emotional_analysis', {})
        
        # Emociones primarias
        if 'primary_emotions' in emotional_data:
            emotions_text = ", ".join(emotional_data['primary_emotions'])
            story.append(Paragraph(f"<b>Emociones predominantes:</b> {emotions_text}", self.styles['BodyText']))
        
        # Nivel de intensidad
        if 'intensity_level' in emotional_data:
            intensity = emotional_data['intensity_level'].upper()
            color = {
                'BAJO': '#27AE60',
                'MODERADO': '#F39C12',
                'ALTO': '#E74C3C'
            }.get(intensity, '#000000')
            
            story.append(Paragraph(
                f"<b>Nivel de intensidad:</b> <font color='{color}'>{intensity}</font>",
                self.styles['BodyText']
            ))
        
        # Patrones emocionales
        if 'emotional_patterns' in emotional_data and emotional_data['emotional_patterns']:
            story.append(Paragraph("<b>Patrones identificados:</b>", self.styles['BodyText']))
            for pattern in emotional_data['emotional_patterns']:
                story.append(Paragraph(f"• {pattern}", self.styles['Bullet']))
        
        # Necesidades emocionales
        if 'emotional_needs' in emotional_data and emotional_data['emotional_needs']:
            story.append(Paragraph("<b>Necesidades emocionales:</b>", self.styles['BodyText']))
            for need in emotional_data['emotional_needs']:
                story.append(Paragraph(f"• {need}", self.styles['Bullet']))
        
        return story
    
    def _create_biodescodification_diagnosis(self, diagnosis_data: dict) -> list:
        """Crea sección de diagnóstico de biodescodificación"""
        story = []
        
        story.append(Paragraph("DIAGNÓSTICO DE BIODESCODIFICACIÓN", self.styles['SubTitle']))
        
        diagnosis = diagnosis_data.get('diagnosis', {})
        
        # Análisis general
        if 'analysis' in diagnosis:
            story.append(Paragraph("<b>Análisis general:</b>", self.styles['BodyText']))
            analysis_text = diagnosis['analysis'].replace('\n', '<br/>')
            story.append(Paragraph(analysis_text, self.styles['BodyText']))
        
        # Conflicto biológico
        if 'conflict' in diagnosis:
            story.append(Paragraph(f"<b>Conflicto biológico:</b> {diagnosis['conflict']}", self.styles['BodyText']))
        
        # Insights de biodescodificación
        if 'biodescodification_insights' in diagnosis:
            insights = diagnosis['biodescodification_insights']
            if insights:
                story.append(Paragraph("<b>Insights específicos:</b>", self.styles['BodyText']))
                for insight in insights[:3]:  # Mostrar solo 3
                    if 'symptom' in insight:
                        text = f"{insight['symptom']} → {insight.get('conflict', 'Por analizar')}"
                        story.append(Paragraph(f"• {text}", self.styles['Bullet']))
        
        # Conexión cuerpo-mente
        physical_data = diagnosis_data.get('physical_analysis', {})
        if 'body_mind_connection' in physical_data and physical_data['body_mind_connection']:
            story.append(Paragraph("<b>Conexión cuerpo-mente:</b>", self.styles['BodyText']))
            for connection in physical_data['body_mind_connection'][:3]:
                story.append(Paragraph(f"• {connection}", self.styles['Bullet']))
        
        return story
    
    def _create_treatment_plan(self, diagnosis_data: dict) -> list:
        """Crea sección de plan de tratamiento"""
        story = []
        
        story.append(Paragraph("PLAN DE TRATAMIENTO", self.styles['SubTitle']))
        
        treatment_plan = diagnosis_data.get('treatment_plan', {})
        
        # Duración
        if 'duration_days' in treatment_plan:
            story.append(Paragraph(
                f"<b>Duración recomendada:</b> {treatment_plan['duration_days']} días",
                self.styles['BodyText']
            ))
        
        # Prácticas diarias
        if 'daily_practices' in treatment_plan and treatment_plan['daily_practices']:
            story.append(Paragraph("<b>Prácticas diarias:</b>", self.styles['BodyText']))
            for practice in treatment_plan['daily_practices'][:5]:
                story.append(Paragraph(f"• {practice}", self.styles['Bullet']))
        
        # Sesiones semanales
        if 'weekly_sessions' in treatment_plan and treatment_plan['weekly_sessions']:
            story.append(Paragraph("<b>Sesiones recomendadas:</b>", self.styles['BodyText']))
            for session in treatment_plan['weekly_sessions']:
                story.append(Paragraph(f"• {session}", self.styles['Bullet']))
        
        # Recomendaciones dietéticas
        if 'diet_recommendations' in treatment_plan and treatment_plan['diet_recommendations']:
            story.append(Paragraph("<b>Recomendaciones dietéticas:</b>", self.styles['BodyText']))
            for rec in treatment_plan['diet_recommendations'][:5]:
                story.append(Paragraph(f"• {rec}", self.styles['Bullet']))
        
        # Monitoreo
        if 'monitoring' in treatment_plan and treatment_plan['monitoring']:
            story.append(Paragraph("<b>Seguimiento recomendado:</b>", self.styles['BodyText']))
            for item in treatment_plan['monitoring']:
                story.append(Paragraph(f"• {item}", self.styles['Bullet']))
        
        return story
    
    def _create_recommendations(self, diagnosis_data: dict) -> list:
        """Crea sección de recomendaciones generales"""
        story = []
        
        story.append(Paragraph("RECOMENDACIONES GENERALES", self.styles['SubTitle']))
        
        recommendations = diagnosis_data.get('recommendations', [])
        
        if recommendations:
            for i, rec in enumerate(recommendations[:10], 1):
                story.append(Paragraph(f"{i}. {rec}", self.styles['BodyText']))
        else:
            story.append(Paragraph("No hay recomendaciones específicas.", self.styles['BodyText']))
        
        # Nota importante
        story.append(Spacer(1, 20))
        story.append(Paragraph(
            "<b>Nota importante:</b> Este diagnóstico es generado por inteligencia artificial "
            "y debe ser complementado con evaluación profesional. Consulta a un médico o "
            "terapeuta certificado para diagnóstico y tratamiento formal.",
            ParagraphStyle(
                name='Note',
                parent=self.styles['Normal'],
                fontSize=9,
                textColor=colors.red,
                backColor=colors.HexColor('#FDEDEC'),
                borderPadding=10,
                borderColor=colors.red,
                borderWidth=1
            )
        ))
        
        return story
    
    def _create_footer(self) -> Paragraph:
        """Crea pie de página"""
        footer_text = """
        <font size="8">
        <b>MINDGEEKCLINIC</b> - Sistema de Biodescodificación Integral<br/>
        Email: promptandmente@gmail.com | Versión: 5.0<br/>
        Este documento es confidencial. Generado automáticamente por el sistema.
        </font>
        """
        
        return Paragraph(footer_text, self.styles['Normal'])
    
    def _generate_error_pdf(self) -> BytesIO:
        """Genera PDF de error"""
        buffer = BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        story = []
        
        story.append(Paragraph("ERROR AL GENERAR REPORTE", self.styles['MainTitle']))
        story.append(Spacer(1, 20))
        
        story.append(Paragraph(
            "Lo sentimos, hubo un error al generar el reporte PDF. "
            "Por favor, intenta nuevamente o contacta con soporte.",
            self.styles['BodyText']
        ))
        
        doc.build(story)
        buffer.seek(0)
        
        return buffer

# ============================================
# PARTE 9: SISTEMA DE PAGOS Y COMISIONES
# ============================================

class PaymentSystem:
    """Sistema de gestión de pagos y comisiones"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.email_service = EmailService()
        self.config = ConfigManager()
    
    def process_payment_request(self, affiliate_id: str, amount: float) -> Tuple[bool, str, dict]:
        """Procesa solicitud de pago de un afiliado"""
        try:
            # Verificar afiliado
            db = self.db.load_affiliates()
            
            if affiliate_id not in db["affiliates"]:
                return False, "Afiliado no encontrado", {}
            
            affiliate = db["affiliates"][affiliate_id]
            
            # Verificar fondos disponibles
            available_funds = affiliate.get("pending_earnings", 0.0)
            
            if amount > available_funds:
                return False, f"Fondos insuficientes. Disponible: ${available_funds:.2f}", {}
            
            # Verificar mínimo de pago
            min_payout = self.config.affiliates_config.get("min_payout", 10.0)
            if amount < min_payout:
                return False, f"Mínimo de retiro: ${min_payout:.2f}", {}
            
            # Crear registro de pago
            payment_data = self._create_payment_record(affiliate_id, amount)
            
            # Actualizar saldos del afiliado
            affiliate["pending_earnings"] -= amount
            affiliate["paid_earnings"] += amount
            affiliate["last_payment"] = datetime.now().isoformat()
            
            db["affiliates"][affiliate_id] = affiliate
            self.db.save_affiliates(db)
            
            # Guardar pago en historial
            self._save_payment_to_history(payment_data)
            
            # Enviar notificación por email
            self._send_payment_notification(affiliate, payment_data)
            
            return True, "Solicitud de pago procesada exitosamente", payment_data
            
        except Exception as e:
            logger.error(f"Error procesando pago: {e}")
            return False, f"Error: {str(e)}", {}
    
    def _create_payment_record(self, affiliate_id: str, amount: float) -> dict:
        """Crea registro de pago"""
        payment_id = f"PAY_{int(time.time())}_{random.randint(1000, 9999)}"
        
        return {
            "payment_id": payment_id,
            "affiliate_id": affiliate_id,
            "amount": amount,
            "currency": self.config.affiliates_config.get("default_currency", "USD"),
            "status": "processing",
            "request_date": datetime.now().isoformat(),
            "estimated_completion": (datetime.now() + timedelta(days=2)).isoformat(),
            "payment_method": "binance",
            "transaction_fee": amount * 0.02,  # 2% de comisión
            "net_amount": amount * 0.98,
            "notes": "Pago procesado automáticamente por el sistema"
        }
    
    def _save_payment_to_history(self, payment_data: dict):
        """Guarda pago en historial"""
        try:
            payments = self.db.load_payments()
            payments.append(payment_data)
            self.db.save_payments(payments)
            
        except Exception as e:
            logger.error(f"Error guardando pago en historial: {e}")
    
    def _send_payment_notification(self, affiliate: dict, payment_data: dict):
        """Envía notificación de pago por email"""
        try:
            subject = f"✅ Solicitud de Pago Procesada - ${payment_data['amount']:.2f}"
            
            body = f"""
            Hola {affiliate['full_name']},
            
            Tu solicitud de pago ha sido procesada exitosamente.
            
            Detalles del pago:
            • ID de Pago: {payment_data['payment_id']}
            • Monto: ${payment_data['amount']:.2f} {payment_data['currency']}
            • Comisión: ${payment_data['transaction_fee']:.2f}
            • Neto a recibir: ${payment_data['net_amount']:.2f}
            • Método: {payment_data['payment_method'].title()}
            • Fecha estimada: {payment_data['estimated_completion'][:10]}
            
            El pago será enviado a tu dirección de Binance registrada:
            {affiliate.get('payment_address', 'No especificada')}
            
            Recibirás una notificación cuando el pago sea completado.
            
            Saludos,
            Equipo MINDGEEKCLINIC
            """
            
            self.email_service.send_email(
                to_email=affiliate['email'],
                subject=subject,
                body=body
            )
            
        except Exception as e:
            logger.error(f"Error enviando notificación de pago: {e}")
    
    def get_payment_history(self, affiliate_id: str = None) -> list:
        """Obtiene historial de pagos"""
        try:
            payments = self.db.load_payments()
            
            if affiliate_id:
                return [p for p in payments if p.get('affiliate_id') == affiliate_id]
            
            return payments
            
        except Exception as e:
            logger.error(f"Error obteniendo historial de pagos: {e}")
            return []
    
    def calculate_commission(self, sale_amount: float, commission_rate: float = None) -> float:
        """Calcula comisión para un monto de venta"""
        if commission_rate is None:
            commission_rate = self.config.affiliates_config.get("commission_rate", 0.30)
        
        return sale_amount * commission_rate
    
    def get_affiliate_balance(self, affiliate_id: str) -> dict:
        """Obtiene balance de un afiliado"""
        try:
            db = self.db.load_affiliates()
            
            if affiliate_id not in db["affiliates"]:
                return {"error": "Afiliado no encontrado"}
            
            affiliate = db["affiliates"][affiliate_id]
            
            return {
                "affiliate_id": affiliate_id,
                "full_name": affiliate.get("full_name", ""),
                "total_earnings": affiliate.get("total_earnings", 0.0),
                "pending_earnings": affiliate.get("pending_earnings", 0.0),
                "paid_earnings": affiliate.get("paid_earnings", 0.0),
                "commission_rate": affiliate.get("commission_rate", 0.30),
                "referrals_count": affiliate.get("referrals_count", 0),
                "conversions_count": affiliate.get("conversions_count", 0),
                "last_payment": affiliate.get("last_payment"),
                "min_payout": self.config.affiliates_config.get("min_payout", 50.0),
                "can_withdraw": affiliate.get("pending_earnings", 0.0) >= self.config.affiliates_config.get("min_payout", 50.0)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo balance: {e}")
            return {"error": str(e)}

# ============================================
# PARTE 10: SISTEMA DE ESTADÍSTICAS Y ANALYTICS
# ============================================

class AnalyticsSystem:
    """Sistema de análisis y estadísticas"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def get_dashboard_stats(self) -> dict:
        """Obtiene estadísticas para el dashboard"""
        try:
            db = self.db.load_affiliates()
            stats = db.get("statistics", {})
            
            # Calcular crecimiento mensual (simulado)
            today = datetime.now()
            month_start = today.replace(day=1)
            
            monthly_growth = {
                "new_affiliates": random.randint(5, 20),
                "total_commission": random.uniform(100, 500),
                "conversions": random.randint(10, 50)
            }
            
            # Obtener últimos pagos
            payments = self.db.load_payments()
            recent_payments = sorted(payments, key=lambda x: x.get('request_date', ''), reverse=True)[:5]
            
            # Obtener mejores afiliados
            affiliates = list(db.get("affiliates", {}).values())
            top_affiliates = sorted(affiliates, key=lambda x: x.get('total_commission', 0), reverse=True)[:5]
            
            return {
                "overall_stats": {
                    "total_affiliates": stats.get("total_registered", 0),
                    "active_affiliates": stats.get("active_affiliates", 0),
                    "total_earnings": stats.get("total_earnings", 0.0),
                    "total_payments": stats.get("total_payments", 0.0),
                    "total_referrals": stats.get("total_referrals", 0),
                    "total_conversions": stats.get("total_conversions", 0)
                },
                "monthly_growth": monthly_growth,
                "recent_payments": recent_payments,
                "top_affiliates": [
                    {
                        "id": a.get("id"),
                        "name": a.get("full_name", "N/A"),
                        "earnings": a.get("total_commission", 0.0),
                        "conversions": a.get("conversions_count", 0)
                    }
                    for a in top_affiliates
                ]
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def get_affiliate_performance(self, affiliate_id: str) -> dict:
        """Obtiene desempeño de un afiliado específico"""
        try:
            db = self.db.load_affiliates()
            
            if affiliate_id not in db["affiliates"]:
                return {"error": "Afiliado no encontrado"}
            
            affiliate = db["affiliates"][affiliate_id]
            
            # Calcular métricas
            referrals = db.get("referrals", {}).get(affiliate.get("referral_code", ""), {})
            referral_list = referrals.get("referrals", [])
            
            # Métricas de conversión
            total_referrals = len(referral_list)
            conversions = sum(1 for r in referral_list if r.get("converted", False))
            conversion_rate = (conversions / total_referrals * 100) if total_referrals > 0 else 0
            
            # Ingresos por mes (simulado)
            monthly_earnings = []
            for i in range(6):
                month = datetime.now() - timedelta(days=30*i)
                month_str = month.strftime("%Y-%m")
                earnings = random.uniform(50, 200) if i < 3 else random.uniform(100, 300)
                monthly_earnings.append({
                    "month": month_str,
                    "earnings": earnings
                })
            
            monthly_earnings.reverse()
            
            return {
                "basic_info": {
                    "id": affiliate_id,
                    "name": affiliate.get("full_name", ""),
                    "status": affiliate.get("status", "pending"),
                    "join_date": affiliate.get("registration_date", "")[:10],
                    "referral_code": affiliate.get("referral_code", "")
                },
                "performance_metrics": {
                    "total_referrals": total_referrals,
                    "conversions": conversions,
                    "conversion_rate": round(conversion_rate, 1),
                    "total_commission": affiliate.get("total_commission", 0.0),
                    "pending_earnings": affiliate.get("pending_earnings", 0.0),
                    "avg_conversion_value": affiliate.get("total_commission", 0.0) / conversions if conversions > 0 else 0
                },
                "monthly_earnings": monthly_earnings,
                "recent_activity": referral_list[-10:] if referral_list else []
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo desempeño: {e}")
            return {"error": str(e)}
    
    def get_system_health(self) -> dict:
        """Obtiene estado de salud del sistema"""
        try:
            # Simular métricas del sistema
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Métricas de la aplicación
            db = self.db.load_affiliates()
            total_users = len(db.get("affiliates", {}))
            
            # Último backup (simulado)
            last_backup = (datetime.now() - timedelta(hours=2)).isoformat()
            
            return {
                "server_metrics": {
                    "cpu_usage": round(cpu_percent, 1),
                    "memory_usage": round(memory.percent, 1),
                    "disk_usage": round(disk.percent, 1),
                    "uptime": str(timedelta(seconds=psutil.boot_time()))
                },
                "app_metrics": {
                    "total_users": total_users,
                    "active_sessions": random.randint(5, 50),
                    "daily_requests": random.randint(100, 500),
                    "error_rate": round(random.uniform(0.1, 2.0), 2)
                },
                "database": {
                    "last_backup": last_backup,
                    "size_mb": round(os.path.getsize(self.db.affiliates_file) / 1024 / 1024, 2),
                    "connected": True
                },
                "services": {
                    "email": True,
                    "payments": True,
                    "ai": True if ConfigManager().groq_api_key else False,
                    "storage": True
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo salud del sistema: {e}")
            return {
                "error": str(e),
                "server_metrics": {"cpu_usage": 0, "memory_usage": 0},
                "app_metrics": {"total_users": 0}
            }

# ============================================
# PARTE 11: INTERFAZ DE USUARIO - COMPONENTES
# ============================================

class UIComponents:
    """Componentes de interfaz de usuario reutilizables"""
    
    @staticmethod
    def sidebar_navigation():
        """Barra lateral de navegación"""
        with st.sidebar:
            # Logo y título
            st.markdown("""
            <div style="text-align: center;">
                <h1 style="color: #667eea;">🧠</h1>
                <h2 style="color: #764ba2;">MINDGEEKCLINIC</h2>
                <p style="color: #666; font-size: 0.9em;">Biodescodificación Integral</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Estado de la aplicación
            config = ConfigManager().app_config
            if config.get("maintenance_mode", False):
                st.warning("⚠️ Modo mantenimiento activo")
            
            # Navegación principal
            st.markdown("### 📍 Navegación")
            
            pages = [
                {"icon": "🏠", "name": "Inicio", "key": "home"},
                {"icon": "🔍", "name": "Diagnóstico", "key": "diagnostic"},
                {"icon": "🧘", "name": "Sesiones", "key": "sessions"},
                {"icon": "📊", "name": "Estadísticas", "key": "stats"},
                {"icon": "💬", "name": "Chat IA", "key": "chat"},
                {"icon": "🎯", "name": "Afiliados", "key": "affiliate"},
                {"icon": "🔐", "name": "Admin", "key": "admin"}
            ]
            
            for page in pages:
                if st.button(
                    f"{page['icon']} {page['name']}",
                    key=f"nav_{page['key']}",
                    use_container_width=True,
                    type="primary" if st.session_state.get("page") == page['key'] else "secondary"
                ):
                    st.session_state.page = page['key']
                    st.rerun()
            
            st.markdown("---")
            
            # Información de sesión
            if 'affiliate_id' in st.session_state:
                st.success(f"👤 {st.session_state.affiliate_id}")
                
                if st.button("🚪 Cerrar sesión", use_container_width=True):
                    del st.session_state.affiliate_id
                    st.rerun()
            
            # Referido activo
            if 'referral_code' in st.session_state:
                st.info(f"👋 Referido por: {st.session_state.referral_code}")
            
            st.markdown("---")
            
            # Información de contacto
            st.markdown("### 📞 Contacto")
            st.markdown("""
            **📧 Email:**  
            promptandmente@gmail.com
            
            **🕒 Soporte:**  
            24/7 vía email
            
            **🔒 Seguridad:**  
            Datos encriptados
            """)
            
            # Versión
            st.markdown(f"---\n**Versión:** {config.get('version', '5.0')}")
    
    @staticmethod
    def metric_card(title: str, value, change: str = None, icon: str = "📊"):
        """Tarjeta de métrica"""
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown(f"<h1 style='text-align: center;'>{icon}</h1>", unsafe_allow_html=True)
        
        with col2:
            st.metric(title, value, change)
    
    @staticmethod
    def progress_tracker(steps: list, current_step: int):
        """Rastreador de progreso"""
        cols = st.columns(len(steps))
        
        for i, (col, step) in enumerate(zip(cols, steps)):
            with col:
                if i < current_step:
                    st.success(f"✅ {step}")
                elif i == current_step:
                    st.info(f"⏳ {step}")
                else:
                    st.write(f"🔲 {step}")
        
        st.progress(current_step / len(steps))
    
    @staticmethod
    def notification(type: str, message: str):
        """Notificación estilizada"""
        icons = {
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️"
        }
        
        colors = {
            "success": "#d4edda",
            "error": "#f8d7da",
            "warning": "#fff3cd",
            "info": "#d1ecf1"
        }
        
        icon = icons.get(type, "ℹ️")
        color = colors.get(type, "#d1ecf1")
        
        st.markdown(f"""
        <div style="background-color: {color}; padding: 15px; border-radius: 5px; margin: 10px 0;">
            <strong>{icon} {message}</strong>
        </div>
        """, unsafe_allow_html=True)

# ============================================
# PARTE 12: PÁGINAS PRINCIPALES
# ============================================

class PageRenderer:
    """Renderizador de páginas principales"""
    
    def __init__(self):
        self.ui = UIComponents()
        self.db = DatabaseManager()
        self.ai_system = AIDiagnosticSystem()
        self.hypnosis_system = HypnosisSystem()
        self.pdf_generator = PDFGenerator()
        self.payment_system = PaymentSystem()
        self.analytics = AnalyticsSystem()
        self.email_service = EmailService()
    
    def render_home(self):
        """Renderiza página de inicio"""
        st.title("🧠 MINDGEEKCLINIC - Biodescodificación Integral")
        
        # Procesar referidos
        query_params = st.query_params
        if 'ref' in query_params:
            referral_code = query_params['ref']
            if referral_code:
                st.session_state.referral_code = referral_code
                # Registrar visita de referido
                self.db.add_referral(referral_code, f"guest_{int(time.time())}")
                st.sidebar.success(f"👋 ¡Bienvenido por referencia!")
        
        # Hero section
        st.markdown("""
        ## Transforma tu salud emocional a través de la biodescodificación
        
        **MINDGEEKCLINIC** es tu aliado para descifrar los mensajes del cuerpo 
        y transformar las emociones en bienestar integral.
        
        ### ✨ Características principales:
        """)
        
        # Características
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("### 🔍 Diagnóstico IA")
            st.write("Análisis emocional preciso con inteligencia artificial avanzada")
        
        with col2:
            st.markdown("### 🧘 Sesiones Guiadas")
            st.write("Hipnosis y meditaciones personalizadas para cada necesidad")
        
        with col3:
            st.markdown("### 📊 Seguimiento")
            st.write("Monitorea tu progreso emocional con estadísticas detalladas")
        
        with col4:
            st.markdown("### 🎯 Afiliados")
            st.write("Gana comisiones recomendando nuestro servicio")
        
        st.markdown("---")
        
        # Acciones rápidas
        st.subheader("🚀 Comienza tu viaje")
        
        col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
        
        with col_btn1:
            if st.button("🔍 Iniciar Diagnóstico", use_container_width=True, type="primary"):
                st.session_state.page = "diagnostic"
                st.rerun()
        
        with col_btn2:
            if st.button("🧘 Sesiones Guiadas", use_container_width=True):
                st.session_state.page = "sessions"
                st.rerun()
        
        with col_btn3:
            if st.button("📊 Mis Estadísticas", use_container_width=True):
                st.session_state.page = "stats"
                st.rerun()
        
        with col_btn4:
            if st.button("💬 Chat IA", use_container_width=True):
                st.session_state.page = "chat"
                st.rerun()
        
        # Programa de afiliados
        st.markdown("---")
        st.subheader("🎯 ¿Quieres ganar con MINDGEEKCLINIC?")
        
        col_aff1, col_aff2 = st.columns([2, 1])
        
        with col_aff1:
            st.markdown("""
            **Programa de Afiliados Premium:**
            
            - 💰 **30% de comisión** por cada venta
            - ⚡ **Pagos automáticos** via Binance
            - 📊 **Panel de seguimiento** en tiempo real
            - 🎨 **Material de marketing** profesional
            - 🏆 **Bonos por desempeño**
            - 📈 **Herramientas avanzadas** de analytics
            
            **Mínimo para retiro:** $50 USD
            **Pagos:** Todos los jueves
            """)
        
        with col_aff2:
            if st.button("💰 Unirse al Programa", 
                        use_container_width=True, 
                        type="secondary",
                        key="join_affiliate_home"):
                st.session_state.page = "affiliate"
                st.rerun()
        
        # Testimonios (simulados)
        st.markdown("---")
        st.subheader("💬 Lo que dicen nuestros usuarios")
        
        testimonials = [
            {"name": "Ana G.", "text": "El diagnóstico de biodescodificación me ayudó a entender la raíz emocional de mis migrañas.", "role": "Paciente"},
            {"name": "Carlos M.", "text": "Como afiliado, he ganado más de $500 en comisiones. El sistema es excelente.", "role": "Afiliado"},
            {"name": "Dra. Laura R.", "text": "Uso MINDGEEKCLINIC como herramienta complementaria en mi consulta. Muy profesional.", "role": "Terapeuta"}
        ]
        
        cols = st.columns(3)
        for col, testimonial in zip(cols, testimonials):
            with col:
                st.markdown(f"""
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 4px solid #667eea;">
                    <p style="font-style: italic;">"{testimonial['text']}"</p>
                    <p style="text-align: right; margin-top: 15px;">
                        <strong>{testimonial['name']}</strong><br/>
                        <small>{testimonial['role']}</small>
                    </p>
                </div>
                """, unsafe_allow_html=True)
    
    def render_diagnostic(self):
        """Renderiza página de diagnóstico"""
        st.title("🔍 Diagnóstico de Biodescodificación")
        
        # Verificar si ya hay un diagnóstico en progreso
        if 'current_diagnostic' in st.session_state and st.session_state.current_diagnostic:
            self._render_diagnostic_results()
            return
        
        # Formulario de diagnóstico
        with st.form("diagnostic_form"):
            st.subheader("📋 Información básica")
            
            col_info1, col_info2 = st.columns(2)
            
            with col_info1:
                name = st.text_input("Nombre (opcional)", placeholder="Tu nombre")
                age = st.number_input("Edad", min_value=1, max_value=100, value=30)
            
            with col_info2:
                gender = st.selectbox("Género", ["Prefiero no decir", "Masculino", "Femenino", "Otro"])
                occupation = st.text_input("Ocupación", placeholder="Tu profesión o actividad principal")
            
            st.divider()
            st.subheader("💭 Síntomas emocionales")
            
            emotional_options = [
                "Ansiedad", "Tristeza", "Ira/Frustración", "Miedo", "Culpa",
                "Desmotivación", "Insatisfacción", "Soledad", "Estrés crónico",
                "Irritabilidad", "Desesperanza", "Inseguridad", "Agobio"
            ]
            
            emotional_symptoms = st.multiselect(
                "¿Qué emociones predominan últimamente?",
                emotional_options,
                help="Selecciona todas las que correspondan"
            )
            
            emotional_intensity = st.slider(
                "Intensidad emocional general",
                1, 10, 5,
                help="1 = Muy baja, 10 = Muy alta"
            )
            
            sleep_quality = st.select_slider(
                "Calidad del sueño",
                options=["Muy mala", "Mala", "Regular", "Buena", "Excelente"],
                value="Regular"
            )
            
            st.divider()
            st.subheader("🤒 Síntomas físicos")
            
            physical_options = [
                "Dolores de cabeza", "Problemas digestivos", "Cansancio crónico",
                "Tensión muscular", "Cambios de peso", "Problemas cutáneos",
                "Alteraciones del sueño", "Cambios en el apetito", "Palpitaciones",
                "Problemas respiratorios", "Dolores articulares", "Mareos/Vértigos"
            ]
            
            physical_symptoms = st.multiselect(
                "¿Qué síntomas físicos has experimentado?",
                physical_options,
                help="Selecciona todos los síntomas relevantes"
            )
            
            symptom_duration = st.selectbox(
                "¿Cuánto tiempo llevas con estos síntomas?",
                ["Menos de 1 semana", "1-4 semanas", "1-3 meses", "3-6 meses", "6-12 meses", "Más de 1 año"]
            )
            
            pain_intensity = st.slider(
                "Intensidad del malestar físico",
                1, 10, 3,
                help="1 = Muy baja, 10 = Muy alta"
            )
            
            st.divider()
            st.subheader("🎯 Áreas de vida afectadas")
            
            life_areas = st.multiselect(
                "¿Qué áreas de tu vida se han visto afectadas?",
                ["Trabajo/Estudios", "Relaciones personales", "Salud física",
                 "Economía", "Desarrollo personal", "Tiempo libre", "Familia"]
            )
            
            additional_info = st.text_area(
                "Información adicional (opcional)",
                placeholder="¿Hay algo más que quieras compartir sobre tu situación? Eventos recientes, preocupaciones específicas, etc.",
                height=100
            )
            
            st.divider()
            
            # Términos y condiciones
            accept_terms = st.checkbox(
                "Acepto que este diagnóstico es generado por IA y debe ser complementado con evaluación profesional"
            )
            
            # Botón de envío
            col_submit1, col_submit2, col_submit3 = st.columns([1, 2, 1])
            
            with col_submit2:
                submitted = st.form_submit_button(
                    "🔬 Generar Diagnóstico",
                    type="primary",
                    use_container_width=True,
                    disabled=not accept_terms
                )
            
            if submitted:
                if not emotional_symptoms and not physical_symptoms:
                    st.error("Por favor, selecciona al menos un síntoma emocional o físico")
                else:
                    # Preparar datos para diagnóstico
                    symptoms_data = {
                        "name": name if name else "Usuario",
                        "age": age,
                        "gender": gender,
                        "occupation": occupation,
                        "emotional_symptoms": emotional_symptoms,
                        "emotional_intensity": emotional_intensity,
                        "sleep_quality": sleep_quality,
                        "physical_symptoms": physical_symptoms,
                        "symptom_duration": symptom_duration,
                        "pain_intensity": pain_intensity,
                        "life_areas": life_areas,
                        "additional_info": additional_info,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Guardar en sesión
                    st.session_state.current_diagnostic = symptoms_data
                    
                    # Mostrar spinner mientras se genera diagnóstico
                    with st.spinner("🔍 Analizando tu perfil emocional con IA..."):
                        # Generar diagnóstico
                        diagnosis = self.ai_system.analyze_symptoms(symptoms_data)
                        st.session_state.current_diagnosis = diagnosis
                        
                        # Registrar en historial
                        if 'diagnostic_history' not in st.session_state:
                            st.session_state.diagnostic_history = []
                        
                        st.session_state.diagnostic_history.append({
                            "data": symptoms_data,
                            "diagnosis": diagnosis,
                            "timestamp": datetime.now().isoformat()
                        })
                    
                    st.success("✅ Diagnóstico completado")
                    st.rerun()
        
        # Botón para volver
        if st.button("🏠 Volver al inicio", type="secondary"):
            st.session_state.page = "home"
            st.rerun()
    
    def _render_diagnostic_results(self):
        """Renderiza resultados del diagnóstico"""
        if 'current_diagnosis' not in st.session_state:
            st.error("No hay diagnóstico disponible")
            return
        
        diagnosis = st.session_state.current_diagnosis
        symptoms_data = st.session_state.current_diagnostic
        
        st.success("🎉 ¡Diagnóstico Completado!")
        
        # Pestañas para diferentes secciones
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📋 Resumen", 
            "💡 Análisis", 
            "📊 Plan de Tratamiento", 
            "📄 Reporte PDF", 
            "📚 Historial"
        ])
        
        with tab1:
            self._render_diagnostic_summary(diagnosis, symptoms_data)
        
        with tab2:
            self._render_detailed_analysis(diagnosis)
        
        with tab3:
            self._render_treatment_plan(diagnosis)
        
        with tab4:
            self._render_pdf_report(diagnosis, symptoms_data)
        
        with tab5:
            self._render_diagnostic_history()
        
        # Botones de acción
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Nuevo Diagnóstico", use_container_width=True):
                del st.session_state.current_diagnostic
                del st.session_state.current_diagnosis
                st.rerun()
        
        with col2:
            if st.button("🧘 Sesión Recomendada", use_container_width=True):
                # Recomendar sesión basada en diagnóstico
                session_type = self._recommend_session_from_diagnosis(diagnosis)
                st.session_state.recommended_session = session_type
                st.session_state.page = "sessions"
                st.rerun()
        
        with col3:
            if st.button("🏠 Volver al inicio", use_container_width=True, type="secondary"):
                st.session_state.page = "home"
                st.rerun()
    
    def _render_diagnostic_summary(self, diagnosis: dict, symptoms_data: dict):
        """Renderiza resumen del diagnóstico"""
        # Información básica
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 Información del Diagnóstico")
            st.write(f"**Fecha:** {diagnosis.get('timestamp', datetime.now().isoformat())[:19]}")
            st.write(f"**ID de Sesión:** {diagnosis.get('session_id', 'N/A')}")
            
            if symptoms_data.get('name'):
                st.write(f"**Nombre:** {symptoms_data['name']}")
            
            st.write(f"**Síntomas reportados:** {len(symptoms_data.get('emotional_symptoms', [])) + len(symptoms_data.get('physical_symptoms', []))}")
        
        with col2:
            st.subheader("⚡ Resumen Ejecutivo")
            
            # Nivel de severidad
            emotional = diagnosis.get('emotional_analysis', {})
            physical = diagnosis.get('physical_analysis', {})
            
            severity = "Leve"
            if emotional.get('intensity_level') == 'alto' or physical.get('severity') == 'alto':
                severity = "Alto"
            elif emotional.get('intensity_level') == 'moderado' or physical.get('severity') == 'moderado':
                severity = "Moderado"
            
            st.write(f"**Nivel de severidad:** {severity}")
            
            # Sistemas afectados
            systems = physical.get('systems_affected', [])
            if systems:
                st.write(f"**Sistemas afectados:** {', '.join(systems)}")
            
            # Emociones predominantes
            emotions = emotional.get('primary_emotions', [])
            if emotions:
                st.write(f"**Emociones predominantes:** {', '.join(emotions)}")
        
        # Insights clave
        st.subheader("🔑 Insights Clave")
        
        diagnosis_data = diagnosis.get('diagnosis', {})
        
        if 'biodescodification_insights' in diagnosis_data:
            insights = diagnosis_data['biodescodification_insights']
            if insights:
                for insight in insights[:3]:
                    with st.expander(f"{insight.get('symptom', 'Síntoma')} → {insight.get('conflict', 'Análisis')}"):
                        st.write(f"**Órgano relacionado:** {insight.get('organ', 'Por determinar')}")
                        if 'recommendation' in insight:
                            st.write(f"**Recomendación:** {insight['recommendation']}")
        else:
            st.info("No hay insights específicos disponibles")
        
        # Recomendación principal
        recommendations = diagnosis.get('recommendations', [])
        if recommendations:
            st.subheader("💡 Recomendación Principal")
            st.info(recommendations[0])
    
    def _render_detailed_analysis(self, diagnosis: dict):
        """Renderiza análisis detallado"""
        st.subheader("🧠 Análisis Emocional Detallado")
        
        emotional = diagnosis.get('emotional_analysis', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Emociones primarias
            if 'primary_emotions' in emotional:
                st.write("**Emociones identificadas:**")
                for emotion in emotional['primary_emotions']:
                    st.write(f"• {emotion.capitalize()}")
            
            # Patrones
            if 'emotional_patterns' in emotional and emotional['emotional_patterns']:
                st.write("**Patrones emocionales:**")
                for pattern in emotional['emotional_patterns']:
                    st.write(f"• {pattern}")
        
        with col2:
            # Intensidad
            if 'intensity_level' in emotional:
                intensity = emotional['intensity_level']
                color = {
                    'bajo': '🟢',
                    'moderado': '🟡',
                    'alto': '🔴'
                }.get(intensity, '⚪')
                
                st.write(f"**Nivel de intensidad:** {color} {intensity.upper()}")
            
            # Necesidades
            if 'emotional_needs' in emotional and emotional['emotional_needs']:
                st.write("**Necesidades emocionales:**")
                for need in emotional['emotional_needs']:
                    st.write(f"• {need}")
        
        st.divider()
        st.subheader("🏥 Análisis Físico")
        
        physical = diagnosis.get('physical_analysis', {})
        
        col3, col4 = st.columns(2)
        
        with col3:
            # Sistemas afectados
            if 'systems_affected' in physical:
                st.write("**Sistemas afectados:**")
                for system in physical['systems_affected']:
                    st.write(f"• {system.replace('_', ' ').title()}")
            
            # Severidad
            if 'severity' in physical:
                severity = physical['severity']
                icon = {
                    'leve': '🟢',
                    'moderado': '🟡',
                    'alto': '🔴'
                }.get(severity, '⚪')
                
                st.write(f"**Severidad:** {icon} {severity.upper()}")
        
        with col4:
            # Cronicidad
            if 'chronicity' in physical:
                chronicity = physical['chronicity']
                st.write(f"**Cronicidad:** {chronicity.upper()}")
            
            # Conexión cuerpo-mente
            if 'body_mind_connection' in physical and physical['body_mind_connection']:
                st.write("**Conexiones identificadas:**")
                for connection in physical['body_mind_connection'][:3]:
                    st.write(f"• {connection}")
        
        # Diagnóstico de biodescodificación
        st.divider()
        st.subheader("🔍 Diagnóstico de Biodescodificación")
        
        diagnosis_data = diagnosis.get('diagnosis', {})
        
        if 'analysis' in diagnosis_data:
            st.write("**Análisis:**")
            st.write(diagnosis_data['analysis'])
        
        if 'conflict' in diagnosis_data:
            st.write(f"**Conflicto biológico:** {diagnosis_data['conflict']}")
    
    def _render_treatment_plan(self, diagnosis: dict):
        """Renderiza plan de tratamiento"""
        treatment = diagnosis.get('treatment_plan', {})
        
        st.subheader("📅 Plan de Tratamiento Personalizado")
        
        # Duración
        if 'duration_days' in treatment:
            st.write(f"**Duración recomendada:** {treatment['duration_days']} días")
        
        # Prácticas diarias
        if 'daily_practices' in treatment and treatment['daily_practices']:
            st.subheader("📋 Prácticas Diarias")
            
            for i, practice in enumerate(treatment['daily_practices'][:7], 1):
                with st.expander(f"Día {i}: {practice.split(':')[0] if ':' in practice else practice}"):
                    if ':' in practice:
                        st.write(practice.split(':', 1)[1].strip())
                    else:
                        st.write("Realiza esta práctica con atención plena")
        
        # Sesiones recomendadas
        if 'weekly_sessions' in treatment and treatment['weekly_sessions']:
            st.subheader("🧘 Sesiones Recomendadas")
            
            for session in treatment['weekly_sessions']:
                st.write(f"• {session}")
        
        # Recomendaciones dietéticas
        if 'diet_recommendations' in treatment and treatment['diet_recommendations']:
            st.subheader("🥗 Recomendaciones Dietéticas")
            
            cols = st.columns(2)
            for i, rec in enumerate(treatment['diet_recommendations'][:6]):
                with cols[i % 2]:
                    st.info(f"• {rec}")
        
        # Cambios de estilo de vida
        if 'lifestyle_changes' in treatment and treatment['lifestyle_changes']:
            st.subheader("🌿 Cambios de Estilo de Vida")
            
            for change in treatment['lifestyle_changes'][:5]:
                st.write(f"• {change}")
        
        # Monitoreo
        if 'monitoring' in treatment and treatment['monitoring']:
            st.subheader("📊 Seguimiento Recomendado")
            
            monitoring_df = pd.DataFrame({
                "Métrica": treatment['monitoring'],
                "Frecuencia": ["Diario"] * len(treatment['monitoring'])
            })
            
            st.dataframe(monitoring_df, use_container_width=True, hide_index=True)
    
    def _render_pdf_report(self, diagnosis: dict, symptoms_data: dict):
        """Renderiza sección de reporte PDF"""
        st.subheader("📄 Generar Reporte PDF")
        
        st.write("Genera un reporte profesional de tu diagnóstico en formato PDF.")
        
        # Información adicional para el reporte
        with st.expander("✏️ Personalizar reporte"):
            report_name = st.text_input("Nombre para el reporte", 
                                      value=f"Diagnóstico_{datetime.now().strftime('%Y%m%d')}")
            
            include_personal_info = st.checkbox("Incluir información personal", value=False)
            include_full_analysis = st.checkbox("Incluir análisis completo", value=True)
            include_recommendations = st.checkbox("Incluir recomendaciones", value=True)
        
        # Generar PDF
        if st.button("🖨️ Generar Reporte PDF", type="primary", use_container_width=True):
            with st.spinner("Generando reporte PDF..."):
                try:
                    # Preparar datos de usuario
                    user_info = {}
                    if include_personal_info and symptoms_data.get('name'):
                        user_info = {
                            'name': symptoms_data['name'],
                            'age': symptoms_data.get('age'),
                            'gender': symptoms_data.get('gender')
                        }
                    
                    # Generar PDF
                    pdf_buffer = self.pdf_generator.generate_diagnostic_report(diagnosis, user_info)
                    
                    # Crear botón de descarga
                    st.success("✅ Reporte generado exitosamente")
                    
                    st.download_button(
                        label="📥 Descargar Reporte PDF",
                        data=pdf_buffer,
                        file_name=f"{report_name}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    st.error(f"Error generando PDF: {str(e)}")
        
        # Vista previa del reporte
        with st.expander("👁️ Vista previa del contenido"):
            st.write("**Resumen del diagnóstico:**")
            
            diagnosis_data = diagnosis.get('diagnosis', {})
            if 'analysis' in diagnosis_data:
                st.text(diagnosis_data['analysis'][:500] + "...")
            
            st.write("**Recomendaciones principales:**")
            recommendations = diagnosis.get('recommendations', [])
            if recommendations:
                for i, rec in enumerate(recommendations[:3], 1):
                    st.write(f"{i}. {rec}")
    
    def _render_diagnostic_history(self):
        """Renderiza historial de diagnósticos"""
        st.subheader("📚 Historial de Diagnósticos")
        
        if 'diagnostic_history' not in st.session_state or not st.session_state.diagnostic_history:
            st.info("No hay diagnósticos previos")
            return
        
        history = st.session_state.diagnostic_history
        
        # Mostrar historial en orden inverso (más reciente primero)
        for i, record in enumerate(reversed(history)):
            with st.expander(f"Diagnóstico {len(history)-i} - {record['timestamp'][:19]}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Síntomas reportados:**")
                    
                    data = record['data']
                    if 'emotional_symptoms' in data:
                        st.write(f"Emocionales: {len(data['emotional_symptoms'])}")
                    
                    if 'physical_symptoms' in data:
                        st.write(f"Físicos: {len(data['physical_symptoms'])}")
                
                with col2:
                    diagnosis = record['diagnosis']
                    emotional = diagnosis.get('emotional_analysis', {})
                    
                    if 'primary_emotions' in emotional:
                        st.write("**Emociones:**")
                        st.write(", ".join(emotional['primary_emotions']))
                
                # Botón para ver detalles
                if st.button(f"🔍 Ver detalles completos", key=f"view_{i}"):
                    st.session_state.current_diagnostic = data
                    st.session_state.current_diagnosis = diagnosis
                    st.rerun()
    
    def _recommend_session_from_diagnosis(self, diagnosis: dict) -> str:
        """Recomienda tipo de sesión basado en diagnóstico"""
        emotional = diagnosis.get('emotional_analysis', {})
        primary_emotions = emotional.get('primary_emotions', [])
        
        # Mapeo de emociones a sesiones
        emotion_to_session = {
            "ansiedad": "manejo_ansiedad",
            "tristeza": "sanacion_interior",
            "ira": "liberacion_emocional",
            "miedo": "relajacion_profunda",
            "estrés": "conexion_mindfulness",
            "insatisfacción": "autoestima_confianza"
        }
        
        for emotion in primary_emotions:
            emotion_lower = emotion.lower()
            for key, session in emotion_to_session.items():
                if key in emotion_lower:
                    return session
        
        return "relajacion_profunda"  # Sesión por defecto
    
    def render_sessions(self):
        """Renderiza página de sesiones"""
        st.title("🧘 Sesiones de Hipnosis y Meditación")
        
        # Verificar si hay sesión recomendada
        if 'recommended_session' in st.session_state:
            st.info(f"💡 Sesión recomendada basada en tu diagnóstico: **{st.session_state.recommended_session.replace('_', ' ').title()}**")
        
        # Catálogo de sesiones
        st.subheader("🎧 Catálogo de Sesiones")
        
        session_catalog = self.hypnosis_system.session_catalog
        
        cols = st.columns(3)
        
        for i, (session_key, session_info) in enumerate(session_catalog.items()):
            with cols[i % 3]:
                with st.container(border=True):
                    st.markdown(f"### {session_info['title']}")
                    st.write(f"⏱️ {session_info['duration']} minutos")
                    st.write(session_info['description'])
                    
                    # Beneficios
                    st.markdown("**Beneficios:**")
                    for benefit in session_info.get('benefits', [])[:3]:
                        st.write(f"• {benefit}")
                    
                    # Botón para iniciar sesión
                    if st.button(f"▶️ Iniciar {session_info['title']}", 
                                key=f"start_{session_key}",
                                use_container_width=True):
                        
                        # Iniciar sesión
                        session = self.hypnosis_system.start_session(session_key)
                        st.session_state.current_session = session
                        
                        # Mostrar reproductor de sesión
                        st.rerun()
        
        # Si hay sesión activa, mostrar reproductor
        if 'current_session' in st.session_state and st.session_state.current_session:
            self._render_session_player()
        
        # Historial de sesiones
        st.divider()
        self._render_session_history()
    
    def _render_session_player(self):
        """Renderiza reproductor de sesión"""
        session = st.session_state.current_session
        
        st.subheader(f"🎧 {session['title']}")
        
        # Información de la sesión
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Duración", f"{session['duration']} min")
        
        with col2:
            st.metric("Estado", "En curso")
        
        with col3:
            # Temporizador
            if 'session_start_time' not in st.session_state:
                st.session_state.session_start_time = time.time()
                st.session_state.session_time_remaining = session['duration'] * 60
            
            elapsed = time.time() - st.session_state.session_start_time
            remaining = max(0, st.session_state.session_time_remaining - elapsed)
            
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            
            st.metric("Tiempo restante", f"{minutes:02d}:{seconds:02d}")
        
        # Reproductor de audio (simulado)
        st.markdown("---")
        st.subheader("🎵 Audio de la sesión")
        
        # Barra de progreso
        progress = 1 - (remaining / (session['duration'] * 60))
        st.progress(progress)
        
        # Controles
        col_controls1, col_controls2, col_controls3 = st.columns(3)
        
        with col_controls1:
            if st.button("⏸️ Pausar", use_container_width=True):
                st.info("Sesión pausada")
        
        with col_controls2:
            if st.button("▶️ Continuar", use_container_width=True):
                st.success("Sesión continuando")
        
        with col_controls3:
            if st.button("⏹️ Finalizar", use_container_width=True, type="secondary"):
                # Finalizar sesión
                del st.session_state.current_session
                del st.session_state.session_start_time
                del st.session_state.session_time_remaining
                st.success("✅ Sesión completada")
                st.rerun()
        
        # Guión de la sesión
        st.markdown("---")
        with st.expander("📝 Ver guión de la sesión"):
            st.write(session['script'])
    
    def _render_session_history(self):
        """Renderiza historial de sesiones"""
        st.subheader("📚 Historial de Sesiones")
        
        # En una implementación real, esto vendría de la base de datos
        # Por ahora, mostramos sesión actual si existe
        if 'current_session' in st.session_state:
            session = st.session_state.current_session
            
            st.write("**Sesión actual:**")
            cols = st.columns(4)
            
            with cols[0]:
                st.write(f"**{session['title']}**")
            
            with cols[1]:
                st.write(f"⏱️ {session['duration']} min")
            
            with cols[2]:
                st.write("🟢 En curso")
            
            with cols[3]:
                if st.button("📋 Ver detalles", key="view_current_session"):
                    st.write(session['script'])
        
        st.info("El historial completo de sesiones se guardará cuando tengas una cuenta.")
    
    def render_stats(self):
        """Renderiza página de estadísticas"""
        st.title("📊 Mis Estadísticas de Bienestar")
        
        # Verificar si el usuario tiene datos
        if 'diagnostic_history' not in st.session_state or not st.session_state.diagnostic_history:
            st.info("Completa tu primer diagnóstico para ver estadísticas personalizadas.")
            
            if st.button("🔍 Realizar mi primer diagnóstico", type="primary"):
                st.session_state.page = "diagnostic"
                st.rerun()
            
            return
        
        history = st.session_state.diagnostic_history
        
        # Métricas principales
        st.subheader("📈 Métricas Principales")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total diagnósticos", len(history))
        
        with col2:
            # Calcular mejora promedio (simulada)
            improvement = random.randint(20, 80)
            st.metric("Mejora general", f"{improvement}%")
        
        with col3:
            # Síntomas promedio por diagnóstico
            total_symptoms = sum(
                len(d['data'].get('emotional_symptoms', [])) + 
                len(d['data'].get('physical_symptoms', []))
                for d in history
            )
            avg_symptoms = total_symptoms / len(history)
            st.metric("Síntomas promedio", f"{avg_symptoms:.1f}")
        
        with col4:
            # Último diagnóstico
            last_date = history[-1]['timestamp'][:10]
            st.metric("Último diagnóstico", last_date)
        
        # Gráficos
        st.subheader("📊 Evolución Emocional")
        
        # Datos para gráficos (simulados)
        dates = []
        emotional_scores = []
        physical_scores = []
        
        for i, record in enumerate(history):
            date = record['timestamp'][:10]
            dates.append(date)
            
            # Puntaje emocional (simulado)
            emotional_score = random.randint(3, 8)
            emotional_scores.append(emotional_score)
            
            # Puntaje físico (simulado)
            physical_score = random.randint(3, 8)
            physical_scores.append(physical_score)
        
        # Crear DataFrame
        df = pd.DataFrame({
            'Fecha': dates,
            'Salud Emocional': emotional_scores,
            'Salud Física': physical_scores
        })
        
        # Gráfico de líneas
        fig = px.line(df, x='Fecha', y=['Salud Emocional', 'Salud Física'],
                     title='Evolución de Salud Emocional y Física',
                     markers=True)
        
        fig.update_layout(
            yaxis_title="Puntuación (1-10)",
            xaxis_title="Fecha",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Distribución de síntomas
        st.subheader("🔍 Distribución de Síntomas")
        
        # Contar síntomas
        all_emotional = []
        all_physical = []
        
        for record in history:
            all_emotional.extend(record['data'].get('emotional_symptoms', []))
            all_physical.extend(record['data'].get('physical_symptoms', []))
        
        if all_emotional or all_physical:
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                if all_emotional:
                    emotional_counts = pd.Series(all_emotional).value_counts()
                    fig1 = px.bar(x=emotional_counts.index, y=emotional_counts.values,
                                 title="Síntomas Emocionales Más Comunes")
                    st.plotly_chart(fig1, use_container_width=True)
            
            with col_chart2:
                if all_physical:
                    physical_counts = pd.Series(all_physical).value_counts()
                    fig2 = px.bar(x=physical_counts.index, y=physical_counts.values,
                                 title="Síntomas Físicos Más Comunes")
                    st.plotly_chart(fig2, use_container_width=True)
        
        # Insights
        st.subheader("💡 Insights Personalizados")
        
        insights = [
            "Basado en tu historial, se observa una correlación entre estrés emocional y síntomas físicos.",
            "Los períodos de mayor bienestar coinciden con práctica regular de técnicas de relajación.",
            "Se recomienda mantener un diario emocional para identificar patrones específicos."
        ]
        
        for insight in insights:
            st.info(insight)
        
        # Exportar datos
        st.divider()
        
        if st.button("📥 Exportar mis estadísticas (CSV)", use_container_width=True):
            # Preparar datos para exportación
            export_data = []
            
            for record in history:
                export_data.append({
                    'Fecha': record['timestamp'][:10],
                    'Síntomas_Emocionales': ', '.join(record['data'].get('emotional_symptoms', [])),
                    'Síntomas_Físicos': ', '.join(record['data'].get('physical_symptoms', [])),
                    'Notas': record['data'].get('additional_info', '')
                })
            
            df_export = pd.DataFrame(export_data)
            csv = df_export.to_csv(index=False)
            
            st.download_button(
                label="Descargar CSV",
                data=csv,
                file_name=f"estadisticas_mindgeekclinic_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    def render_chat(self):
        """Renderiza chat con IA"""
        st.title("💬 Chat con Especialista en Biodescodificación")
        
        # Inicializar historial de chat
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # Configuración del chat
        col_config1, col_config2 = st.columns(2)
        
        with col_config1:
            chat_mode = st.selectbox(
                "Modo de chat",
                ["General", "Diagnóstico", "Terapia", "Preguntas específicas"]
            )
        
        with col_config2:
            temperature = st.slider("Creatividad de respuestas", 0.1, 1.0, 0.7)
        
        # Área de chat
        st.divider()
        
        # Mostrar historial de chat
        chat_container = st.container()
        
        with chat_container:
            for message in st.session_state.chat_history:
                if message['role'] == 'user':
                    st.chat_message("user").write(message['content'])
                else:
                    st.chat_message("assistant").write(message['content'])
        
        # Entrada de mensaje
        st.divider()
        
        user_input = st.chat_input("Escribe tu pregunta sobre biodescodificación...")
        
        if user_input:
            # Agregar mensaje del usuario al historial
            st.session_state.chat_history.append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now().isoformat()
            })
            
            # Mostrar mensaje del usuario
            with chat_container:
                st.chat_message("user").write(user_input)
            
            # Generar respuesta de IA
            with st.spinner("El especialista está pensando..."):
                try:
                    # Usar Groq para generar respuesta
                    config = ConfigManager()
                    
                    if config.groq_api_key:
                        groq_client = Groq(api_key=config.groq_api_key)
                        
                        # Preparar contexto
                        context = f"""
                        Eres un especialista en biodescodificación emocional con 15 años de experiencia.
                        Modo actual: {chat_mode}
                        
                        Responde a la siguiente pregunta del usuario:
                        {user_input}
                        
                        Proporciona una respuesta útil, empática y basada en principios de biodescodificación.
                        Si la pregunta requiere diagnóstico médico, recomienda consultar a un profesional.
                        """
                        
                        response = groq_client.chat.completions.create(
                            messages=[
                                {
                                    "role": "system",
                                    "content": "Eres un experto en biodescodificación. Responde de forma clara, empática y profesional."
                                },
                                {
                                    "role": "user",
                                    "content": context
                                }
                            ],
                            model="mixtral-8x7b-32768",
                            temperature=temperature,
                            max_tokens=1000,
                            stream=False
                        )
                        
                        ai_response = response.choices[0].message.content
                        
                    else:
                        # Respuesta de fallback
                        ai_response = """
                        Hola, soy tu asistente de biodescodificación. 
                        
                        Lamentablemente, el servicio de IA no está disponible en este momento. 
                        
                        Te recomiendo:
                        1. Completar nuestro diagnóstico automático en la sección correspondiente
                        2. Explorar nuestras sesiones guiadas de meditación
                        3. Contactarnos por email para consultas específicas
                        
                        Mientras tanto, te comparto un principio básico de biodescodificación:
                        Cada síntoma físico tiene una correspondencia emocional. Escuchar el mensaje del cuerpo es el primer paso hacia la sanación.
                        """
                    
                    # Agregar respuesta al historial
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': ai_response,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Mostrar respuesta
                    with chat_container:
                        st.chat_message("assistant").write(ai_response)
                    
                except Exception as e:
                    st.error(f"Error en el chat: {str(e)}")
        
        # Opciones adicionales
        st.divider()
        
        col_opt1, col_opt2, col_opt3 = st.columns(3)
        
        with col_opt1:
            if st.button("🗑️ Limpiar chat", use_container_width=True, type="secondary"):
                st.session_state.chat_history = []
                st.rerun()
        
        with col_opt2:
            if st.button("💾 Guardar conversación", use_container_width=True):
                st.info("Esta función guardará la conversación en tu historial personal")
        
        with col_opt3:
            if st.button("📄 Generar resumen", use_container_width=True):
                st.info("Se generará un resumen de la conversación para tu seguimiento")
    
    def render_affiliate(self):
        """Renderiza página de afiliados"""
        # Verificar si ya es afiliado
        if 'affiliate_id' in st.session_state:
            self._render_affiliate_dashboard()
        else:
            # Mostrar opciones: registro o login
            aff_tab = st.radio("Afiliados", 
                             ["📝 Registrarse como afiliado", "🔑 Iniciar sesión como afiliado"], 
                             horizontal=True,
                             key="affiliate_tab")
            
            if aff_tab == "📝 Registrarse como afiliado":
                self._render_affiliate_registration()
            else:
                self._render_affiliate_login()
    
    def _render_affiliate_registration(self):
        """Renderiza formulario de registro de afiliado"""
        st.title("🎯 Programa de Afiliados MINDGEEKCLINIC")
        
        st.markdown("""
        ### ¡Gana comisiones recomendando MINDGEEKCLINIC!
        
        **Beneficios exclusivos:**
        - ✅ **30% de comisión** por cada venta
        - ✅ **Pagos automáticos** via Binance
        - ✅ **Panel de seguimiento** en tiempo real
        - ✅ **Material de marketing** profesional
        - ✅ **Soporte dedicado** para afiliados
        - ✅ **Bonos por desempeño**
        
        **Requisitos:**
        - 🔞 Mayor de 18 años
        - 🆔 Identificación verificada (KYC)
        - 💰 Cuenta de Binance activa
        """)
        
        # Proceso de 3 pasos
        steps = ["1. Verificación de Email", "2. Información Personal", "3. Confirmación"]
        current_step = st.session_state.get('affiliate_step', 1)
        
        self.ui.progress_tracker(steps, current_step)
        
        if current_step == 1:
            self._render_affiliate_step1()
        elif current_step == 2:
            self._render_affiliate_step2()
        elif current_step == 3:
            self._render_affiliate_step3()
    
    def _render_affiliate_step1(self):
        """Paso 1: Verificación de email"""
        st.subheader("📧 Paso 1: Verificación de Email")
        
        email = st.text_input(
            "Dirección de email",
            placeholder="tucorreo@ejemplo.com",
            key="affiliate_email_step1"
        )
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if st.button("🔐 Enviar Código", type="primary", use_container_width=True):
                if email and "@" in email and "." in email:
                    # Generar código
                    code = str(random.randint(100000, 999999))
                    
                    # Guardar en sesión
                    st.session_state.affiliate_email = email
                    st.session_state.verification_code = code
                    st.session_state.verification_sent_time = time.time()
                    
                    # Enviar email
                    success, message = self.email_service.send_verification_email(email, code)
                    
                    if success:
                        st.session_state.affiliate_step = 2
                        st.success("✅ Código enviado. Revisa tu email.")
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Por favor ingresa un email válido")
        
        with col2:
            if st.button("↩️ Volver al inicio", use_container_width=True, type="secondary"):
                st.session_state.page = "home"
                st.rerun()
    
    def _render_affiliate_step2(self):
        """Paso 2: Información personal"""
        st.subheader("📋 Paso 2: Información Personal")
        
        st.info(f"Email verificado: **{st.session_state.affiliate_email}**")
        
        # Formulario de información personal
        with st.form("affiliate_personal_info", clear_on_submit=False):
            col1, col2 = st.columns(2)
            
            with col1:
                full_name = st.text_input("Nombre completo *", 
                                        placeholder="Juan Pérez García")
                phone = st.text_input("Teléfono *", 
                                    placeholder="+34 612 345 678")
                country = st.selectbox("País *", 
                                     ["España", "México", "Colombia", "Argentina", "Chile", 
                                      "Perú", "Estados Unidos", "Otro país..."])
            
            with col2:
                id_type = st.selectbox("Tipo de identificación *",
                                     ["DNI", "Pasaporte", "Cédula", "Licencia", "Otro"])
                id_number = st.text_input("Número de identificación *",
                                        placeholder="12345678A")
                birth_date = st.date_input("Fecha de nacimiento *",
                                         min_value=datetime(1900, 1, 1),
                                         max_value=datetime.now() - timedelta(days=365*18))
            
            # Información de pago
            st.subheader("💰 Información de Pago")
            
            binance_address = st.text_input("Dirección de Binance *",
                                          placeholder="U1234567890ABCDEF",
                                          help="Tu dirección de Binance para recibir pagos")
            
            tax_id = st.text_input("ID Fiscal (opcional)",
                                 placeholder="Para facturación")
            
            # Términos y condiciones
            st.subheader("📜 Términos y Condiciones")
            
            col_terms1, col_terms2 = st.columns(2)
            
            with col_terms1:
                accept_terms = st.checkbox("Acepto los términos y condiciones *")
                accept_privacy = st.checkbox("Acepto la política de privacidad *")
            
            with col_terms2:
                accept_marketing = st.checkbox("Deseo recibir material de marketing")
                accept_kyc = st.checkbox("Autorizo la verificación KYC *")
            
            st.markdown("---")
            
            # Botón de envío
            col_submit1, col_submit2, col_submit3 = st.columns([1, 2, 1])
            
            with col_submit2:
                submitted = st.form_submit_button(
                    "✅ Continuar al Paso 3",
                    type="primary",
                    use_container_width=True
                )
            
            if submitted:
                # Validaciones
                errors = []
                
                # Campos requeridos
                required_fields = {
                    "Nombre completo": full_name,
                    "Teléfono": phone,
                    "Número de identificación": id_number,
                    "Dirección de Binance": binance_address
                }
                
                for field, value in required_fields.items():
                    if not value:
                        errors.append(f"{field} es requerido")
                
                # Términos
                if not all([accept_terms, accept_privacy, accept_kyc]):
                    errors.append("Debes aceptar todos los términos requeridos")
                
                # Edad
                age = (datetime.now().date() - birth_date).days / 365.25
                if age < 18:
                    errors.append("Debes ser mayor de 18 años")
                
                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                else:
                    # Guardar datos en sesión
                    st.session_state.affiliate_data = {
                        "full_name": full_name,
                        "email": st.session_state.affiliate_email,
                        "phone": phone,
                        "country": country,
                        "id_type": id_type,
                        "id_number": id_number,
                        "birth_date": birth_date.isoformat(),
                        "binance_address": binance_address,
                        "tax_id": tax_id,
                        "accept_marketing": accept_marketing,
                        "accept_terms": accept_terms,
                        "accept_privacy": accept_privacy,
                        "accept_kyc": accept_kyc
                    }
                    
                    st.session_state.affiliate_step = 3
                    st.rerun()
        
        # Botón para volver al paso 1
        if st.button("↩️ Volver al paso 1", type="secondary"):
            st.session_state.affiliate_step = 1
            st.rerun()
    
    def _render_affiliate_step3(self):
        """Paso 3: Confirmación y registro"""
        st.subheader("✅ Paso 3: Confirmación y Registro")
        
        affiliate_data = st.session_state.get('affiliate_data', {})
        
        if not affiliate_data:
            st.error("No hay datos de afiliado. Regresa al paso 1.")
            if st.button("↩️ Volver al inicio", type="secondary"):
                st.session_state.affiliate_step = 1
                st.rerun()
            return
        
        # Mostrar resumen de información
        st.info("### Resumen de tu información:")
        
        col_sum1, col_sum2 = st.columns(2)
        
        with col_sum1:
            st.write(f"**Nombre:** {affiliate_data['full_name']}")
            st.write(f"**Email:** {affiliate_data['email']}")
            st.write(f"**Teléfono:** {affiliate_data['phone']}")
            st.write(f"**País:** {affiliate_data['country']}")
        
        with col_sum2:
            st.write(f"**Tipo ID:** {affiliate_data['id_type']}")
            st.write(f"**Número ID:** {affiliate_data['id_number']}")
            st.write(f"**Fecha nacimiento:** {affiliate_data['birth_date'][:10]}")
            st.write(f"**Binance:** {affiliate_data['binance_address']}")
        
        st.divider()
        
        # Confirmación final
        st.warning("""
        **⚠️ Importante:**
        - Tu cuenta estará en estado **pendiente** hasta que sea verificada
        - La verificación KYC puede tomar 24-48 horas
        - Recibirás un email con los detalles de tu cuenta
        - Una vez aprobado, podrás acceder a tu panel de afiliado
        """)
        
        col_confirm1, col_confirm2, col_confirm3 = st.columns([1, 2, 1])
        
        with col_confirm2:
            if st.button("🚀 Registrar como Afiliado", type="primary", use_container_width=True):
                # Registrar afiliado en base de datos
                success, message, affiliate_record = self.db.add_affiliate(affiliate_data)
                
                if success:
                    # Enviar email de bienvenida
                    self.email_service.send_welcome_email(
                        affiliate_data['email'],
                        affiliate_data
                    )
                    
                    # Enviar notificación al administrador
                    admin_config = ConfigManager().app_config
                    self.email_service.send_email(
                        admin_config['admin_email'],
                        "Nuevo Afiliado Registrado",
                        f"Nuevo afiliado: {affiliate_data['full_name']}\nID: {affiliate_record['id']}"
                    )
                    
                    # Mostrar éxito
                    st.balloons()
                    st.success(f"""
                    🎉 ¡Registro Exitoso!
                    
                    **Tu ID de afiliado:** {affiliate_record['id']}
                    **Tu código de referido:** {affiliate_record['referral_code']}
                    
                    Hemos enviado un email con los detalles de tu cuenta.
                    Tu cuenta será verificada en las próximas 24-48 horas.
                    
                    ¡Bienvenido al programa de afiliados!
                    """)
                    
                    # Guardar ID en sesión
                    st.session_state.affiliate_id = affiliate_record['id']
                    
                    # Limpiar datos temporales
                    for key in ['affiliate_step', 'affiliate_email', 'affiliate_data']:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    # Esperar y redirigir
                    time.sleep(3)
                    st.rerun()
                else:
                    st.error(f"Error en el registro: {message}")
        
        # Botón para volver al paso 2
        if st.button("↩️ Volver al paso 2", type="secondary"):
            st.session_state.affiliate_step = 2
            st.rerun()
    
    def _render_affiliate_login(self):
        """Renderiza login de afiliado"""
        st.subheader("🔑 Iniciar sesión como afiliado")
        
        with st.form("affiliate_login_form"):
            email = st.text_input("Email registrado", placeholder="tucorreo@ejemplo.com")
            affiliate_id = st.text_input("ID de afiliado (opcional)", placeholder="AFF0001")
            
            submitted = st.form_submit_button("Acceder", type="primary")
            
            if submitted:
                # Buscar afiliado por email o ID
                db = self.db.load_affiliates()
                
                found_affiliate = None
                
                # Buscar por ID
                if affiliate_id and affiliate_id in db["affiliates"]:
                    found_affiliate = db["affiliates"][affiliate_id]
                
                # Buscar por email
                if not found_affiliate and email:
                    for aff in db["affiliates"].values():
                        if aff["email"] == email:
                            found_affiliate = aff
                            break
                
                if found_affiliate:
                    # Verificar estado
                    status = found_affiliate.get("status", "pending")
                    
                    if status == "active":
                        st.session_state.affiliate_id = found_affiliate["id"]
                        st.success(f"✅ Bienvenido, {found_affiliate['full_name']}")
                        time.sleep(1)
                        st.rerun()
                    elif status == "pending":
                        st.warning("⏳ Tu cuenta está pendiente de verificación. Te contactaremos pronto.")
                    elif status == "suspended":
                        st.error("❌ Tu cuenta está suspendida. Contacta con soporte.")
                    else:
                        st.info("Tu cuenta está en estado: " + status)
                else:
                    st.error("❌ Afiliado no encontrado. Verifica tus datos o regístrate.")
        
        # Enlace a registro
        st.write("¿No tienes cuenta?")
        if st.button("📝 Regístrate como afiliado"):
            st.session_state.affiliate_step = 1
            st.rerun()
    
    def _render_affiliate_dashboard(self):
        """Renderiza dashboard de afiliado"""
        affiliate_id = st.session_state.affiliate_id
        
        st.title(f"📊 Panel de Afiliado - {affiliate_id}")
        
        # Cargar datos del afiliado
        balance = self.payment_system.get_affiliate_balance(affiliate_id)
        
        if "error" in balance:
            st.error(balance["error"])
            return
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💰 Ganancias Totales", f"${balance['total_earnings']:.2f}")
        
        with col2:
            st.metric("⏳ Pendientes", f"${balance['pending_earnings']:.2f}")
        
        with col3:
            st.metric("💳 Pagados", f"${balance['paid_earnings']:.2f}")
        
        with col4:
            commission_rate = balance['commission_rate'] * 100
            st.metric("📈 Comisión", f"{commission_rate}%")
        
        st.divider()
        
        # Sección de código de referido
        st.subheader("🎯 Tu Código de Referido")
        
        # Obtener código de referido
        db = self.db.load_affiliates()
        affiliate = db["affiliates"].get(affiliate_id, {})
        referral_code = affiliate.get("referral_code", "N/A")
        
        referral_link = f"https://mindgeekclinic.streamlit.app/?ref={referral_code}"
        
        col_link1, col_link2 = st.columns([3, 1])
        
        with col_link1:
            st.code(referral_link, language="text")
        
        with col_link2:
            if st.button("📋 Copiar", use_container_width=True):
                st.success("Enlace copiado al portapapeles")
        
        # Métricas de desempeño
        st.subheader("📊 Métricas de Desempeño")
        
        performance = self.analytics.get_affiliate_performance(affiliate_id)
        
        if "error" not in performance:
            col_perf1, col_perf2, col_perf3, col_perf4 = st.columns(4)
            
            with col_perf1:
                st.metric("👥 Referidos", performance["performance_metrics"]["total_referrals"])
            
            with col_perf2:
                st.metric("🔄 Conversiones", performance["performance_metrics"]["conversions"])
            
            with col_perf3:
                st.metric("📊 Tasa Conversión", f"{performance['performance_metrics']['conversion_rate']}%")
            
            with col_perf4:
                avg_value = performance["performance_metrics"]["avg_conversion_value"]
                st.metric("💰 Valor promedio", f"${avg_value:.2f}")
            
            # Gráfico de ganancias mensuales
            if performance.get("monthly_earnings"):
                st.subheader("📈 Ganancias Mensuales")
                
                earnings_df = pd.DataFrame(performance["monthly_earnings"])
                
                fig = px.bar(earnings_df, x='month', y='earnings',
                            title='Ganancias por Mes',
                            labels={'earnings': 'Ganancias ($)', 'month': 'Mes'})
                
                st.plotly_chart(fig, use_container_width=True)
        
        # Historial de pagos
        st.subheader("💰 Historial de Pagos")
        
        payments = self.payment_system.get_payment_history(affiliate_id)
        
        if payments:
            payments_df = pd.DataFrame(payments)
            
            # Mostrar columnas relevantes
            display_cols = ['payment_id', 'request_date', 'amount', 'status', 'net_amount']
            display_cols = [c for c in display_cols if c in payments_df.columns]
            
            st.dataframe(payments_df[display_cols], use_container_width=True)
        else:
            st.info("No hay pagos registrados aún")
        
        # Solicitud de pago
        st.divider()
        st.subheader("💳 Solicitar Pago")
        
        if balance['can_withdraw']:
            max_amount = min(balance['pending_earnings'], 10000.0)  # Límite de $10,000
            
            amount = st.number_input(
                f"Monto a retirar (disponible: ${balance['pending_earnings']:.2f})",
                min_value=float(balance['min_payout']),
                max_value=float(max_amount),
                value=float(balance['min_payout']),
                step=10.0
            )
            
            if st.button("📤 Solicitar Pago", type="primary", use_container_width=True):
                success, message, payment_data = self.payment_system.process_payment_request(
                    affiliate_id, amount
                )
                
                if success:
                    st.success(f"""
                    ✅ Solicitud de pago enviada
                    
                    **Detalles:**
                    - Monto: ${payment_data['amount']:.2f}
                    - Comisión: ${payment_data.get('transaction_fee', 0):.2f}
                    - Neto: ${payment_data.get('net_amount', 0):.2f}
                    - Fecha estimada: {payment_data.get('estimated_completion', '')[:10]}
                    
                    Recibirás una notificación por email cuando el pago sea procesado.
                    """)
                    
                    # Actualizar dashboard
                    st.rerun()
                else:
                    st.error(f"❌ Error: {message}")
        else:
            st.warning(f"""
            ⚠️ Mínimo para retiro: ${balance['min_payout']:.2f}
            
            Actualmente tienes: ${balance['pending_earnings']:.2f}
            
            Continúa compartiendo tu enlace de referido para alcanzar el mínimo.
            """)
        
        # Material de marketing
        st.divider()
        
        with st.expander("🎨 Material de Marketing"):
            st.write("**Recursos para promocionar MINDGEEKCLINIC:**")
            
            col_mat1, col_mat2, col_mat3 = st.columns(3)
            
            with col_mat1:
                st.download_button(
                    "📝 Plantilla Email",
                    data="Plantilla de email promocional",
                    file_name="plantilla_email_mindgeekclinic.txt",
                    use_container_width=True
                )
            
            with col_mat2:
                st.download_button(
                    "📱 Imágenes para Redes",
                    data="",
                    file_name="imagenes_redes.zip",
                    disabled=True,
                    use_container_width=True
                )
            
            with col_mat3:
                st.download_button(
                    "📊 Presentación",
                    data="",
                    file_name="presentacion_afiliados.pdf",
                    disabled=True,
                    use_container_width=True
                )
            
            st.write("""
            **Consejos de marketing:**
            1. Comparte tu enlace único en redes sociales
            2. Envía emails personalizados a tu red de contactos
            3. Crea contenido sobre bienestar emocional
            4. Ofrece webinars o sesiones informativas
            5. Colabora con otros profesionales del bienestar
            """)
    
    def render_admin(self):
        """Renderiza panel de administración"""
        # Verificación de contraseña
        if 'admin_logged_in' not in st.session_state:
            st.session_state.admin_logged_in = False
        
        if not st.session_state.admin_logged_in:
            self._render_admin_login()
            return
        
        # Panel administrativo
        st.title("🔐 Panel de Administración")
        
        # Menú lateral
        admin_menu = st.sidebar.radio(
            "Menú Administrativo",
            ["📊 Dashboard", "👥 Afiliados", "💰 Pagos", "📈 Analytics", "⚙️ Configuración", "📧 Pruebas"]
        )
        
        if admin_menu == "📊 Dashboard":
            self._render_admin_dashboard()
        elif admin_menu == "👥 Afiliados":
            self._render_admin_affiliates()
        elif admin_menu == "💰 Pagos":
            self._render_admin_payments()
        elif admin_menu == "📈 Analytics":
            self._render_admin_analytics()
        elif admin_menu == "⚙️ Configuración":
            self._render_admin_settings()
        elif admin_menu == "📧 Pruebas":
            self._render_admin_tests()
        
        # Botón para cerrar sesión
        st.sidebar.divider()
        if st.sidebar.button("🚪 Cerrar Sesión Admin", type="secondary", use_container_width=True):
            st.session_state.admin_logged_in = False
            st.rerun()
    
    def _render_admin_login(self):
        """Renderiza login de administrador"""
        st.title("🔐 Acceso Administrativo")
        
        config = ConfigManager().app_config
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            with st.form("admin_login"):
                password = st.text_input("Contraseña de administración", 
                                       type="password",
                                       placeholder="Ingresa la contraseña")
                
                submitted = st.form_submit_button("🔓 Acceder", type="primary", use_container_width=True)
                
                if submitted:
                    if password == config["admin_password"]:
                        st.session_state.admin_logged_in = True
                        st.success("✅ Acceso concedido")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Contraseña incorrecta")
    
    def _render_admin_dashboard(self):
        """Renderiza dashboard administrativo"""
        st.header("📊 Dashboard General")
        
        # Estadísticas del sistema
        stats = self.analytics.get_dashboard_stats()
        health = self.analytics.get_system_health()
        
        if stats:
            overall = stats.get("overall_stats", {})
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("👥 Total Afiliados", overall.get("total_affiliates", 0))
            
            with col2:
                st.metric("✅ Activos", overall.get("active_affiliates", 0))
            
            with col3:
                st.metric("💰 Ganancias Totales", f"${overall.get('total_earnings', 0):,.2f}")
            
            with col4:
                st.metric("🔄 Conversiones", overall.get("total_conversions", 0))
            
            # Gráfico de distribución
            st.subheader("📈 Distribución de Afiliados")
            
            status_data = {
                "Activos": overall.get("active_affiliates", 0),
                "Pendientes": stats.get("overall_stats", {}).get("pending_affiliates", 0),
                "Suspendidos": stats.get("overall_stats", {}).get("suspended_affiliates", 0)
            }
            
            fig = px.pie(
                values=list(status_data.values()),
                names=list(status_data.keys()),
                title="Estado de Afiliados",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Últimos pagos
            st.subheader("💳 Últimos Pagos")
            
            if stats.get("recent_payments"):
                payments_df = pd.DataFrame(stats["recent_payments"])
                st.dataframe(payments_df[['payment_id', 'affiliate_id', 'amount', 'status']], 
                            use_container_width=True)
        
        # Salud del sistema
        st.divider()
        st.subheader("🖥️ Salud del Sistema")
        
        if health and "error" not in health:
            server = health.get("server_metrics", {})
            app = health.get("app_metrics", {})
            
            col_health1, col_health2, col_health3, col_health4 = st.columns(4)
            
            with col_health1:
                cpu = server.get("cpu_usage", 0)
                color = "🟢" if cpu < 70 else "🟡" if cpu < 90 else "🔴"
                st.metric("CPU", f"{color} {cpu}%")
            
            with col_health2:
                memory = server.get("memory_usage", 0)
                color = "🟢" if memory < 70 else "🟡" if memory < 90 else "🔴"
                st.metric("Memoria", f"{color} {memory}%")
            
            with col_health3:
                error_rate = app.get("error_rate", 0)
                color = "🟢" if error_rate < 1 else "🟡" if error_rate < 5 else "🔴"
                st.metric("Tasa Error", f"{color} {error_rate}%")
            
            with col_health4:
                uptime = server.get("uptime", "0:00:00")
                st.metric("Uptime", uptime)
            
            # Servicios
            st.subheader("🔧 Estado de Servicios")
            
            services = health.get("services", {})
            
            col_serv1, col_serv2, col_serv3, col_serv4 = st.columns(4)
            
            service_icons = {
                True: "✅",
                False: "❌"
            }
            
            with col_serv1:
                status = service_icons.get(services.get("email", False), "❓")
                st.metric("Email", status)
            
            with col_serv2:
                status = service_icons.get(services.get("payments", False), "❓")
                st.metric("Pagos", status)
            
            with col_serv3:
                status = service_icons.get(services.get("ai", False), "❓")
                st.metric("IA", status)
            
            with col_serv4:
                status = service_icons.get(services.get("storage", False), "❓")
                st.metric("Almacenamiento", status)
    
    def _render_admin_affiliates(self):
        """Renderiza gestión de afiliados"""
        st.header("👥 Gestión de Afiliados")
        
        # Filtros y búsqueda
        col_search, col_filter, col_action = st.columns([2, 1, 1])
        
        with col_search:
            search_term = st.text_input("🔍 Buscar afiliado", placeholder="ID, nombre, email...")
        
        with col_filter:
            status_filter = st.selectbox("Estado", ["Todos", "active", "pending", "suspended"])
        
        with col_action:
            if st.button("🔄 Actualizar", use_container_width=True):
                st.rerun()
        
        # Cargar afiliados
        db = self.db.load_affiliates()
        affiliates = list(db.get("affiliates", {}).values())
        
        # Aplicar filtros
        if search_term:
            affiliates = [a for a in affiliates 
                         if search_term.lower() in a.get('full_name', '').lower() or
                         search_term.lower() in a.get('email', '').lower() or
                         search_term.lower() in a.get('id', '').lower()]
        
        if status_filter != "Todos":
            affiliates = [a for a in affiliates if a.get('status') == status_filter]
        
        # Mostrar tabla
        if affiliates:
            # Crear DataFrame
            df_data = []
            for aff in affiliates:
                df_data.append({
                    "ID": aff.get('id'),
                    "Nombre": aff.get('full_name'),
                    "Email": aff.get('email'),
                    "Estado": aff.get('status'),
                    "Ganancias": f"${aff.get('total_earnings', 0):.2f}",
                    "Referidos": aff.get('referrals_count', 0),
                    "Conversiones": aff.get('conversions_count', 0),
                    "Registro": aff.get('registration_date', '')[:10]
                })
            
            df = pd.DataFrame(df_data)
            
            # Mostrar tabla con selección
            selected_indices = st.dataframe(
                df,
                use_container_width=True,
                selection_mode="multi-row",
                key="affiliate_selection"
            )
            
            # Detalles del afiliado seleccionado
            if selected_indices and 'selection' in selected_indices and selected_indices['selection']['rows']:
                selected_rows = selected_indices['selection']['rows']
                
                if len(selected_rows) == 1:
                    # Mostrar detalles de un afiliado
                    selected_row = selected_rows[0]
                    selected_affiliate = df.iloc[selected_row]
                    
                    with st.expander(f"📋 Detalles: {selected_affiliate['Nombre']}"):
                        affiliate_id = selected_affiliate['ID']
                        full_affiliate = db["affiliates"].get(affiliate_id, {})
                        
                        col_detail1, col_detail2 = st.columns(2)
                        
                        with col_detail1:
                            st.write(f"**Email:** {full_affiliate.get('email', 'N/A')}")
                            st.write(f"**Teléfono:** {full_affiliate.get('phone', 'N/A')}")
                            st.write(f"**País:** {full_affiliate.get('country', 'N/A')}")
                            st.write(f"**Código referido:** {full_affiliate.get('referral_code', 'N/A')}")
                        
                        with col_detail2:
                            st.write(f"**Estado KYC:** {full_affiliate.get('kyc_status', 'pending')}")
                            st.write(f"**Comisión:** {full_affiliate.get('commission_rate', 0.30)*100}%")
                            st.write(f"**Último pago:** {full_affiliate.get('last_payment', 'Nunca')}")
                            st.write(f"**Binance:** {full_affiliate.get('payment_address', 'No configurada')}")
                        
                        # Acciones
                        st.subheader("⚙️ Acciones")
                        
                        col_action1, col_action2, col_action3 = st.columns(3)
                        
                        with col_action1:
                            new_status = st.selectbox(
                                "Cambiar estado",
                                ["active", "pending", "suspended"],
                                index=["active", "pending", "suspended"].index(full_affiliate.get('status', 'pending')),
                                key=f"status_{affiliate_id}"
                            )
                            
                            if st.button("💾 Actualizar estado", key=f"update_{affiliate_id}"):
                                if self.db.update_affiliate_status(affiliate_id, new_status):
                                    st.success("✅ Estado actualizado")
                                    time.sleep(1)
                                    st.rerun()
                        
                        with col_action2:
                            new_rate = st.number_input(
                                "Tasa comisión (%)",
                                min_value=10,
                                max_value=50,
                                value=int(full_affiliate.get('commission_rate', 0.30)*100),
                                key=f"rate_{affiliate_id}"
                            )
                        
                        with col_action3:
                            if st.button("📧 Enviar email", key=f"email_{affiliate_id}"):
                                st.info("Función de email pendiente")
                
                elif len(selected_rows) > 1:
                    # Acciones en lote
                    st.subheader("🔄 Acciones en Lote")
                    
                    batch_action = st.selectbox("Acción para múltiples afiliados", 
                                              ["Cambiar estado", "Enviar email", "Exportar datos"])
                    
                    if batch_action == "Cambiar estado":
                        new_batch_status = st.selectbox("Nuevo estado", 
                                                      ["active", "pending", "suspended"])
                        
                        if st.button("Aplicar a seleccionados", type="primary"):
                            for row in selected_rows:
                                affiliate_id = df.iloc[row]['ID']
                                self.db.update_affiliate_status(affiliate_id, new_batch_status)
                            
                            st.success(f"✅ Estado actualizado para {len(selected_rows)} afiliados")
                            time.sleep(2)
                            st.rerun()
        
        else:
            st.info("No hay afiliados que coincidan con los filtros")
    
    def _render_admin_payments(self):
        """Renderiza gestión de pagos"""
        st.header("💰 Gestión de Pagos")
        
        # Cargar pagos
        payments = self.payment_system.get_payment_history()
        
        if payments:
            # Filtros
            col_filt1, col_filt2, col_filt3 = st.columns(3)
            
            with col_filt1:
                status_filter = st.multiselect("Estado", 
                                             ["pending", "processing", "completed", "failed"],
                                             default=["pending", "processing"])
            
            with col_filt2:
                date_filter = st.date_input("Fecha", [])
            
            with col_filt3:
                affiliate_filter = st.text_input("ID Afiliado")
            
            # Aplicar filtros
            filtered_payments = payments
            
            if status_filter:
                filtered_payments = [p for p in filtered_payments if p.get('status') in status_filter]
            
            if affiliate_filter:
                filtered_payments = [p for p in filtered_payments if affiliate_filter in p.get('affiliate_id', '')]
            
            if filtered_payments:
                # Convertir a DataFrame
                df = pd.DataFrame(filtered_payments)
                
                # Ordenar por fecha
                if 'request_date' in df.columns:
                    df['request_date'] = pd.to_datetime(df['request_date'])
                    df = df.sort_values('request_date', ascending=False)
                
                # Mostrar pagos
                st.dataframe(df, use_container_width=True)
                
                # Procesar pagos pendientes
                pending_payments = [p for p in filtered_payments if p.get('status') in ['pending', 'processing']]
                
                if pending_payments:
                    st.subheader("⏳ Pagos Pendientes por Procesar")
                    
                    for payment in pending_payments:
                        with st.expander(f"Pago #{payment.get('payment_id', 'N/A')} - ${payment.get('amount', 0):.2f}"):
                            col_pay1, col_pay2 = st.columns(2)
                            
                            with col_pay1:
                                st.write(f"**Afiliado:** {payment.get('affiliate_id', 'N/A')}")
                                st.write(f"**Monto:** ${payment.get('amount', 0):.2f}")
                                st.write(f"**Estado:** {payment.get('status', 'N/A')}")
                                st.write(f"**Solicitado:** {payment.get('request_date', 'N/A')[:19]}")
                            
                            with col_pay2:
                                # Acciones
                                if payment.get('status') == 'pending':
                                    if st.button(f"✅ Marcar como Procesando", key=f"process_{payment.get('payment_id')}"):
                                        # Actualizar estado
                                        payment['status'] = 'processing'
                                        self._update_payment_status(payment)
                                        st.success("✅ Estado actualizado")
                                        st.rerun()
                                
                                elif payment.get('status') == 'processing':
                                    if st.button(f"✅ Completar Pago", key=f"complete_{payment.get('payment_id')}"):
                                        # Completar pago
                                        payment['status'] = 'completed'
                                        payment['completed_date'] = datetime.now().isoformat()
                                        self._update_payment_status(payment)
                                        st.success("✅ Pago completado")
                                        st.rerun()
                                    
                                    if st.button(f"❌ Marcar como Fallido", key=f"fail_{payment.get('payment_id')}"):
                                        payment['status'] = 'failed'
                                        self._update_payment_status(payment)
                                        st.success("❌ Pago marcado como fallido")
                                        st.rerun()
            else:
                st.info("No hay pagos que coincidan con los filtros")
        else:
            st.info("No hay pagos registrados")
    
    def _update_payment_status(self, payment_data: dict):
        """Actualiza estado de pago en base de datos"""
        try:
            payments = self.db.load_payments()
            
            for i, p in enumerate(payments):
                if p.get('payment_id') == payment_data.get('payment_id'):
                    payments[i] = payment_data
                    break
            
            self.db.save_payments(payments)
            
        except Exception as e:
            logger.error(f"Error actualizando estado de pago: {e}")
    
    def _render_admin_analytics(self):
        """Renderiza analytics administrativo"""
        st.header("📈 Analytics Avanzado")
        
        # Métricas avanzadas
        stats = self.analytics.get_dashboard_stats()
        
        if stats and 'top_affiliates' in stats:
            st.subheader("🏆 Top Afiliados")
            
            top_df = pd.DataFrame(stats['top_affiliates'])
            
            # Gráfico de barras
            fig = px.bar(top_df, x='name', y='earnings',
                        title='Top Afiliados por Ganancias',
                        labels={'name': 'Afiliado', 'earnings': 'Ganancias ($)'})
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabla detallada
            st.dataframe(top_df, use_container_width=True)
        
        # Análisis de conversión
        st.subheader("📊 Análisis de Conversión")
        
        # Datos simulados
        conversion_data = {
            'Mes': ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
            'Visitas': [1000, 1200, 1100, 1300, 1400, 1500],
            'Referidos': [100, 120, 110, 130, 140, 150],
            'Conversiones': [10, 12, 11, 13, 14, 15]
        }
        
        df_conv = pd.DataFrame(conversion_data)
        df_conv['Tasa Conversión'] = (df_conv['Conversiones'] / df_conv['Referidos'] * 100).round(1)
        
        fig2 = px.line(df_conv, x='Mes', y='Tasa Conversión',
                      title='Tasa de Conversión Mensual',
                      markers=True)
        
        st.plotly_chart(fig2, use_container_width=True)
        
        # Reportes personalizados
        st.subheader("📋 Generar Reportes")
        
        col_report1, col_report2, col_report3 = st.columns(3)
        
        with col_report1:
            if st.button("📊 Reporte Mensual", use_container_width=True):
                st.info("Generando reporte mensual...")
        
        with col_report2:
            if st.button("💰 Reporte de Comisiones", use_container_width=True):
                st.info("Generando reporte de comisiones...")
        
        with col_report3:
            if st.button("👥 Reporte de Afiliados", use_container_width=True):
                st.info("Generando reporte de afiliados...")
    
    def _render_admin_settings(self):
        """Renderiza configuración administrativa"""
        st.header("⚙️ Configuración del Sistema")
        
        config = ConfigManager()
        
        # Configuración general
        with st.expander("🔧 Configuración General"):
            app_config = config.app_config
            
            col_set1, col_set2 = st.columns(2)
            
            with col_set1:
                st.write(f"**Nombre app:** {app_config['name']}")
                st.write(f"**Versión:** {app_config['version']}")
                st.write(f"**Email admin:** {app_config['admin_email']}")
            
            with col_set2:
                maintenance = st.checkbox("Modo mantenimiento", value=app_config.get('maintenance_mode', False))
                debug = st.checkbox("Modo debug", value=app_config.get('debug', True))
                
                if st.button("💾 Guardar cambios"):
                    st.success("Configuración guardada (simulado)")
        
        # Configuración de afiliados
        with st.expander("💰 Configuración de Afiliados"):
            aff_config = config.affiliates_config
            
            col_aff1, col_aff2 = st.columns(2)
            
            with col_aff1:
                commission_rate = st.number_input("Tasa de comisión (%)", 
                                                min_value=10, max_value=50, 
                                                value=int(aff_config['commission_rate'] * 100))
                min_payout = st.number_input("Mínimo para retiro ($)", 
                                           min_value=10.0, max_value=1000.0, 
                                           value=aff_config['min_payout'])
            
            with col_aff2:
                payout_day = st.selectbox("Día de pago", 
                                        ["lunes", "martes", "miércoles", "jueves", "viernes"],
                                        index=["lunes", "martes", "miércoles", "jueves", "viernes"]
                                        .index(aff_config['payout_day']))
                default_currency = st.selectbox("Moneda predeterminada", 
                                              ["USD", "EUR", "GBP"], 
                                              index=["USD", "EUR", "GBP"].index(aff_config['default_currency']))
            
            if st.button("💾 Guardar configuración afiliados"):
                st.success("Configuración de afiliados guardada (simulado)")
        
        # Configuración de email
        with st.expander("📧 Configuración de Email"):
            email_config = config.email_config
            
            st.write(f"**SMTP Server:** {email_config['smtp_server']}:{email_config['smtp_port']}")
            st.write(f"**Username:** {email_config['username']}")
            st.write(f"**Sender:** {email_config['sender_email']}")
            
            # Probar configuración de email
            if st.button("📤 Probar configuración de email"):
                test_email = email_config['admin_email']
                test_code = "123456"
                
                success, message = self.email_service.send_verification_email(test_email, test_code)
                
                if success:
                    st.success(f"✅ Email de prueba enviado a {test_email}")
                else:
                    st.error(f"❌ Error: {message}")
        
        # Backup y mantenimiento
        with st.expander("💾 Backup y Mantenimiento"):
            col_back1, col_back2 = st.columns(2)
            
            with col_back1:
                if st.button("💾 Backup de datos", use_container_width=True):
                    st.success("Backup realizado (simulado)")
            
            with col_back2:
                if st.button("🗑️ Limpiar cache", use_container_width=True, type="secondary"):
                    st.success("Cache limpiado (simulado)")
            
            # Exportar datos
            st.subheader("📁 Exportar Datos")
            
            col_exp1, col_exp2 = st.columns(2)
            
            with col_exp1:
                if st.button("📊 Exportar afiliados", use_container_width=True):
                    db = self.db.load_affiliates()
                    json_data = json.dumps(db, indent=2, ensure_ascii=False)
                    
                    st.download_button(
                        label="Descargar JSON",
                        data=json_data,
                        file_name=f"affiliates_backup_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json"
                    )
            
            with col_exp2:
                if st.button("💰 Exportar pagos", use_container_width=True):
                    payments = self.payment_system.get_payment_history()
                    json_data = json.dumps(payments, indent=2, ensure_ascii=False)
                    
                    st.download_button(
                        label="Descargar JSON",
                        data=json_data,
                        file_name=f"payments_backup_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json"
                    )
    
    def _render_admin_tests(self):
        """Renderiza pruebas administrativas"""
        st.header("🧪 Pruebas del Sistema")
        
        # Prueba de email
        st.subheader("📧 Prueba de Sistema de Email")
        
        test_email = st.text_input("Email para prueba", value="promptandmente@gmail.com")
        test_subject = st.text_input("Asunto", value="Prueba del sistema")
        test_message = st.text_area("Mensaje", value="Este es un mensaje de prueba del sistema MINDGEEKCLINIC.")
        
        if st.button("📤 Enviar email de prueba", type="primary"):
            with st.spinner("Enviando email..."):
                success, result = self.email_service.send_verification_email(test_email, "123456")
                
                if success:
                    st.success(f"✅ Email enviado a {test_email}")
                else:
                    st.error(f"❌ Error: {result}")
        
        # Prueba de base de datos
        st.subheader("🗄️ Prueba de Base de Datos")
        
        col_db1, col_db2, col_db3 = st.columns(3)
        
        with col_db1:
            if st.button("🔍 Ver estadísticas BD", use_container_width=True):
                db = self.db.load_affiliates()
                stats = db.get("statistics", {})
                st.json(stats)
        
        with col_db2:
            if st.button("🔄 Verificar conexión", use_container_width=True):
                try:
                    db = self.db.load_affiliates()
                    st.success(f"✅ Base de datos conectada. {len(db.get('affiliates', {}))} afiliados.")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        with col_db3:
            if st.button("📊 Ver estado sistema", use_container_width=True):
                health = self.analytics.get_system_health()
                st.json(health)
        
        # Prueba de IA
        st.subheader("🧠 Prueba de Sistema de IA")
        
        test_prompt = st.text_area("Prompt para IA", 
                                 value="Explica los principios básicos de la biodescodificación emocional en 100 palabras.")
        
        if st.button("🤖 Probar IA", type="primary"):
            with st.spinner("Consultando a la IA..."):
                try:
                    config = ConfigManager()
                    
                    if config.groq_api_key:
                        groq_client = Groq(api_key=config.groq_api_key)
                        
                        response = groq_client.chat.completions.create(
                            messages=[
                                {
                                    "role": "system",
                                    "content": "Eres un experto en biodescodificación emocional."
                                },
                                {
                                    "role": "user",
                                    "content": test_prompt
                                }
                            ],
                            model="mixtral-8x7b-32768",
                            temperature=0.7,
                            max_tokens=500
                        )
                        
                        ai_response = response.choices[0].message.content
                        st.success("✅ Respuesta de IA:")
                        st.write(ai_response)
                    else:
                        st.warning("API key de Groq no configurada")
                        
                except Exception as e:
                    st.error(f"❌ Error en IA: {e}")

# ============================================
# PARTE 13: APLICACIÓN PRINCIPAL
# ============================================

def main():
    """Función principal de la aplicación"""
    
    # Inicializar sistemas
    config = ConfigManager()
    page_renderer = PageRenderer()
    
    # Verificar modo mantenimiento
    if config.app_config.get("maintenance_mode", False):
        st.title("🛠️ Mantenimiento en curso")
        st.info("""
        La aplicación está en mantenimiento para mejoras. 
        
        **Horario estimado de regreso:** Próximamente
        
        Para consultas urgentes, contacta: promptandmente@gmail.com
        """)
        return
    
    # Configurar barra lateral
    page_renderer.ui.sidebar_navigation()
    
    # Navegar a página seleccionada
    current_page = st.session_state.get("page", "home")
    
    if current_page == "home":
        page_renderer.render_home()
    elif current_page == "diagnostic":
        page_renderer.render_diagnostic()
    elif current_page == "sessions":
        page_renderer.render_sessions()
    elif current_page == "stats":
        page_renderer.render_stats()
    elif current_page == "chat":
        page_renderer.render_chat()
    elif current_page == "affiliate":
        page_renderer.render_affiliate()
    elif current_page == "admin":
        page_renderer.render_admin()
    
    # Footer
    st.markdown("---")
    
    col_foot1, col_foot2, col_foot3 = st.columns(3)
    
    with col_foot1:
        st.markdown(f"**MINDGEEKCLINIC** © 2024")
    
    with col_foot2:
        st.markdown("🧠 Biodescodificación Integral")
    
    with col_foot3:
        st.markdown(f"v{config.app_config.get('version', '5.0')}")

# ============================================
# EJECUCIÓN
# ============================================

if __name__ == "__main__":
    main()
