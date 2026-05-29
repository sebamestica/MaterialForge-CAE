import sys
from pathlib import Path

# Setup paths
BASE_DIR = Path(__file__).parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))
if str(BASE_DIR / "backend") not in sys.path:
    sys.path.append(str(BASE_DIR / "backend"))

from ia_agent.tools.prediction_tool import PredictionTool

def main():
    print("=== MODEL INFERENCE CLI TEST ===")
    tool = PredictionTool()
    
    mock_config = {
        "material": "PLA",
        "infill": 35.0,
        "pattern": "gyroid",
        "cellSize": 3.0,
        "cellThickness": 0.6,
        "wallThickness": 1.2,
        "dimX": 5.0,
        "dimY": 5.0,
        "dimZ": 5.0,
        "resolution": "Alta",
        "layerHeight": 0.20,
        "printSpeed": 50.0,
        "viewportMode": "solid",
        "shapeType": "Cubo"
    }
    
    print("Running prediction for mock config:")
    for k, v in mock_config.items():
        print(f"  {k}: {v}")
        
    res = tool.predict_mechanical_response(mock_config)
    print("\nPrediction Results:")
    import json
    print(json.dumps(res, indent=4))

if __name__ == "__main__":
    main()
