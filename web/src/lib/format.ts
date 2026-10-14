// Plain-language labels for importer error and flag codes (what happened + what it means for the data).
export const CODE_TEXT: Record<string, string> = {
  invalid_timestamp: "Date could not be read — row quarantined",
  timestamp_out_of_range: "Date before 2000 or in the future — row quarantined",
  missing_category: "No category — row quarantined",
  coords_possibly_swapped: "Latitude/longitude look swapped — quarantined, not auto-corrected",
  coords_out_of_bounds: "Point outside the study area — row quarantined",
  coords_invalid_range: "Coordinates impossible — row quarantined",
  coords_incomplete: "Only one of latitude/longitude given — row quarantined",
  coords_not_numeric: "Coordinates are not numbers — row quarantined",
  conflicting_duplicate_id: "Same ID, different content — quarantined, nothing overwritten",
  field_too_long: "A cell is too long — row quarantined",
  missing_timestamp: "No time given — kept as unknown (not replaced by import time)",
  no_point_coordinates: "No point — kept at area level",
  location_unresolved: "Location unresolved — kept without a place",
  tz_assumed: "No timezone — Asia/Kolkata assumed",
  dmy_format_assumed: "dd/mm/yyyy assumed",
  pii_redacted: "Phone/email redacted from text",
  formula_like_text: "Text looks like a spreadsheet formula — stored as plain text",
  unrecognised_category: "Category not in the known vocabulary",
  outside_all_areas: "Point is inside the study box but outside every area",
  text_truncated: "Text cut to 2,000 characters",
};

export const describe = (code: string) => CODE_TEXT[code] ?? code;

export function formatWhen(v: string | null, precision: string): string {
  if (!v) return "unknown";
  if (precision === "day") return v;
  const d = new Date(v);
  return Number.isNaN(d.getTime()) ? v : d.toLocaleString("en-IN", { timeZone: "Asia/Kolkata", dateStyle: "medium", timeStyle: "short" }) + " IST";
}

/** Headers from the first line of a CSV, for building a mapping form before the server has seen the file. */
export function sniffHeaders(text: string): string[] {
  const first = text.split(/\r?\n/, 1)[0] ?? "";
  const delim = [",", ";", "\t", "|"].map((d) => [d, first.split(d).length] as const).sort((a, b) => b[1] - a[1])[0][0];
  return first.split(delim).map((h) => h.replace(/^"|"$/g, "").trim()).filter(Boolean);
}
