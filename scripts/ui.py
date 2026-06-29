import tomllib
import tomli_w
import streamlit as st
from datetime import date
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.toml"

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


def lines_to_list(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


@st.cache_data
def load_config() -> dict:
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


st.set_page_config(page_title="WG Bot Config", layout="centered")
st.title("WG-Gesucht Bot Config")

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
    errors = []
    if max_rent <= 0:
        errors.append("Max rent must be > 0.")
    if move_in_from > move_in_to:
        errors.append("Move-in from must be ≤ move-in to.")
    if move_in_to > stay_until:
        errors.append("Move-in to must be ≤ stay until.")
    if max_pages < 1:
        errors.append("Max pages must be ≥ 1.")
    if not url.strip():
        errors.append("Search URL cannot be empty.")

    if errors:
        for e in errors:
            st.error(e)
    else:
        new_cfg = {
            "search": {
                "url": url.strip(),
                "max_rent": int(max_rent),
                "move_in_from": move_in_from.isoformat(),
                "move_in_to": move_in_to.isoformat(),
                "stay_until": stay_until.isoformat(),
                "search_apartments": search_apartments,
                "search_wg": search_wg,
                "furnished_only": furnished_only,
                "pets_allowed": pets_allowed,
                "categories": [int(c) for c in categories],
                "last_online_max_days": int(last_online_max_days),
                "max_pages": int(max_pages),
                "headless": headless,
            },
            "districts": {
                "preferred": lines_to_list(preferred_raw),
                "fallback_city": fallback_city.strip(),
            },
            "wg": {
                "wg_size_max": int(wg_size_max),
                "flatshare_types": flatshare_types,
            },
            "ai": {
                "enabled": ai_enabled,
                "model": model.strip(),
                "max_calls_per_run": int(max_calls_per_run),
                "max_detail_chars": int(max_detail_chars),
                "max_output_tokens": int(max_output_tokens),
            },
            "profile": {
                "name": profile_name.strip(),
                "context": "\n" + profile_context.strip() + "\n",
                "must_haves": lines_to_list(must_haves_raw),
                "strong_preferences": lines_to_list(strong_prefs_raw),
                "nice_to_haves": lines_to_list(nice_raw),
            },
        }
        with open(CONFIG_PATH, "wb") as f:
            tomli_w.dump(new_cfg, f)
        st.cache_data.clear()
        st.success("Saved to config.toml.")
