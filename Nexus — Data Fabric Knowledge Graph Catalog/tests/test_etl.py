
from pathlib import Path
import json
import pandas as pd
import unittest

BASE_DIR = Path(__file__).resolve().parents[1]

class ETLOutputsTest(unittest.TestCase):
    def test_processed_files_exist(self):
        self.assertTrue((BASE_DIR / "data/processed/base_integrada.csv").exists())
        self.assertTrue((BASE_DIR / "data/processed/quality_report.json").exists())

    def test_base_not_empty(self):
        df = pd.read_csv(BASE_DIR / "data/processed/base_integrada.csv")
        self.assertGreater(len(df), 0)
        required = {"id_transacao","id_contrato","id_cliente","id_agencia","id_produto","transacao_valor"}
        self.assertTrue(required.issubset(df.columns))

if __name__ == "__main__":
    unittest.main()
