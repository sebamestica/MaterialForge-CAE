from typing import Dict, Any, List, Optional
from ..data_access.tabular_store import TabularStore

class MaterialLookupTool:
    def __init__(self, store: Optional[TabularStore] = None):
        self.store = store or TabularStore()

    def get_material_info(self, material: str) -> Dict[str, Any]:
        """Queries training data to get average properties and samples count of a material."""
        return self.store.get_material_summary(material)

    def get_known_materials(self) -> List[str]:
        """Gets a list of all materials in the training set."""
        return self.store.get_available_materials()
