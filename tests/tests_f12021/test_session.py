from unittest import TestCase
from unittest.mock import patch, MagicMock

from receiver.f12021.session import F12021Session


class F12021SessionTest(TestCase):
    def test_string(self):
        session = F12021Session(123)
        session.team_id = 1
        session.lap_list = {2: []}
        self.assertEqual(str(session), "F12021 Session 123 (None, team 1, type None, offline, 1 laps)")
        session.track_id = 2
        self.assertEqual(str(session), "F12021 Session 123 (Shanghai, team 1, type None, offline, 1 laps)")
        session.session_type = 6
        self.assertEqual(str(session), "F12021 Session 123 (Shanghai, team 1, type qualifying_2, offline, 1 laps)")

    @patch('receiver.f12021.session.F12021Session.post_process')
    def test_complete_lap(self, mock_post_process):
        session = F12021Session(123)
        session.complete_lap(lap_number = 1, sector_1_ms = 11111, sector_2_ms = 22222, sector_3_ms = 33333, tyre_visual = 16)
        self.assertEqual(session.lap_list, {1: {'lap_number': 1, 'sector_1_ms': 11111, 'sector_2_ms': 22222, 'sector_3_ms': 33333, 'tyre_compound_visual': 16}})
        self.assertEqual(mock_post_process.call_count, 1)

    def test_get_track_name(self):
        session = F12021Session(123)
        session.track_id = 5
        self.assertEqual(session.get_track_name(), "Monaco")

    def test_get_session_type(self):
        session = F12021Session(123)
        session.session_type = 7
        self.assertEqual(session.get_session_type(), "qualifying_3")

    def test_lap_should_be_sent_to_f1laps(self):
        session = F12021Session(123)
        # Test lap not found
        self.assertEqual(session.lap_should_be_sent_to_f1laps(1), False)
        session.lap_list = {1: {1: {'lap_number': 1, 'sector_1_ms': 11111, 'sector_2_ms': 22222, 'tyre_compound_visual': 16}}}
        # Test lap doesnt have all sectors
        self.assertEqual(session.lap_should_be_sent_to_f1laps(1), False)
        session.lap_list = {1: {'lap_number': 1, 'sector_1_ms': 11111, 'sector_2_ms': 22222, 'sector_3_ms': 33333, 'tyre_compound_visual': 16}}
        # Test success case
        self.assertEqual(session.lap_should_be_sent_to_f1laps(1), True)
        # Test lap was already sent to F1Laps
        self.assertEqual(session.lap_should_be_sent_to_f1laps(1), False)

    def test_lap_should_be_sent_as_session(self):
        session = F12021Session(123)
        self.assertEqual(session.lap_should_be_sent_as_session(), False)
        session.session_type = 10
        self.assertEqual(session.lap_should_be_sent_as_session(), True)
        session.session_type = 13
        self.assertEqual(session.lap_should_be_sent_as_session(), False)

    @patch('receiver.f12021.session.F1LapsAPI2021.lap_create')
    def test_send_lap_to_f1laps(self, mock_api):
        mock_api.return_value = MagicMock(status_code=201)
        session = F12021Session(123)
        session.track_id = 10
        session.team_id = 2
        session.session_type = 13
        session.lap_list = {1: {'lap_number': 1, 'sector_1_ms': 11111, 'sector_2_ms': 22222, 'sector_3_ms': 33333, 'tyre_compound_visual': 16}}
        self.assertEqual(session.send_lap_to_f1laps(1), None)
        mock_api.assert_called_with(track_id=10, team_id=2, conditions='dry', game_mode='time_trial', sector_1_time=11111, sector_2_time=22222, sector_3_time=33333, setup_data={}, is_valid=True, telemetry_data_string=None)

    @patch('receiver.f12021.session.F1LapsAPI2021.session_create_or_update')
    def test_send_session_to_f1laps(self, mock_api):
        mock_api.return_value = True, "vettel2021"
        session = F12021Session(123)
        session.track_id = 10
        session.team_id = 2
        session.session_type = 10
        session.lap_list = {}
        session.send_session_to_f1laps()
        self.assertEqual(session.f1_laps_session_id, "vettel2021")
        mock_api.assert_called_with(f1laps_session_id=None, track_id=10, team_id=2, session_uid=123, conditions='dry', session_type='race', finish_position=None, points=None, result_status=None, lap_times=[], setup_data={}, is_online_game=False, ai_difficulty=None)

    def test_is_valid_for_f1laps_team_zero(self):
        session = F12021Session(123)
        session.team_id = 0
        session.session_type = 1
        self.assertEqual(session.is_valid_for_f1laps(), True)
        session.team_id = None
        self.assertEqual(session.is_valid_for_f1laps(), False)


if __name__ == '__main__':
    unittest.main()