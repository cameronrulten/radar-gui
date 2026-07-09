from radar_gui.serial_source import _parse_line


def test_parses_angle_line():
    assert _parse_line(b"90 degrees\r\n") == ("angle", 90)


def test_parses_distance_line():
    assert _parse_line(b"23 cm\r\n") == ("distance", 23)


def test_tolerant_of_whitespace_and_case():
    assert _parse_line(b"  180 DEGREES \n") == ("angle", 180)
    assert _parse_line(b"118cm\n") == ("distance", 118)


def test_ignores_lines_matching_neither_pattern():
    assert _parse_line(b"\r\n") is None
    assert _parse_line(b"garbage\n") is None
