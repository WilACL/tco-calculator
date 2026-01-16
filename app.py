import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
from fpdf import FPDF
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO
# ==========================================
st.set_page_config(page_title="TCO Crystal Box - EP Equipment", page_icon="🚜", layout="wide")

# Estilos CSS personalizados para parecer una App Nativa
st.markdown("""
    <style>
    .main {background-color: #f5f5f5;}
    .stButton>button {width: 100%; border-radius: 5px; height: 3em; background-color: #FF0000; color: white;}
    .metric-card {background-color: white; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);}
    h1 {color: #cc0000;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. BASE DE CONOCIMIENTO (Igual que en Colab)
# ==========================================
CONSTANTS = {
    'IVA': 0.19,
    'COP_kWh': 920.0,
    'COP_Diesel_gal': 11000.0,
    'COP_Gasolina_gal': 16500.0,
    'COP_GLP_kg': 6000.0
}

TECH_DB = {
    1.8: {'EP': 4.2, 'Diesel': 0.75, 'LPG': 1.6, 'Gasolina': 0.9},
    2.5: {'EP': 4.8, 'Diesel': 0.90, 'LPG': 2.1, 'Gasolina': 1.1},
    3.0: {'EP': 5.1, 'Diesel': 1.05, 'LPG': 2.4, 'Gasolina': 1.25},
    3.5: {'EP': 5.8, 'Diesel': 1.20, 'LPG': 2.8, 'Gasolina': 1.40},
    5.0: {'EP': 9.2, 'Diesel': 1.60, 'LPG': 3.5, 'Gasolina': 1.90},
    7.0: {'EP': 14.5,'Diesel': 2.20, 'LPG': 4.8, 'Gasolina': 2.60},
    10.0:{'EP': 19.5,'Diesel': 3.10, 'LPG': 6.5, 'Gasolina': 3.80}
}

# ==========================================
# 3. LÓGICA DE ESTADO (SESSION STATE)
# ==========================================
# Esto permite que al cambiar la capacidad, se actualicen los inputs automáticamente
if 'first_load' not in st.session_state:
    st.session_state.update(TECH_DB[3.0]) # Cargar 3.0T por defecto
    st.session_state.first_load = False

def actualizar_presets():
    cap = st.session_state.capacidad_selector
    vals = TECH_DB[cap]
    st.session_state.cons_ep = vals['EP']
    st.session_state.cons_diesel = vals['Diesel']
    st.session_state.cons_lpg = vals['LPG']
    st.session_state.cons_gaso = vals['Gasolina']

# ==========================================
# 4. INTERFAZ DE USUARIO (SIDEBAR + TABS)
# ==========================================

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/1200px-Python-logo-notext.svg.png", width=50) # Placeholder logo
    st.title("Parámetros Cliente")
    cliente = st.text_input("Nombre Cliente", "Empresa SAS")
    ciudad = st.selectbox("Ciudad Operación", ['Cali', 'Bogotá', 'Medellín', 'Barranquilla'])
    
    # Selector con Callback
    capacidad = st.selectbox("Capacidad Equipo (T)", options=list(TECH_DB.keys()), index=2, key='capacidad_selector', on_change=actualizar_presets)
    
    st.divider()
    turnos = st.radio("Intensidad", ["1 Turno", "2 Turnos", "3 Turnos"], index=1)
    horas_base = 1800 if turnos == "1 Turno" else (3600 if turnos == "2 Turnos" else 5400)
    horas_ano = st.slider("Horas/Año", 1000, 8000, horas_base, 100)
    anios = st.slider("Años Proyecto", 2, 10, 5)

st.title("🚜 Calculadora TCO Crystal Box")
st.markdown("Comparativa financiera: **Litio EP Equipment** vs **Combustión Interna**")

# TABS PRINCIPALES
tab1, tab2, tab3 = st.tabs(["💰 Costos & Energía", "🛠️ Equipos & Mtto", "📊 Reporte Ejecutivo"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Tarifas Energía (Editables)")
        p_elec = st.number_input("Electricidad ($/kWh)", value=CONSTANTS['COP_kWh'])
        p_diesel = st.number_input("Diesel ($/gal)", value=CONSTANTS['COP_Diesel_gal'])
        p_glp = st.number_input("GLP ($/kg)", value=CONSTANTS['COP_GLP_kg'])
        p_gaso = st.number_input("Gasolina ($/gal)", value=CONSTANTS['COP_Gasolina_gal'])
    
    with col2:
        st.info("💡 Nota: Las tarifas de electricidad están basadas en promedios industriales no regulados (Celsia/Emcali 2026).")

with tab2:
    st.subheader("Datos Técnicos (VDI 2198)")
    c1, c2, c3, c4 = st.columns(4)
    
    # Inputs vinculados al Session State (key=...)
    with c1:
        st.markdown("**EP (Litio)**")
        capex_ep = st.number_input("Precio ($)", value=135000000.0, step=1000000.0, format="%.0f")
        cons_ep = st.number_input("Consumo (kWh/h)", key='cons_ep')
        mtto_ep = st.number_input("Mtto Mensual ($)", value=150000)
        llantas_ep = st.number_input("Llantas (Año)", value=2000000)
        salv_ep = st.number_input("% Salvamento", value=25)
        
    with c2:
        st.markdown("**Diesel**")
        capex_diesel = st.number_input("Precio ($) ", value=110000000.0, step=1000000.0, format="%.0f", key="p_d")
        cons_diesel = st.number_input("Consumo (Gal/h)", key='cons_diesel')
        mtto_ic = st.number_input("Mtto Mensual ($) ", value=450000, key="m_ic") # Compartido
        llantas_ic = st.number_input("Llantas (Año) ", value=3500000, key="l_ic") # Compartido
        salv_ic = st.number_input("% Salvamento ", value=15, key="s_ic") # Compartido

    with c3:
        st.markdown("**GLP**")
        capex_lpg = st.number_input("Precio ($)", value=105000000.0, step=1000000.0, format="%.0f")
        cons_lpg = st.number_input("Consumo (Kg/h)", key='cons_lpg')
    
    with c4:
        st.markdown("**Gasolina**")
        capex_gaso = st.number_input("Precio ($)", value=100000000.0, step=1000000.0, format="%.0f")
        cons_gaso = st.number_input("Consumo (Gal/h)", key='cons_gaso')

# ==========================================
# 5. CÁLCULOS
# ==========================================
horas_totales = horas_ano * anios
meses_totales = anios * 12

def calcular_linea(capex, consumo, precio_energia, mtto_mes, llantas_ano, salv_pct):
    capex_iva = capex * 1.19
    opex_energ = consumo * precio_energia * horas_totales
    opex_mtto = (mtto_mes * meses_totales) + (llantas_ano * anios)
    recuperacion = capex * (salv_pct / 100)
    tco = capex_iva + opex_energ + opex_mtto - recuperacion
    return capex_iva, opex_energ, opex_mtto, recuperacion, tco

# Ejecutar cálculos
res_ep = calcular_linea(capex_ep, cons_ep, p_elec, mtto_ep, llantas_ep, salv_ep)
res_di = calcular_linea(capex_diesel, cons_diesel, p_diesel, mtto_ic, llantas_ic, salv_ic)
res_gl = calcular_linea(capex_lpg, cons_lpg, p_glp, mtto_ic, llantas_ic, salv_ic)
res_ga = calcular_linea(capex_gaso, cons_gaso, p_gaso, mtto_ic, llantas_ic, salv_ic)

df = pd.DataFrame({
    'Tecnología': ['EP Litio', 'Diesel', 'GLP', 'Gasolina'],
    'Inversión (CAPEX)': [res_ep[0], res_di[0], res_gl[0], res_ga[0]],
    'Energía': [res_ep[1], res_di[1], res_gl[1], res_ga[1]],
    'Mantenimiento': [res_ep[2], res_di[2], res_gl[2], res_ga[2]],
    'Salvamento (-)': [-res_ep[3], -res_di[3], -res_gl[3], -res_ga[3]],
    'TCO Neto': [res_ep[4], res_di[4], res_gl[4], res_ga[4]]
}).set_index('Tecnología')

ahorro_vs_diesel = res_di[4] - res_ep[4]

# ==========================================
# 6. VISUALIZACIÓN
# ==========================================
with tab3:
    st.subheader(f"Resultados: {cliente}")
    
    # Métricas KPI
    k1, k2, k3 = st.columns(3)
    k1.metric("TCO EP Equipment", f"${res_ep[4]/1e6:,.1f} M")
    k2.metric("TCO Diesel", f"${res_di[4]/1e6:,.1f} M")
    k3.metric("AHORRO PROYECTADO", f"${ahorro_vs_diesel/1e6:,.1f} M", delta_color="normal")
    
    if ahorro_vs_diesel > 0:
        st.success(f"✅ **Viabilidad Confirmada:** La tecnología EP genera un ahorro de **${ahorro_vs_diesel:,.0f} COP** en {anios} años.")

    # Gráfico
    fig, ax = plt.subplots(figsize=(10, 5))
    tecs = df.index
    
    # Barras
    ax.bar(tecs, df['Inversión (CAPEX)'], label='Inversión', color='#1f77b4')
    ax.bar(tecs, df['Energía'], bottom=df['Inversión (CAPEX)'], label='Energía', color='#ff7f0e')
    ax.bar(tecs, df['Mantenimiento'], bottom=df['Inversión (CAPEX)']+df['Energía'], label='Mtto', color='#2ca02c')
    
    # Línea TCO
    ax.plot(tecs, df['TCO Neto'], color='black', marker='o', linestyle='--', linewidth=2, label='TCO Neto')
    
    # Anotación Ahorro
    if ahorro_vs_diesel > 0:
        ax.annotate(f"Ahorro: ${ahorro_vs_diesel/1e6:.1f}M", 
                    xy=(1, res_di[4]), xytext=(0, 20), textcoords='offset points',
                    ha='center', color='green', fontweight='bold',
                    arrowprops=dict(arrowstyle='->', color='green'))

    ax.set_ylabel("Millones de COP")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,.0f}M".format(x/1e6)))
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    
    st.pyplot(fig)
    
    st.dataframe(df.style.format("${:,.0f}"))

# ==========================================
# 7. GENERADOR PDF
# ==========================================
def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Analisis TCO Crystal Box: {cliente}", 0, 1, 'C')
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, f"Generado el: {datetime.now().strftime('%Y-%m-%d')} | Ciudad: {ciudad}", 0, 1, 'C')
    
    # Guardar gráfico en memoria
    img_data = io.BytesIO()
    fig.savefig(img_data, format='png')
    img_data.seek(0)
    
    # FPDF necesita un archivo físico temporal desgraciadamente, o un link. 
    # Workaround simple: guardar temp
    with open("temp_chart.png", "wb") as f:
        f.write(img_data.getbuffer())
        
    pdf.image("temp_chart.png", x=10, y=30, w=190)
    
    pdf.set_y(140)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Resumen Ejecutivo (Millones COP)", 0, 1)
    pdf.set_font("Arial", size=11)
    
    pdf.cell(0, 8, f"Inversion Inicial EP: ${res_ep[0]/1e6:,.1f} M", 0, 1)
    pdf.cell(0, 8, f"Gasto Energia 5 Anios (EP): ${res_ep[1]/1e6:,.1f} M", 0, 1)
    pdf.cell(0, 8, f"Gasto Energia 5 Anios (Diesel): ${res_di[1]/1e6:,.1f} M", 0, 1)
    
    pdf.set_text_color(0, 150, 0)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 15, f"AHORRO TOTAL: ${ahorro_vs_diesel/1e6:,.1f} Millones", 0, 1)
    
    return pdf.output(dest='S').encode('latin-1')

st.sidebar.markdown("---")
pdf_bytes = create_pdf()
st.sidebar.download_button(
    label="📥 Descargar Informe PDF",
    data=pdf_bytes,
    file_name=f"TCO_{cliente}.pdf",
    mime="application/pdf"
)
