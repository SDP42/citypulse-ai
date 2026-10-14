import pytest

from citypulse.core.csv_safety import is_formula_like, neutralise_formula
from citypulse.core.errors import AppError
from citypulse.ingest.normalise import parse_timestamp, redact, slug_category
from citypulse.ingest.parse import auto_map, parse_csv, validate_mapping
from tests.conftest import NOW


def ts(s, tz="Asia/Kolkata"):
    return parse_timestamp(s, tz, NOW)


def test_naive_timestamp_assumes_tz_and_converts_to_utc():
    value, precision, flags = ts("2026-08-03 09:00")
    assert value == "2026-08-03T03:30:00+00:00"  # 09:00 IST = 03:30 UTC
    assert precision == "minute" and "tz_assumed" in flags


def test_aware_timestamp_not_flagged():
    value, _, flags = ts("2026-08-03T10:00:00+05:30")
    assert value == "2026-08-03T04:30:00+00:00" and flags == []


def test_date_only_is_a_date_not_a_midnight_instant():
    assert ts("2026-08-03") == ("2026-08-03", "day", [])


def test_dmy_is_flagged_and_validated():
    assert ts("03/08/2026")[0] == "2026-08-03" and "dmy_format_assumed" in ts("03/08/2026")[2]
    for bad in ("31/02/2026", "29/02/2026", "not a date", "2026-13-01", ""):
        with pytest.raises(ValueError, match="invalid_timestamp"):
            ts(bad)


def test_out_of_range_timestamps_rejected():
    for bad in ("1999-12-31", "2026-10-20", "2030-01-01T00:00:00+00:00"):
        with pytest.raises(ValueError, match="timestamp_out_of_range"):
            ts(bad)


def test_redaction_phone_and_email():
    out, changed = redact("call 98765 43210 or +91 9876543210 / a.b@x.in")
    assert changed and "9876" not in out.replace("[phone]", "") and "[email]" in out
    assert redact("pothole near 12 main road")[1] is False


def test_category_slugs():
    assert slug_category(" Water Logging ") == "waterlogging"
    assert slug_category("street-light") == "streetlight"
    assert slug_category("") == ""


def test_formula_detection_does_not_flag_numbers():
    assert is_formula_like("=1+1") and is_formula_like("@SUM(A1)") and is_formula_like("-cmd|x")
    assert not is_formula_like("-12.5") and not is_formula_like("+91")
    assert neutralise_formula("=1+1") == "'=1+1" and neutralise_formula("plain") == "plain"
    assert neutralise_formula("-12.5") == "-12.5"


def test_parse_semicolon_and_cp1252():
    p = parse_csv("category;text\npothole;café road\n".encode("cp1252"))
    assert p.delimiter == ";" and p.encoding == "cp1252" and "encoding_cp1252_assumed" in p.flags
    assert p.rows == [{"category": "pothole", "text": "café road"}]


def test_parse_quoted_commas_and_multiline():
    p = parse_csv(b'category,text\npothole,"big, deep\nhole"\n')
    assert p.rows[0]["text"] == "big, deep\nhole"


@pytest.mark.parametrize("data,code", [(b"", "empty_file"), (b"   \n", "empty_file"), (b",,\n1,2,3\n", "no_header")])
def test_parse_rejects_bad_files(data, code):
    with pytest.raises(AppError) as e:
        parse_csv(data)
    assert e.value.code == code


def test_mapping_validation():
    h = ["Type", "Lat", "Lon", "when"]
    m = auto_map(h)
    assert m["category"] == "Type" and m["latitude"] == "Lat" and m["reported_at"] is None
    validate_mapping(m, h)
    with pytest.raises(AppError, match="not in the file"):
        validate_mapping({**m, "reported_at": "nope"}, h)
    with pytest.raises(AppError, match="Required"):
        validate_mapping({**m, "category": None}, h)
