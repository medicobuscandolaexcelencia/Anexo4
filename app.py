import streamlit as st
import json
import time
from google import genai
from google.genai import types
from fpdf import FPDF

# Configuración inicial de la página web
st.set_page_config(page_title="Generador de Anexo 4", page_icon="🏥", layout="wide")

# --- INICIALIZAR HISTORIAL EN LA SESIÓN ---
if 'historial_pacientes' not in st.session_state:
    st.session_state['historial_pacientes'] = []

# --- CONEXIÓN A IA CON EXTRACCIÓN DETALLADA ---
def extraer_datos_capturas_consolidadas(lista_bytes_imagenes):
    client = genai.Client()
    
    modelos = ['gemini-2.5-flash', 'gemini-1.5-flash']
    
    contents = []
    for img_bytes in lista_bytes_imagenes:
        contents.append(types.Part.from_bytes(data=img_bytes, mime_type="image/png"))
    
    instrucciones = """
    Analiza TODAS las capturas de pantalla adjuntas que corresponden al MISMO paciente. 
    Integra y consolida la información dispersa entre las distintas capturas y extrae un solo JSON estructurado:
    {
        "apellidos_paciente": "",
        "nombres_paciente": "",
        "cedula": "",
        "sexo": "",
        "edad": "",
        "cuadro_clinico_texto": "Texto completo y consolidado de la enfermedad actual / evolución que aparezca en las capturas",
        "pa": "", "fc": "", "fr": "", "sao2": "", "temperatura": "",
        "cie10_codigo": "",
        "cie10_descripcion": "",
        "servicio_solicitado": "Identifica la especialidad médica según el cuadro clínico",
        "codigo_servicio": "",
        "requerimiento": "",
        "numero_caso": ""
    }
    """
    contents.append(instrucciones)

    ultimo_error = None

    for modelo in modelos:
        for intento in range(3):
            try:
                response = client.models.generate_content(
                    model=modelo,
                    contents=contents,
                    config=types.GenerateContentConfig(response_mime_type="application/json"),
                )
                return json.loads(response.text)
            except Exception as e:
                ultimo_error = e
                if "503" in str(e) or "UNAVAILABLE" in str(e):
                    time.sleep(2)
                else:
                    break

    raise ultimo_error


# --- NUEVA FUNCIÓN: GENERA TEXTO PERFECTO PARA WHATSAPP ---
def generar_texto_whatsapp(datos):
    texto = f"""ANEXO NO. 4
SOLICITUD DE DERIVACIÓN
SUBSISTEMA: MSP

DATOS DEL PACIENTE
1. Apellidos: {datos.get('apellidos_paciente', '')}
2. Nombres: {datos.get('nombres_paciente', '')}
3. Cédula de Identidad: {datos.get('cedula', '')}
4. Sexo: {datos.get('sexo', '')}
5. Edad: {datos.get('edad', '')}

6. CUADRO CLÍNICO:
{datos.get('cuadro_clinico_texto', '')}

Signos Vitales:
PA: {datos.get('pa', '')} | FC: {datos.get('fc', '')} | FR: {datos.get('fr', '')} | SpO2: {datos.get('sao2', '')}% | T°: {datos.get('temperatura', '')}°C

DETALLES DE LA SOLICITUD
7. Diagnóstico Principal y CIE-10: {datos.get('cie10_codigo', '')} - {datos.get('cie10_descripcion', '')}
8. Servicio(s) solicitado(s) y código: {datos.get('servicio_solicitado', '')}
9. Colocar requerimiento: {datos.get('requerimiento', '')}
10. Sustento de la solicitud: {datos.get('sustento', 'LIMITADA CAPACIDAD RESOLUTIVA')}
11. Institución que deriva/remite: HOSPITAL BASICO DEL CANTON PICHINCHA
12. Profesional que deriva/remite: DR RHONNIE DUARTE MORAN, MEDICO GENERAL
13. Institución que recibe / hace solicitud: {datos.get('inst_recibe', '')}
14. Profesional que acepta la derivación: {datos.get('prof_acepta', '')}
15. Número caso: {datos.get('numero_caso', '')}"""
    return texto


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
    
    # Detalles de Solicitud (Puntos 7 al 15)
    pdf.ln(4)
    pdf.set_fill_color(43, 108, 176)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, ' DETALLES DE LA SOLICITUD', ln=True, fill=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 9.5)
    
    # 7. Diagnóstico Principal y código CIE 10
    pdf.cell(75, 7, '7. Diagnóstico Principal y CIE-10:', border=1)
    pdf.cell(0, 7, f" {datos.get('cie10_codigo', '')} - {datos.get('cie10_descripcion', '')}", border=1, ln=True)
    
    # 8. Servicio(s) solicitado(s) con su respectivo código
    serv_texto = f"{datos.get('servicio_solicitado', '')}"
    if datos.get('codigo_servicio'):
        serv_texto += f" (CÓD: {datos.get('codigo_servicio')})"
    pdf.cell(75, 7, '8. Servicio(s) solicitado(s) y código:', border=1)
    pdf.cell(0, 7, f" {serv_texto.upper()}", border=1, ln=True)
    
    # 9. Colocar requerimiento
    pdf.cell(75, 7, '9. Colocar requerimiento:', border=1)
    pdf.cell(0, 7, f" {datos.get('requerimiento', 'VALORACIÓN Y MANEJO POR ESPECIALIDAD')}", border=1, ln=True)
    
    # 10. Sustento de la solicitud
    pdf.cell(75, 7, '10. Sustento de la solicitud:', border=1)
    pdf.cell(0, 7, f" {datos.get('sustento', 'LIMITADA CAPACIDAD RESOLUTIVA')}", border=1, ln=True)
    
    # 11. Institución que deriva/remite
    pdf.cell(75, 7, '11. Institución que deriva/remite:', border=1)
    pdf.cell(0, 7, ' HOSPITAL BASICO DEL CANTON PICHINCHA', border=1, ln=True)
    
    # 12. Profesional que deriva/remite
    pdf.cell(75, 7, '12. Profesional que deriva/remite:', border=1)
    pdf.cell(0, 7, ' DR RHONNIE DUARTE MORAN, MEDICO GENERAL', border=1, ln=True)
    
    # 13. Institución que recibe y hace la solicitud
    pdf.cell(75, 7, '13. Institución que recibe / hace solicitud:', border=1)
    pdf.cell(0, 7, f" {datos.get('inst_recibe', '')}", border=1, ln=True)
    
    # 14. Profesional que acepta la derivación
    pdf.cell(75, 7, '14. Profesional que acepta la derivación:', border=1)
    pdf.cell(0, 7, f" {datos.get('prof_acepta', '')}", border=1, ln=True)
    
    # 15. Número caso
    pdf.cell(75, 7, '15. Número caso:', border=1)
    pdf.cell(0, 7, f" {datos.get('numero_caso', '')}", border=1, ln=True)
    
    # Firmas
    pdf.ln(18)
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

