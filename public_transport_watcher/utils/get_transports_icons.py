import re
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any


class ParisTransportMapping:
    METRO_LINES = {}
    RER_LINES = {}
    TRANSILIEN_LINES = {}
    TRAM_LINES = {}
    SPECIAL_LINES = {}

    @classmethod
    def _load_data_if_needed(cls):
        """Load data from JSON if not already loaded"""
        if not cls.METRO_LINES:
            current_dir = Path(__file__).parent
            json_file = current_dir / "transports_lines.json"

            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                cls.METRO_LINES = data["metro_lines"]
                cls.RER_LINES = data["rer_lines"]
                cls.TRANSILIEN_LINES = data["transilien_lines"]
                cls.TRAM_LINES = data["tram_lines"]
                cls.SPECIAL_LINES = data["special_lines"]
            except Exception as e:
                print(f"Error loading transport data: {e}")
                cls.METRO_LINES = {}
                cls.RER_LINES = {}
                cls.TRANSILIEN_LINES = {}
                cls.TRAM_LINES = {}
                cls.SPECIAL_LINES = {}

    @classmethod
    def get_line_info(cls, line_code: str) -> Optional[Dict[str, Any]]:
        if not line_code:
            return None

        cls._load_data_if_needed()

        line_code = str(line_code).strip().upper()

        all_lines = {**cls.METRO_LINES, **cls.RER_LINES, **cls.TRANSILIEN_LINES, **cls.TRAM_LINES, **cls.SPECIAL_LINES}

        return all_lines.get(line_code)

    @classmethod
    def get_line_color(cls, line_code: str) -> Optional[str]:
        line_info = cls.get_line_info(line_code)
        return line_info["color"] if line_info else None

    @classmethod
    def get_transport_type(cls, line_code: str) -> str:
        cls._load_data_if_needed()

        if not line_code:
            return "unknown"

        line_code = str(line_code).strip().upper()

        if line_code in cls.METRO_LINES:
            return "metro"

        if line_code in cls.RER_LINES:
            return "rer"

        if line_code in cls.TRANSILIEN_LINES:
            return "transilien"

        if line_code in cls.TRAM_LINES:
            return "tram"

        if line_code in cls.SPECIAL_LINES:
            return "special"

        return "unknown"


def extract_line_code_from_text(text: str) -> str:
    if not text:
        return ""

    text = str(text).strip()

    patterns = [
        r"(?:Metro|Métro|RER|Tramway|Tram|Ligne)\s*([A-Z0-9]+[AB]?)",
        r"\b(T[0-9]+[AB]?)\b",
        r"\bRER\s*([A-E])\b",
        r"\b([0-9]+[AB]?)\b",
        r"\b([A-Z])\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            code = match.group(1).upper()
            if ParisTransportMapping.get_line_info(code):
                return code

    clean_text = text.upper().strip()
    if ParisTransportMapping.get_line_info(clean_text):
        return clean_text

    return ""


def _create_line_badge_html(line_code: str, size: str = "medium") -> str:
    if not line_code:
        return ""

    line_info = ParisTransportMapping.get_line_info(line_code)
    if not line_info:
        return f"""<span style="
            background-color: #ccc; 
            color: #000; 
            width: 24px;
            height: 24px;
            border-radius: 50%;
            font-size: 12px; 
            font-weight: bold;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        ">{line_code}</span>"""

    bg_color = line_info["color"]
    text_color = line_info["text_color"]

    sizes = {
        "small": {"size": "20px", "font_size": "10px"},
        "medium": {"size": "28px", "font_size": "12px"},
        "large": {"size": "36px", "font_size": "14px"},
    }

    style = sizes.get(size, sizes["medium"])

    return f"""<span style="
        background-color: {bg_color}; 
        color: {text_color}; 
        width: {style["size"]};
        height: {style["size"]};
        border-radius: 50%;
        font-size: {style["font_size"]}; 
        font-weight: bold; 
        font-family: Arial, sans-serif;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border: 2px solid rgba(0,0,0,0.1);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    ">{line_code}</span>"""


def get_line_badge_for_streamlit(ligne_complete: str, size: str = "medium") -> str:
    line_code = extract_line_code_from_text(ligne_complete)
    if not line_code:
        return ""
    return _create_line_badge_html(line_code, size)
