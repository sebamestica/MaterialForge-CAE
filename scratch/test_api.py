import requests
import json

BACKEND_URL = "http://127.0.0.1:8000"

def test_predict():
    url = f"{BACKEND_URL}/api/predict_structural_load"
    payload = {
        "source": "experimental_lab",
        "geometry": {
            "boundingBoxMm": [50.0, 50.0, 50.0],
            "volumeMm3": 125000.0,
        },
        "material": {
            "type": "pla",
        },
        "slicing": {
            "patternType": "gyroid",
            "infillPercentage": 35.0,
            "shellThicknessMm": 1.2,
            "printOrientationDeg": 0.0,
            "layerHeightMm": 0.2,
            "printSpeedMmS": 50.0,
        },
        "printerName": "Creality K1 Max"
    }
    print(f"Testing POST {url}...")
    try:
        res = requests.post(url, json=payload)
        print("Status code:", res.status_code)
        print("Response:", json.dumps(res.json(), indent=2)[:500])
    except Exception as e:
        print("Error:", e)

def test_mesh():
    url = f"{BACKEND_URL}/api/generate_mesh"
    payload = {
        "pattern": "gyroid",
        "infillDensity": 35.0,
        "wallThickness": 1.2,
        "infillThickness": 0.6,
        "material": "pla",
        "size": 50.0,
        "showShell": True,
        "cellSize": 6.0,
        "orientation": "Isotrópica",
        "resolution": "Alta"
    }
    print(f"Testing POST {url}...")
    try:
        res = requests.post(url, json=payload)
        print("Status code:", res.status_code)
        data = res.json()
        print("Response keys:", list(data.keys()))
        print("Vertices count:", len(data.get("vertices", [])))
        print("Faces count:", len(data.get("faces", [])))
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_predict()
    print("\n" + "="*40 + "\n")
    test_mesh()
