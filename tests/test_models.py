from itertools import islice

from radar_gui.models import sweep_angles


def test_sweep_angles_matches_arduino_loop_sequence():
    angles = list(islice(sweep_angles(), 0, 365))
    assert angles[:5] == [0, 1, 2, 3, 4]
    assert angles[179:183] == [179, 180, 180, 179]
    # index 361 is the last step of the down-sweep (angle 0); the cycle then
    # restarts the up-sweep from 0 again at index 362.
    assert angles[360:365] == [1, 0, 0, 1, 2]


def test_sweep_angles_stays_within_servo_range():
    for angle in islice(sweep_angles(), 0, 2000):
        assert 0 <= angle <= 180
