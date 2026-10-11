"""Учебный пример обработки таблицы сценариев; расчётов tNavigator здесь нет."""
import argparse
import csv
import math
from pathlib import Path


def compare_runs(rows):
    normalized = []
    for row in rows:
        item = {**row}
        for col in ["water_mass_fraction", "inlet_pressure", "outlet_pressure", "inlet_temperature", "outlet_temperature"]:
            item[col] = float(row[col])
            if not math.isfinite(item[col]):
                raise ValueError(f"Неконечное значение в {col}")
        if not 0 <= item["water_mass_fraction"] <= 1:
            raise ValueError("Массовая доля воды должна быть от 0 до 1")
        if item["inlet_pressure"] <= 0 or item["outlet_pressure"] <= 0:
            raise ValueError("Давления должны быть положительными")
        item["pressure_drop"] = item["inlet_pressure"] - item["outlet_pressure"]
        item["temperature_drop"] = item["inlet_temperature"] - item["outlet_temperature"]
        normalized.append(item)
    conditions = {(r["inlet_pressure"], r["inlet_temperature"]) for r in normalized}
    if len(conditions) > 1:
        raise ValueError("Для этого сравнения фиксируйте входные давление и температуру")
    result = []
    for correlation in sorted({r["correlation"] for r in normalized}):
        group = sorted((r for r in normalized if r["correlation"] == correlation), key=lambda r:r["water_mass_fraction"])
        fractions = [r["water_mass_fraction"] for r in group]
        if len(set(fractions)) != len(fractions):
            raise ValueError("Повторяющиеся доли воды внутри одного варианта")
        previous = None
        for row in group:
            row["pressure_sensitivity"] = ""
            if previous is not None:
                row["pressure_sensitivity"] = (row["pressure_drop"]-previous["pressure_drop"])/(row["water_mass_fraction"]-previous["water_mass_fraction"])
            result.append(row)
            previous = row
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--output", type=Path, default=Path("comparison.csv"))
    args = parser.parse_args()
    with args.csv.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        required = {"correlation","water_mass_fraction","inlet_pressure","outlet_pressure","inlet_temperature","outlet_temperature"}
        if not fields or not required.issubset(fields):
            raise ValueError("В таблице не хватает столбцов сценария")
        result = compare_runs(list(reader))
    with args.output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields+["pressure_drop","temperature_drop","pressure_sensitivity"])
        writer.writeheader(); writer.writerows(result)
    print(f"Обработано {len(result)} строк. Результат: {args.output}")
