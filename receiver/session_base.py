import json


class SessionBase:
    weather_ids = []
    telemetry_enabled = True

    def __str__(self):
        return "%s Session %s (%s, team %s, type %s, %s, %s laps)" % (
            self.game_version.upper(),
            self.session_udp_uid,
            self.get_track_name(),
            self.team_id,
            self.get_session_type(),
            "online" if self.is_online_game else "offline",
            len(self.lap_list) if self.lap_list else 0
            )

    def map_weather_ids_to_f1laps_token(self):
        """
        Map UDP weather IDs to F1Laps weather token
        0-2: dry; 3-5: wet; both: mixed
        """
        has_dry_weather = any(x in self.weather_ids for x in [0, 1, 2])
        has_wet_weather = any(x in self.weather_ids for x in [3, 4, 5])
        if has_dry_weather and has_wet_weather:
            return 'mixed'
        else:
            return 'wet' if has_wet_weather else 'dry'

    def get_lap_telemetry_data(self, lap_number):
        if self.telemetry_enabled:
            telemetry_data = self.telemetry.get_telemetry_api_dict(lap_number)
            if telemetry_data:
                return json.dumps(telemetry_data)
        return None