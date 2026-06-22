import streamlit as st
import json
from google import genai
from google.genai import types
from fpdf import FPDF

# Configuración inicial de la página web
st.set_page_config(page_title="Generador de Anexo 4", page_icon="🏥", layout="centered")

# --- CONEXIÓN CON EL CEREBRO DE IA ---
def extraer_datos_captura(imagen_bytes):
    client = genai.Client()
    imagen_input = types.Part.from_bytes(data=imagen_bytes, mime_type="image/png")
    
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

# --- NUEVO GENERADOR DE PDF (100% COMPATIBLE CON LA NUBE) ---
class PDFAnexo(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 7, 'ANEXO No. 4', ln=True, align='C')
        self.cell(0, 7, 'SOLICITUD DE DERIVACIÓN', ln=True, align='C')
        self.set_font('Arial', '', 10)
        self.cell(0, 6, 'SUBSISTEMA: MSP', ln=True, align='C')
        self.ln(5)

def generar_pdf_fpdf(datos):
    pdf = PDFAnexo()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
    
    # Sección Datos Paciente
    pdf.set_fill_color(43, 108, 176) # Azul
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, ' DATOS DEL PACIENTE', ln=True, fill=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(50, 7, '1. Apellidos:', border=1)
    pdf.cell(0, 7, f" {datos['apellidos_paciente']}", border=1, ln=True)
    pdf.cell(50, 7, '2. Nombres:', border=1)
    pdf.cell(0, 7, f" {datos['nombres_paciente']}", border=1, ln=True)
    pdf.cell(50, 7, '3. Cédula de Identidad:', border=1)
    pdf.cell(0, 7, f" {datos['cedula']}", border=1, ln=True)
    pdf.cell(50, 7, '4. Sexo:', border=1)
    pdf.cell(0, 7, f" {datos['sexo']}", border=1, ln=True)
    pdf.cell(50, 7, '5. Edad:', border=1)
    pdf.cell(0, 7, f" {datos['edad']}", border=1, ln=True)
    
    # Cuadro Clínico
    pdf.ln(4)
    pdf.set_fill_color(43, 108, 176)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, ' 6. CUADRO CLÍNICO', ln=True, fill=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 9.5)
    pdf.multi_cell(0, 5, f"\n{datos['cuadro_clinico_texto']}\n", border=1)
    
    # Signos Vitales
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 9.5)
    pdf.cell(0, 6, 'Signos Vitales extraídos:', ln=True)
    pdf.set_font('Arial', '', 9)
    pdf.cell(35, 6, f"PA: {datos['pa']}", border=1)
    pdf.cell(35, 6, f"FC: {datos['fc']} x min", border=1)
    pdf.cell(35, 6, f"FR: {datos['fr']} x min", border=1)
    pdf.cell(35, 6, f"SpO2: {datos['sao2']}%", border=1)
    pdf.cell(0, 6, f"T°: {datos['temperatura']} °C", border=1, ln=True)
    
    # Detalles de Solicitud
    pdf.ln(4)
    pdf.set_fill_color(43, 108, 176)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, ' DETALLES DE LA SOLICITUD', ln=True, fill=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(60, 7, '7. Diagnóstico Principal CIE-10:', border=1)
    pdf.cell(0, 7, f" {datos['cie10_codigo']} - {datos['cie10_descripcion']}", border=1, ln=True)
    pdf.cell(60, 7, '8. Servicio Solicitado:', border=1)
    pdf.cell(0, 7, ' UCI / ESPECIALIDAD REQUERIDA', border=1, ln=True)
    pdf.cell(60, 7, '10. Sustento de Solicitud:', border=1)
    pdf.cell(0, 7, ' LIMITADA CAPACIDAD RESOLUTIVA', border=1, ln=True)
    pdf.cell(60, 7, '11. Institución que Deriva:', border=1)
    pdf.cell(0, 7, ' HOSPITAL BÁSICO PICHINCHA', border=1, ln=True)
    pdf.cell(60, 7, '12. Profesional que Deriva:', border=1)
    pdf.cell(0, 7, ' DR. RHONNIE DUARTE MORAN', border=1, ln=True)
    
    # Firmas
    pdf.ln(20)
    pdf.cell(90, 5, '__________________________________', align='C')
    pdf.cell(0, 5, '__________________________________', align='C', ln=True)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(90, 4, 'Dr. Rhonnie Duarte Morán', align='C')
    pdf.cell(0, 4, 'Profesional que Acepta', align='C', ln=True)
    pdf.set_font('Arial', '', 8.5)
    pdf.cell(90, 4, 'Médico Solicitante / Hosp. Pichincha', align='C')
    pdf.cell(0, 4, 'Firma y Sello', align='C', ln=True)
    
    return pdf.output()

# --- INTERFAZ DE USUARIO (STREAMLIT) ---
st.title("🏥 Automatización de Anexo No. 4")
st.write("Sube la captura de pantalla del sistema para rellenar el formulario automáticamente.")

archivo = st.file_uploader("Arrastra aquí la imagen de la consulta", type=["png", "jpg", "jpeg"])

if archivo is not None:
    bytes_data = archivo.read()
    st.image(bytes_data, caption="Captura cargada", use_container_width=True)
    
    if st.button("🪄 Procesar Captura"):
        with st.spinner("La IA está leyendo los datos médicos..."):
            try:
                st.session_state['datos_clinicos'] = extraer_datos_captura(bytes_data)
                st.success("¡Datos extraídos con éxito!")
            except Exception as e:
                st.error(f"Error al procesar la imagen: {e}")

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
            datos['cie10_descripcion'] = st.text_input("Descripción CIE-10", value=datos.get('cie10_descripcion', ''))
            
        datos['cuadro_clinico_texto'] = st.text_area("Cuadro Clínico", value=datos.get('cuadro_clinico_texto', ''), height=150)
        
        try:
            pdf_data = generar_pdf_fpdf(datos)
            st.markdown("---")
            st.download_button(
                label="📥 Descargar Anexo 4 en PDF",
                data=bytes(pdf_data),
                file_name=f"Anexo_4_{datos['cedula']}.pdf",
                mime="application/pdf"
            )
        except Exception as pdf_err:
            st.error(f"Error al preparar el PDF: {pdf_err}")
