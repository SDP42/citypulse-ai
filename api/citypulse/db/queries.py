"""Shared, parameterised filter builder: lists, exports and analytics use the SAME filters so a number and the
rows behind it cannot disagree (blueprint 042). No caller-supplied SQL ever reaches the database."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Filters:
    category: str | None = None
    area_id: str | None = None
    source_id: str | None = None
    date_from: str | None = None  # inclusive IST day, 'YYYY-MM-DD'
    date_to: str | None = None    # inclusive IST day, 'YYYY-MM-DD'

    def as_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v}


# IST calendar day of a report: date-only values are already dates; instants are shifted +05:30 then truncated.
# Filters and trends share this expression so a number and the rows behind it always use the same day boundary.
IST_DAY = "(CASE WHEN length(o.reported_at)=10 THEN o.reported_at ELSE date(o.reported_at,'+330 minutes') END)"

FROM = ("FROM observation o JOIN source_registry s ON s.source_id=o.source_id "
        "LEFT JOIN area a ON a.area_id=o.area_id")


def where(synthetic: bool, f: Filters) -> tuple[str, list]:
    """WHERE clause. Synthetic and real data are never mixed in one result."""
    clauses, args = ["s.is_synthetic = ?"], [int(synthetic)]
    for col, val in (("o.category", f.category), ("o.area_id", f.area_id), ("o.source_id", f.source_id)):
        if val:
            clauses.append(f"{col} = ?")
            args.append(val)
    if f.date_from:  # Asia/Kolkata calendar days; undated rows never match a date filter
        clauses.append(f"{IST_DAY} >= ?")
        args.append(f.date_from)
    if f.date_to:
        clauses.append(f"{IST_DAY} <= ?")
        args.append(f.date_to)
    return " AND ".join(clauses), args
