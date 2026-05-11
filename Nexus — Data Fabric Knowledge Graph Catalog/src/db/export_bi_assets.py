
from __future__ import annotations
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
POWERBI_DIR = BASE_DIR / "powerbi"

def main():
    for path in POWERBI_DIR.glob("*.csv"):
        df = pd.read_csv(path)
        print(f"{path.name}: {df.shape}")
    print("Assets do Power BI validados.")

if __name__ == "__main__":
    main()
