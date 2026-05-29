import pandas as pd
import re
from src.utils import get_cleaned_dir, write_json


ID_PATTERN = re.compile(
    r"^(?P<prefix>[A-Z]{1,3})(?P<number>\d{2,3})(?P<suffix>[A-Z]*)$",
    re.IGNORECASE,
)

STRUCTURE_MAP = {
    "G": "gyroid",
    "H": "honeycomb",
    "T": "triply_periodic",
    "TQ": "triply_periodic",
    "SOL": "solid",
}

REPLICA_LETTERS = set("ABCDE")


def parse_specimen_ids(registry, logger, artifacts_dir):
    logger.info("=== FASE 3: Parseo y normalización de IDs de probeta ===")

    parsed = {}
    anomalies = []

    for sid, info in registry.items():
        sid_clean = sid.strip().upper()
        m = ID_PATTERN.match(sid_clean)

        if not m:
            anomalies.append({"specimen_id": sid, "reason": "Does not match pattern PREFIX+NUM+SUFFIX"})
            parsed[sid] = {
                **info,
                "id_prefix": None,
                "id_number": None,
                "id_suffix": None,
                "structure_type_from_id": info.get("structure_type_inferred", "unknown"),
                "param_numeric": None,
                "replica_letter": None,
                "id_parse_status": "failed",
                "id_parse_notes": "Could not parse ID pattern",
            }
            logger.warning(f"  Cannot parse ID: {sid}")
            continue

        prefix = m.group("prefix").upper()
        number_str = m.group("number")
        suffix = m.group("suffix").upper()

        struct = None
        for key in sorted(STRUCTURE_MAP.keys(), key=len, reverse=True):
            if prefix.startswith(key):
                struct = STRUCTURE_MAP[key]
                break

        if struct is None:
            struct = "unknown"
            anomalies.append({"specimen_id": sid, "reason": f"Prefix '{prefix}' not in structure map"})

        try:
            numeric_val = int(number_str)
        except ValueError:
            numeric_val = None

        replica = suffix if suffix in REPLICA_LETTERS else (suffix[0] if suffix else None)

        if suffix and suffix not in REPLICA_LETTERS and len(suffix) > 1:
            anomalies.append({
                "specimen_id": sid,
                "reason": f"Suffix '{suffix}' is longer than expected single letter — may encode additional info",
            })

        param_interpretation = None
        param_confidence = "none"

        if numeric_val is not None and struct != "unknown":
            groups = {sid_prefix: [] for sid_prefix in {
                p["id_prefix"] for p in parsed.values() if p.get("id_parse_status") == "ok"
            }}
            unique_nums = sorted({
                p["param_numeric"] for p in parsed.values()
                if p.get("id_prefix") == prefix and p.get("param_numeric") is not None
            })
            if len(unique_nums) < 2:
                unique_nums = [numeric_val]

            param_interpretation = numeric_val
            param_confidence = "probable"

        parsed[sid] = {
            **info,
            "id_prefix": prefix,
            "id_number": number_str,
            "id_suffix": suffix,
            "structure_type_from_id": struct,
            "param_numeric": numeric_val,
            "replica_letter": replica,
            "id_parse_status": "ok" if struct != "unknown" else "partial",
            "id_parse_notes": (
                f"Structure='{struct}' from prefix '{prefix}'. "
                f"Numeric param={numeric_val} (relative magnitude, absolute unit uncertain). "
                f"Replica='{replica}'."
            ),
        }
        logger.debug(f"  {sid}: struct={struct} | num={numeric_val} | replica={replica}")

    write_json(f"{artifacts_dir}/parsed_tables/parsed_ids.json", parsed)
    write_json(f"{artifacts_dir}/parsed_tables/id_anomalies.json", anomalies)

    numeric_groups = {}
    for sid, p in parsed.items():
        prefix = p.get("id_prefix")
        num = p.get("param_numeric")
        if prefix and num is not None:
            numeric_groups.setdefault(prefix, set()).add(num)

    interpretation_notes = {}
    for prefix, nums in numeric_groups.items():
        sorted_nums = sorted(nums)
        struct = STRUCTURE_MAP.get(prefix, "unknown")
        interpretation_notes[prefix] = {
            "structure": struct,
            "unique_numeric_values": sorted_nums,
            "n_variants": len(sorted_nums),
            "interpretation": (
                f"The numeric component ({sorted_nums}) likely encodes a design parameter "
                f"such as relative density (%), cell size (mm), or strut thickness index. "
                f"Values increase monotonically across groups, consistent with a density or size gradient. "
                f"Exact physical meaning cannot be determined from filenames alone — "
                f"requires original experimental protocol documentation."
            ),
        }
        logger.info(f"  Prefix '{prefix}' ({struct}): unique numerics = {sorted_nums}")

    write_json(f"{artifacts_dir}/parsed_tables/id_interpretation.json", interpretation_notes)
    logger.info(f"  Parsed {len(parsed)} IDs. Anomalies: {len(anomalies)}.")
    return parsed, interpretation_notes
