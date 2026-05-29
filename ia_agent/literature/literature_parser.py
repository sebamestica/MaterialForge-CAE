import re
from typing import Dict, Any, List

class LiteratureParser:
    KEYWORDS = {
        "TPU": [r"tpu", r"polyurethane", r"elastomer", r"shore", r"elastómero"],
        "PLA": [r"pla", r"polylactic", r"polilactico", r"poliláctico"],
        "gyroid": [r"gyroid", r"giroide", r"tpms", r"minimal surface"],
        "honeycomb": [r"honeycomb", r"nido de abeja", r"hexagonal lattice"],
        "compression": [r"compression", r"compresión", r"crush", r"uniaxial", r"pandeo", r"buckling"],
        "energy_absorption": [r"energy absorption", r"absorción", r"damping", r"viscoplastic", r"sea", r"impact", r"disipación"],
        "anisotropy": [r"anisotrop", r"anisotropía", r"direction", r"layer orientation", r"orientación"],
        "manufacturing_constraints": [r"print speed", r"velocidad", r"temperature", r"temperatura", r"cooling", r"adhesion", r"adherencia", r"layer height", r"altura de capa", r"flow rate"]
    }

    @classmethod
    def parse_text(cls, text: str) -> Dict[str, List[str]]:
        """Scans the text and groups relevant sentences/paragraphs by keywords."""
        parsed_data = {key: [] for key in cls.KEYWORDS}
        
        # Split text into paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        for para in paragraphs:
            para_clean = para.replace('\n', ' ').strip()
            # Clean extra spaces
            para_clean = re.sub(r'\s+', ' ', para_clean)
            if len(para_clean) < 30:
                continue
                
            for key, patterns in cls.KEYWORDS.items():
                for pattern in patterns:
                    if re.search(pattern, para_clean, re.IGNORECASE):
                        # Avoid duplicates
                        if para_clean not in parsed_data[key]:
                            parsed_data[key].append(para_clean)
                        break # found match for this keyword in this paragraph, move to next keyword
                        
        # Limit the number of paragraphs per keyword to keep it light
        for key in parsed_data:
            parsed_data[key] = parsed_data[key][:25]
            
        return parsed_data
