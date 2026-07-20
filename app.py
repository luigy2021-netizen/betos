from __future__ import annotations

from datetime import datetime, time
from urllib.parse import quote
from zoneinfo import ZoneInfo

import base64
import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Beto's | Flautas & Asada", page_icon="🌮", layout="wide", initial_sidebar_state="collapsed")

TZ = ZoneInfo("America/Ojinaga")
HEADERS = ["Fecha y hora", "Folio", "Nombre del cliente", "Teléfono", "Pedido", "Total", "Fecha de recogida", "Hora de recogida", "Notas", "Forma de pago", "Estado"]
PRODUCTS = {
    "Flautas": [
        ("Flauta de carne", 45, "Crujiente, sabrosa y hecha con orgullo"),
        ("Flauta de papa", 40, "Dorada al momento"),
        ("Soda", 29, ""), ("Cueritos", 10, ""), ("Guacamole extra", 10, ""),
        ("Salsa extra", 10, ""), ("Crema extra", 10, ""),
    ],
    "Carne asada": [
        ("1 kg de carne asada", 400, "Papa, cebolla, tortillas y chiles toreados"),
        ("½ kg de carne asada", 250, "Papa, cebolla, tortillas y chiles toreados"),
        ("Platillo individual", 150, "250 g de carne, papa, cebolla, tortillas y chiles"),
        ("1 kg de costilla", 300, "Papa, cebolla, tortillas y salsas"),
        ("½ kg de costilla", 200, "Papa, cebolla, tortillas y salsa"),
        ("Platillo individual de costilla", 120, "250 g con papa, cebolla, tortillas y chiles"),
        ("Soda", 29, ""),
    ],
}

def image_b64(path: str) -> str:
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()


logo_b64 = image_b64("public/brand/betos-logo.png")
flautas_b64 = image_b64("public/brand/plato-flautas.png")
asada_b64 = image_b64("public/brand/plato-carne-asada.png")
portada_b64 = image_b64("public/brand/portada-betos.png")
kroniq_b64 = image_b64("public/brand/kroniq-logo.png")

