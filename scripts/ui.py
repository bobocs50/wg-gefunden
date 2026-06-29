import tomli_w
import streamlit as st
import sys
from datetime import date
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.ui_config import build_config, validate_form

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - runtime compatibility branch
    import tomli as tomllib

CONFIG_PATH = ROOT_DIR / "config.toml"

WG_TYPE_LABELS = {
    "2": "2 – Frauen-WG",
    "12": "12 – Gemischte WG",
    "3": "3 – Männer-WG",
    "1": "1 – Studenten-WG",
    "4": "4 – Business-WG",
    "5": "5 – Wohnheim",
    "6": "6 – Berufstätigen-WG",
    "7": "7 – Azubi-WG",
    "9": "9 – WG mit Kindern",
    "16": "16 – LGBTQIA+",
    "19": "19 – Internationals welcome",
    "23": "23 – Keine Angaben",
}

CATEGORY_LABELS = {1: "1 – 1-Zimmer-Wohnung", 2: "2 – Wohnung", 3: "3 – Haus"}


def parse_date(s: str) -> date:
    return date.fromisoformat(s)


@st.cache_data
def load_config() -> dict:
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap');

        :root {
            --bg-main: #f6f8fb;
            --surface: #ffffff;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --line: #e2e8f0;
            --accent: #2d63e2;
            --accent-strong: #214ec2;
            --ease-out-strong: cubic-bezier(0.23, 1, 0.32, 1);
        }

        html, body, .stApp {
            font-family: "Manrope", sans-serif;
        }

        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        .stApp {
            background: var(--bg-main);
            color: var(--text-main);
        }

        header[data-testid="stHeader"] {
            background: transparent !important;
            border-bottom: none !important;
        }

        .block-container {
            max-width: 820px;
            padding-top: 2.8rem;
            padding-bottom: 2.2rem;
        }

        h1 {
            letter-spacing: -0.04em;
            font-weight: 800;
            color: var(--text-main);
            margin-bottom: 0.35rem;
            text-align: center;
            font-size: clamp(2rem, 5vw, 3.4rem);
            line-height: 1.02;
        }

        .stCaption {
            color: var(--text-muted);
            text-align: center;
            margin-bottom: 0.85rem;
        }

        [data-testid="stExpander"] {
            border: 1px solid var(--line);
            border-radius: 10px;
            background: var(--surface);
            margin-bottom: 0.7rem;
            overflow: hidden;
            box-shadow: none;
            transition: border-color 150ms var(--ease-out-strong), background-color 150ms var(--ease-out-strong);
        }

        [data-testid="stExpander"] > details,
        [data-testid="stExpander"] > details > summary {
            background: #ffffff !important;
        }

        [data-testid="stExpander"]:hover {
            border-color: #dfe5ea;
            box-shadow: none;
            transform: none;
        }

        [data-testid="stExpander"] details summary {
            font-weight: 700;
            font-size: 0.95rem;
            color: #2b3136;
            padding-top: 0.35rem;
            padding-bottom: 0.35rem;
        }

        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stDateInput"] input,
        [data-testid="stTextArea"] textarea {
            border: 1px solid var(--line);
            border-radius: 7px;
            background: #ffffff !important;
            color: var(--text-main) !important;
            transition: border-color 140ms var(--ease-out-strong), box-shadow 140ms var(--ease-out-strong), transform 120ms var(--ease-out-strong);
        }

        [data-testid="stTextInput"] [data-baseweb="input"],
        [data-testid="stNumberInput"] [data-baseweb="input"],
        [data-testid="stDateInput"] [data-baseweb="input"],
        [data-testid="stTextArea"] [data-baseweb="textarea"] {
            background: #ffffff !important;
            border-color: var(--line) !important;
        }

        [data-testid="stTextInput"] input:focus,
        [data-testid="stNumberInput"] input:focus,
        [data-testid="stDateInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus {
            border-color: #bcc9ff;
            box-shadow: 0 0 0 3px rgba(45, 99, 226, 0.12);
        }

        [data-testid="stNumberInput"] button {
            background: #ffffff !important;
            color: #334155 !important;
            border-left: 1px solid var(--line) !important;
        }

        [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
            border-radius: 7px;
            border-color: var(--line) !important;
            background: #ffffff !important;
            transition: border-color 150ms var(--ease-out-strong), box-shadow 150ms var(--ease-out-strong);
        }

        [data-testid="stMultiSelect"] [data-baseweb="tag"] {
            background: #eff6ff !important;
            border: 1px solid #dbeafe !important;
            color: #1e3a8a !important;
        }

        [data-testid="stMultiSelect"] [data-baseweb="select"] > div:focus-within {
            border-color: #bcc9ff;
            box-shadow: 0 0 0 3px rgba(45, 99, 226, 0.12);
        }

        [data-testid="stButton"] > button {
            min-height: 2.6rem;
            border-radius: 7px;
            border: 1px solid #2d63e2;
            background: #2d63e2;
            color: #ffffff;
            font-weight: 700;
            letter-spacing: 0.01em;
            transition: transform 120ms var(--ease-out-strong), filter 120ms var(--ease-out-strong), background-color 120ms var(--ease-out-strong), border-color 120ms var(--ease-out-strong);
        }

        [data-testid="stButton"] > button:hover {
            filter: brightness(1);
            box-shadow: none;
            background: #214ec2;
            border-color: #214ec2;
        }

        [data-testid="stButton"] > button:active {
            transform: scale(0.97);
        }

        [data-testid="stToggle"] label[data-testid="stWidgetLabel"] p,
        [data-testid="stCheckbox"] label p {
            font-weight: 600;
            color: #2f3438;
        }

        [data-testid="stRadio"] label p,
        [data-testid="stMultiSelect"] label p,
        [data-testid="stTextInput"] label p,
        [data-testid="stDateInput"] label p,
        [data-testid="stNumberInput"] label p,
        [data-testid="stTextArea"] label p {
            color: #394045;
            font-weight: 600;
            font-size: 0.9rem;
        }

        code {
            font-family: "JetBrains Mono", monospace;
            font-size: 0.82em;
            color: #334155;
        }

        @media (hover: none) {
            [data-testid="stExpander"]:hover {
                transform: none;
                box-shadow: 0 1px 0 rgba(12, 24, 22, 0.04);
            }
        }

        @media (max-width: 760px) {
            .block-container {
                padding-top: 1.4rem;
            }

            h1 {
                text-align: left;
            }

            .stCaption {
                text-align: left;
            }
        }

        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
                scroll-behavior: auto !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="WG Bot Config", layout="centered")
