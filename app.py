import base64
import json
import mimetypes
import re
from datetime import date, datetime, time, timedelta
from html import escape
from pathlib import Path
from urllib.parse import quote_plus

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials


st.set_page_config(
    page_title="Europa Spa",
    page_icon="E",
    layout="centered",
    initial_sidebar_state="collapsed",
)


SHEET_ID = "1erDwwIzWkQzkEpL8RgqvXQ0dqgowSNg1PYZmlf8Yj24"
ADMIN_PASSWORD_DEFAULT = "1234"

NEGOCIO = {
    "nombre": "Europa Spa",
    "categoria": "Spa premium para caballeros",
    "telefono": "6567059823",
    "horario": "Lunes a sabado, 10:00 am a 10:00 pm",
    "precio": "Desde $750. Precio final en lugar.",
}

SERVICIOS = {
    "Masaje relajante": {
        "duracion": 60,
        "precio": "Desde $750",
        "descripcion": "Sesion enfocada en descanso, suavidad y bienestar general.",
    },
    "Masaje descontracturante": {
        "duracion": 90,
        "precio": "Desde $750",
        "descripcion": "Sesion profunda para liberar tension muscular acumulada.",
    },
    "Aromaterapia": {
        "duracion": 90,
        "precio": "Desde $750",
        "descripcion": "Masaje con aromas relajantes y ambiente sensorial premium.",
    },
}

HORARIO_GENERAL = {
    "lunes": ("10:00", "22:00"),
    "martes": ("10:00", "22:00"),
    "miercoles": ("10:00", "22:00"),
    "jueves": ("10:00", "22:00"),
    "viernes": ("10:00", "22:00"),
    "sabado": ("10:00", "22:00"),
}

TERAPEUTAS = [
    {
        "id": "terapeuta-1",
        "nombre": "Terapeuta 1",
        "foto": "static/terapeutas/terapeuta-1.jpg",
        "especialidades": ["Relajante", "Aromaterapia"],
        "servicios": ["Masaje relajante", "Aromaterapia"],
        "horario": HORARIO_GENERAL,
    },
    {
        "id": "terapeuta-2",
        "nombre": "Terapeuta 2",
        "foto": "static/terapeutas/terapeuta-2.jpg",
        "especialidades": ["Descontracturante", "Presion media"],
        "servicios": ["Masaje relajante", "Masaje descontracturante"],
        "horario": HORARIO_GENERAL,
    },
    {
        "id": "terapeuta-3",
        "nombre": "Terapeuta 3",
        "foto": "static/terapeutas/terapeuta-3.jpg",
        "especialidades": ["Relajante", "Sesion extendida"],
        "servicios": ["Masaje relajante", "Masaje descontracturante", "Aromaterapia"],
        "horario": HORARIO_GENERAL,
    },
    {
        "id": "terapeuta-4",
        "nombre": "Terapeuta 4",
        "foto": "static/terapeutas/terapeuta-4.jpg",
        "especialidades": ["Aromaterapia", "Relajante premium"],
        "servicios": ["Masaje relajante", "Aromaterapia"],
        "horario": HORARIO_GENERAL,
    },
    {
        "id": "terapeuta-5",
        "nombre": "Terapeuta 5",
        "foto": "static/terapeutas/terapeuta-5.jpg",
        "especialidades": ["Descontracturante", "Sesion profunda"],
        "servicios": ["Masaje descontracturante", "Aromaterapia"],
        "horario": HORARIO_GENERAL,
    },
]

DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
BUFFER_MINUTOS = 15
PASO_MINUTOS = 30

COLUMNAS = [
    "id",
    "negocio",
    "terapeuta_id",
    "terapeuta",
    "cliente",
    "whatsapp",
    "servicio",
    "duracion",
    "fecha",
    "hora",
    "estatus",
    "comentarios",
    "creado_en",
]


