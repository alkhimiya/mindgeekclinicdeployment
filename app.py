# -*- coding: utf-8 -*-
"""
MINDGEEKCLINIC - Sistema de Biodescodificación con Afiliados
Versión: 3.0
Fecha: Diciembre 2024
Corrección: Error de formulario de afiliados solucionado
"""

# ============================================
# PARTE 1: CONFIGURACIÓN INICIAL E IMPORTACIONES
# ============================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import hashlib
import time
import re
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from io import BytesIO
import base64
import traceback
import os
from typing import Dict, List, Optional, Tuple
import sqlite3
from contextlib import contextmanager
import pickle
import warnings
warnings.filterwarnings('ignore')

# Configuración de la página
st.set_page_config(
    page_title="MINDGEEKCLINIC - Biodescodificación",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# PARTE 2: FUNCIONES DEL SISTEMA BASE
# ============================================

# Base de datos para afiliados
AFFILIATES_DB = "affiliates_db.json"
PAYMENT_LOG = "payment_log.json"

def init_affiliates_db():
    """Inicializa la base de datos de afiliados"""
    if not os.path.exists(AFFILIATES_DB):
        with open(AFFILIATES_DB, 'w') as f:
            json.dump({
                "affiliates": {},
                "next_id": 1,
                "referrals": {},
                "payment_history": []
            }, f)

def load_affiliates_db():
    """Carga la base de datos de afiliados"""
    init_affiliates_db()
    with open(AFFILIATES_DB, 'r') as f:
        return json.load(f)

def save_affiliates_db(data):
    """Guarda la base de datos de afiliados"""
    with open(AFFILIATES_DB, 'w') as f:
        json.dump(data, f, indent=2)

def init_payment_log():
    """Inicializa el log de pagos"""
    if not os.path.exists(PAYMENT_LOG):
        with open(PAYMENT_LOG, 'w') as f:
            json.dump([], f)

def log_payment(affiliate_id, amount, currency, status, details):
    """Registra un pago en el historial"""
    init_payment_log()
    with open(PAYMENT_LOG, 'r') as f:
        payments = json.load(f)
    
    payment = {
        "id": len(payments) + 1,
        "affiliate_id": affiliate_id,
        "amount": amount,
        "currency": currency,
        "status": status,
        "details": details,
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    payments.append(payment)
    
    with open(PAYMENT_LOG, 'w') as f:
        json.dump(payments, f, indent=2)
    
    return payment

# Configuración de email para notificaciones
EMAIL_CONFIG = {
    "sender": "promptandmente@gmail.com",
    "password": st.secrets.get("EMAIL_PASSWORD", ""),
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587
}

def send_email(to_email, subject, body):
    """Envía un email de notificación"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG["sender"]
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"])
        server.starttls()
        server.login(EMAIL_CONFIG["sender"], EMAIL_CONFIG["password"])
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        st.error(f"Error enviando email: {e}")
        return False

def generate_verification_code():
    """Genera un código de verificación de 6 dígitos"""
    return str(random.randint(100000, 999999))

# ============================================
# PARTE 3: SISTEMA DE AFILIADOS CORREGIDO
# ============================================

def show_affiliate_registration():
    """Muestra el formulario de registro de afiliados - CORREGIDO"""
    st.title("🎯 Programa de Afiliados MINDGEEKCLINIC")
    
    st.markdown("""
    ### ¡Gana comisiones recomendando MINDGEEKCLINIC!
    
    **Beneficios:**
    - 30% de comisión por cada venta
    - Panel de seguimiento en tiempo real
    - Pagos automáticos via Binance
    - Material de marketing proporcionado
    
    **Requisitos:**
    - Mayor de 18 años
    - Identificación verificada (KYC)
    - Cuenta de Binance activa
    """)
    
    # Inicializar estado para verificación de email
    if 'verification_code' not in st.session_state:
        st.session_state.verification_code = None
    if 'verified_email' not in st.session_state:
        st.session_state.verified_email = None
    if 'verification_sent' not in st.session_state:
        st.session_state.verification_sent = False
    
    # SECCIÓN 1: VERIFICACIÓN DE EMAIL (FUERA DEL FORMULARIO)
    st.subheader("1. Verificación de Email")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        email_to_verify = st.text_input("📧 Email para verificación", 
                                      key="verify_email_input",
                                      placeholder="tucorreo@ejemplo.com")
    
    with col2:
        st.write("")  # Espacio vertical
        st.write("")  # Espacio vertical
        
        # BOTÓN DE ENVÍO DE CÓDIGO - FUERA DE st.form()
        if st.button("📨 Enviar código de verificación", 
                    key="send_verification_button",
                    type="primary"):
            if email_to_verify and "@" in email_to_verify:
                # Generar y guardar código
                verification_code = generate_verification_code()
                st.session_state.verification_code = verification_code
                st.session_state.email_to_verify = email_to_verify
                
                # Enviar email
                email_sent = send_email(
                    email_to_verify,
                    "Código de verificación MINDGEEKCLINIC",
                    f"""Tu código de verificación para el programa de afiliados es: {verification_code}
                    
Este código expirará en 15 minutos.
                    
Saludos,
Equipo MINDGEEKCLINIC"""
                )
                
                if email_sent:
                    st.session_state.verification_sent = True
                    st.success(f"Código enviado a {email_to_verify}")
                else:
                    st.error("Error enviando el código. Intenta nuevamente.")
            else:
                st.warning("Por favor ingresa un email válido")
    
    # Mostrar campo para código si ya se envió
    if st.session_state.verification_sent:
        verification_input = st.text_input("🔢 Código de verificación",
                                         placeholder="Ingresa el código de 6 dígitos",
                                         key="code_input")
        
        if st.button("✅ Verificar código", key="verify_code_button"):
            if (verification_input == st.session_state.verification_code and 
                st.session_state.verification_code):
                st.session_state.verified_email = st.session_state.email_to_verify
                st.session_state.verification_code = None  # Limpiar código
                st.success("✅ Email verificado correctamente!")
            else:
                st.error("❌ Código incorrecto. Intenta nuevamente.")
    
    # Mostrar email verificado
    if st.session_state.verified_email:
        st.info(f"**Email verificado:** {st.session_state.verified_email}")
    
    st.divider()
    
    # SECCIÓN 2: FORMULARIO DE REGISTRO (CON st.form_submit_button())
    st.subheader("2. Información Personal")
    
    # FORMULARIO PRINCIPAL
    with st.form("affiliate_registration_form", clear_on_submit=True):
        # Campos del formulario
        col1, col2 = st.columns(2)
        
        with col1:
            full_name = st.text_input("👤 Nombre completo *", 
                                    placeholder="Ej: Juan Pérez García")
            phone = st.text_input("📱 Teléfono *", 
                                placeholder="Ej: +34 612 345 678")
            country = st.text_input("🌍 País *", 
                                  placeholder="Ej: España")
        
        with col2:
            id_type = st.selectbox("📄 Tipo de identificación *",
                                 ["DNI", "Pasaporte", "Cédula", "Otro"])
            id_number = st.text_input("🔢 Número de identificación *",
                                    placeholder="Ej: 12345678A")
            birth_date = st.date_input("🎂 Fecha de nacimiento *",
                                     min_value=datetime(1900, 1, 1),
                                     max_value=datetime.now() - timedelta(days=365*18))
        
        # Información bancaria
        st.subheader("3. Información de Pago")
        
        binance_address = st.text_input("💰 Dirección de Binance *",
                                      placeholder="Ej: U1234567890ABCDEF",
                                      help="Tu dirección de Binance para recibir pagos")
        
        tax_id = st.text_input("💼 ID Fiscal (opcional)",
                             placeholder="Para facturación")
        
        # Términos y condiciones
        st.subheader("4. Términos y Condiciones")
        
        col_terms1, col_terms2 = st.columns(2)
        
        with col_terms1:
            accept_terms = st.checkbox("✅ Acepto los términos y condiciones *")
            accept_privacy = st.checkbox("✅ Acepto la política de privacidad *")
        
        with col_terms2:
            accept_marketing = st.checkbox("📧 Deseo recibir material de marketing")
            accept_kyc = st.checkbox("🆔 Autorizo la verificación KYC *")
        
        # BOTÓN DE ENVÍO DENTRO DEL FORMULARIO (CORRECTO)
        submitted = st.form_submit_button("🚀 Registrar como Afiliado", 
                                        type="primary",
                                        use_container_width=True)
        
        # Validación después del envío
        if submitted:
            # Validar email verificado
            if not st.session_state.verified_email:
                st.error("❌ Debes verificar tu email primero")
                st.stop()
            
            # Validar campos requeridos
            required_fields = {
                "Nombre completo": full_name,
                "Teléfono": phone,
                "País": country,
                "Dirección de Binance": binance_address
            }
            
            missing_fields = [field for field, value in required_fields.items() if not value]
            
            if missing_fields:
                st.error(f"❌ Campos requeridos faltantes: {', '.join(missing_fields)}")
                st.stop()
            
            # Validar aceptación de términos
            if not all([accept_terms, accept_privacy, accept_kyc]):
                st.error("❌ Debes aceptar todos los términos requeridos")
                st.stop()
            
            # Validar mayoría de edad
            age = (datetime.now().date() - birth_date).days / 365.25
            if age < 18:
                st.error("❌ Debes ser mayor de 18 años para registrarte")
                st.stop()
            
            # Registrar afiliado
            try:
                db = load_affiliates_db()
                
                # Generar ID único
                affiliate_id = f"AFF{db['next_id']:04d}"
                referral_code = f"MG{random.randint(1000, 9999)}"
                
                # Crear registro
                affiliate_data = {
                    "id": affiliate_id,
                    "full_name": full_name,
                    "email": st.session_state.verified_email,
                    "phone": phone,
                    "country": country,
                    "id_type": id_type,
                    "id_number": id_number,
                    "birth_date": birth_date.isoformat(),
                    "binance_address": binance_address,
                    "tax_id": tax_id,
                    "referral_code": referral_code,
                    "status": "pending",
                    "commission_rate": 30,
                    "total_earnings": 0,
                    "pending_earnings": 0,
                    "registration_date": datetime.now().isoformat(),
                    "last_payment_date": None,
                    "accept_marketing": accept_marketing,
                    "kyc_status": "pending"
                }
                
                # Guardar en base de datos
                db["affiliates"][affiliate_id] = affiliate_data
                db["next_id"] += 1
                db["referrals"][referral_code] = {
                    "affiliate_id": affiliate_id,
                    "referrals": [],
                    "conversions": 0
                }
                
                save_affiliates_db(db)
                
                # Enviar notificación por email
                send_email(
                    st.session_state.verified_email,
                    "Registro de Afiliado Exitoso - MINDGEEKCLINIC",
                    f"""¡Felicidades {full_name}!

Tu registro como afiliado ha sido exitoso.

**Detalles de tu cuenta:**
- ID de Afiliado: {affiliate_id}
- Código de Referido: {referral_code}
- Comisión: 30%
- Estado: Pendiente de verificación

Tu cuenta será verificada en las próximas 24-48 horas.
Una vez aprobada, podrás comenzar a compartir tu código de referido.

**Tu enlace de referido:**
https://mindgeekclinic.streamlit.app/?ref={referral_code}

Saludos,
Equipo MINDGEEKCLINIC"""
                )
                
                # Notificar al administrador
                send_email(
                    "promptandmente@gmail.com",
                    f"Nuevo Afiliado Registrado: {affiliate_id}",
                    f"""Nuevo registro de afiliado:

ID: {affiliate_id}
Nombre: {full_name}
Email: {st.session_state.verified_email}
País: {country}
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Revisar verificación KYC requerida."""
                )
                
                st.success("""
                ✅ ¡Registro exitoso!
                
                Hemos enviado un email con los detalles de tu cuenta.
                Tu cuenta está pendiente de verificación y será activada
                en las próximas 24-48 horas.
                
                **Tu código de referido:** {}
                """.format(referral_code))
                
                # Limpiar estado
                st.session_state.verified_email = None
                st.session_state.verification_sent = False
                
            except Exception as e:
                st.error(f"❌ Error en el registro: {str(e)}")
                st.error("Por favor, intenta nuevamente o contacta con soporte")

def show_affiliate_dashboard():
    """Muestra el panel de control del afiliado"""
    st.title("📊 Panel de Afiliado")
    
    if 'affiliate_id' not in st.session_state:
        st.warning("Debes iniciar sesión como afiliado")
        return
    
    affiliate_id = st.session_state.affiliate_id
    db = load_affiliates_db()
    
    if affiliate_id not in db["affiliates"]:
        st.error("Afiliado no encontrado")
        return
    
    affiliate = db["affiliates"][affiliate_id]
    
    # Mostrar información del afiliado
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("💰 Ganancias Totales", f"${affiliate['total_earnings']:.2f}")
    
    with col2:
        st.metric("⏳ Pendientes", f"${affiliate['pending_earnings']:.2f}")
    
    with col3:
        st.metric("📈 Tasa de Comisión", f"{affiliate['commission_rate']}%")
    
    st.divider()
    
    # Sección de código de referido
    st.subheader("🎯 Tu Código de Referido")
    
    referral_code = affiliate['referral_code']
    referral_link = f"https://mindgeekclinic.streamlit.app/?ref={referral_code}"
    
    col_link1, col_link2 = st.columns([3, 1])
    
    with col_link1:
        st.code(referral_link, language="text")
    
    with col_link2:
        if st.button("📋 Copiar Enlace", use_container_width=True):
            st.success("Enlace copiado al portapapeles")
    
    # Métricas de referidos
    st.subheader("📈 Métricas de Referidos")
    
    referrals = db["referrals"].get(referral_code, {}).get("referrals", [])
    conversions = db["referrals"].get(referral_code, {}).get("conversions", 0)
    
    col_ref1, col_ref2, col_ref3 = st.columns(3)
    
    with col_ref1:
        st.metric("👥 Referidos", len(referrals))
    
    with col_ref2:
        st.metric("🔄 Conversiones", conversions)
    
    with col_ref3:
        conversion_rate = (conversions / len(referrals) * 100) if referrals else 0
        st.metric("📊 Tasa de Conversión", f"{conversion_rate:.1f}%")
    
    # Historial de pagos
    st.subheader("💰 Historial de Pagos")
    
    try:
        with open(PAYMENT_LOG, 'r') as f:
            payments = json.load(f)
        
        affiliate_payments = [p for p in payments if p.get('affiliate_id') == affiliate_id]
        
        if affiliate_payments:
            payment_df = pd.DataFrame(affiliate_payments)
            payment_df = payment_df[['date', 'amount', 'currency', 'status']]
            st.dataframe(payment_df, use_container_width=True)
        else:
            st.info("No hay pagos registrados aún")
    except:
        st.info("No hay pagos registrados aún")
    
    # Botón para solicitar pago
    if affiliate['pending_earnings'] > 10:  # Mínimo $10 para retirar
        st.divider()
        
        if st.button("💳 Solicitar Pago", type="primary", use_container_width=True):
            # Registrar solicitud de pago
            payment = log_payment(
                affiliate_id=affiliate_id,
                amount=affiliate['pending_earnings'],
                currency="USDT",
                status="pending",
                details=f"Solicitud de pago manual - {datetime.now().strftime('%Y-%m-%d')}"
            )
            
            # Actualizar base de datos
            affiliate['pending_earnings'] = 0
            db["affiliates"][affiliate_id] = affiliate
            save_affiliates_db(db)
            
            # Notificar al administrador
            send_email(
                "promptandmente@gmail.com",
                f"Solicitud de Pago Afiliado: {affiliate_id}",
                f"""Solicitud de pago recibida:

Afiliado: {affiliate['full_name']} ({affiliate_id})
Monto: ${payment['amount']} {payment['currency']}
Fecha: {payment['date']}

Por favor, procesar el pago via Binance."""
            )
            
            st.success(f"""
            ✅ Solicitud de pago enviada
            
            **Monto:** ${payment['amount']} {payment['currency']}
            **Estado:** Pendiente de procesamiento
            
            El pago será procesado en las próximas 24-48 horas.
            Recibirás una notificación por email cuando sea completado.
            """)

def process_referral(referral_code):
    """Procesa un código de referido"""
    db = load_affiliates_db()
    
    if referral_code in db["referrals"]:
        referral_data = db["referrals"][referral_code]
        
        # Registrar la visita (simplificado)
        if "visits" not in referral_data:
            referral_data["visits"] = 0
        referral_data["visits"] += 1
        
        # Guardar en sesión para tracking
        st.session_state['referral_code'] = referral_code
        
        # Guardar cambios
        db["referrals"][referral_code] = referral_data
        save_affiliates_db(db)
        
        return True
    
    return False

def track_conversion(amount):
    """Registra una conversión para el referido actual"""
    if 'referral_code' in st.session_state:
        referral_code = st.session_state['referral_code']
        
        db = load_affiliates_db()
        
        if referral_code in db["referrals"]:
            referral_data = db["referrals"][referral_code]
            
            # Incrementar conversiones
            if "conversions" not in referral_data:
                referral_data["conversions"] = 0
            referral_data["conversions"] += 1
            
            # Calcular comisión (30%)
            commission = amount * 0.30
            
            # Obtener ID del afiliado
            affiliate_id = referral_data["affiliate_id"]
            
            # Actualizar ganancias del afiliado
            if affiliate_id in db["affiliates"]:
                affiliate = db["affiliates"][affiliate_id]
                
                # Actualizar ganancias
                affiliate["total_earnings"] = affiliate.get("total_earnings", 0) + commission
                affiliate["pending_earnings"] = affiliate.get("pending_earnings", 0) + commission
                
                # Registrar en log de pagos
                log_payment(
                    affiliate_id=affiliate_id,
                    amount=commission,
                    currency="USDT",
                    status="earned",
                    details=f"Comisión por venta referida - {datetime.now().strftime('%Y-%m-%d')}"
                )
                
                # Guardar cambios
                db["affiliates"][affiliate_id] = affiliate
            
            # Guardar cambios en referidos
            db["referrals"][referral_code] = referral_data
            save_affiliates_db(db)
            
            # Notificar al afiliado
            if affiliate_id in db["affiliates"]:
                affiliate_email = db["affiliates"][affiliate_id]["email"]
                
                send_email(
                    affiliate_email,
                    "¡Nueva Comisión Ganada! - MINDGEEKCLINIC",
                    f"""¡Felicidades!

Has ganado una nueva comisión por una venta referida.

**Detalles:**
- Monto de venta: ${amount:.2f}
- Tu comisión (30%): ${commission:.2f}
- Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Total acumulado: ${affiliate['total_earnings']:.2f}

Continúa compartiendo tu enlace de referido para ganar más comisiones.

Saludos,
Equipo MINDGEEKCLINIC"""
                )

# ============================================
# PARTE 4: PANEL DE ADMINISTRACIÓN
# ============================================

def show_admin_panel():
    """Muestra el panel de administración"""
    st.title("🔐 Panel de Administración")
    
    # Verificación de contraseña
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    
    if not st.session_state.admin_authenticated:
        password = st.text_input("Contraseña de administración", 
                               type="password",
                               placeholder="Ingresa la contraseña")
        
        if st.button("Acceder", type="primary"):
            # Contraseña: Enaraure25..
            if password == "Enaraure25..":
                st.session_state.admin_authenticated = True
                st.success("✅ Acceso concedido")
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")
        return
    
    # Menú de administración
    admin_tab = st.sidebar.radio("Administración", [
        "📊 Dashboard",
        "👥 Afiliados",
        "💰 Pagos",
        "⚙️ Configuración"
    ])
    
    if admin_tab == "📊 Dashboard":
        show_admin_dashboard()
    elif admin_tab == "👥 Afiliados":
        show_admin_affiliates()
    elif admin_tab == "💰 Pagos":
        show_admin_payments()
    elif admin_tab == "⚙️ Configuración":
        show_admin_settings()

def show_admin_dashboard():
    """Dashboard de administración"""
    st.header("📊 Dashboard General")
    
    db = load_affiliates_db()
    
    # Métricas generales
    col1, col2, col3, col4 = st.columns(4)
    
    total_affiliates = len(db["affiliates"])
    active_affiliates = len([a for a in db["affiliates"].values() if a["status"] == "active"])
    pending_affiliates = len([a for a in db["affiliates"].values() if a["status"] == "pending"])
    
    total_earnings = sum([a.get("total_earnings", 0) for a in db["affiliates"].values()])
    pending_payments = sum([a.get("pending_earnings", 0) for a in db["affiliates"].values()])
    
    with col1:
        st.metric("👥 Total Afiliados", total_affiliates)
    
    with col2:
        st.metric("✅ Activos", active_affiliates)
    
    with col3:
        st.metric("⏳ Pendientes", pending_affiliates)
    
    with col4:
        st.metric("💰 Ganancias Totales", f"${total_earnings:.2f}")
    
    st.divider()
    
    # Gráfico de afiliados por estado
    status_data = pd.DataFrame({
        "Estado": ["Activos", "Pendientes", "Inactivos"],
        "Cantidad": [active_affiliates, pending_affiliates, total_affiliates - active_affiliates - pending_affiliates]
    })
    
    fig = px.pie(status_data, values="Cantidad", names="Estado", 
                 title="Distribución de Afiliados por Estado")
    st.plotly_chart(fig, use_container_width=True)
    
    # Actividad reciente
    st.subheader("📋 Actividad Reciente")
    
    try:
        with open(PAYMENT_LOG, 'r') as f:
            payments = json.load(f)
        
        if payments:
            recent_payments = sorted(payments, key=lambda x: x.get('timestamp', ''), reverse=True)[:10]
            payment_df = pd.DataFrame(recent_payments)
            
            if not payment_df.empty:
                payment_df = payment_df[['date', 'affiliate_id', 'amount', 'status', 'details']]
                st.dataframe(payment_df, use_container_width=True)
            else:
                st.info("No hay actividad reciente")
        else:
            st.info("No hay actividad reciente")
    except:
        st.info("No hay actividad reciente")

def show_admin_affiliates():
    """Gestión de afiliados"""
    st.header("👥 Gestión de Afiliados")
    
    db = load_affiliates_db()
    
    # Búsqueda y filtros
    col_search, col_filter = st.columns([2, 1])
    
    with col_search:
        search_term = st.text_input("Buscar afiliado", 
                                  placeholder="ID, nombre, email...")
    
    with col_filter:
        status_filter = st.selectbox("Filtrar por estado", 
                                   ["Todos", "active", "pending", "suspended"])
    
    # Lista de afiliados
    affiliates_list = list(db["affiliates"].values())
    
    # Aplicar filtros
    if search_term:
        affiliates_list = [a for a in affiliates_list if 
                          search_term.lower() in str(a.get('id', '')).lower() or
                          search_term.lower() in str(a.get('full_name', '')).lower() or
                          search_term.lower() in str(a.get('email', '')).lower()]
    
    if status_filter != "Todos":
        affiliates_list = [a for a in affiliates_list if a.get('status') == status_filter]
    
    # Mostrar tabla
    if affiliates_list:
        # Convertir a DataFrame para mejor visualización
        display_data = []
        for aff in affiliates_list:
            display_data.append({
                "ID": aff.get('id'),
                "Nombre": aff.get('full_name'),
                "Email": aff.get('email'),
                "Estado": aff.get('status'),
                "Ganancias": f"${aff.get('total_earnings', 0):.2f}",
                "Pendiente": f"${aff.get('pending_earnings', 0):.2f}",
                "Registro": aff.get('registration_date', '')[:10]
            })
        
        df = pd.DataFrame(display_data)
        st.dataframe(df, use_container_width=True)
        
        # Detalles del afiliado seleccionado
        st.subheader("📋 Detalles del Afiliado")
        
        selected_ids = st.multiselect("Seleccionar afiliados para detalles", 
                                    df['ID'].tolist())
        
        if selected_ids:
            for aff_id in selected_ids:
                if aff_id in db["affiliates"]:
                    affiliate = db["affiliates"][aff_id]
                    
                    with st.expander(f"Afiliado: {affiliate['full_name']} ({aff_id})"):
                        col_info1, col_info2 = st.columns(2)
                        
                        with col_info1:
                            st.write(f"**Email:** {affiliate['email']}")
                            st.write(f"**Teléfono:** {affiliate['phone']}")
                            st.write(f"**País:** {affiliate['country']}")
                            st.write(f"**Fecha nacimiento:** {affiliate['birth_date'][:10]}")
                        
                        with col_info2:
                            st.write(f"**Código referido:** {affiliate['referral_code']}")
                            st.write(f"**Dirección Binance:** {affiliate['binance_address']}")
                            st.write(f"**Estado KYC:** {affiliate.get('kyc_status', 'pending')}")
                            st.write(f"**Tasa comisión:** {affiliate['commission_rate']}%")
                        
                        # Acciones del administrador
                        st.subheader("⚙️ Acciones")
                        
                        col_act1, col_act2, col_act3 = st.columns(3)
                        
                        with col_act1:
                            new_status = st.selectbox("Cambiar estado",
                                                    ["active", "pending", "suspended"],
                                                    index=["active", "pending", "suspended"].index(affiliate['status']),
                                                    key=f"status_{aff_id}")
                        
                        with col_act2:
                            new_rate = st.number_input("Tasa de comisión (%)",
                                                     min_value=10,
                                                     max_value=50,
                                                     value=affiliate['commission_rate'],
                                                     key=f"rate_{aff_id}")
                        
                        with col_act3:
                            st.write("")  # Espacio
                            if st.button("💾 Guardar cambios", key=f"save_{aff_id}"):
                                # Actualizar afiliado
                                affiliate['status'] = new_status
                                affiliate['commission_rate'] = new_rate
                                db["affiliates"][aff_id] = affiliate
                                save_affiliates_db(db)
                                
                                # Notificar al afiliado
                                if new_status != affiliate['status']:
                                    status_text = {
                                        "active": "activa",
                                        "pending": "pendiente",
                                        "suspended": "suspendida"
                                    }
                                    
                                    send_email(
                                        affiliate['email'],
                                        f"Actualización de Estado - MINDGEEKCLINIC",
                                        f"""Hola {affiliate['full_name']},

El estado de tu cuenta de afiliado ha sido actualizado.

**Nuevo estado:** {status_text.get(new_status, new_status)}
**Tasa de comisión:** {new_rate}%

Si tienes preguntas, contacta con soporte.

Saludos,
Equipo MINDGEEKCLINIC"""
                                    )
                                
                                st.success(f"✅ Cambios guardados para {aff_id}")
                                st.rerun()
    else:
        st.info("No hay afiliados que coincidan con los filtros")

def show_admin_payments():
    """Gestión de pagos"""
    st.header("💰 Gestión de Pagos")
    
    try:
        with open(PAYMENT_LOG, 'r') as f:
            payments = json.load(f)
        
        if not payments:
            st.info("No hay pagos registrados")
            return
        
        # Filtros
        col_filt1, col_filt2, col_filt3 = st.columns(3)
        
        with col_filt1:
            status_filter = st.multiselect("Estado", 
                                         ["pending", "paid", "cancelled", "earned"],
                                         default=["pending"])
        
        with col_filt2:
            date_filter = st.date_input("Fecha", [])
        
        with col_filt3:
            affiliate_filter = st.text_input("ID Afiliado")
        
        # Filtrar pagos
        filtered_payments = payments
        
        if status_filter:
            filtered_payments = [p for p in filtered_payments if p.get('status') in status_filter]
        
        if affiliate_filter:
            filtered_payments = [p for p in filtered_payments if affiliate_filter in p.get('affiliate_id', '')]
        
        # Mostrar pagos
        if filtered_payments:
            payment_df = pd.DataFrame(filtered_payments)
            
            # Ordenar por fecha
            payment_df['date'] = pd.to_datetime(payment_df['date'])
            payment_df = payment_df.sort_values('date', ascending=False)
            
            # Columnas a mostrar
            display_cols = ['id', 'date', 'affiliate_id', 'amount', 'currency', 'status', 'details']
            display_cols = [c for c in display_cols if c in payment_df.columns]
            
            st.dataframe(payment_df[display_cols], use_container_width=True)
            
            # Procesar pagos pendientes
            pending_payments = [p for p in filtered_payments if p.get('status') == 'pending']
            
            if pending_payments:
                st.subheader("⏳ Pagos Pendientes por Procesar")
                
                for payment in pending_payments:
                    with st.expander(f"Pago #{payment['id']} - ${payment['amount']} {payment['currency']}"):
                        st.write(f"**Afiliado:** {payment['affiliate_id']}")
                        st.write(f"**Fecha:** {payment['date']}")
                        st.write(f"**Detalles:** {payment['details']}")
                        
                        col_proc1, col_proc2 = st.columns(2)
                        
                        with col_proc1:
                            if st.button(f"✅ Marcar como Pagado", key=f"paid_{payment['id']}"):
                                # Actualizar estado
                                payment['status'] = 'paid'
                                payment['processed_date'] = datetime.now().isoformat()
                                
                                # Actualizar en archivo
                                for i, p in enumerate(payments):
                                    if p['id'] == payment['id']:
                                        payments[i] = payment
                                        break
                                
                                with open(PAYMENT_LOG, 'w') as f:
                                    json.dump(payments, f, indent=2)
                                
                                # Obtener email del afiliado
                                db = load_affiliates_db()
                                affiliate_id = payment['affiliate_id']
                                
                                if affiliate_id in db["affiliates"]:
                                    affiliate_email = db["affiliates"][affiliate_id]["email"]
                                    affiliate_name = db["affiliates"][affiliate_id]["full_name"]
                                    
                                    # Enviar notificación
                                    send_email(
                                        affiliate_email,
                                        "✅ Pago Procesado - MINDGEEKCLINIC",
                                        f"""Hola {affiliate_name},

Tu pago ha sido procesado exitosamente.

**Detalles del pago:**
- Monto: ${payment['amount']} {payment['currency']}
- Fecha de procesamiento: {payment['processed_date'][:10]}
- ID de transacción: {payment['id']}

El pago ha sido enviado a tu dirección de Binance registrada.

Saludos,
Equipo MINDGEEKCLINIC"""
                                    )
                                
                                st.success(f"✅ Pago #{payment['id']} marcado como pagado")
                                st.rerun()
                        
                        with col_proc2:
                            if st.button(f"❌ Cancelar Pago", key=f"cancel_{payment['id']}"):
                                # Actualizar estado
                                payment['status'] = 'cancelled'
                                
                                # Actualizar en archivo
                                for i, p in enumerate(payments):
                                    if p['id'] == payment['id']:
                                        payments[i] = payment
                                        break
                                
                                with open(PAYMENT_LOG, 'w') as f:
                                    json.dump(payments, f, indent=2)
                                
                                st.success(f"❌ Pago #{payment['id']} cancelado")
                                st.rerun()
        else:
            st.info("No hay pagos que coincidan con los filtros")
            
    except Exception as e:
        st.error(f"Error cargando pagos: {str(e)}")

def show_admin_settings():
    """Configuración del sistema"""
    st.header("⚙️ Configuración del Sistema")
    
    st.subheader("📧 Configuración de Email")
    
    col_email1, col_email2 = st.columns(2)
    
    with col_email1:
        st.text_input("Email remitente", 
                     value="promptandmente@gmail.com",
                     disabled=True)
    
    with col_email2:
        st.text_input("SMTP Server", 
                     value="smtp.gmail.com:587",
                     disabled=True)
    
    st.divider()
    
    st.subheader("💰 Configuración de Comisiones")
    
    default_rate = st.number_input("Tasa de comisión predeterminada (%)",
                                 min_value=10,
                                 max_value=50,
                                 value=30)
    
    min_payout = st.number_input("Mínimo para retiro ($)",
                               min_value=10,
                               max_value=1000,
                               value=10)
    
    st.divider()
    
    st.subheader("🔄 Exportar Datos")
    
    col_exp1, col_exp2 = st.columns(2)
    
    with col_exp1:
        if st.button("📊 Exportar Afiliados (CSV)", use_container_width=True):
            db = load_affiliates_db()
            
            if db["affiliates"]:
                df = pd.DataFrame(db["affiliates"].values())
                csv = df.to_csv(index=False)
                
                st.download_button(
                    label="Descargar CSV",
                    data=csv,
                    file_name=f"affiliados_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
    
    with col_exp2:
        if st.button("💰 Exportar Pagos (CSV)", use_container_width=True):
            try:
                with open(PAYMENT_LOG, 'r') as f:
                    payments = json.load(f)
                
                if payments:
                    df = pd.DataFrame(payments)
                    csv = df.to_csv(index=False)
                    
                    st.download_button(
                        label="Descargar CSV",
                        data=csv,
                        file_name=f"pagos_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
            except:
                st.warning("No hay datos de pagos para exportar")
    
    st.divider()
    
    st.subheader("⚠️ Acciones Peligrosas")
    
    if st.button("🔄 Reiniciar Base de Datos", type="secondary"):
        st.warning("""
        **¡ADVERTENCIA!**
        
        Esta acción eliminará todos los datos de afiliados y pagos.
        Solo continuar si es absolutamente necesario.
        
        ¿Estás seguro de continuar?
        """)
        
        col_conf1, col_conf2 = st.columns(2)
        
        with col_conf1:
            if st.button("✅ Sí, reiniciar todo", type="primary"):
                # Reiniciar base de datos
                with open(AFFILIATES_DB, 'w') as f:
                    json.dump({
                        "affiliates": {},
                        "next_id": 1,
                        "referrals": {},
                        "payment_history": []
                    }, f)
                
                with open(PAYMENT_LOG, 'w') as f:
                    json.dump([], f)
                
                st.success("✅ Base de datos reiniciada exitosamente")
                st.rerun()
        
        with col_conf2:
            if st.button("❌ Cancelar"):
                st.info("Acción cancelada")

# ============================================
# PARTE 5: PÁGINAS PRINCIPALES DE LA APLICACIÓN
# ============================================

def show_home_page():
    """Página principal de la aplicación"""
    st.title("🧠 MINDGEEKCLINIC - Biodescodificación Integral")
    
    # Verificar si hay código de referido en la URL
    query_params = st.query_params
    if 'ref' in query_params:
        referral_code = query_params['ref']
        if process_referral(referral_code):
            st.sidebar.success(f"👋 ¡Bienvenido por referencia de {referral_code}!")
    
    st.markdown("""
    ## Transforma tu salud emocional a través de la biodescodificación
    
    **MINDGEEKCLINIC** es tu aliado para descifrar los mensajes del cuerpo 
    y transformar las emociones en bienestar integral.
    
    ### ✨ Características principales:
    
    🔍 **Diagnóstico inteligente** - Análisis emocional y biológico preciso  
    🧘 **Sesiones guiadas** - Hipnosis y meditaciones personalizadas  
    📊 **Seguimiento integral** - Monitorea tu progreso emocional  
    📄 **Reportes detallados** - Documentación profesional de tus sesiones  
    🎯 **Programa de afiliados** - Gana comisiones recomendando nuestro servicio  
    
    ### 🚀 Comienza tu viaje de sanación:
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Iniciar Diagnóstico", use_container_width=True):
            st.session_state.page = "diagnostic"
            st.rerun()
    
    with col2:
        if st.button("🧘 Sesiones Guiadas", use_container_width=True):
            st.session_state.page = "sessions"
            st.rerun()
    
    with col3:
        if st.button("📊 Mis Estadísticas", use_container_width=True):
            st.session_state.page = "stats"
            st.rerun()
    
    st.divider()
    
    # Sección de afiliados
    st.markdown("### 🎯 ¿Quieres ganar con MINDGEEKCLINIC?")
    
    col_aff1, col_aff2 = st.columns(2)
    
    with col_aff1:
        st.markdown("""
        **Programa de Afiliados:**
        - 30% de comisión por cada venta
        - Pagos automáticos via Binance
        - Panel de seguimiento en tiempo real
        - Material de marketing incluido
        """)
    
    with col_aff2:
        if st.button("💰 Unirse al Programa", use_container_width=True, type="secondary"):
            st.session_state.page = "affiliate"
            st.rerun()

def show_diagnostic_page():
    """Página de diagnóstico emocional"""
    st.title("🔍 Diagnóstico Emocional")
    
    st.markdown("""
    ### Analiza la relación entre tus emociones y síntomas físicos
    
    Completa el siguiente cuestionario para obtener un diagnóstico
    personalizado basado en principios de biodescodificación.
    """)
    
    # Cuestionario simplificado
    with st.form("diagnostic_form"):
        st.subheader("📝 Información básica")
        
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            age = st.number_input("Edad", min_value=1, max_value=100, value=30)
            gender = st.selectbox("Género", ["Masculino", "Femenino", "Otro"])
        
        with col_info2:
            occupation = st.text_input("Ocupación", placeholder="Tu profesión o actividad principal")
            stress_level = st.slider("Nivel de estrés general", 1, 10, 5)
        
        st.divider()
        st.subheader("💭 Síntomas emocionales")
        
        emotional_symptoms = st.multiselect(
            "¿Qué emociones predominan últimamente?",
            ["Ansiedad", "Tristeza", "Ira/Frustración", "Miedo", "Culpa", 
             "Desmotivación", "Insatisfacción", "Soledad", "Estrés crónico"]
        )
        
        sleep_quality = st.select_slider(
            "Calidad del sueño",
            options=["Muy mala", "Mala", "Regular", "Buena", "Excelente"]
        )
        
        st.divider()
        st.subheader("🤒 Síntomas físicos")
        
        physical_symptoms = st.multiselect(
            "¿Qué síntomas físicos has experimentado?",
            ["Dolores de cabeza", "Problemas digestivos", "Cansancio crónico",
             "Tensión muscular", "Cambios de peso", "Problemas cutáneos",
             "Alteraciones del sueño", "Cambios en el apetito"]
        )
        
        symptom_duration = st.selectbox(
            "¿Cuánto tiempo llevas con estos síntomas?",
            ["Menos de 1 mes", "1-3 meses", "3-6 meses", "6-12 meses", "Más de 1 año"]
        )
        
        st.divider()
        st.subheader("🎯 Áreas de vida afectadas")
        
        life_areas = st.multiselect(
            "¿Qué áreas de tu vida se han visto afectadas?",
            ["Trabajo/Estudios", "Relaciones personales", "Salud física",
             "Economía", "Desarrollo personal", "Tiempo libre"]
        )
        
        # Botón de envío
        submitted = st.form_submit_button("🔬 Generar Diagnóstico", type="primary")
        
        if submitted:
            # Simular análisis
            with st.spinner("Analizando tu perfil emocional..."):
                time.sleep(2)
                
                # Generar diagnóstico basado en respuestas
                st.success("✅ Diagnóstico completado")
                
                # Mostrar resultados
                st.subheader("📋 Resultados del Diagnóstico")
                
                col_res1, col_res2 = st.columns(2)
                
                with col_res1:
                    st.metric("Nivel de estrés", f"{stress_level}/10")
                    st.metric("Síntomas emocionales", len(emotional_symptoms))
                    st.metric("Síntomas físicos", len(physical_symptoms))
                
                with col_res2:
                    # Recomendaciones basadas en síntomas
                    recommendations = []
                    
                    if "Ansiedad" in emotional_symptoms:
                        recommendations.append("🧘 **Técnicas de respiración** - Practica 5 minutos al día")
                    
                    if "Problemas digestivos" in physical_symptoms:
                        recommendations.append("🍎 **Atención a la alimentación** - Lleva un diario alimenticio")
                    
                    if stress_level >= 7:
                        recommendations.append("⏰ **Gestión del tiempo** - Prioriza descansos breves cada 2 horas")
                    
                    if "Mala" in sleep_quality or "Muy mala" in sleep_quality:
                        recommendations.append("🌙 **Higiene del sueño** - Establece una rutina pre-sueño")
                    
                    if recommendations:
                        st.markdown("### 💡 Recomendaciones personalizadas")
                        for rec in recommendations:
                            st.markdown(f"- {rec}")
                
                # Opción para guardar diagnóstico
                if st.button("💾 Guardar este diagnóstico"):
                    st.session_state.last_diagnostic = {
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "emotional_symptoms": emotional_symptoms,
                        "physical_symptoms": physical_symptoms,
                        "stress_level": stress_level,
                        "recommendations": recommendations
                    }
                    st.success("Diagnóstico guardado en tu historial")

def show_sessions_page():
    """Página de sesiones guiadas"""
    st.title("🧘 Sesiones Guiadas de Biodescodificación")
    
    st.markdown("""
    ### Accede a sesiones personalizadas para tu bienestar emocional
    
    Selecciona el tipo de sesión que necesitas:
    """)
    
    # Tipos de sesiones
    session_types = st.radio(
        "Tipo de sesión:",
        ["Relajación profunda", "Liberación emocional", "Sanación interior", 
         "Refuerzo de autoestima", "Manejo del estrés"],
        horizontal=True
    )
    
    st.divider()
    
    # Descripción de la sesión seleccionada
    session_descriptions = {
        "Relajación profunda": """
        **Objetivo:** Reducir tensión física y mental
        
        **Duración:** 20 minutos
        **Beneficios:**
        - Disminución del cortisol (hormona del estrés)
        - Mejora de la claridad mental
        - Reducción de la tensión muscular
        - Equilibrio del sistema nervioso
        """,
        "Liberación emocional": """
        **Objetivo:** Liberar emociones bloqueadas
        
        **Duración:** 25 minutos
        **Beneficios:**
        - Liberación de traumas emocionales
        - Desbloqueo de recuerdos limitantes
        - Sanación de heridas emocionales
        - Reconexión con el bienestar interior
        """,
        "Sanación interior": """
        **Objetivo:** Activar procesos naturales de sanación
        
        **Duración:** 30 minutos
        **Beneficios:**
        - Fortalecimiento del sistema inmunológico
        - Activación de la capacidad autocurativa
        - Armonización cuerpo-mente
        - Regeneración celular optimizada
        """,
        "Refuerzo de autoestima": """
        **Objetivo:** Fortalecer la autoimagen y confianza
        
        **Duración:** 22 minutos
        **Beneficios:**
        - Mejora de la autoaceptación
        - Fortalecimiento de la confianza
        - Desarrollo de pensamientos positivos
        - Conexión con el potencial interno
        """,
        "Manejo del estrés": """
        **Objetivo:** Desarrollar herramientas antiestrés
        
        **Duración:** 18 minutos
        **Beneficios:**
        - Técnicas prácticas para el día a día
        - Reducción inmediata de la ansiedad
        - Mejora de la resiliencia emocional
        - Herramientas para situaciones desafiantes
        """
    }
    
    col_desc1, col_desc2 = st.columns([2, 1])
    
    with col_desc1:
        st.markdown(session_descriptions[session_types])
    
    with col_desc2:
        # Temporizador para la sesión
        st.subheader("⏱️ Configurar sesión")
        
        duration = st.slider("Duración (minutos)", 5, 60, 
                           value=20 if "Relajación" in session_types else 
                                 25 if "Liberación" in session_types else
                                 30 if "Sanación" in session_types else
                                 22 if "autoestima" in session_types else 18)
        
        background = st.selectbox("Sonido de fondo", 
                                ["Lluvia suave", "Olas del mar", "Bosque", "Silencio"])
    
    # Botón para iniciar sesión
    if st.button("🎧 Iniciar sesión guiada", type="primary", use_container_width=True):
        # Iniciar temporizador
        st.session_state.session_start = time.time()
        st.session_state.session_duration = duration * 60
        st.session_state.session_active = True
        st.session_state.session_type = session_types
        
        st.success(f"🎯 Sesión '{session_types}' iniciada por {duration} minutos")
        
        # Mostrar reproductor simulado
        st.markdown(f"""
        ### 🎵 Reproduciendo: {session_types}
        
        **Sonido ambiente:** {background}
        **Duración restante:** {duration}:00
        
        ---
        
        🎧 Usa auriculares para mejor experiencia
        🌿 Encuentra una posición cómoda
        👁️ Mantén los ojos cerrados durante la sesión
        """)
        
        # Barra de progreso
        progress_bar = st.progress(0)
        
        # Simular progreso
        for i in range(100):
            time.sleep(duration * 0.6)  # Simulación acelerada
            progress_bar.progress(i + 1)
        
        st.success("✅ Sesión completada")
        
        # Registrar en estadísticas
        if 'sessions_completed' not in st.session_state:
            st.session_state.sessions_completed = 0
        st.session_state.sessions_completed += 1

def show_stats_page():
    """Página de estadísticas personales"""
    st.title("📊 Mis Estadísticas de Bienestar")
    
    # Datos de ejemplo (en una app real vendrían de una base de datos)
    if 'sessions_completed' not in st.session_state:
        st.session_state.sessions_completed = 3
    
    if 'stress_levels' not in st.session_state:
        # Datos semanales de ejemplo
        st.session_state.stress_levels = {
            "Lunes": 7,
            "Martes": 6,
            "Miércoles": 5,
            "Jueves": 4,
            "Viernes": 6,
            "Sábado": 3,
            "Domingo": 2
        }
    
    # Métricas principales
    col_met1, col_met2, col_met3, col_met4 = st.columns(4)
    
    with col_met1:
        st.metric("🧘 Sesiones completadas", st.session_state.sessions_completed)
    
    with col_met2:
        avg_stress = sum(st.session_state.stress_levels.values()) / 7
        st.metric("😥 Estrés promedio", f"{avg_stress:.1f}/10")
    
    with col_met3:
        improvement = ((7 - avg_stress) / 7) * 100
        st.metric("📈 Mejora general", f"{improvement:.1f}%")
    
    with col_met4:
        consistency = min(st.session_state.sessions_completed, 7) / 7 * 100
        st.metric("✅ Consistencia", f"{consistency:.1f}%")
    
    st.divider()
    
    # Gráfico de evolución del estrés
    st.subheader("📈 Evolución del estrés semanal")
    
    fig = go.Figure(data=[
        go.Scatter(
            x=list(st.session_state.stress_levels.keys()),
            y=list(st.session_state.stress_levels.values()),
            mode='lines+markers',
            name='Nivel de estrés',
            line=dict(color='red', width=3),
            marker=dict(size=10)
        )
    ])
    
    fig.update_layout(
        title="Evolución diaria",
        xaxis_title="Día",
        yaxis_title="Nivel de estrés (1-10)",
        yaxis=dict(range=[0, 10]),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Gráfico de sesiones por tipo
    st.subheader("🧠 Distribución de sesiones")
    
    session_types = ["Relajación", "Liberación", "Sanación", "Autoestima", "Estrés"]
    session_counts = [5, 3, 2, 4, 3]  # Datos de ejemplo
    
    fig2 = px.pie(
        values=session_counts,
        names=session_types,
        title="Sesiones por tipo",
        color_discrete_sequence=px.colors.sequential.RdBu
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    
    # Registro de síntomas
    st.divider()
    st.subheader("📝 Registro diario de síntomas")
    
    with st.form("daily_tracking"):
        today = datetime.now().strftime("%A")
        
        col_track1, col_track2 = st.columns(2)
        
        with col_track1:
            daily_stress = st.slider(f"Estrés hoy ({today})", 1, 10, 5)
            energy_level = st.slider("Nivel de energía", 1, 10, 6)
        
        with col_track2:
            sleep_hours = st.number_input("Horas de sueño", min_value=0, max_value=12, value=7)
            mood = st.select_slider("Estado de ánimo", 
                                  options=["😔", "😟", "😐", "🙂", "😊"])
        
        notes = st.text_area("Notas adicionales", 
                           placeholder="¿Algo específico que quieras registrar?")
        
        if st.form_submit_button("💾 Guardar registro diario"):
            # Actualizar datos
            st.session_state.stress_levels[today] = daily_stress
            
            st.success(f"Registro guardado para {today}")
            time.sleep(1)
            st.rerun()

# ============================================
# PARTE 6: FUNCIÓN MAIN Y CONFIGURACIÓN
# ============================================

def main():
    """Función principal de la aplicación"""
    
    # Inicializar estado de la aplicación
    if 'page' not in st.session_state:
        st.session_state.page = "home"
    
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    
    # Sidebar con navegación
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/brain.png", width=80)
        st.title("MINDGEEKCLINIC")
        
        st.markdown("---")
        
        # Navegación principal
        page_options = [
            ("🏠 Inicio", "home"),
            ("🔍 Diagnóstico", "diagnostic"),
            ("🧘 Sesiones", "sessions"),
            ("📊 Estadísticas", "stats"),
            ("🎯 Afiliados", "affiliate"),
            ("🔐 Admin", "admin")
        ]
        
        for icon, page_key in page_options:
            if st.button(icon, key=f"nav_{page_key}", use_container_width=True):
                st.session_state.page = page_key
                st.rerun()
        
        st.markdown("---")
        
        # Información de sesión
        if 'affiliate_id' in st.session_state:
            st.success(f"👤 Afiliado: {st.session_state.affiliate_id}")
            
            if st.button("🚪 Cerrar sesión afiliado", use_container_width=True):
                del st.session_state.affiliate_id
                st.rerun()
        
        # Enlace de referencia si existe
        if 'referral_code' in st.session_state:
            st.info(f"👋 Referido por: {st.session_state.referral_code}")
        
        st.markdown("---")
        
        # Información de contacto
        st.markdown("""
        **📧 Contacto:**  
        promptandmente@gmail.com
        
        **🕒 Soporte:**  
        24/7 vía email
        
        **🔒 Privacidad:**  
        Tus datos están protegidos
        """)
    
    # Contenido principal basado en página seleccionada
    if st.session_state.page == "home":
        show_home_page()
    
    elif st.session_state.page == "diagnostic":
        show_diagnostic_page()
    
    elif st.session_state.page == "sessions":
        show_sessions_page()
    
    elif st.session_state.page == "stats":
        show_stats_page()
    
    elif st.session_state.page == "affiliate":
        # Verificar si ya es afiliado
        if 'affiliate_id' in st.session_state:
            show_affiliate_dashboard()
        else:
            # Mostrar opciones: registro o login
            aff_tab = st.radio("Afiliados", ["📝 Registrarse", "🔑 Iniciar sesión"], horizontal=True)
            
            if aff_tab == "📝 Registrarse":
                show_affiliate_registration()
            else:
                # Login para afiliados existentes
                st.subheader("🔑 Iniciar sesión como afiliado")
                
                aff_id = st.text_input("ID de afiliado", placeholder="AFF0001")
                email = st.text_input("Email registrado", placeholder="tucorreo@ejemplo.com")
                
                if st.button("Acceder", type="primary"):
                    db = load_affiliates_db()
                    
                    if aff_id in db["affiliates"]:
                        affiliate = db["affiliates"][aff_id]
                        
                        if affiliate["email"] == email:
                            st.session_state.affiliate_id = aff_id
                            st.success(f"✅ Bienvenido, {affiliate['full_name']}")
                            st.rerun()
                        else:
                            st.error("❌ Email incorrecto")
                    else:
                        st.error("❌ ID de afiliado no encontrado")
    
    elif st.session_state.page == "admin":
        show_admin_panel()
    
    # Footer
    st.markdown("---")
    col_foot1, col_foot2, col_foot3 = st.columns(3)
    
    with col_foot1:
        st.markdown("**MINDGEEKCLINIC** © 2024")
    
    with col_foot2:
        st.markdown("🧠 Biodescodificación Integral")
    
    with col_foot3:
        st.markdown("v3.0 - Sistema de Afiliados")

# ============================================
# EJECUCIÓN PRINCIPAL
# ============================================

if __name__ == "__main__":
    # Inicializar bases de datos
    init_affiliates_db()
    init_payment_log()
    
    # Ejecutar app
    main()
