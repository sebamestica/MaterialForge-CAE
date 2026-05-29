import os
import json
import sys
from pathlib import Path

# Setup path resolution
BASE_DIR = Path(__file__).parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from ia_agent.literature.pdf_extractor import PDFExtractor
from ia_agent.literature.literature_parser import LiteratureParser
from ia_agent.literature.literature_summarizer import LiteratureSummarizer

def build_context():
    print("==================================================")
    print("  BUILDING LIGHT LITERATURE KNOWLEDGE CONTEXT     ")
    print("==================================================")

    # Directories
    papers_dir = BASE_DIR / "data" / "papers"
    context_dir = BASE_DIR / "data" / "context"
    os.makedirs(papers_dir, exist_ok=True)
    os.makedirs(context_dir, exist_ok=True)

    # 1. Scan for PDFs
    pdfs = list(papers_dir.glob("*.pdf"))
    if not pdfs:
        # Fallback to copy from data/ direct
        data_dir = BASE_DIR / "data"
        print(f"No PDFs found in {papers_dir.relative_to(BASE_DIR)}. Scanning {data_dir.relative_to(BASE_DIR)}...")
        for data_pdf in data_dir.glob("*.pdf"):
            import shutil
            shutil.copy(data_pdf, papers_dir / data_pdf.name)
        pdfs = list(papers_dir.glob("*.pdf"))

    print(f"Found {len(pdfs)} PDF papers to process.")

    # 2. Extract and parse text from each PDF
    aggregated_parsed_data = {key: [] for key in LiteratureParser.KEYWORDS}
    
    for pdf_path in pdfs:
        print(f"Processing paper: {pdf_path.name}...")
        raw_text = PDFExtractor.extract_text(pdf_path)
        if not raw_text:
            continue
        
        parsed = LiteratureParser.parse_text(raw_text)
        for key, list_paras in parsed.items():
            aggregated_parsed_data[key].extend(list_paras)

    # De-duplicate and limit paragraphs to avoid huge memory profiles
    for key in aggregated_parsed_data:
        # De-duplicate while preserving order
        seen = set()
        deduped = [x for x in aggregated_parsed_data[key] if not (x in seen or seen.add(x))]
        aggregated_parsed_data[key] = deduped[:25] # Cap to 25 items per keyword
        print(f" - {key}: {len(deduped)} parsed segments collected.")

    # 3. Summarize using Ollama or Fallback Heuristics
    summarizer = LiteratureSummarizer()
    summary_json = summarizer.summarize_literature(aggregated_parsed_data)

    # Write data/context/literature_summary.json
    summary_file = context_dir / "literature_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary_json, f, indent=2, ensure_ascii=False)
    print(f"[SUCCESS] Wrote literature summary to {summary_file.relative_to(BASE_DIR)}")

    # 4. Generate data/context/knowledge_cache.json
    # Combines literature rules, physical constraints, and ML/Dataset bounds
    knowledge_cache = {
        "project": "MaterialForge",
        "last_compiled": datetime_now_str(),
        "papers_processed": [p.name for p in pdfs],
        "literature_summary": summary_json,
        "heuristics": {
            "TPU_compression": {
                "pattern": "gyroid",
                "infill_min": 55,
                "infill_max": 80,
                "wall_thickness_min": 1.6,
                "wall_thickness_max": 2.4,
                "speed_min": 20,
                "speed_max": 35,
                "nozzle_temp_min": 220,
                "nozzle_temp_max": 235,
                "layer_height_optimal": 0.16,
                "print_orientation": "Isotrópica (perpendicular al esfuerzo Z)",
                "wall_ordering": "outer_before_inner_OFF"
            },
            "PLA_stiffness": {
                "pattern": "honeycomb",
                "infill_min": 60,
                "infill_max": 80,
                "wall_thickness_min": 1.6,
                "wall_thickness_max": 2.4,
                "speed_min": 35,
                "speed_max": 50,
                "nozzle_temp_min": 210,
                "nozzle_temp_max": 220
            }
        },
        "scoring_weights": {
            "compression_strength": 0.40,
            "structural_stability": 0.20,
            "energy_absorption": 0.15,
            "manufacturability": 0.10,
            "printability": 0.10,
            "material_efficiency": 0.05
        }
    }

    cache_file = context_dir / "knowledge_cache.json"
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(knowledge_cache, f, indent=2, ensure_ascii=False)
    print(f"[SUCCESS] Wrote unified knowledge cache to {cache_file.relative_to(BASE_DIR)}")

def datetime_now_str() -> str:
    from datetime import datetime
    return datetime.utcnow().isoformat() + "Z"

if __name__ == "__main__":
    build_context()
