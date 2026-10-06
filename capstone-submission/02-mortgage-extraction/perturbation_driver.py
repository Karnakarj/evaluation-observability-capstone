"""System 2 perturbation driver (no system code changed).
Takes the extraction the CLI produced for income_sum_mismatch.txt (discrepancy-run.txt),
perturbs ONLY income.stated_monthly_total, and re-runs the real validator (default $1 tolerance).
Run from the mortgage solution dir:  .venv/bin/python perturbation_driver.py
"""
import json
from pathlib import Path

from mortgage_extractor.models import MortgageExtraction
from mortgage_extractor.validator import validate

raw = Path(__file__).with_name("discrepancy-run.txt").read_text().splitlines()
body = json.loads("\n".join(raw[next(i for i, s in enumerate(raw) if s.startswith("{")):]))
base = body["extraction"]

cases = [
    ("A. UNPERTURBED - stated total as printed on the paystub", None),
    ("B. PERTURBED - stated total edited to the line-item sum", 9642.17),
    ("C. PERTURBED - stated total off by $0.50 (inside tolerance)", 9642.67),
    ("D. PERTURBED - stated total off by $1.50 (outside tolerance)", 9643.67),
]
for label, stated in cases:
    data = json.loads(json.dumps(base))
    if stated is not None:
        data["income"]["stated_monthly_total"] = stated
    ext = MortgageExtraction.model_validate(data)
    rep = validate(ext)
    print(f"== {label}")
    print(f"   line-item sum : {ext.income.calculated_monthly_total}")
    print(f"   stated total  : {ext.income.stated_monthly_total}")
    print(f"   report        : {rep.model_dump_json()}")
    print()
