import os
import openpyxl
import pandas as pd

def inspect_mendeley_lattice():
    print("=== INSPECTING MENDELEY LATTICE ===")
    path = r"C:\dev\impresorav3\PLA_3dPrinter_RESISTENCE\data\nvzrft8c7d-2"
    if not os.path.exists(path):
        print(f"Path not found: {path}")
        return
        
    for fname in os.listdir(path):
        if fname.endswith(".xlsx"):
            filepath = os.path.join(path, fname)
            print(f"\nFile: {fname}")
            try:
                xl = pd.ExcelFile(filepath)
                sheets = xl.sheet_names
                print(f"Number of sheets: {len(sheets)}")
                print(f"First 5 sheets: {sheets[:5]}")
                # Load first sheet and print info
                df = xl.parse(sheets[0], nrows=5)
                print("First sheet columns & preview:")
                print(df.columns.tolist())
                print(df.head(2))
            except Exception as e:
                print(f"Error reading {fname}: {e}")

def inspect_carbon_pla():
    print("\n=== INSPECTING CARBON-PLA ===")
    path = r"C:\dev\impresorav3\PLA_3dPrinter_RESISTENCE\data\Mechanical Properties of 3D-Printing Carbon-PLA Filament with Various Printing Directions"
    if not os.path.exists(path):
        print(f"Path not found: {path}")
        return
        
    for fname in os.listdir(path):
        if fname.endswith(".xls") or fname.endswith(".xlsx"):
            filepath = os.path.join(path, fname)
            print(f"\nFile: {fname}")
            try:
                xl = pd.ExcelFile(filepath)
                sheets = xl.sheet_names
                print(f"Sheets: {sheets}")
                df = xl.parse(sheets[0], nrows=5)
                print("First sheet columns & preview:")
                print(df.columns.tolist())
                print(df.head(2))
                break # inspect just one
            except Exception as e:
                print(f"Error reading {fname}: {e}")

def inspect_auxiliary_stress_strain():
    print("\n=== INSPECTING AUXILIARY STRESS-STRAIN ===")
    path = r"C:\dev\impresorav3\PLA_3dPrinter_RESISTENCE\data\Raw Dataset of tensile engineering stress-strain from advanced polymer architecture fluoroelastomer test inflatable seals, produced by cold feed extrusion and continuous cure and aimed at Gen IV Sodium-cooled Fast Reactor technology\RAW_ESS_SEALS_CSV"
    if not os.path.exists(path):
        print(f"Path not found: {path}")
        return
        
    for root, dirs, files in os.walk(path):
        for f in files:
            if f.endswith(".csv"):
                filepath = os.path.join(root, f)
                print(f"\nFile: {f}")
                try:
                    df = pd.read_csv(filepath, nrows=5)
                    print("Columns & preview:")
                    print(df.columns.tolist())
                    print(df.head(2))
                    return # just one
                except Exception as e:
                    print(f"Error reading {f}: {e}")

if __name__ == "__main__":
    inspect_mendeley_lattice()
    inspect_carbon_pla()
    inspect_auxiliary_stress_strain()
