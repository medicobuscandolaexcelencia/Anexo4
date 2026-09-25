import streamlit as st
import json
from google import genai
from google.genai import types
from fpdf import FPDF

# Configuración inicial de la página web
st.set_page_config(page_title="Generador de Anexo 4", page_icon="🏥", layout="wide")

# --- INICIALIZAR HISTORIAL EN LA SESIÓN ---
if 'historial_pacientes' not in st.session_state:
    st.session_state['historial_pacientes'] = []

# --- CONEXIÓN CON EL CEREBRO DE IA (PROCESAMIENTO MULTI-IMAGEN CONSOLIDADO) ---
def extraer_datos_capturas_consolidadas(lista_bytes_imagenes):
    client = genai.Client()
    
    # Convertimos todas las capturas en partes para enviar a Gemini a la vez
    contents = []
    for img_bytes in lista_bytes_imagenes:
        contents.append(types.Part.from_bytes(data=img_bytes, mime_type="image/png"))
    
    instrucciones = """
    Analiza TODAS las capturas de pantalla adjuntas que corresponden al MISMO paciente. 
    Integra y consolida la información dispersa entre las distintas capturas (por ejemplo, si en una está la filiación y en otra la evolución o historia clínica) y extrae un solo JSON estructurado:
    {
        "apellidos_paciente": "",
        "nombres_paciente": "",
        "cedula": "",
        "sexo": "",
        "edad": "",
        "cuadro_clinico_texto": "Texto completo y consolidado de la enfermedad actual / evolución que aparezca en las capturas",
        "pa": "", "fc": "", "fr": "", "sao2": "", "temperatura": "",
        "cie10_codigo": "",
        "cie10_descripcion": ""
    }
    """
    contents.append(instrucciones)
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=contents,
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    return json.loads(response.text)

# --- GENERADOR DE PDF ---
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
    pdf.set_fill_color(43, 108, 176)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, ' DATOS DEL PACIENTE', ln=True, fill=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(50, 7, '1. Apellidos:', border=1)
    pdf.cell(0, 7, f" {datos.get('apellidos_paciente', '')}", border=1, ln=True)
    pdf.cell(50, 7, '2. Nombres:', border=1)
    pdf.cell(0, 7, f" {datos.get('nombres_paciente', '')}", border=1, ln=True)
    pdf.cell(50, 7, '3. Cédula de Identidad:', border=1)
    pdf.cell(0, 7, f" {datos.get('cedula', '')}", border=1, ln=True)
    pdf.cell(50, 7, '4. Sexo:', border=1)
    pdf.cell(0, 7, f" {datos.get('sexo', '')}", border=1, ln=True)
    pdf.cell(50, 7, '5. Edad:', border=1)
    pdf.cell(0, 7, f" {datos.get('edad', '')}", border=1, ln=True)
    
    # Cuadro Clínico
    pdf.ln(4)
    pdf.set_fill_color(43, 108, 176)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, ' 6. CUADRO CLÍNICO', ln=True, fill=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 9.5)
    pdf.multi_cell(0, 5, f"\n{datos.get('cuadro_clinico_texto', '')}\n", border=1)
    
    # Signos Vitales
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 9.5)
    pdf.cell(0, 6, 'Signos Vitales extraídos:', ln=True)
    pdf.set_font('Arial', '', 9)
    pdf.cell(35, 6, f"PA: {datos.get('pa', '')}", border=1)
    pdf.cell(35, 6, f"FC: {datos.get('fc', '')} x min", border=1)
    pdf.cell(35, 6, f"FR: {datos.get('fr', '')} x min", border=1)
    pdf.cell(35, 6, f"SpO2: {datos.get('sao2', '')}%", border=1)
    pdf.cell(0, 6, f"T°: {datos.get('temperatura', '')} °C", border=1, ln=True)
    
    # Detalles de Solicitud
    pdf.ln(4)
    pdf.set_fill_color(43, 108, 176)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, ' DETALLES DE LA SOLICITUD', ln=True, fill=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(60, 7, '7. Diagnóstico Principal CIE-10:', border=1)
    pdf.cell(0, 7, f" {datos.get('cie10_codigo', '')} - {datos.get('cie10_descripcion', '')}", border=1, ln=True)
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

