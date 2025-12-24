
st.subheader("📋 Datos del Paciente")

# Campos del formulario
iniciales = st.text_input("Iniciales del paciente (ej: A.B.):", max_chars=10)
edad = st.number_input("Edad:", min_value=1, max_value=120, value=30)
estado_civil = st.selectbox("Estado civil:", ["Soltero/a", "Casado/a", "Divorciado/a", "Viudo/a", "Unión libre", "Otro"])
situacion_laboral = st.selectbox("Situación laboral:", ["Empleado", "Desempleado", "Independiente", "Estudiante", "Jubilado", "Otro"])
tension = st.selectbox("Tensión arterial:", ["Normal", "Hipotensión", "Hipertensión", "No sabe"])

# DOLENCIA AHORA PRIMERO
dolencia = st.text_area("Dolencia o síntoma principal:", 
                       placeholder="Describa su dolencia principal (ej: dolor de cabeza recurrente, ansiedad, problemas digestivos...)", 
                       height=80)

# TIEMPO DE PADECIMIENTO AHORA DESPUÉS
tiempo_padecimiento = st.text_input("Tiempo de padecimiento (ej: 3 meses, 2 años, desde la infancia):")

frecuencia = st.selectbox("Frecuencia:", ["Constante", "Diaria", "Semanal", "Mensual", "Ocasional", "Variable"])
intensidad = st.slider("Intensidad (1-10):", min_value=1, max_value=10, value=5)
