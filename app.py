# streamlit_app.py - APLICACIÓN STREAMLIT COMPLETA
import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime

# ============================================
# CONFIGURACIÓN DE PÁGINA
# ============================================
st.set_page_config(
    page_title="MindGeek Clinic",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# FUNCIONES DE BASE DE DATOS JSON
# ============================================
def cargar_usuarios():
    """Carga usuarios desde data/users_db.json"""
    try:
        if os.path.exists("data/users_db.json"):
            with open("data/users_db.json", "r", encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return []

def guardar_usuarios(usuarios):
    """Guarda usuarios en data/users_db.json"""
    try:
        os.makedirs("data", exist_ok=True)
        with open("data/users_db.json", "w", encoding='utf-8') as f:
            json.dump(usuarios, f, indent=2, ensure_ascii=False)
        return True
    except:
        return False

def cargar_citas():
    """Carga citas desde data/citas.json"""
    try:
        if os.path.exists("data/citas.json"):
            with open("data/citas.json", "r", encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return []

def guardar_citas(citas):
    """Guarda citas en data/citas.json"""
    try:
        os.makedirs("data", exist_ok=True)
        with open("data/citas.json", "w", encoding='utf-8') as f:
            json.dump(citas, f, indent=2, ensure_ascii=False)
        return True
    except:
        return False

# ============================================
# INTERFAZ PRINCIPAL
# ============================================
st.title("🧠 MindGeek Clinic - Asistente IA")
st.markdown("### Sistema de diagnóstico de biodescodificación, hipnosis y asistencia psicológica")

# ============================================
# BARRA LATERAL - MENÚ
# ============================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    st.title("Navegación")
    
    menu_option = st.radio(
        "**Selecciona un módulo:**",
        [
            "🏠 Dashboard Principal",
            "👤 Gestión de Usuarios",
            "📅 Agenda de Citas",
            "🧠 Consultas Psicológicas",
            "🧬 Biodescodificación",
            "💆 Hipnosis y Terapia",
            "💬 Chat Terapéutico",
            "📊 Reportes y Análisis",
            "⚙️ Configuración del Sistema"
        ]
    )
    
    st.markdown("---")
    
    # Estado del sistema
    st.caption("**Estado del sistema:**")
    col1, col2 = st.columns(2)
    with col1:
        st.success("✅ Online")
    with col2:
        usuarios = cargar_usuarios()
        st.info(f"👥 {len(usuarios)}")
    
    st.markdown("---")
    st.caption(f"© {datetime.now().year} MindGeek Clinic v1.0")

# ============================================
# CONTENIDO PRINCIPAL SEGÚN OPCIÓN
# ============================================

# 1. DASHBOARD PRINCIPAL
if menu_option == "🏠 Dashboard Principal":
    st.header("📊 Dashboard de Control")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        usuarios = cargar_usuarios()
        pacientes = [u for u in usuarios if u.get('tipo') == 'Paciente']
        st.metric("Pacientes Registrados", len(pacientes))
    with col2:
        terapeutas = [u for u in usuarios if u.get('tipo') == 'Terapeuta']
        st.metric("Terapeutas", len(terapeutas))
    with col3:
        citas = cargar_citas()
        citas_hoy = [c for c in citas if c.get('fecha') == str(datetime.now().date())]
        st.metric("Citas Hoy", len(citas_hoy))
    with col4:
        st.metric("Módulos Activos", "8/10")
    
    st.markdown("---")
    
    # Acciones rápidas
    st.subheader("🚀 Acciones Rápidas")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("➕ Nuevo Paciente", use_container_width=True):
            st.session_state.menu_option = "👤 Gestión de Usuarios"
            st.rerun()
    with col2:
        if st.button("📅 Programar Cita", use_container_width=True):
            st.session_state.menu_option = "📅 Agenda de Citas"
            st.rerun()
    with col3:
        if st.button("🧠 Nueva Consulta", use_container_width=True):
            st.session_state.menu_option = "🧠 Consultas Psicológicas"
            st.rerun()
    
    st.markdown("---")
    
    # Próximas citas
    st.subheader("📅 Próximas Citas")
    if citas:
        citas_proximas = sorted(citas, key=lambda x: x.get('fecha', ''))[:5]
        for cita in citas_proximas:
            st.write(f"**{cita.get('paciente', 'N/A')}** - {cita.get('fecha', '')} - {cita.get('hora', '')}")
    else:
        st.info("No hay citas programadas")
    
    st.markdown("---")
    st.success("✅ Sistema base funcionando correctamente. Listo para migrar funcionalidades desde Flask.")

# 2. GESTIÓN DE USUARIOS
elif menu_option == "👤 Gestión de Usuarios":
    st.header("👤 Gestión de Usuarios y Pacientes")
    
    tab1, tab2, tab3 = st.tabs(["📝 Registrar Nuevo", "👁️ Ver Usuarios", "🔍 Buscar/Editar"])
    
    with tab1:
        st.subheader("Registrar Nuevo Usuario")
        
        with st.form("form_nuevo_usuario"):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre *", placeholder="Juan")
                email = st.text_input("Email *", placeholder="juan@ejemplo.com")
                telefono = st.text_input("Teléfono", placeholder="+123456789")
            with col2:
                apellido = st.text_input("Apellido *", placeholder="Pérez")
                fecha_nac = st.date_input("Fecha de Nacimiento", datetime.now())
                tipo_usuario = st.selectbox("Tipo de Usuario *", 
                    ["Paciente", "Terapeuta", "Administrador", "Colaborador"])
            
            # Información médica/psicológica
            st.subheader("Información Clínica")
            col1, col2 = st.columns(2)
            with col1:
                motivo_consulta = st.text_area("Motivo de Consulta", 
                    placeholder="Describa brevemente...")
            with col2:
                antecedentes = st.text_area("Antecedentes Relevantes",
                    placeholder="Historial médico, psicológico...")
            
            st.markdown("**Campos obligatorios ***")
            
            if st.form_submit_button("💾 Guardar Usuario", use_container_width=True):
                if nombre and apellido and email and tipo_usuario:
                    usuarios = cargar_usuarios()
                    
                    nuevo_usuario = {
                        "id": len(usuarios) + 1,
                        "nombre": nombre,
                        "apellido": apellido,
                        "email": email,
                        "telefono": telefono,
                        "fecha_nacimiento": str(fecha_nac),
                        "tipo": tipo_usuario,
                        "motivo_consulta": motivo_consulta,
                        "antecedentes": antecedentes,
                        "fecha_registro": str(datetime.now()),
                        "estado": "activo"
                    }
                    
                    usuarios.append(nuevo_usuario)
                    if guardar_usuarios(usuarios):
                        st.success(f"✅ Usuario **{nombre} {apellido}** registrado exitosamente!")
                        st.balloons()
                    else:
                        st.error("❌ Error al guardar el usuario")
                else:
                    st.error("❌ Por favor completa los campos obligatorios (*)")
    
    with tab2:
        st.subheader("Usuarios Registrados")
        
        usuarios = cargar_usuarios()
        if usuarios:
            # Convertir a DataFrame para mejor visualización
            datos = []
            for user in usuarios:
                datos.append({
                    "ID": user.get("id"),
                    "Nombre": f"{user.get('nombre', '')} {user.get('apellido', '')}",
                    "Email": user.get("email"),
                    "Tipo": user.get("tipo"),
                    "Teléfono": user.get("telefono", ""),
                    "Registro": user.get("fecha_registro", ""),
                    "Estado": user.get("estado", "activo")
                })
            
            df = pd.DataFrame(datos)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Estadísticas
            st.subheader("📈 Estadísticas")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Usuarios", len(usuarios))
            with col2:
                pacientes = len([u for u in usuarios if u.get('tipo') == 'Paciente'])
                st.metric("Pacientes", pacientes)
            with col3:
                terapeutas = len([u for u in usuarios if u.get('tipo') == 'Terapeuta'])
                st.metric("Terapeutas", terapeutas)
        else:
            st.info("📭 No hay usuarios registrados todavía.")
    
    with tab3:
        st.subheader("Buscar y Editar Usuarios")
        st.info("🔧 Esta funcionalidad se migrará desde Flask próximamente")

# 3. AGENDA DE CITAS
elif menu_option == "📅 Agenda de Citas":
    st.header("📅 Sistema de Gestión de Citas")
    st.info("Esta es la versión Streamlit. Migraremos la lógica completa desde Flask.")
    
    with st.form("form_nueva_cita"):
        col1, col2 = st.columns(2)
        with col1:
            paciente = st.text_input("Nombre del Paciente")
            tipo_consulta = st.selectbox("Tipo de Consulta", 
                ["Evaluación Inicial", "Seguimiento Psicológico", "Biodescodificación", 
                 "Sesión de Hipnosis", "Terapia Breve", "Emergencia"])
        with col2:
            terapeuta = st.selectbox("Terapeuta", 
                ["Dr. Alejandro Pérez", "Dra. María García", "Dr. Carlos Rodríguez", 
                 "Dra. Laura Martínez", "Equipo Multidisciplinar"])
            duracion = st.select_slider("Duración (minutos)", 
                options=[30, 45, 60, 90, 120], value=60)
        
        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha", datetime.now())
        with col2:
            hora = st.time_input("Hora", datetime.now().time())
        
        notas = st.text_area("Notas adicionales", 
            placeholder="Detalles importantes para la sesión...")
        
        if st.form_submit_button("✅ Programar Cita", use_container_width=True):
            st.success(f"📅 Cita programada para {fecha} a las {hora}")
            # Aquí irá la lógica de guardado

# 4. CONSULTAS PSICOLÓGICAS
elif menu_option == "🧠 Consultas Psicológicas":
    st.header("🧠 Sistema de Consultas Psicológicas")
    st.warning("⚠️ Módulo en desarrollo - Se migrará desde Flask")
    
    st.info("""
    **Funcionalidades que se migrarán:**
    - Análisis de patrones emocionales
    - Diario terapéutico digital
    - Evaluaciones psicológicas automatizadas
    - Seguimiento de progreso
    - Generación de informes
    """)

# 5. BIODESCODIFICACIÓN
elif menu_option == "🧬 Biodescodificación":
    st.header("🧬 Sistema de Biodescodificación")
    st.warning("⚠️ Módulo en desarrollo - Se migrará desde Flask")
    
    st.info("""
    **Funcionalidades que se migrarán:**
    - Diccionario de biodescodificación
    - Análisis de síntomas-emociones
    - Protocolos de intervención
    - Historial de casos
    - Integración con chat IA
    """)

# 6. HIPNOSIS Y TERAPIA
elif menu_option == "💆 Hipnosis y Terapia":
    st.header("💆 Sistema de Hipnosis y Terapia")
    st.warning("⚠️ Módulo en desarrollo - Se migrará desde Flask")

# 7. CHAT TERAPÉUTICO
elif menu_option == "💬 Chat Terapéutico":
    st.header("💬 Chat con Asistente IA Terapéutico")
    
    # Inicializar historial de chat
    if "mensajes" not in st.session_state:
        st.session_state.mensajes = []
    
    # Mostrar historial
    for mensaje in st.session_state.mensajes:
        with st.chat_message(mensaje["role"]):
            st.markdown(mensaje["content"])
    
    # Input de usuario
    if prompt := st.chat_input("Escribe tu mensaje aquí..."):
        # Añadir mensaje de usuario
        st.session_state.mensajes.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Simular respuesta de IA
        with st.chat_message("assistant"):
            respuesta = f"Entiendo que preguntas sobre '{prompt}'. Como asistente terapéutico, te recomendaría..."
            st.markdown(respuesta)
            st.session_state.mensajes.append({"role": "assistant", "content": respuesta})

# 8. REPORTES Y ANÁLISIS
elif menu_option == "📊 Reportes y Análisis":
    st.header("📊 Sistema de Reportes")
    
    tipo_reporte = st.selectbox("Selecciona tipo de reporte", 
        ["Reporte de Usuarios", "Reporte de Citas", "Reporte de Consultas", 
         "Estadísticas Mensuales", "Ingresos y Finanzas"])
    
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input("Fecha inicio", datetime.now().replace(day=1))
    with col2:
        fecha_fin = st.date_input("Fecha fin", datetime.now())
    
    if st.button("📈 Generar Reporte", use_container_width=True):
        st.info("Generando reporte... (Funcionalidad en desarrollo)")
        # Aquí irá la generación de reportes desde Flask

# 9. CONFIGURACIÓN DEL SISTEMA
elif menu_option == "⚙️ Configuración del Sistema":
    st.header("⚙️ Configuración y Ajustes")
    
    st.subheader("📁 Estado del Sistema")
    
    # Verificar archivos importantes
    archivos_importantes = [
        ("app.py", "Aplicación Flask original"),
        ("streamlit_app.py", "Aplicación Streamlit"),
        ("Procfile", "Configuración de despliegue"),
        ("requirements.txt", "Dependencias Python"),
        ("data/users_db.json", "Base de datos de usuarios"),
        ("streamlit/secrets.toml", "Configuración básica")
    ]
    
    for archivo, descripcion in archivos_importantes:
        existe = os.path.exists(archivo)
        if existe:
            st.success(f"✅ **{archivo}** - {descripcion}")
        else:
            st.error(f"❌ **{archivo}** - {descripcion} (No encontrado)")
    
    st.markdown("---")
    
    st.subheader("🔄 Acciones del Sistema")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Recargar Datos", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("📊 Ver Logs", use_container_width=True):
            st.info("Los logs están disponibles en Streamlit Cloud → Manage app")

# ============================================
# PIE DE PÁGINA
# ============================================
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption(f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
with col2:
    st.caption("🧠 MindGeek Clinic v1.0")
with col3:
    st.caption("🔒 Sistema en migración a Streamlit")

# ============================================
# ESTILOS ADICIONALES
# ============================================
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
    }
    .stProgress > div > div > div > div {
        background-color: #4CAF50;
    }
</style>
""", unsafe_allow_html=True)
