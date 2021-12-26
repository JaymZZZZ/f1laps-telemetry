from unittest import TestCase
from unittest.mock import MagicMock, patch

from receiver.penalty_base import PenaltyBase


class PenaltyBaseTest(TestCase):

    def test_no_api_class_returns_none(self):
        penalty = PenaltyBase()
        penalty.session = MagicMock()
        self.assertIsNone(penalty.send_to_f1laps())
    
    def test_no_session_returns_none(self):
        penalty = PenaltyBase()
        penalty.f1laps_api_class = MagicMock()
        self.assertIsNone(penalty.send_to_f1laps())
    
    def test_success_api(self):
        penalty = PenaltyBase()
        penalty.session = MagicMock()
        api_mock = MagicMock()
        api_mock.penalty_create.return_value = True
        penalty.f1laps_api_class = api_mock
        penalty.infringement_type = 5
        success = penalty.send_to_f1laps()
        self.assertTrue(success)
        penalty.f1laps_api_class.return_value.penalty_create.assert_called_with(penalty_type=None, infringement_type=5, vehicle_index=None, other_vehicle_index=None, time_spent_gained=None, lap_number=None, places_gained=None)
    
    def test_error_api(self):
        penalty = PenaltyBase()
        penalty.session = MagicMock()
        api_mock = MagicMock()
        api_mock.penalty_create.return_value = False
        penalty.f1laps_api_class = api_mock
        penalty.infringement_type = 5
        success = penalty.send_to_f1laps()
        self.assertFalse(success)
        penalty.f1laps_api_class.return_value.penalty_create.assert_called_with(penalty_type=None, infringement_type=5, vehicle_index=None, other_vehicle_index=None, time_spent_gained=None, lap_number=None, places_gained=None)


if __name__ == '__main__':
    unittest.main()