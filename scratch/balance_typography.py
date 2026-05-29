import re

files_to_adjust = [
    "C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/frontend/src/components/layout/LeftPanel.tsx",
    "C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/frontend/src/components/layout/RightPanel.tsx",
    "C:/dev/impresorav3/PLA_3dPrinter_RESISTENCE/frontend/src/components/ai/ManufacturingPanel.tsx"
]

def balance_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Replace text-3xl with text-xl
    content = content.replace("text-3xl", "text-xl")
    
    # 2. Replace text-lg with text-base
    content = content.replace("text-lg", "text-base")
    
    # 3. Replace text-base with text-sm
    content = content.replace("text-base", "text-sm")
    
    # 4. Check for layout widths/heights that might have been scaled up
    # We keep standard padding and layout margins

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"Balanced typography in: {filepath}")

for path in files_to_adjust:
    balance_file(path)
