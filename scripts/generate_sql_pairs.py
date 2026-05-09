"""Text-to-SQL: generate training pairs + self-correction examples."""
import json, random, argparse, numpy as np
from pathlib import Path
random.seed(42); np.random.seed(42)

TABLES = {
    "promotional_performance": ["brand","channel","quarter","spend","roi","trx_volume","response_rate"],
    "hcp_engagement": ["hcp_id","specialty","region","channel","touches","responses","tier"],
    "brand_metrics": ["brand","quarter","market_share","nbrx","adherence_rate","awareness"],
}

def gen_pair():
    table = random.choice(list(TABLES.keys()))
    cols = TABLES[table]
    col = random.choice(cols)
    brand = random.choice(["Cardivex","Immunolex","OncoPrime","NeuraStar","RespiClear"])
    templates = [
        (f"What is the total {col} for {brand}?",
         f"SELECT SUM({col}) FROM {table} WHERE brand = '{brand}';"),
        (f"Show top 5 records by {col} from {table}.",
         f"SELECT * FROM {table} ORDER BY {col} DESC LIMIT 5;"),
        (f"What is the average {col} per quarter for {brand}?",
         f"SELECT quarter, AVG({col}) FROM {table} WHERE brand = '{brand}' GROUP BY quarter;"),
    ]
    q, sql = random.choice(templates)
    # Self-correction example (30% of the time)
    if random.random() < 0.3:
        bad_sql = sql.replace("SUM", "COUNT").replace("AVG", "SUM")
        error = f"ERROR: column '{random.choice(cols)}' ambiguous"
        corrected = sql
        return {"instruction": q, "initial_sql": bad_sql, "error": error,
                "corrected_sql": corrected, "category": "self_correct", "table": table}
    return {"instruction": q, "sql": sql, "category": "direct", "table": table}

def main():
    p = argparse.ArgumentParser(); p.add_argument("--n", type=int, default=1000)
    p.add_argument("--output_dir", default="data"); a = p.parse_args()
    out = Path(a.output_dir); out.mkdir(parents=True, exist_ok=True)
    examples = [gen_pair() for _ in range(a.n)]
    random.shuffle(examples); split = int(len(examples) * 0.9)
    for name, data in [("train", examples[:split]), ("eval", examples[split:])]:
        with open(out / f"{name}.jsonl", "w") as f:
            for e in data: f.write(json.dumps(e) + "\n")
    direct = sum(1 for e in examples if e["category"] == "direct")
    sc = sum(1 for e in examples if e["category"] == "self_correct")
    print(f"✅ Generated {len(examples)} Text-to-SQL pairs")
    print(f"   Direct: {direct}, Self-correct: {sc}")
    print(f"   Tables: {list(TABLES.keys())}")
    print(f"   📁 {out}/train.jsonl, eval.jsonl")

if __name__ == "__main__": main()