inject_styles()
st.title("WG-Gesucht Bot Config")
st.caption("Minimal config editor for `config.toml`.")

cfg = load_config()

# ── Search ────────────────────────────────────────────────────────────────────
with st.expander("Search", expanded=True):
    url = st.text_input("Search URL", cfg["search"]["url"])
    max_rent = st.number_input("Max rent (€)", value=cfg["search"]["max_rent"], min_value=1, step=50)
    col1, col2, col3 = st.columns(3)
    with col1:
        move_in_from = st.date_input("Move-in from", parse_date(cfg["search"]["move_in_from"]))
    with col2:
        move_in_to = st.date_input("Move-in to", parse_date(cfg["search"]["move_in_to"]))
    with col3:
        stay_until = st.date_input("Stay until", parse_date(cfg["search"]["stay_until"]))

    col4, col5 = st.columns(2)
    with col4:
        search_apartments = st.toggle("Search apartments", cfg["search"]["search_apartments"])
        furnished_only = st.toggle("Furnished only", cfg["search"]["furnished_only"])
    with col5:
        search_wg = st.toggle("Search WG rooms", cfg["search"]["search_wg"])
        pets_allowed = st.toggle("Pets allowed", cfg["search"]["pets_allowed"])

    categories = st.multiselect(
        "Apartment categories (when search apartments = on)",
        options=list(CATEGORY_LABELS.keys()),
        default=cfg["search"]["categories"],
        format_func=lambda x: CATEGORY_LABELS[x],
    )

    col6, col7, col8 = st.columns(3)
    with col6:
        last_online_max_days = st.number_input(
            "Last online max days", value=cfg["search"]["last_online_max_days"], min_value=1
        )
    with col7:
        max_pages = st.number_input("Max pages", value=cfg["search"]["max_pages"], min_value=1)
    with col8:
        headless = st.toggle("Headless browser", cfg["search"]["headless"])

