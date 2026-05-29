import json
from pathlib import Path
from typing import Dict, Any

class MaterialDatabaseManager:
    def __init__(self):
        self.materials_dir = Path("C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/materials")
        self.db = {}
        self.load_database()

    def load_database(self):
        # 1. Load shared categories
        self.db["shared"] = {}
        shared_path = self.materials_dir / "shared"
        for category_dir in shared_path.iterdir():
            if category_dir.is_dir():
                prop_file = category_dir / "properties.json"
                rules_file = category_dir / "rules.json"
                
                if prop_file.exists():
                    with open(prop_file, "r", encoding="utf-8") as f:
                        self.db["shared"][category_dir.name] = json.load(f)
                elif rules_file.exists():
                    with open(rules_file, "r", encoding="utf-8") as f:
                        self.db["shared"][category_dir.name] = json.load(f)

        # 2. Load polymer categories (TPU, ABS, PETG)
        for material_name in ["TPU", "ABS", "PETG"]:
            self.db[material_name] = {}
            mat_path = self.materials_dir / material_name
            if mat_path.exists():
                for category_dir in mat_path.iterdir():
                    if category_dir.is_dir():
                        prop_file = category_dir / "properties.json"
                        profiles_file = category_dir / "profiles.json"
                        variants_file = category_dir / "variants.json"
                        
                        target_file = None
                        if prop_file.exists():
                            target_file = prop_file
                        elif profiles_file.exists():
                            target_file = profiles_file
                        elif variants_file.exists():
                            target_file = variants_file
                            
                        if target_file:
                            with open(target_file, "r", encoding="utf-8") as f:
                                self.db[material_name][category_dir.name] = json.load(f)

    def get_full_database(self) -> Dict[str, Any]:
        return self.db

    def get_material_data(self, material: str) -> Dict[str, Any]:
        mat_key = str(material).upper().strip()
        return self.db.get(mat_key, {})

    def get_shared_data(self, category: str) -> Dict[str, Any]:
        return self.db.get("shared", {}).get(category, {})

_manager_instance = None

def get_material_db_manager() -> MaterialDatabaseManager:
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = MaterialDatabaseManager()
    return _manager_instance
