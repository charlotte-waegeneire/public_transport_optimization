import re
from typing import Optional, Dict, Any


class ParisTransportMapping:
    METRO_LINES = {
        "1": {"name": "1", "color": "#ffbe00", "text_color": "#000000", "id": "C01371"},
        "2": {"name": "2", "color": "#0055c8", "text_color": "#ffffff", "id": "C01372"},
        "3": {"name": "3", "color": "#6e6e00", "text_color": "#ffffff", "id": "C01373"},
        "3B": {"name": "3B", "color": "#6ec4e8", "text_color": "#000000", "id": "C01386"},
        "4": {"name": "4", "color": "#a0006e", "text_color": "#ffffff", "id": "C01374"},
        "5": {"name": "5", "color": "#ff7e2e", "text_color": "#000000", "id": "C01375"},
        "6": {"name": "6", "color": "#6eca97", "text_color": "#000000", "id": "C01376"},
        "7": {"name": "7", "color": "#f49fb3", "text_color": "#000000", "id": "C01377"},
        "7B": {"name": "7B", "color": "#6eca97", "text_color": "#000000", "id": "C01387"},
        "8": {"name": "8", "color": "#d282be", "text_color": "#000000", "id": "C01378"},
        "9": {"name": "9", "color": "#b6bd00", "text_color": "#000000", "id": "C01379"},
        "10": {"name": "10", "color": "#c9910d", "text_color": "#000000", "id": "C01380"},
        "11": {"name": "11", "color": "#704b1c", "text_color": "#ffffff", "id": "C01381"},
        "12": {"name": "12", "color": "#007852", "text_color": "#ffffff", "id": "C01382"},
        "13": {"name": "13", "color": "#6ec4e8", "text_color": "#000000", "id": "C01383"},
        "14": {"name": "14", "color": "#62259d", "text_color": "#ffffff", "id": "C01384"},
    }

    RER_LINES = {
        "A": {"name": "A", "color": "#eb2132", "text_color": "#ffffff", "id": "C01742"},
        "B": {"name": "B", "color": "#5091cb", "text_color": "#ffffff", "id": "C01743"},
        "C": {"name": "C", "color": "#ffcc30", "text_color": "#000000", "id": "C01727"},
        "D": {"name": "D", "color": "#008b5b", "text_color": "#ffffff", "id": "C01728"},
        "E": {"name": "E", "color": "#b94e9a", "text_color": "#ffffff", "id": "C01729"},
    }

    TRANSILIEN_LINES = {
        "H": {"name": "H", "color": "#84653d", "text_color": "#ffffff", "id": "C01737"},
        "J": {"name": "J", "color": "#cec73d", "text_color": "#000000", "id": "C01739"},
        "K": {"name": "K", "color": "#9b9842", "text_color": "#ffffff", "id": "C01738"},
        "L": {"name": "L", "color": "#c4a4cc", "text_color": "#000000", "id": "C01740"},
        "N": {"name": "N", "color": "#00b297", "text_color": "#ffffff", "id": "C01736"},
        "P": {"name": "P", "color": "#f58f53", "text_color": "#000000", "id": "C01730"},
        "R": {"name": "R", "color": "#f49fb3", "text_color": "#000000", "id": "C01731"},
        "U": {"name": "U", "color": "#b6134c", "text_color": "#ffffff", "id": "C01741"},
        "V": {"name": "V", "color": "#9f9825", "text_color": "#ffffff", "id": "C02711"},
    }

    TRAM_LINES = {
        "T1": {"name": "T1", "color": "#003ca6", "text_color": "#ffffff", "id": "C01389"},
        "T2": {"name": "T2", "color": "#cf009e", "text_color": "#ffffff", "id": "C01390"},
        "T3A": {"name": "T3a", "color": "#ff7e2e", "text_color": "#000000", "id": "C01391"},
        "T3B": {"name": "T3b", "color": "#00ae41", "text_color": "#ffffff", "id": "C01679"},
        "T4": {"name": "T4", "color": "#dfaf47", "text_color": "#000000", "id": "C01843"},
        "T5": {"name": "T5", "color": "#62259d", "text_color": "#ffffff", "id": "C01684"},
        "T6": {"name": "T6", "color": "#e2231a", "text_color": "#ffffff", "id": "C01794"},
        "T7": {"name": "T7", "color": "#704b1c", "text_color": "#ffffff", "id": "C01774"},
        "T8": {"name": "T8", "color": "#837902", "text_color": "#000000", "id": "C01795"},
        "T9": {"name": "T9", "color": "#5091cb", "text_color": "#ffffff", "id": "C02317"},
        "T10": {"name": "T10", "color": "#6e6e00", "text_color": "#ffffff", "id": "C02528"},
        "T11": {"name": "T11", "color": "#f58f53", "text_color": "#000000", "id": "C01999"},
        "T12": {"name": "T12", "color": "#a50034", "text_color": "#000000", "id": "C02529"},
        "T13": {"name": "T13", "color": "#8d653d", "text_color": "#000000", "id": "C02344"},
        "T14": {"name": "T14", "color": "#00a092", "text_color": "#000000", "id": "C02732"},
    }

    SPECIAL_LINES = {
        "ORLYVAL": {"name": "ORLYVAL", "color": "#5ec5ed", "text_color": "#ffffff", "id": "C01388"},
        "CDGVAL": {"name": "CDG VAL", "color": "#5cc5ed", "text_color": "#ffffff", "id": "C00563"},
    }

    @classmethod
    def get_line_info(cls, line_code: str) -> Optional[Dict[str, Any]]:
        if not line_code:
            return None

        line_code = str(line_code).strip().upper()

        all_lines = {**cls.METRO_LINES, **cls.RER_LINES, **cls.TRANSILIEN_LINES, **cls.TRAM_LINES, **cls.SPECIAL_LINES}

        return all_lines.get(line_code)

    @classmethod
    def get_line_color(cls, line_code: str) -> Optional[str]:
        line_info = cls.get_line_info(line_code)
        return line_info["color"] if line_info else None

    @classmethod
    def get_transport_type(cls, line_code: str) -> str:
        if not line_code:
            return "unknown"

        line_code = str(line_code).strip().upper()

        if line_code in cls.METRO_LINES:
            return "metro"
        elif line_code in cls.RER_LINES:
            return "rer"
        elif line_code in cls.TRANSILIEN_LINES:
            return "transilien"
        elif line_code in cls.TRAM_LINES:
            return "tram"
        elif line_code in cls.SPECIAL_LINES:
            return "special"
        else:
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
