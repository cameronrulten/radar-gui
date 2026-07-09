from radar_gui.audio_warning import _zone_for_distance


def test_no_warning_at_or_beyond_warn_range():
    assert _zone_for_distance(40.0, 40.0) is None
    assert _zone_for_distance(100.0, 40.0) is None


def test_zone_boundaries_scale_with_warn_range():
    warn_range = 40.0
    assert _zone_for_distance(3.0, warn_range) == 0  # < 10% of warn_range -> tightest zone
    assert _zone_for_distance(20.0, warn_range) == 2  # 30%-60% band
    assert _zone_for_distance(35.0, warn_range) == 3  # 60%-100% band, loosest


def test_negative_distance_ignored():
    assert _zone_for_distance(-1.0, 40.0) is None
