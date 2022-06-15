import logging
log = logging.getLogger(__name__)

from receiver.lap_telemetry_base import LapTelemetryBase
from receiver.f12022.types import SESSION_TYPES_WITH_OUTLAP, \
                                  SESSION_TYPES_WITH_IN_AND_OUT_LAP, \
                                  SESSION_TYPES_TIME_TRIAL


class LapBase:
    """Holds all information about a lap"""
    # Session info
    session_type = None

    # Lap info
    lap_number = None
    pit_status = None
    car_race_position = None
    is_valid = True
    sector_1_ms = None
    sector_2_ms = None
    sector_3_ms = None

    # Telemetry
    telemetry = None
    telemetry_model = LapTelemetryBase

    # Settings
    MAX_DISTANCE_COUNT_AS_NEW_LAP = 200

    def __init__(self, lap_number, session_type):
        # Set variables
        self.lap_number = lap_number
        self.session_type = session_type

        # Log lap init
        log.info("### %s started" % self)

    def __str__(self):
        return "Lap #%s" % self.lap_number
    
    def update(self, lap_values=None, telemetry_values=None):
        """Update the lap with new data"""
        current_distance = telemetry_values.get("lap_distance")
        new_sector_1_time = telemetry_values.get("sector_1_ms")
        if self.is_in_or_outlap(current_distance):
            # Don't update values for in or outlaps
            pass
        elif self.lap_is_complete(new_sector_1_time):
            # Don't update values for completed laps
            pass
        else:
            # Init telemetry if we don't have it yet
            if not self.telemetry:
                self.telemetry = self.telemetry_model(self.lap_number, self.session_type)
            # Update this lap object
            for key, value in lap_values:
                setattr(self, key, value)
            # Update linked LapTelemetry object
            self.telemetry.update(telemetry_values)
    
    def lap_is_complete(self, new_sector_1_time):
        """
        Check if the current lap is complete, i.e. has all sector times, 
        in which case we don't overwrite it anymore
        """
        if self.session_type in SESSION_TYPES_TIME_TRIAL:
            return False
        all_sectors_set = bool(self.sector_1_ms and self.sector_2_ms and self.sector_3_ms)
        if all_sectors_set and new_sector_1_time in ["0", 0, None, ""]:
            return True
        return False
    
    def is_in_or_outlap(self, current_distance):
        """Check if the current lap is an inlap or outlap"""
        if self.session_type in SESSION_TYPES_WITH_OUTLAP:
            return self.is_race_inlap(current_distance)
        # Quali sessions have inlaps and outlaps
        elif self.session_type in SESSION_TYPES_WITH_IN_AND_OUT_LAP:
            return self.is_quali_out_or_inlap()
        else: # time trial, practice
            """ Todo: time trial outlaps """
            return False

    def is_race_inlap(self, current_distance):
        """ 
        Check if the current lap is an inlap in a race
        Reason: for race or OSQ inlaps (lap after last lap), the lap number doesn't increment
        Logic: If we're in the first x meters of a lap and also have all sector data -- it's an inlap
        """
        if (current_distance and current_distance < self.MAX_DISTANCE_COUNT_AS_NEW_LAP) and \
           self.sector_1_ms and self.sector_2_ms and self.sector_3_ms:
            log.info("%s is a race inlap" % self)
            return True
        return False
    
    def is_quali_out_or_inlap(self):
        """
        Check if the current lap is an in- or outlap in quali (where it's more complicated)
        Reason: for qualifying sessions (non-OSQ), the inlap and outlaps need to be ignored
        Logic: We check this based on pit status -- if no pits on entire lap, it's a real lap
        """
        return bool(self.pit_status and self.pit_status > 0)
    
    def set_pit_status(self, pit_status):
        """
        Set the pit value for the current lap
        Pit status changes over the course of a lap
        We want to keep the highest number of:
            0 = no pit --- 1 = pit entry/exit --- 2 = pitting
        So that we store the "slowest" pit value
        """
        self.pit_status = max((self.pit_status or 0), (pit_status or 0))
        return self.pit_status
    
    def process_flashback_event(self, frame_id_flashed_back_to):
        """ Update telemetry frame dict after a flashback """
        self.telemetry.process_flashback_event(frame_id_flashed_back_to)
