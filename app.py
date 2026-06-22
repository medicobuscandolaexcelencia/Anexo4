import streamlit as st
import json
import os
from google import genai
from google.genai import types
from weasyprint import HTML

# Configuración inicial de la página web
st.set_page_config(page_title="Generador de Anexo 4", page_icon="🏥", layout="centered")

# --- CONEXIÓN CON EL CEREBRO DE IA ---
def extraer_datos_captura(imagen_bytes):
    """Envía la imagen a la API de Gemini para extraer los datos clínicos"""
    # Se requiere configurar la variable de entorno GEMINI_API_KEY en la plataforma en la nube
    client = genai.Client()
    
    # Preparamos el archivo para la IA
    imagen_input = types.Part.from_bytes(
        data=imagen_bytes,
        mime_type="image/png",
    )
    
    instrucciones = """
    Analiza la captura de pantalla del sistema médico y extrae los datos en formato JSON estricto:
    {
        "apellidos_paciente": "",
        "nombres_paciente": "",
        "cedula": "",
        "sexo": "",
        "edad": "",
        "cuadro_clinico_texto": "Texto íntegro del recuadro de enfermedad actual",
        "pa": "", "fc": "", "fr": "", "sao2": "", "temperatura": "",
        "cie10_codigo": "",
        "cie10_descripcion": ""
    }
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[imagen_input, instrucciones],
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return json.loads(response.text)

# --- GENERADOR DE REPORTE PDF ---
def generar_pdf(datos):
    """Crea el HTML dinámico con los datos actuales y lo exporta a PDF"""
    html_template = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; color: #333; line-height: 1.4; font-size: 11pt; }}
            .header {{ text-align: center; font-weight: bold; font-size: 14pt; margin-bottom: 20px; text-transform: uppercase; }}
            .section {{ background-color: #2b6cb0; color: white; padding: 5px 10px; font-weight: bold; margin-top: 15px; border-radius: 3px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ border: 1px solid #cbd5e0; padding: 8px; text-align: left; vertical-align: top; }}
            th {{ background-color: #f7fafc; width: 30%; font-weight: bold; }}
            .vitals-table {{ text-align: center; }}
            .vitals-table th, .vitals-table td {{ text-align: center; }}
        </style>
    </head>
    <body>
        <div class="header">Anexo No. 4 - Solicitud de Derivación<br><small>SUBSISTEMA: MSP</small></div>
        
        <div class="section">Datos del Paciente</div>
        <table>
            <tr><th>1. Apellidos</th><td>{datos['apellidos_paciente']}</td></tr>
            <tr><th>2. Nombres</th><td>{datos['nombres_paciente']}</td></tr>
            <tr><th>3. Cédula</th><td>{datos['cedula']}</td></tr>
            <tr><th>4. Sexo</th><td>{datos['sexo']}</td></tr>
            <tr><th>5. Edad</th><td>{datos['edad']}</td></tr>
        </table>

        <div class="section">6. Cuadro Clínico</div>
        <p style="text-align: justify;">{datos['cuadro_clinico_texto']}</p>
        
        <h4 style="margin: 10px 0 5px 0;">Signos Vitales:</h4>
        <table class="vitals-table">
            <tr><th>PA (mmHg)</th><th>FC (min)</th><th>FR (min)</th><th>SpO₂ (%)</th><th>T° (°C)</th></tr>
            <tr>
                <td>{datos['pa']}</td><td>{datos['fc']}</td><td>{datos['fr']}</td><td>{datos['sao2']}%</td><td>{datos['temperatura']}°C</td>
            </tr>
        </table>

        <div class="section">Detalles de la Solicitud</div>
        <table>
            <tr><th>7. Diagnóstico Principal (CIE-10)</th><td><strong>{datos['cie10_codigo']}</strong> - {datos['cie10_descripcion']}</td></tr>
            <tr><th>8. Servicio Solicitado</th><td>UCI / ESPECIALIDAD CORRESPONDIENTE</td></tr>
            <tr><th>10. Sustento de la Solicitud</th><td>LIMITADA CAPACIDAD RESOLUTIVA</td></tr>
            <tr><th>11. Institución que Deriva</th><td>HOSPITAL BÁSICO PICHINCHA</td></tr>
            <tr><th>12. Profesional que Deriva</th><td>DR. RHONNIE DUARTE MORAN</td></tr>
        </table>
    </body>
    </html>
    """
    # Guarda el PDF en memoria temporal para descarga inmediata
    return HTML(string=html_template).write_pdf()

# --- INTERFAZ DE USUARIO (STREAMLIT) ---
st.title("🏥 Automatización de Anexo No. 4")
st.write("Sube la captura de pantalla del sistema para rellenar el formulario de derivación automáticamente.")

archivo = st.file_uploader("Arrastra aquí la imagen de la consulta", type=["png", "jpg", "jpeg"])

if archivo is not None:
    bytes_data = archivo.read()
    st.image(bytes_data, caption="Captura cargada", use_container_width=True)
    
    if st.button("🪄 Procesar Captura"):
        with st.spinner("La IA está leyendo los datos médicos..."):
            try:
                # 1. Ejecutar lectura de la imagen
                st.session_state['datos_clinicos'] = extraer_datos_captura(bytes_data)
                st.success("¡Datos extraídos con éxito!")
            except Exception as e:
                st.error(f"Error al procesar la imagen: {e}")

    # Si los datos ya fueron extraídos, permitir revisión y descarga
    if 'datos_clinicos' in st.session_state:
        datos = st.session_state['datos_clinicos']
        
        st.subheader("📝 Revisión de Datos Extraídos")
        col1, col2 = st.columns(2)
        with col1:
            datos['apellidos_paciente'] = st.text_input("Apellidos", value=datos.get('apellidos_paciente', ''))
            datos['nombres_paciente'] = st.text_input("Nombres", value=datos.get('nombres_paciente', ''))
            datos['cedula'] = st.text_input("Cédula", value=datos.get('cedula', ''))
        with col2:
            datos['sexo'] = st.text_input("Sexo", value=datos.get('sexo', ''))
            datos['edad'] = st.text_input("Edad", value=datos.get('edad', ''))
            datos['cie10_codigo'] = st.text_input("Código CIE-10", value=datos.get('cie10_codigo', ''))
            
        datos['cuadro_clinico_texto'] = st.text_area("Cuadro Clínico", value=datos.get('cuadro_clinico_texto', ''), height=150)
        
        # Generar el PDF final basado en los campos editados
        pdf_data = generar_pdf(datos)
        
        st.markdown("---")
        st.download_button(
            label="📥 Descargar Anexo 4 en PDF",
            data=pdf_data,
            file_name=f"Anexo_4_{datos['cedula']}.pdf",
            mime="application/pdf"
        )