def inject_css():
    st.markdown(
        """
        <style>
            #MainMenu, footer, header,
            [data-testid="stToolbar"],
            [data-testid="stDecoration"],
            [data-testid="stStatusWidget"],
            [data-testid="stHeader"],
            .stDeployButton {
                display: none !important;
            }

            :root {
                --bg: #08090b;
                --panel: rgba(18, 20, 25, .78);
                --panel-strong: #141821;
                --line: rgba(255,255,255,.11);
                --text: #f8fafc;
                --soft: rgba(248,250,252,.68);
                --gold: #c8a96a;
                --gold-2: #f1d99b;
                --rose: #d85c74;
                --blue: #7dd3fc;
            }

            html, body, [data-testid="stAppViewContainer"] {
                background:
                    linear-gradient(145deg, rgba(200,169,106,.13), transparent 34rem),
                    radial-gradient(circle at bottom right, rgba(125,211,252,.09), transparent 30rem),
                    var(--bg);
                color: var(--text);
            }

            [data-testid="stAppViewBlockContainer"] {
                max-width: 860px;
                padding: 1.15rem 1rem 4.5rem;
            }

            h1, h2, h3, p, label, span {
                letter-spacing: 0;
            }

            h1 {
                font-size: 2.35rem !important;
                line-height: 1.03 !important;
                margin-bottom: .4rem !important;
            }

            h2 {
                font-size: 1.28rem !important;
                margin: .35rem 0 .85rem !important;
            }

            .eu-hero, .eu-section {
                border: 1px solid var(--line);
                border-radius: 8px;
                background: linear-gradient(145deg, rgba(20,24,33,.94), rgba(12,14,18,.94));
                box-shadow: 0 22px 70px rgba(0,0,0,.38);
            }

            .eu-hero {
                padding: 1.15rem;
                margin-bottom: 1rem;
            }

            .eu-section {
                padding: 1rem;
                margin: 1rem 0;
            }

            .eu-mark {
                display: inline-flex;
                width: 3rem;
                height: 3rem;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                background: linear-gradient(135deg, var(--gold), var(--gold-2));
                color: #08090b;
                font-weight: 900;
                margin-bottom: .9rem;
                box-shadow: 0 14px 34px rgba(200,169,106,.22);
            }

            .eu-eyebrow {
                color: var(--gold-2);
                font-size: .76rem;
                font-weight: 800;
                text-transform: uppercase;
                margin-bottom: .5rem;
            }

            .eu-copy, .eu-muted {
                color: var(--soft);
                line-height: 1.5;
                font-size: .96rem;
            }

            .eu-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: .75rem;
                margin-top: .7rem;
            }

            .eu-card {
                border: 1px solid var(--line);
                border-radius: 8px;
                background: linear-gradient(145deg, rgba(255,255,255,.065), rgba(255,255,255,.025));
                overflow: hidden;
            }

            .eu-card-body {
                padding: .85rem;
            }

            .eu-card-title {
                color: #fff7ed;
                font-size: 1rem;
                font-weight: 900;
                margin-bottom: .35rem;
            }

            .eu-card-meta {
                color: var(--gold-2);
                font-size: .83rem;
                font-weight: 800;
                margin-bottom: .45rem;
            }

            .eu-photo, .eu-placeholder {
                width: 100%;
                aspect-ratio: 4 / 3;
                display: block;
            }

            .eu-photo {
                object-fit: cover;
            }

            .eu-placeholder {
                display: grid;
                place-items: center;
                background: linear-gradient(135deg, #f1d99b, #7dd3fc);
                color: #08090b;
                font-size: 2.35rem;
                font-weight: 900;
            }

            .eu-slots {
                display: flex;
                flex-wrap: wrap;
                gap: .35rem;
                margin-top: .65rem;
            }

            .eu-slot {
                border: 1px solid rgba(200,169,106,.36);
                border-radius: 999px;
                color: #fff7ed;
                background: rgba(200,169,106,.12);
                padding: .25rem .5rem;
                font-size: .75rem;
                font-weight: 800;
            }

            .eu-summary, .eu-success {
                border-radius: 8px;
                padding: .9rem;
                margin: .8rem 0;
            }

            .eu-summary {
                border: 1px solid rgba(200,169,106,.35);
                background: rgba(200,169,106,.09);
                color: #fff7ed;
            }

            .eu-success {
                border: 1px solid rgba(34,197,94,.36);
                background: rgba(34,197,94,.13);
                color: #dcfce7;
            }

            .eu-admin-row {
                border-bottom: 1px solid var(--line);
                padding: .75rem 0;
            }

            .stTextInput input,
            .stTextArea textarea,
            .stSelectbox div[data-baseweb="select"] > div,
            .stDateInput input {
                border-radius: 8px !important;
                border: 1px solid rgba(148,163,184,.24) !important;
                background-color: #151821 !important;
                color: #f8fafc !important;
                min-height: 3rem;
                box-shadow: none !important;
            }

            .stTextInput label,
            .stTextArea label,
            .stSelectbox label,
            .stDateInput label {
                color: rgba(255,255,255,.84) !important;
                font-weight: 750 !important;
            }

            .stButton button,
            .stFormSubmitButton button {
                border-radius: 8px !important;
                min-height: 3.1rem;
                font-weight: 850 !important;
                border: 1px solid rgba(255,255,255,.12) !important;
            }

            .stFormSubmitButton button {
                width: 100%;
                border: none !important;
                color: white !important;
                background: linear-gradient(135deg, var(--gold), var(--rose)) !important;
                box-shadow: 0 14px 34px rgba(200,169,106,.25);
            }

            div[data-testid="stForm"] {
                border: 1px solid var(--line);
                border-radius: 8px;
                padding: 1rem;
                background: rgba(18,20,25,.70);
            }

            @media (max-width: 620px) {
                [data-testid="stAppViewBlockContainer"] {
                    padding-left: .82rem;
                    padding-right: .82rem;
                }

                h1 {
                    font-size: 1.85rem !important;
                }

                .eu-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_service_account_info():
    try:
        return dict(st.secrets["gcp_service_account"])
    except Exception:
        pass

    for json_path in Path(".").glob("*.json"):
        with json_path.open("r", encoding="utf-8") as file:
            service_account = json.load(file)
        if "client_email" in service_account and "private_key" in service_account:
            return service_account

    raise RuntimeError("Faltan las credenciales de Google Sheets en Secrets o en un JSON.")


@st.cache_resource(show_spinner=False)
def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(get_service_account_info(), scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID).sheet1


def ensure_headers(sheet):
    primera_fila = sheet.row_values(1)
    if primera_fila[: len(COLUMNAS)] != COLUMNAS:
        sheet.update("A1:M1", [COLUMNAS])


def normalizar_whatsapp(valor):
    return re.sub(r"\D", "", valor or "")


def parse_time(valor):
    hora, minuto = valor.split(":")
    return time(int(hora), int(minuto))


def dia_key(fecha):
    return DIAS[fecha.weekday()]


def formato_hora(dt):
    return dt.strftime("%I:%M %p").lstrip("0")


def normalizar_hora(valor):
    valor = str(valor).strip().upper()
    valor = valor.replace(".", "")
    return valor


def formato_duracion(minutos):
    if minutos == 60:
        return "1 hora"
    if minutos == 90:
        return "1 hora 30 min"
    return f"{minutos} min"


def opciones_fecha(dias=21):
    opciones = {}
    hoy = date.today()
    for offset in range(dias):
        fecha = hoy + timedelta(days=offset)
        if offset == 0:
            etiqueta = "Hoy"
        elif offset == 1:
            etiqueta = "Manana"
        else:
            etiqueta = f"{DIAS[fecha.weekday()]} {fecha.day} {MESES[fecha.month - 1]}"
        opciones[etiqueta] = fecha
    return opciones


def es_fecha_cerrada(fecha):
    return fecha.weekday() == 6


def horario_terapeuta(terapeuta, fecha):
    horario = terapeuta["horario"].get(dia_key(fecha))
    if not horario:
        return None
    return parse_time(horario[0]), parse_time(horario[1])


def se_empalma(inicio_1, fin_1, inicio_2, fin_2):
    return inicio_1 < fin_2 and inicio_2 < fin_1


def obtener_citas(fecha, terapeuta_id):
    sheet = get_sheet()
    ensure_headers(sheet)
    filas = sheet.get_all_records()
    citas = []

    for fila in filas:
        try:
            if str(fila.get("fecha")) != str(fecha):
                continue
            if fila.get("terapeuta_id") != terapeuta_id:
                continue

            inicio = datetime.strptime(
                f"{fila['fecha']} {normalizar_hora(fila['hora'])}",
                "%Y-%m-%d %I:%M %p",
            )
            duracion = int(fila["duracion"])
            fin = inicio + timedelta(minutes=duracion + BUFFER_MINUTOS)
            citas.append((inicio, fin))
        except (KeyError, TypeError, ValueError):
            continue

    return citas


def horarios_disponibles(fecha, duracion, terapeuta):
    if es_fecha_cerrada(fecha):
        return []

    horario = horario_terapeuta(terapeuta, fecha)
    if not horario:
        return []

    citas = obtener_citas(fecha, terapeuta["id"])
    inicio_dia = datetime.combine(fecha, horario[0])
    cierre_dia = datetime.combine(fecha, horario[1])
    actual = inicio_dia
    disponibles = []

    while actual < cierre_dia:
        fin_servicio = actual + timedelta(minutes=duracion + BUFFER_MINUTOS)
        if fin_servicio <= cierre_dia:
            ocupado = any(se_empalma(actual, fin_servicio, cita_inicio, cita_fin) for cita_inicio, cita_fin in citas)
            if not ocupado:
                disponibles.append(formato_hora(actual))
        actual += timedelta(minutes=PASO_MINUTOS)

    return disponibles


def terapeutas_para_servicio(servicio):
    return [terapeuta for terapeuta in TERAPEUTAS if servicio in terapeuta["servicios"]]


def obtener_citas_admin(fecha):
    sheet = get_sheet()
    ensure_headers(sheet)
    filas = sheet.get_all_records()
    citas = []

    for fila in filas:
        if str(fila.get("fecha")) != str(fecha):
            continue
        citas.append(
            {
                "Fecha": fila.get("fecha", ""),
                "Hora": fila.get("hora", ""),
                "Terapeuta": fila.get("terapeuta", ""),
                "Cliente": fila.get("cliente", ""),
                "WhatsApp": fila.get("whatsapp", ""),
                "Servicio": fila.get("servicio", ""),
                "Duracion": fila.get("duracion", ""),
                "Estatus": fila.get("estatus", ""),
                "Comentarios": fila.get("comentarios", ""),
            }
        )

    return sorted(citas, key=lambda item: item["Hora"])


def render_hero():
    st.markdown(
        f"""
        <div class="eu-hero">
            <div class="eu-mark">E</div>
            <div class="eu-eyebrow">{escape(NEGOCIO["categoria"])}</div>
            <h1>{escape(NEGOCIO["nombre"])}</h1>
            <p class="eu-copy">
                Agenda tu masaje con la terapeuta de tu preferencia. El spa revisa tu solicitud
                y confirma directamente por WhatsApp.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_servicios():
    cards = ['<div class="eu-grid">']
    for nombre, datos in SERVICIOS.items():
        cards.append(
            f'<div class="eu-card"><div class="eu-card-body">'
            f'<div class="eu-card-title">{escape(nombre)}</div>'
            f'<div class="eu-card-meta">{formato_duracion(datos["duracion"])} | {escape(datos["precio"])}</div>'
            f'<div class="eu-muted">{escape(datos["descripcion"])}</div>'
            f"</div></div>"
        )
    cards.append("</div>")
    st.markdown("".join(cards), unsafe_allow_html=True)


def render_catalogo(disponibilidad):
    cards = ['<div class="eu-grid">']
    for terapeuta in TERAPEUTAS:
        foto = Path(terapeuta["foto"])
        inicial = terapeuta["nombre"].split()[-1]
        if foto.exists():
            mime_type = mimetypes.guess_type(foto.name)[0] or "image/jpeg"
            encoded = base64.b64encode(foto.read_bytes()).decode("utf-8")
            media = (
                f'<img class="eu-photo" src="data:{mime_type};base64,{encoded}" '
                f'alt="{escape(terapeuta["nombre"])}">'
            )
        else:
            media = f'<div class="eu-placeholder">{escape(inicial)}</div>'

        slots = disponibilidad.get(terapeuta["id"], [])
        if slots:
            slots_html = "".join(f'<span class="eu-slot">{escape(slot)}</span>' for slot in slots[:6])
            if len(slots) > 6:
                slots_html += f'<span class="eu-slot">+{len(slots) - 6}</span>'
        else:
            slots_html = '<span class="eu-muted">Sin horarios disponibles para esta seleccion.</span>'

        cards.append(
            f'<div class="eu-card">'
            f"{media}"
            f'<div class="eu-card-body">'
            f'<div class="eu-card-title">{escape(terapeuta["nombre"])}</div>'
            f'<div class="eu-card-meta">{escape(", ".join(terapeuta["especialidades"]))}</div>'
            f'<div class="eu-muted">{escape(" | ".join(terapeuta["servicios"]))}</div>'
            f'<div class="eu-slots">{slots_html}</div>'
            f"</div></div>"
        )
    cards.append("</div>")
    st.markdown("".join(cards), unsafe_allow_html=True)


def render_admin():
    st.markdown('<div class="eu-section">', unsafe_allow_html=True)
    st.markdown("## Panel interno")
    st.markdown(
        '<p class="eu-muted">Vista privada para revisar citas y abrir el mensaje de confirmacion por WhatsApp.</p>',
        unsafe_allow_html=True,
    )

    password_configurada = st.secrets.get("admin_password", ADMIN_PASSWORD_DEFAULT)
    password = st.text_input("Clave de administrador", type="password")

    if password != password_configurada:
        st.info("Ingresa la clave para ver las citas.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    fecha_admin = st.date_input("Fecha", value=date.today(), key="fecha_admin")

    try:
        citas = obtener_citas_admin(fecha_admin)
    except Exception as error:
        st.error(f"No pude cargar las citas: {error}")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    if not citas:
        st.success("No hay citas registradas para esta fecha.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.dataframe(citas, use_container_width=True, hide_index=True)

    for cita in citas:
        whatsapp = normalizar_whatsapp(str(cita["WhatsApp"]))
        mensaje = (
            f"Hola {cita['Cliente']}, te contactamos de Europa Spa para confirmar tu cita "
            f"de {cita['Servicio']} con {cita['Terapeuta']} el {cita['Fecha']} a las {cita['Hora']}."
        )
        link = f"https://wa.me/52{whatsapp}?text={quote_plus(mensaje)}"
        st.markdown(
            f"""
            <div class="eu-admin-row">
                <strong>{escape(cita["Hora"])} | {escape(cita["Terapeuta"])}</strong><br>
                {escape(cita["Cliente"])} - {escape(cita["Servicio"])} - {escape(cita["WhatsApp"])}<br>
                <a href="{escape(link)}" target="_blank">Abrir WhatsApp de confirmacion</a>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def app_cliente():
    st.markdown('<div class="eu-section">', unsafe_allow_html=True)
    st.markdown("## Servicio y fecha")
    st.markdown(
        f"""
        <div class="eu-summary">
            <strong>{escape(NEGOCIO["nombre"])}</strong><br>
            {escape(NEGOCIO["horario"])}<br>
            {escape(NEGOCIO["precio"])}
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_servicios()
    servicio = st.selectbox("Servicio", list(SERVICIOS.keys()))
    duracion = SERVICIOS[servicio]["duracion"]
    fechas = opciones_fecha()
    fecha_label = st.selectbox("Fecha", list(fechas.keys()))
    fecha = fechas[fecha_label]
    st.markdown("</div>", unsafe_allow_html=True)

    disponibilidad = {
        terapeuta["id"]: horarios_disponibles(fecha, duracion, terapeuta)
        for terapeuta in terapeutas_para_servicio(servicio)
    }

    st.markdown('<div class="eu-section">', unsafe_allow_html=True)
    st.markdown("## Catalogo de terapeutas")
    if es_fecha_cerrada(fecha):
        st.warning("Domingo cerrado. Selecciona otra fecha.")
    else:
        render_catalogo(disponibilidad)
    st.markdown("</div>", unsafe_allow_html=True)

    terapeutas_con_horario = {
        f'{terapeuta["nombre"]} - {len(disponibilidad.get(terapeuta["id"], []))} horarios': terapeuta
        for terapeuta in terapeutas_para_servicio(servicio)
        if disponibilidad.get(terapeuta["id"])
    }

    if es_fecha_cerrada(fecha) or not terapeutas_con_horario:
        st.warning("No hay horarios disponibles para este servicio en la fecha seleccionada.")
        return

    st.markdown('<div class="eu-section">', unsafe_allow_html=True)
    st.markdown("## Confirmar solicitud")

    with st.form("form_reserva", clear_on_submit=True):
        terapeuta_label = st.selectbox("Terapeuta", list(terapeutas_con_horario.keys()))
        terapeuta = terapeutas_con_horario[terapeuta_label]
        hora = st.selectbox("Hora disponible", disponibilidad[terapeuta["id"]])
        nombre = st.text_input("Nombre del cliente", placeholder="Nombre completo")
        whatsapp = st.text_input("WhatsApp", placeholder="10 digitos", max_chars=14)
        comentarios = st.text_area("Comentarios adicionales", placeholder="Opcional")
        enviar = st.form_submit_button("Guardar solicitud")

    st.markdown("</div>", unsafe_allow_html=True)

    if not enviar:
        return

    nombre = nombre.strip()
    whatsapp_limpio = normalizar_whatsapp(whatsapp)
    horas_actualizadas = horarios_disponibles(fecha, duracion, terapeuta)

    if not nombre:
        st.error("Escribe el nombre del cliente.")
        return

    if len(whatsapp_limpio) != 10:
        st.error("El WhatsApp debe tener exactamente 10 digitos.")
        return

    if hora not in horas_actualizadas:
        st.error("Ese horario acaba de ocuparse. Elige otro.")
        return

    try:
        sheet = get_sheet()
        ensure_headers(sheet)
        sheet.append_row(
            [
                datetime.now().strftime("%Y%m%d%H%M%S"),
                NEGOCIO["nombre"],
                terapeuta["id"],
                terapeuta["nombre"],
                nombre,
                whatsapp_limpio,
                servicio,
                duracion,
                str(fecha),
                hora,
                "Pendiente",
                comentarios,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ]
        )
        get_sheet.clear()
        st.markdown(
            f"""
            <div class="eu-success">
                <strong>Cita guardada correctamente.</strong><br>
                {escape(servicio)} con {escape(terapeuta["nombre"])} el {fecha.strftime("%d/%m/%Y")}
                a las {escape(hora)}. Europa Spa recibio la solicitud para confirmar por WhatsApp.
            </div>
            """,
            unsafe_allow_html=True,
        )
    except Exception as error:
        st.error(f"No pude guardar la cita: {error}")


inject_css()
render_hero()

vista = st.radio("Vista", ["Agendar cita", "Panel interno"], horizontal=True, label_visibility="collapsed")

if vista == "Agendar cita":
    app_cliente()
else:
    render_admin()

st.caption("Europa Spa | Agenda digital privada")
