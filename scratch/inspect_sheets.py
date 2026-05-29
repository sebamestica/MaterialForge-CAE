import pandas as pd
import os

def inspect_mendeley_sheets():
    filepath = r"C:\dev\impresorav3\PLA_3dPrinter_RESISTENCE\data\nvzrft8c7d-2\Compressivedata.xlsx"
    xl = pd.ExcelFile(filepath)
    print("Mendeley Compressivedata G29A:")
    df = xl.parse("G29A")
    print("G29A columns:", df.columns.tolist())
    print(df.head(10))
    print(df.tail(5))
    
    filepath_t = r"C:\dev\impresorav3\PLA_3dPrinter_RESISTENCE\data\nvzrft8c7d-2\TensiondataA.xlsx"
    xl_t = pd.ExcelFile(filepath_t)
    print("\nMendeley TensiondataA Resumen:")
    df_res = xl_t.parse("Resumen")
    print(df_res.head(10))

def inspect_carbon_sheets():
    filepath = r"C:\dev\impresorav3\PLA_3dPrinter_RESISTENCE\data\Mechanical Properties of 3D-Printing Carbon-PLA Filament with Various Printing Directions\0 Deg.xls"
    xl = pd.ExcelFile(filepath)
    print("\nCarbon-PLA 0 Deg UniTest.TensileCond:")
    df_cond = xl.parse("UniTest.TensileCond")
    print(df_cond.head(20))
    
    print("\nCarbon-PLA 0 Deg Data:")
    df_data = xl.parse("Data")
    print(df_data.head(20))
    
    print("\nCarbon-PLA 0 Deg SS-Curve001:")
    df_curve = xl.parse("SS-Curve001")
    print(df_curve.head(10))

if __name__ == "__main__":
    inspect_mendeley_sheets()
    inspect_carbon_sheets()
