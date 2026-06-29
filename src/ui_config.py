from copy import deepcopy


def lines_to_list(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def validate_form(values: dict) -> list[str]:
    errors: list[str] = []
    if values["max_rent"] <= 0:
        errors.append("Max rent must be > 0.")
    if values["move_in_from"] > values["move_in_to"]:
        errors.append("Move-in from must be ≤ move-in to.")
    if values["move_in_to"] > values["stay_until"]:
        errors.append("Move-in to must be ≤ stay until.")
    if values["max_pages"] < 1:
        errors.append("Max pages must be ≥ 1.")
    if not values["url"].strip():
        errors.append("Search URL cannot be empty.")
    return errors


def build_config(existing_cfg: dict, values: dict) -> dict:
    cfg = deepcopy(existing_cfg)
    cfg["search"] = {
        **cfg.get("search", {}),
        "url": values["url"].strip(),
        "max_rent": int(values["max_rent"]),
        "move_in_from": values["move_in_from"].isoformat(),
        "move_in_to": values["move_in_to"].isoformat(),
        "stay_until": values["stay_until"].isoformat(),
        "search_apartments": values["search_apartments"],
        "search_wg": values["search_wg"],
        "furnished_only": values["furnished_only"],
        "pets_allowed": values["pets_allowed"],
        "categories": [int(c) for c in values["categories"]],
        "last_online_max_days": int(values["last_online_max_days"]),
        "max_pages": int(values["max_pages"]),
        "headless": values["headless"],
    }
    cfg["districts"] = {
        **cfg.get("districts", {}),
        "preferred": lines_to_list(values["preferred_raw"]),
        "fallback_city": values["fallback_city"].strip(),
    }
    cfg["wg"] = {
        **cfg.get("wg", {}),
        "wg_size_max": int(values["wg_size_max"]),
        "flatshare_types": values["flatshare_types"],
    }
    cfg["ai"] = {
        **cfg.get("ai", {}),
        "enabled": values["ai_enabled"],
        "model": values["model"].strip(),
        "max_calls_per_run": int(values["max_calls_per_run"]),
        "max_detail_chars": int(values["max_detail_chars"]),
        "max_output_tokens": int(values["max_output_tokens"]),
    }
    cfg["profile"] = {
        **cfg.get("profile", {}),
        "name": values["profile_name"].strip(),
        "context": "\n" + values["profile_context"].strip() + "\n",
        "must_haves": lines_to_list(values["must_haves_raw"]),
        "strong_preferences": lines_to_list(values["strong_prefs_raw"]),
        "nice_to_haves": lines_to_list(values["nice_raw"]),
    }
    return cfg
