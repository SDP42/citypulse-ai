"""Join DataMeet BMC ward polygons (CC BY-SA 2.5 IN) with Census 2011 ward population (public domain).
Output: data/processed/mumbai_wards.geojson  (derived; keep DataMeet attribution + ShareAlike).
Population is Census 2011 - an exposure denominator with a 15-year vintage gap, NOT current.
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

pop = defaultdict(int)
for r in csv.DictReader(open(RAW / "census" / "mumbai_census_2011_wardlevel.csv")):
    pop[r["Ward Name"].strip()] += int(r["Total Population"])

gj = json.load(open(RAW / "boundaries" / "BMC_Wards.geojson"))
missing = []
for f in gj["features"]:
    w = f["properties"]["name"]
    f["properties"] = {"ward": w, "population_2011": pop.get(w), "population_source": "Census 2011 (ORGI via OpenCity)",
                       "boundary_source": "datameet-bmc-wards", "boundary_vintage": "unstated"}
    if w not in pop:
        missing.append(w)
gj["crs"] = {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}}
out = ROOT / "data" / "processed" / "mumbai_wards.geojson"
out.write_text(json.dumps(gj, separators=(",", ":")))
print(f"{len(gj['features'])} wards, total pop {sum(pop.values()):,}, unmatched: {missing or 'none'}")