archivos = st.file_uploader("Selecciona o arrastra las capturas del sistema (filiación, evolución, etc.)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

if archivos:
    if st.button("🪄 Procesar y Consolidar Caso"):
        with st.spinner("La IA está analizando y unificando los datos..."):
            try:
                lista_bytes = [a.read() for a in archivos]
                datos_consolidados = extraer_datos_capturas_consolidadas(lista_bytes)
                st.session_state['historial_pacientes'].append(datos_consolidados)
                st.success("¡Caso procesado y consolidado con éxito!")
            except Exception as e:
                st.error(f"El servicio de IA está experimentando alta demanda. Por favor, presiona el botón nuevamente en unos segundos. Detalle: {e}")

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
        datos_actuales['servicio_solicitado'] = st.text_input("8. Servicio Solicitado", value=datos_actuales.get('servicio_solicitado', ''), key=f"serv_{paciente_sel_idx}")
        datos_actuales['requerimiento'] = st.text_input("9. Colocar Requerimiento", value=datos_actuales.get('requerimiento', 'VALORACIÓN Y MANEJO POR ESPECIALIDAD'), key=f"req_{paciente_sel_idx}")
        datos_actuales['inst_recibe'] = st.text_input("13. Institución que recibe", value=datos_actuales.get('inst_recibe', ''), key=f"ir_{paciente_sel_idx}")

    with col2:
        datos_actuales['sexo'] = st.text_input("Sexo", value=datos_actuales.get('sexo', ''), key=f"sx_{paciente_sel_idx}")
        datos_actuales['edad'] = st.text_input("Edad", value=datos_actuales.get('edad', ''), key=f"ed_{paciente_sel_idx}")
        datos_actuales['cie10_codigo'] = st.text_input("Código CIE-10", value=datos_actuales.get('cie10_codigo', ''), key=f"cie_{paciente_sel_idx}")
        datos_actuales['cie10_descripcion'] = st.text_input("7. Descripción CIE-10", value=datos_actuales.get('cie10_descripcion', ''), key=f"cied_{paciente_sel_idx}")
        datos_actuales['prof_acepta'] = st.text_input("14. Profesional que acepta", value=datos_actuales.get('prof_acepta', ''), key=f"pa_{paciente_sel_idx}")
        datos_actuales['numero_caso'] = st.text_input("15. Número caso", value=datos_actuales.get('numero_caso', ''), key=f"nc_{paciente_sel_idx}")
        
    datos_actuales['cuadro_clinico_texto'] = st.text_area("6. Cuadro Clínico (Consolidado)", value=datos_actuales.get('cuadro_clinico_texto', ''), height=150, key=f"cc_{paciente_sel_idx}")
    
    # --- MOSTRAR CUADRO DE TEXTO PARA COPIAR A WHATSAPP ---
    st.markdown("---")
    st.subheader("📱 Texto Formateado para WhatsApp")
    st.write("Haz clic en el icono de **Copiar** (arriba a la derecha del cuadro negro) y pégalo directamente en WhatsApp:")
    texto_wa = generar_texto_whatsapp(datos_actuales)
    st.code(texto_wa, language="markdown")
    st.markdown("---")

    pdf_bytes = generar_pdf_fpdf(datos_actuales)
    
    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        st.download_button(
            label=f"📥 Descargar PDF Anexo 4 ({datos_actuales.get('cedula', 'paciente')})",
            data=bytes(pdf_bytes),
            file_name=f"Anexo_4_{datos_actuales.get('cedula', 'paciente')}.pdf",
            mime="application/pdf",
            key=f"dl_{paciente_sel_idx}"
        )
    with col_btn2:
        if st.button("🗑️ Limpiar Pacientes"):
            st.session_state['historial_pacientes'] = []
            st.rerun()