# --- INTERFAZ PRINCIPAL ---
st.title("🏥 Gestor de Anexo No. 4")
st.write("Sube una o varias capturas del MISMO PACIENTE para consolidar la información en una sola solicitud.")

# Cargar capturas del mismo caso
archivos = st.file_uploader("Selecciona o arrastra las capturas del sistema (filiación, evolución, etc.)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

if archivos:
    if st.button("🪄 Procesar y Consolidar Caso"):
        with st.spinner("La IA está leyendo y unificando los datos de las capturas..."):
            try:
                # Obtenemos los bytes de todas las capturas cargadas
                lista_bytes = [a.read() for a in archivos]
                datos_consolidados = extraer_datos_capturas_consolidadas(lista_bytes)
                
                # Añadimos al historial el paciente unificado
                st.session_state['historial_pacientes'].append(datos_consolidados)
                st.success("¡Caso procesado y consolidado con éxito!")
            except Exception as e:
                st.error(f"Error al consolidar las imágenes: {e}")

# --- SECCIÓN DE PACIENTES PROCESADOS ---
if st.session_state['historial_pacientes']:
    st.markdown("---")
    st.subheader(f"📋 Pacientes Procesados ({len(st.session_state['historial_pacientes'])})")
    
    nombres_pacientes = [
        f"{p.get('cedula', 'Sin CI')} - {p.get('apellidos_paciente', '')} {p.get('nombres_paciente', '')}" 
        for p in st.session_state['historial_pacientes']
    ]
    
    paciente_sel_idx = st.selectbox("Selecciona un paciente para editar o generar su PDF:", range(len(nombres_pacientes)), format_func=lambda x: nombres_pacientes[x])
    
    datos_actuales = st.session_state['historial_pacientes'][paciente_sel_idx]
    
    col1, col2 = st.columns(2)
    with col1:
        datos_actuales['apellidos_paciente'] = st.text_input("Apellidos", value=datos_actuales.get('apellidos_paciente', ''), key=f"ap_{paciente_sel_idx}")
        datos_actuales['nombres_paciente'] = st.text_input("Nombres", value=datos_actuales.get('nombres_paciente', ''), key=f"nom_{paciente_sel_idx}")
        datos_actuales['cedula'] = st.text_input("Cédula", value=datos_actuales.get('cedula', ''), key=f"ci_{paciente_sel_idx}")
    with col2:
        datos_actuales['sexo'] = st.text_input("Sexo", value=datos_actuales.get('sexo', ''), key=f"sx_{paciente_sel_idx}")
        datos_actuales['edad'] = st.text_input("Edad", value=datos_actuales.get('edad', ''), key=f"ed_{paciente_sel_idx}")
        datos_actuales['cie10_codigo'] = st.text_input("Código CIE-10", value=datos_actuales.get('cie10_codigo', ''), key=f"cie_{paciente_sel_idx}")
        datos_actuales['cie10_descripcion'] = st.text_input("Descripción CIE-10", value=datos_actuales.get('cie10_descripcion', ''), key=f"cied_{paciente_sel_idx}")
        
    datos_actuales['cuadro_clinico_texto'] = st.text_area("Cuadro Clínico (Consolidado)", value=datos_actuales.get('cuadro_clinico_texto', ''), height=150, key=f"cc_{paciente_sel_idx}")
    
    pdf_bytes = generar_pdf_fpdf(datos_actuales)
    
    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        st.download_button(
            label=f"📥 Descargar PDF ({datos_actuales.get('cedula', 'paciente')})",
            data=bytes(pdf_bytes),
            file_name=f"Anexo_4_{datos_actuales.get('cedula', 'paciente')}.pdf",
            mime="application/pdf",
            key=f"dl_{paciente_sel_idx}"
        )
    with col_btn2:
        if st.button("🗑️ Limpiar Pacientes"):
            st.session_state['historial_pacientes'] = []
            st.rerun()
