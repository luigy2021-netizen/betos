from __future__ import annotations

import base64
from datetime import datetime, time, timedelta
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials


st.set_page_config(
    page_title="Beto's | Flautas & Asada",
    page_icon="🌮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

TZ = ZoneInfo("America/Ojinaga")
WHATSAPP_NUMBER = "526561614536"
ADDRESS_LINE_1 = "Calle Oaxaca #2537"
ADDRESS_LINE_2 = "Entre Henequén y Santiago Blancas"
GOOGLE_MAPS_URL = "https://www.google.com/maps/place/C.+Oaxaca+2537,+Eco+2000,+32574+Ju%C3%A1rez,+Chih./@31.6385404,-106.3841634,15z/data=!4m6!3m5!1s0x86e76791d9de6b7f:0xb1a490fa09e0c37b!8m2!3d31.6369682!4d-106.3780037!16s%2Fg%2F11mtdjfy39?entry=ttu&g_ep=EgoyMDI2MDcyNy4wIKXMDSoASAFQAw%3D%3D"
BANK_NAME = "Banco Azteca"
BANK_CARD = "4198 2101 9694 6056"

HEADERS = [
    "Fecha y hora",
    "Folio",
    "Nombre del cliente",
    "Teléfono",
    "Pedido",
    "Total",
    "Fecha de recogida",
    "Hora estimada listo",
    "Notas",
    "Forma de pago",
    "Estado",
]

PRODUCTS = {
    "Flautas Beto's": [
        ("Flauta de carne", 45, "Crujiente, sabrosa y hecha con orgullo"),
        ("Flauta de papa", 40, "Dorada al momento"),
        ("Cueritos", 10, ""),
        ("Guacamole extra", 10, ""),
        ("Salsa extra", 10, ""),
        ("Crema extra", 10, ""),
        ("Soda Coca-Cola", 25, ""),
        ("Soda Sprite", 25, ""),
        ("Soda Dr Pepper", 25, ""),
        ("Soda Manzana", 25, ""),
    ],
    "Carne Asada Beto's": [
        ("1 kg de carne asada", 400, "Papa, cebolla, tortillas y chiles toreados"),
        ("½ kg de carne asada", 250, "Papa, cebolla, tortillas y chiles toreados"),
        ("Platillo individual", 150, "250 g de carne, papa, cebolla, tortillas y chiles"),
        ("1 kg de costilla", 300, "Papa, cebolla, tortillas y salsas"),
        ("½ kg de costilla", 200, "Papa, cebolla, tortillas y salsa"),
        ("Platillo individual de costilla", 120, "250 g con papa, cebolla, tortillas y chiles"),
        ("Soda Coca-Cola", 25, ""),
        ("Soda Sprite", 25, ""),
        ("Soda Dr Pepper", 25, ""),
        ("Soda Manzana", 25, ""),
    ],
}

SCHEDULES = {
    "Flautas Beto's": {
        "days": {3, 4, 5, 6},
        "days_text": "Jueves a Domingo",
        "hours_text": "2:00 PM a 9:00 PM",
        "open": time(14, 0),
        "close": time(21, 0),
    },
    "Carne Asada Beto's": {
        "days": {5, 6},
        "days_text": "Sábado y Domingo",
        "hours_text": "2:00 PM a 8:00 PM",
        "open": time(14, 0),
        "close": time(20, 0),
    },
}


def find_asset(*candidates: str) -> Path:
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return path
    raise FileNotFoundError(f"No se encontró el recurso: {candidates[0]}")


def image_b64(*candidates: str) -> str:
    with find_asset(*candidates).open("rb") as image_file:
        return base64.b64encode(image_file.read()).decode()


def optional_image_b64(*candidates: str) -> str:
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            with path.open("rb") as image_file:
                return base64.b64encode(image_file.read()).decode()
    return ""


logo_b64 = image_b64("public/brand/betos-logo.png", "beto's-logo.png")
carne_logo_b64 = optional_image_b64(
    "public/brand/logo-carne-asada.png",
    "public/brand/logo carne asada.png",
    "logo carne asada.png",
)
carne_logo_markup = (
    f'<img class="choice-logo" src="data:image/png;base64,{carne_logo_b64}" alt="Carne Asada Beto\'s">'
    if carne_logo_b64
    else '<div class="missing-logo">Sube logo-carne-asada.png a public/brand/</div>'
)
flautas_b64 = image_b64("public/brand/plato-flautas.png", "Plato-flautas.png")
asada_b64 = image_b64(
    "public/brand/plato-carne-asada.png",
    "plato.carne-asada.png",
)
events_b64 = image_b64(
    "public/brand/eventos-familia-betos.png",
    "public/brand/reunion.png",
    "eventos-familia-betos.png",
    "reunion.png",
    "public/brand/plato-carne-asada.png",
    "plato.carne-asada.png",
)
kroniq_b64 = image_b64("public/brand/kroniq-logo.png", "kroniq-logo.png")

styles = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700;800&family=Oswald:wght@500;600;700&display=swap');
:root{--red:#981b16;--gold:#e7a833;--cream:#fff7e7;--ink:#1b1712;--green:#217a3f}
.stApp{background:#fffaf0;color:var(--ink)}
.block-container{max-width:1120px;padding-top:1rem;padding-bottom:6rem}
[data-testid="stHeader"]{background:transparent}
h1,h2,h3{font-family:'Oswald',sans-serif!important;text-transform:uppercase}
p,div,label,input,textarea,button{font-family:'DM Sans',sans-serif}
.brandbar{display:flex;align-items:center;justify-content:space-between;gap:1rem;margin-bottom:.8rem}
.brandbar img{width:145px;height:145px;object-fit:contain}
.pickup-chip{padding:.7rem 1rem;border:1px solid #d9c9aa;border-radius:999px;font-weight:800;background:#fff;text-align:center}
.welcome{border-radius:20px;padding:clamp(2rem,6vw,5rem);color:#fff8e8;background:linear-gradient(115deg,rgba(22,12,8,.96),rgba(61,18,12,.78)),url('data:image/png;base64,FLAUTAS_BG') center 55%/cover;box-shadow:0 18px 50px rgba(76,33,15,.18)}
.welcome .eyebrow,.events .eyebrow{color:var(--gold)}
.welcome h1{font-size:clamp(3.2rem,8vw,7rem);line-height:.88;letter-spacing:-.035em;margin:.6rem 0 1.2rem;max-width:900px}
.welcome h1 span{color:var(--gold)}
.welcome p{font-size:clamp(1rem,2vw,1.25rem);line-height:1.6;max-width:650px;color:#f3e6d2}
.eyebrow{color:var(--red);font-size:.78rem;font-weight:800;letter-spacing:.16em;text-transform:uppercase}
.choice-title{text-align:center;margin:3.7rem 0 1.3rem}
.choice-title h2{font-size:clamp(2.5rem,6vw,4.5rem);margin:.25rem 0}
.choice-card{border:2px solid #d8c6a6;border-radius:16px;padding:1.5rem;background:#fff;margin-bottom:.8rem;min-height:430px;display:flex;flex-direction:column;justify-content:center}
.choice-card h3{font-size:2rem;margin:.2rem 0 .8rem}
.choice-card p{margin:.3rem 0;line-height:1.5}
.choice-card strong{color:var(--red)}
.choice-logo{width:min(90%,290px);height:185px;object-fit:contain;display:block;margin:0 auto 1.25rem}
.missing-logo{margin:0 auto 1.25rem;padding:1rem;border:2px dashed #bda987;border-radius:10px;text-align:center;font-weight:800;color:#7d291f}
div.stButton>button{min-height:58px;border-radius:9px;font-weight:900;font-size:1.05rem}
.active-choice{border-color:var(--red);box-shadow:0 0 0 3px rgba(152,27,22,.12)}
.selected-banner{margin:1.1rem 0;padding:1rem 1.2rem;border-radius:10px;background:#efe3ca;font-weight:800}
div[data-testid="stNumberInput"]{background:#fff;border-radius:10px;padding:.5rem .8rem;border:1px solid #e1d4bc}
div[data-testid="stForm"]{background:#fff;border:1px solid #dfd1b8;border-radius:16px;padding:1.4rem}
.ready-box{background:#f4ead4;border-left:5px solid var(--gold);border-radius:8px;padding:1rem 1.1rem;margin:.7rem 0 1.2rem}
.ready-box strong{display:block;color:var(--red);font-size:1.3rem;margin-top:.25rem}
.pending-note{background:#fff4d7;border:1px solid #e5ca7a;border-radius:9px;padding:.9rem 1rem;margin:1rem 0;line-height:1.5}
.total-box{background:#201a14;color:white;border-radius:12px;padding:1.1rem 1.3rem;display:flex;justify-content:space-between;font-size:1.2rem;font-weight:900;margin:1rem 0}
.total-box strong{color:#f1b43e;font-size:1.55rem}
.wa-link a{display:block;text-align:center;background:var(--green);color:#fff!important;text-decoration:none;padding:1rem;border-radius:9px;font-weight:900}
.location{margin:4rem 0 0;padding:2rem;border:1px solid #dfd1b8;border-radius:16px;background:#fff;display:flex;justify-content:space-between;gap:2rem;align-items:center}
.location h2{font-size:2.3rem;margin:.2rem 0 .8rem}.location p{margin:.2rem 0;font-size:1.05rem}
.events{margin-top:2rem;border-radius:16px;padding:clamp(2rem,5vw,4rem);color:white;background:linear-gradient(100deg,rgba(13,18,9,.94),rgba(26,43,14,.48)),url('data:image/png;base64,EVENTS_BG') center 52%/cover}
.events h2{font-size:clamp(2.6rem,6vw,4.5rem);max-width:700px;margin:.5rem 0 1rem}
.events p{max-width:760px;line-height:1.65}.event-list{font-weight:800;color:#fff}
.events a{display:inline-block;margin-top:1rem;padding:1rem 1.25rem;border-radius:9px;background:#fff;color:#18200f!important;text-decoration:none;font-weight:900}
.kroniq-ad{margin-top:4rem;padding:1.5rem 1.7rem;border-radius:16px;background:#050817;display:grid;grid-template-columns:210px 1fr auto;gap:1.6rem;align-items:center;color:#fff;border:1px solid #232b50}
.kroniq-ad img{width:100%;max-height:115px;object-fit:contain}.kroniq-ad h3{margin:0 0 .35rem;font-size:1.65rem;text-transform:none}
.kroniq-ad p{margin:0;color:#c9cde0;line-height:1.5}.kroniq-ad a{display:inline-block;padding:.85rem 1.05rem;border-radius:9px;background:linear-gradient(90deg,#793dff,#00aee8);color:#fff!important;text-decoration:none;font-weight:800;white-space:nowrap}
@media(max-width:700px){
 .block-container{padding:1rem .85rem 5rem}.brandbar img{width:112px;height:112px}.pickup-chip{font-size:.72rem;padding:.55rem .7rem}
 .welcome{padding:2.2rem 1.2rem;min-height:510px;display:flex;flex-direction:column;justify-content:center;background-position:58% center}
 .welcome h1{font-size:3.5rem}.choice-title{margin-top:3rem}.choice-card{min-height:380px;padding:1rem}
 .choice-card h3{font-size:1.7rem}.choice-logo{width:240px;height:155px}.location{display:block;padding:1.4rem}.events{padding:2.2rem 1.2rem}
 .kroniq-ad{grid-template-columns:1fr;text-align:center}.kroniq-ad img{width:210px;margin:auto}.kroniq-ad a{white-space:normal}
 div[data-testid="stForm"]{padding:1rem}.stHorizontalBlock{flex-wrap:wrap}.stHorizontalBlock>div{min-width:100%}
}
</style>
"""

st.markdown(
    styles.replace("FLAUTAS_BG", flautas_b64)
    .replace("ASADA_BG", asada_b64)
    .replace("EVENTS_BG", events_b64),
    unsafe_allow_html=True,
)


@st.cache_resource
def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=scopes,
    )
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(st.secrets["spreadsheet_id"]).get_worksheet(0)
    current_headers = sheet.row_values(1)
    if not current_headers:
        sheet.update(values=[HEADERS], range_name="A1:K1")
    return sheet


def safe_cell(value: str) -> str:
    text = str(value or "").strip()
    return "'" + text if text.startswith(("=", "+", "-", "@")) else text


def ready_datetime(pickup_date, selected_time: time) -> datetime:
    selected_datetime = datetime.combine(pickup_date, selected_time, tzinfo=TZ)
    return selected_datetime + timedelta(minutes=20)


if "order_category" not in st.session_state:
    st.session_state.order_category = "Flautas Beto's"
if "last_order" not in st.session_state:
    st.session_state.last_order = None

st.markdown(
    f"""
    <div class="brandbar">
      <img src="data:image/png;base64,{logo_b64}" alt="Beto's">
      <div class="pickup-chip">📍 Oaxaca #2537 · Recoge en local</div>
    </div>
    <section class="welcome">
      <div class="eyebrow">Beto's · Sabor casero, fuego y tradición</div>
      <h1>El sabor que<br><span>reúne a todos</span></h1>
      <p>Flautas doradas y carne asada preparadas para compartir. Elige lo que se te antoja y arma tu pedido.</p>
    </section>
    <div class="choice-title">
      <div class="eyebrow">Elige tu menú</div>
      <h2>¿Qué se te antoja hoy?</h2>
    </div>
    """,
    unsafe_allow_html=True,
)

choice_left, choice_right = st.columns(2)
with choice_left:
    active_class = " active-choice" if st.session_state.order_category == "Flautas Beto's" else ""
    st.markdown(
        f"""
        <div class="choice-card{active_class}">
          <img class="choice-logo" src="data:image/png;base64,{logo_b64}" alt="Flautas Beto's">
          <div class="eyebrow">Opción 1</div>
          <h3>Flautas Beto's</h3>
          <p><strong>Horario</strong></p>
          <p>Jueves a Domingo<br>2:00 PM a 9:00 PM</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Elegir Flautas Beto's", use_container_width=True, type="primary"):
        st.session_state.order_category = "Flautas Beto's"
        st.session_state.last_order = None
        st.rerun()

with choice_right:
    active_class = " active-choice" if st.session_state.order_category == "Carne Asada Beto's" else ""
    st.markdown(
        f"""
        <div class="choice-card{active_class}">
          {carne_logo_markup}
          <div class="eyebrow">Opción 2</div>
          <h3>Carne Asada Beto's</h3>
          <p><strong>Horario</strong></p>
          <p>Sábado y Domingo<br>2:00 PM a 8:00 PM</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Elegir Carne Asada Beto's", use_container_width=True, type="primary"):
        st.session_state.order_category = "Carne Asada Beto's"
        st.session_state.last_order = None
        st.rerun()

category = st.session_state.order_category
schedule = SCHEDULES[category]
category_image = (
    find_asset("public/brand/plato-flautas.png", "Plato-flautas.png")
    if category == "Flautas Beto's"
    else find_asset("public/brand/plato-carne-asada.png", "plato.carne-asada.png")
)

st.markdown(
    f'<div class="selected-banner">Seleccionaste: {category} · {schedule["days_text"]} · {schedule["hours_text"]}</div>',
    unsafe_allow_html=True,
)

with st.form("order_form", clear_on_submit=False):
    st.markdown(f"## Menú de {category}")
    menu_left, menu_right = st.columns([1.05, 1.6], vertical_alignment="top")
    quantities = {}
    with menu_left:
        st.image(category_image, use_container_width=True)
    with menu_right:
        for product_name, price, description in PRODUCTS[category]:
            quantities[product_name] = st.number_input(
                f"{product_name} — ${price}",
                min_value=0,
                max_value=50,
                value=0,
                step=1,
                help=description or None,
                key=f"qty-{category}-{product_name}",
            )

    st.markdown("### Datos para recoger")
    c1, c2 = st.columns(2)
    customer_name = c1.text_input("Nombre del cliente", max_chars=80)
    phone = c2.text_input("Teléfono (10 dígitos)", max_chars=14)
    c3, c4 = st.columns(2)
    pickup_date = c3.date_input(
        "Fecha de recogida",
        min_value=datetime.now(TZ).date(),
    )
    selected_time = c4.time_input(
        "Hora estimada en que estará listo el pedido",
        value=time(18, 0),
        step=900,
        help="El sistema agregará automáticamente 20 minutos a la hora seleccionada.",
    )

    calculated_ready = ready_datetime(pickup_date, selected_time)
    st.markdown(
        f"""
        <div class="ready-box">
          Pedido listo aproximadamente a las
          <strong>{calculated_ready.strftime("%I:%M %p")}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    payment_method = st.radio(
        "Método de pago",
        ["Efectivo", "Transferencia bancaria"],
    )
    if payment_method == "Transferencia bancaria":
        st.markdown(
            f"""
            <div class="pending-note">
              <strong>Datos para transferencia</strong><br>
              Banco: {BANK_NAME}<br>
              Tarjeta: {BANK_CARD}<br>
              Envía tu comprobante al confirmar el pedido por WhatsApp.
            </div>
            """,
            unsafe_allow_html=True,
        )
    notes = st.text_area(
        "Notas (opcional)",
        max_chars=300,
        placeholder="Ej. sin salsa, bien doradas…",
    )

    selected = []
    total = 0
    for product_name, price, _ in PRODUCTS[category]:
        quantity = quantities[product_name]
        if quantity:
            selected.append((product_name, price, quantity))
            total += price * quantity

    st.markdown(
        f'<div class="total-box"><span>Total a pagar</span><strong>${total:,}</strong></div>',
        unsafe_allow_html=True,
    )
    submitted = st.form_submit_button(
        "Registrar pedido",
        type="primary",
        use_container_width=True,
    )

if submitted:
    digits = "".join(character for character in phone if character.isdigit())
    ready_time = calculated_ready.time()
    errors = []

    if not selected:
        errors.append("Agrega al menos un producto.")
    if len(customer_name.strip()) < 2:
        errors.append("Escribe el nombre del cliente.")
    if len(digits) != 10:
        errors.append("El teléfono debe tener 10 dígitos.")
    if pickup_date.weekday() not in schedule["days"]:
        errors.append(
            f"{category} está disponible únicamente de {schedule['days_text']}."
        )
    if selected_time < schedule["open"]:
        errors.append(
            f"La hora seleccionada debe ser a partir de las {schedule['open'].strftime('%I:%M %p')}."
        )
    if ready_time > schedule["close"] or calculated_ready.date() != pickup_date:
        errors.append(
            f"El pedido debe quedar listo antes de las {schedule['close'].strftime('%I:%M %p')}."
        )

    if errors:
        for error in errors:
            st.error(error)
    else:
        now = datetime.now(TZ)
        folio = f"BET-{now.strftime('%m%d%H%M%S')}"
        order_text = " | ".join(
            f"{quantity} × {product_name}"
            for product_name, _, quantity in selected
        )
        ready_text = calculated_ready.strftime("%I:%M %p")

        try:
            get_sheet().append_row(
                [
                    now.strftime("%d/%m/%Y %I:%M:%S %p"),
                    folio,
                    safe_cell(customer_name),
                    digits,
                    safe_cell(f"{category}: {order_text}"),
                    total,
                    pickup_date.strftime("%d/%m/%Y"),
                    ready_text,
                    safe_cell(notes),
                    payment_method,
                    "Nuevo",
                ],
                value_input_option="USER_ENTERED",
            )

            lines = [
                f"• {quantity} × {product_name} — ${price * quantity:,}"
                for product_name, price, quantity in selected
            ]
            message = "\n".join(
                [
                    "¡Hola, Beto's! Quiero confirmar este pedido para recoger:",
                    f"Folio: {folio}",
                    f"Menú: {category}",
                    f"Nombre: {customer_name.strip()}",
                    f"Teléfono: {digits}",
                    f"Fecha: {pickup_date.strftime('%d/%m/%Y')}",
                    "Pedido listo aproximadamente a las",
                    ready_text,
                    "",
                    *lines,
                    "",
                    f"TOTAL: ${total:,}",
                    (
                        f"Pago: {payment_method} ({BANK_NAME}, tarjeta {BANK_CARD})"
                        if payment_method == "Transferencia bancaria"
                        else f"Pago: {payment_method}"
                    ),
                    f"Lugar: {ADDRESS_LINE_1}, {ADDRESS_LINE_2}",
                    f"Notas: {notes.strip()}" if notes.strip() else "",
                    "",
                    "¿Me confirman el pedido?",
                ]
            )
            st.session_state.last_order = {
                "folio": folio,
                "url": f"https://wa.me/{WHATSAPP_NUMBER}?text={quote(message)}",
            }
        except Exception:
            st.error(
                "No se pudo registrar el pedido. Revisa la conexión con Google Sheets."
            )

if st.session_state.last_order:
    order = st.session_state.last_order
    st.success(f"Pedido {order['folio']} registrado en Google Sheets.")
    st.markdown(
        f'<div class="wa-link"><a href="{order["url"]}" target="_blank" rel="noopener noreferrer">Confirmar por WhatsApp</a></div>',
        unsafe_allow_html=True,
    )

st.markdown(
    f"""
    <section class="location">
      <div>
        <div class="eyebrow">Visítanos</div>
        <h2>Dirección</h2>
        <p><strong>{ADDRESS_LINE_1}</strong></p>
        <p>{ADDRESS_LINE_2}</p>
        <a href="{GOOGLE_MAPS_URL}" target="_blank" rel="noopener noreferrer">Abrir ubicación en Google Maps</a>
      </div>
      <div class="pickup-chip">📍 Recoge tu pedido en el local</div>
    </section>
    <section class="events">
      <div class="eyebrow">Beto's va a tu evento</div>
      <h2>Servicio para eventos</h2>
      <p class="event-list">Flautas · Carne Asada · Cumpleaños · Posadas · Eventos empresariales · Fiestas · Reuniones familiares · Todo tipo de eventos</p>
      <p>Cuéntanos cuántas personas asistirán y qué servicio necesitas. Te ayudamos a preparar una cotización.</p>
      <a href="https://wa.me/{WHATSAPP_NUMBER}?text=Hola%2C%20quiero%20cotizar%20un%20evento%20con%20Beto%27s." target="_blank" rel="noopener noreferrer">Cotizar por WhatsApp</a>
    </section>
    """,
    unsafe_allow_html=True,
)

kroniq_url = (
    "https://wa.me/526563079754?text=Hola%2C%20quiero%20informaci%C3%B3n%20"
    "sobre%20una%20agenda%20digital%20para%20mi%20negocio."
)
st.markdown(
    f"""
    <section class="kroniq-ad">
      <img src="data:image/png;base64,{kroniq_b64}" alt="Kroniq Booking">
      <div>
        <h3>¿Tienes un negocio? ¿Quieres una agenda como esta?</h3>
        <p>Automatiza tus citas o pedidos con una solución digital profesional creada por Kroniq.</p>
      </div>
      <a href="{kroniq_url}" target="_blank" rel="noopener noreferrer">Quiero información</a>
    </section>
    """,
    unsafe_allow_html=True,
)