# ── Districts ─────────────────────────────────────────────────────────────────
with st.expander("Districts", expanded=True):
    st.caption("One district name per line (case-insensitive). A listing passes if its location contains any entry.")
    preferred_raw = st.text_area(
        "Preferred districts",
        "\n".join(cfg["districts"]["preferred"]),
        height=200,
    )
    fallback_city = st.text_input(
        "Fallback city (pass listings with no sub-district, e.g. 'Hamburg')",
        cfg["districts"].get("fallback_city", ""),
    )

# ── WG ────────────────────────────────────────────────────────────────────────
with st.expander("WG Filters"):
    wg_size_max = st.number_input(
        "Max WG size (0 = no limit)", value=cfg["wg"]["wg_size_max"], min_value=0
    )
    flatshare_types = st.multiselect(
        "Accepted flatshare types (empty = accept all)",
        options=list(WG_TYPE_LABELS.keys()),
        default=cfg["wg"]["flatshare_types"],
        format_func=lambda x: WG_TYPE_LABELS[x],
    )

# ── AI ────────────────────────────────────────────────────────────────────────
with st.expander("AI"):
    ai_enabled = st.toggle("AI enabled", cfg["ai"]["enabled"])
    model = st.text_input("Model", cfg["ai"]["model"])
    col9, col10, col11 = st.columns(3)
    with col9:
        max_calls_per_run = st.number_input(
            "Max AI calls per run", value=cfg["ai"]["max_calls_per_run"], min_value=1
        )
    with col10:
        max_detail_chars = st.number_input(
            "Max detail chars", value=cfg["ai"]["max_detail_chars"], min_value=100, step=100
        )
    with col11:
        max_output_tokens = st.number_input(
            "Max output tokens", value=cfg["ai"]["max_output_tokens"], min_value=50, step=50
        )

# ── Profile ───────────────────────────────────────────────────────────────────
with st.expander("Profile"):
    profile_name = st.text_input("Name", cfg["profile"]["name"])
    profile_context = st.text_area("Context (inserted into AI prompt)", cfg["profile"]["context"].strip(), height=120)
    must_haves_raw = st.text_area(
        "Must-haves (one per line)", "\n".join(cfg["profile"]["must_haves"]), height=100
    )
    strong_prefs_raw = st.text_area(
        "Strong preferences (one per line)", "\n".join(cfg["profile"]["strong_preferences"]), height=100
    )
    nice_raw = st.text_area(
        "Nice-to-haves (one per line)", "\n".join(cfg["profile"]["nice_to_haves"]), height=100
    )

# ── Save ──────────────────────────────────────────────────────────────────────
st.divider()
if st.button("Save config.toml", type="primary", use_container_width=True):
    values = {
        "url": url,
        "max_rent": max_rent,
        "move_in_from": move_in_from,
        "move_in_to": move_in_to,
        "stay_until": stay_until,
        "search_apartments": search_apartments,
        "search_wg": search_wg,
        "furnished_only": furnished_only,
        "pets_allowed": pets_allowed,
        "categories": categories,
        "last_online_max_days": last_online_max_days,
        "max_pages": max_pages,
        "headless": headless,
        "preferred_raw": preferred_raw,
        "fallback_city": fallback_city,
        "wg_size_max": wg_size_max,
        "flatshare_types": flatshare_types,
        "ai_enabled": ai_enabled,
        "model": model,
        "max_calls_per_run": max_calls_per_run,
        "max_detail_chars": max_detail_chars,
        "max_output_tokens": max_output_tokens,
        "profile_name": profile_name,
        "profile_context": profile_context,
        "must_haves_raw": must_haves_raw,
        "strong_prefs_raw": strong_prefs_raw,
        "nice_raw": nice_raw,
    }
    errors = validate_form(values)

    if errors:
        for e in errors:
            st.error(e)
    else:
        new_cfg = build_config(cfg, values)
        with open(CONFIG_PATH, "wb") as f:
            tomli_w.dump(new_cfg, f)
        st.cache_data.clear()
        st.success("Saved to config.toml.")
