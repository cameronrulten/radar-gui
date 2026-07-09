from radar_gui.serial_source import _DISTANCE_RE


def test_parses_plain_reading():
    match = _DISTANCE_RE.search(b"23cm\r\n")
    assert match is not None
    assert match.group(1) == b"23"


def test_parses_reading_with_extra_whitespace_and_case():
    match = _DISTANCE_RE.search(b"  118 CM \n")
    assert match is not None
    assert match.group(1) == b"118"


def test_ignores_lines_without_a_reading():
    assert _DISTANCE_RE.search(b"\r\n") is None
    assert _DISTANCE_RE.search(b"garbage\n") is None
