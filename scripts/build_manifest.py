"""Write data/raw/MANIFEST.json: url, sha256, bytes, licence, attribution for every downloaded raw file.
Only openly-licensed data is collected (see docs/DATA_POLICY.md). Re-run after adding files.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
OC = "https://data.opencity.in/dataset/1a81291d-369d-43e6-97b1-e62680434437/resource"

FILES = [
    ("osm/western-zone-latest.osm.pbf", "osm-extract",
     "https://download.geofabrik.de/asia/india/western-zone-latest.osm.pbf", "ODbL 1.0",
     "(c) OpenStreetMap contributors; extract by Geofabrik GmbH", "OSM data to 2026-10-13T20:21Z"),
    ("boundaries/BMC_Wards.geojson", "datameet-bmc-wards",
     "https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/Mumbai/BMC_Wards.geojson",
     "CC BY-SA 2.5 India", "DataMeet (Pune chapter) - Mumbai Municipal Data", "24 BMC wards; vintage unstated"),
    ("boundaries/datameet_Mumbai_Readme.md", "datameet-bmc-wards",
     "https://raw.githubusercontent.com/datameet/Municipal_Spatial_Data/master/Mumbai/Readme.md",
     "CC BY-SA 2.5 India", "DataMeet", "licence evidence"),
    ("census/mumbai_census_2011_wardlevel.csv", "opencity-mumbai-census",
     f"{OC}/fcfeacdc-aa80-4028-a468-f0267fa05d23/download/95e22d97-7f59-4214-b244-2abbf52e6027.csv",
     "Public Domain (Open Definition) per OpenCity", "Office of the Registrar General & Census Commissioner, India via OpenCity", "Census 2011"),
    ("census/mumbai_city_pca.csv", "opencity-mumbai-census",
     f"{OC}/b2261b97-db46-4d14-a1a7-a2a14976cede/download/fca87e9a-f012-41fe-93bc-cd1ae7e1f82a.csv",
     "Public Domain (Open Definition) per OpenCity", "ORGI via OpenCity", "Wards 1-9"),
    ("census/mumbai_suburban_pca.csv", "opencity-mumbai-census",
     f"{OC}/a33e01ed-6dec-458b-af70-395c59d4f89e/download/43c17944-e918-4270-ae91-63f986adfb93.csv",
     "Public Domain (Open Definition) per OpenCity", "ORGI via OpenCity", "Wards 10-24"),
]
for name in ("south", "central", "north"):
    FILES.append((f"weather/openmeteo_{name}_2018_2026.json", "openmeteo-archive",
                  "https://archive-api.open-meteo.com/v1/archive (daily precipitation_sum, rain_sum, precipitation_hours; 2018-01-01..2026-10-10)",
                  "CC BY 4.0", "Weather data by Open-Meteo.com (https://open-meteo.com/)",
                  "Reanalysis grid cell, NOT a gauge; response lat/lon is the snapped cell"))

out = []
for rel, sid, url, lic, attr, note in FILES:
    p = RAW / rel
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    out.append({"path": f"data/raw/{rel}", "source_id": sid, "url": url, "licence": lic,
                "attribution": attr, "bytes": p.stat().st_size, "sha256": h.hexdigest(), "note": note})
(RAW / "MANIFEST.json").write_text(json.dumps(
    {"generated_at": datetime.now(timezone.utc).isoformat(), "files": out}, indent=1))
print(f"manifest: {len(out)} files")