styles = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700;800&family=Oswald:wght@500;600;700&display=swap');
:root{--red:#981b16;--gold:#e7a833;--cream:#fff7e7;--ink:#1b1712}.stApp{background:#fffaf0;color:var(--ink)}
.block-container{max-width:1120px;padding-top:1.2rem;padding-bottom:6rem}[data-testid="stHeader"]{background:transparent}
h1,h2,h3{font-family:'Oswald',sans-serif!important;text-transform:uppercase}p,div,label,input,textarea,button{font-family:'DM Sans',sans-serif}
.brandbar{display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem}.brandbar img{width:160px;height:160px;object-fit:contain}
.pickup-chip{padding:.65rem 1rem;border:1px solid #d9c9aa;border-radius:999px;font-weight:800;background:#fff}
.hero{min-height:520px;border-radius:18px;display:flex;align-items:center;overflow:hidden;background-image:url('data:image/png;base64,PORTADA_BG');background-position:center;background-size:cover;background-repeat:no-repeat}
.hero-copy{width:58%;padding:3.2rem;display:flex;flex-direction:column;justify-content:center;color:#fff8e8}.eyebrow{color:var(--gold);font-size:.78rem;font-weight:800;letter-spacing:.16em;text-transform:uppercase}
.hero h1{font-size:clamp(3.2rem,7vw,6.2rem);line-height:.88;margin:.6rem 0 1.3rem;letter-spacing:-.03em}.hero h1 span{color:var(--gold)}.hero p{font-size:1.05rem;line-height:1.6;max-width:520px;color:#efe3ce}
.section-title{margin:4.5rem 0 1rem}.section-title h2{font-size:3rem;margin:.2rem 0}.schedule{background:#efe3ca;border-radius:10px;padding:.85rem 1rem;margin-bottom:1rem}
div[data-testid="stNumberInput"]{background:#fff;border-radius:10px;padding:.5rem .8rem;border:1px solid #e1d4bc}div[data-testid="stForm"]{background:#fff;border:1px solid #dfd1b8;border-radius:16px;padding:1.4rem}
.events{margin-top:4rem;border-radius:16px;padding:3rem;color:white;background:linear-gradient(100deg,rgba(13,18,9,.93),rgba(26,43,14,.42)),url('data:image/png;base64,ASADA_BG') center 62%/cover}.events h2{font-size:3rem;max-width:600px;margin:.5rem 0 1rem}.events p{max-width:600px;line-height:1.6}
.total-box{background:#201a14;color:white;border-radius:12px;padding:1.1rem 1.3rem;display:flex;justify-content:space-between;font-size:1.2rem;font-weight:900;margin:1rem 0}.total-box strong{color:#f1b43e;font-size:1.55rem}
.wa-link a{display:block;text-align:center;background:#217a3f;color:#fff!important;text-decoration:none;padding:1rem;border-radius:9px;font-weight:900}
.kroniq-ad{margin-top:4rem;padding:1.5rem 1.7rem;border-radius:16px;background:#050817;display:grid;grid-template-columns:210px 1fr auto;gap:1.6rem;align-items:center;color:#fff;border:1px solid #232b50;box-shadow:0 18px 45px rgba(13,18,45,.16)}.kroniq-ad img{width:100%;max-height:115px;object-fit:contain}.kroniq-ad h3{margin:0 0 .35rem;font-size:1.65rem;text-transform:none}.kroniq-ad p{margin:0;color:#c9cde0;line-height:1.5}.kroniq-ad a{display:inline-block;padding:.85rem 1.05rem;border-radius:9px;background:linear-gradient(90deg,#793dff,#00aee8);color:#fff!important;text-decoration:none;font-weight:800;white-space:nowrap}
@media(max-width:700px){.block-container{padding:1rem 1rem 5rem}.brandbar img{width:125px;height:125px}.pickup-chip{font-size:.72rem}.hero{min-height:520px;background-position:42% center}.hero-copy{width:72%;padding:2.2rem 1.3rem}.hero h1{font-size:3.25rem}.section-title h2,.events h2{font-size:2.4rem}.events{padding:2rem 1.3rem}.kroniq-ad{grid-template-columns:1fr;text-align:center}.kroniq-ad img{width:210px;margin:auto}.kroniq-ad a{white-space:normal}}
</style>
"""
st.markdown(styles.replace("FLAUTAS_BG", flautas_b64).replace("ASADA_BG", asada_b64).replace("PORTADA_BG", portada_b64), unsafe_allow_html=True)

@st.cache_resource
def get_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=scopes)
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(st.secrets["spreadsheet_id"]).get_worksheet(0)
    if sheet.row_values(1)[:len(HEADERS)] != HEADERS:
        sheet.update(values=[HEADERS], range_name="A1:K1")
    return sheet

def safe_cell(value: str) -> str:
    text = str(value or "").strip()
    return "'" + text if text.startswith(("=", "+", "-", "@")) else text

st.markdown(f'<div class="brandbar"><img src="data:image/png;base64,{logo_b64}" alt="Beto\'s"><div class="pickup-chip">📍 Oaxaca 2537 · Recoge en local</div></div>', unsafe_allow_html=True)
st.markdown("""<section class="hero"><div class="hero-copy"><div class="eyebrow">Sabor casero · Fuego y tradición</div><h1>Tu antojo,<br><span>listo para recoger.</span></h1><p>Elige tus favoritos, revisa el total y confirma tu pedido por WhatsApp. Pagas en efectivo al recoger.</p></div></section><div class="section-title"><div class="eyebrow">Ordena a tu gusto</div><h2>¿Qué se te antoja?</h2></div>""", unsafe_allow_html=True)
st.markdown('<div class="schedule"><b>Flautas:</b> jueves a domingo · 2–9 PM &nbsp; | &nbsp; <b>Carne asada:</b> sábado y domingo · 2–9 PM</div>', unsafe_allow_html=True)

if "last_order" not in st.session_state:
    st.session_state.last_order = None

with st.form("order_form", clear_on_submit=False):
    tabs = st.tabs(["🌮 Flautas", "🔥 Carne asada"])
    quantities = {}
    for tab, category in zip(tabs, PRODUCTS):
        with tab:
            image = "public/brand/plato-flautas.png" if category == "Flautas" else "public/brand/plato-carne-asada.png"
            left, right = st.columns([1.05, 1.6], vertical_alignment="top")
            with left:
                st.image(image, use_container_width=True)
            with right:
                for product_name, price, description in PRODUCTS[category]:
                    quantities[(category, product_name)] = st.number_input(f"{product_name} — ${price}", 0, 50, 0, 1, help=description or None, key=f"qty-{category}-{product_name}")

    st.markdown("### Datos para recoger")
    c1, c2 = st.columns(2)
    customer_name = c1.text_input("Nombre del cliente", max_chars=80)
    phone = c2.text_input("Teléfono (10 dígitos)", max_chars=14)
    c3, c4 = st.columns(2)
    pickup_date = c3.date_input("Fecha de recogida", min_value=datetime.now(TZ).date())
    pickup_time = c4.time_input("Hora de recogida", value=time(18, 0), step=900)
    notes = st.text_area("Notas (opcional)", max_chars=300, placeholder="Ej. sin salsa, bien doradas…")
    selected, total = [], 0
    for category, products in PRODUCTS.items():
        for product_name, price, _ in products:
            quantity = quantities[(category, product_name)]
            if quantity:
                selected.append((product_name, price, quantity))
                total += price * quantity
    st.markdown(f'<div class="total-box"><span>Total a pagar</span><strong>${total:,}</strong></div>', unsafe_allow_html=True)
    submitted = st.form_submit_button("Registrar pedido", type="primary", use_container_width=True)

if submitted:
    digits = "".join(ch for ch in phone if ch.isdigit())
    errors = []
    if not selected: errors.append("Agrega al menos un producto.")
    if len(customer_name.strip()) < 2: errors.append("Escribe el nombre del cliente.")
    if len(digits) != 10: errors.append("El teléfono debe tener 10 dígitos.")
    if not time(14, 0) <= pickup_time <= time(21, 0): errors.append("La hora debe ser entre 2:00 y 9:00 PM.")
    if errors:
        for error in errors: st.error(error)
    else:
        now = datetime.now(TZ)
        folio = f"BET-{now.strftime('%m%d%H%M%S')}"
        order_text = " | ".join(f"{qty} × {product}" for product, _, qty in selected)
        try:
            get_sheet().append_row([now.strftime("%d/%m/%Y %I:%M:%S %p"), folio, safe_cell(customer_name), digits, safe_cell(order_text), total, pickup_date.strftime("%d/%m/%Y"), pickup_time.strftime("%I:%M %p"), safe_cell(notes), "Efectivo", "Nuevo"], value_input_option="USER_ENTERED")
            lines = [f"• {qty} × {product} — ${price * qty:,}" for product, price, qty in selected]
            message = "\n".join(["¡Hola, Beto's! Quiero confirmar este pedido para recoger:", f"Folio: {folio}", f"Nombre: {customer_name.strip()}", f"Teléfono: {digits}", f"Recoger: {pickup_date.strftime('%d/%m/%Y')} a las {pickup_time.strftime('%I:%M %p')}", "", *lines, "", f"TOTAL: ${total:,}", "Pago: efectivo al recoger", "Lugar: Calle Oaxaca 2537", f"Notas: {notes.strip()}" if notes.strip() else "", "", "¿Me confirman el pedido?"])
            st.session_state.last_order = {"folio": folio, "url": f"https://wa.me/526561614536?text={quote(message)}"}
        except Exception:
            st.error("No se pudo registrar el pedido. Revisa la conexión con Google Sheets.")

if st.session_state.last_order:
    order = st.session_state.last_order
    st.success(f"Pedido {order['folio']} registrado en Google Sheets.")
    st.markdown(f'<div class="wa-link"><a href="{order["url"]}" target="_blank">Confirmar por WhatsApp</a></div>', unsafe_allow_html=True)

st.markdown("""<section class="events"><div class="eyebrow">Beto's va a tu evento</div><h2>El sabor que reúne a todos.</h2><p>¿Cumpleaños, reunión o evento especial? Cotizamos el servicio a domicilio según tus invitados y necesidades.</p></section>""", unsafe_allow_html=True)
st.link_button("Cotizar evento por WhatsApp", "https://wa.me/526561614536?text=Hola%2C%20quiero%20cotizar%20un%20evento%20a%20domicilio%20con%20Beto%27s.", use_container_width=True)

kroniq_url = "https://wa.me/526563079754?text=Hola%2C%20quiero%20informaci%C3%B3n%20sobre%20una%20agenda%20digital%20para%20mi%20negocio."
st.markdown(f"""<section class="kroniq-ad"><img src="data:image/png;base64,{kroniq_b64}" alt="Kroniq Booking"><div><h3>¿Tienes un negocio? ¿Quieres una agenda como esta?</h3><p>Automatiza tus citas o pedidos con una solución digital profesional creada por Kroniq.</p></div><a href="{kroniq_url}" target="_blank" rel="noopener noreferrer">Quiero información</a></section>""", unsafe_allow_html=True)
