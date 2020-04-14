
def update_single_sensor(track, val, track_len):
    # Adds newest sensor reading to end of track.
    # Only store most recent [track_len] values.

    # Check if list is already at max track length:
    if (len(track) >= track_len):
        # Remove first element
        track.pop(0)
    # Add current sensor reading to track:
    track.append(val)
    return track


class SensorTracking:
    # A class for keeping track of prior sensor values.
    # These are used by controllers and to sound alarms.
    def __init__(self, jp):
        self.jp = jp
        self._track_len = 50    # Type int: How long to retain sensor data. Could vary this later per sensor. 
        self.pres1_track = []
        self.pres2_track = []
        self.o2_track = []
        self.flow_track = []
        self.temp_track = []
        self.humid_track = []
        
    def update_all_sensors(self):
        # Takes in current sensor readings object; updates tracking log for all sensors.
        self.pres1_track = update_single_sensor(self.pres1_track, self.jp.get_pressure1_reading(), self._track_len)
        self.pres2_track = update_single_sensor(self.pres2_track, self.jp.get_pressure2_reading(), self._track_len)
        self.o2_track = update_single_sensor(self.o2_track, self.jp.get_o2_reading(), self._track_len)
        self.flow_track = update_single_sensor(self.flow_track, self.jp.get_flow_reading(), self._track_len)
        self.temp_track = update_single_sensor(self.temp_track, self.jp.get_temp_reading(), self._track_len)
        self.humid_track = update_single_sensor(self.humid_track, self.jp.get_humid_reading(), self._track_len)
        
    def reset(self):
        self.pres1_track = []
        self.pres2_track = []
        self.o2_track = []
        self.flow_track = []
        self.temp_track = []
        self.humid_track = []

    
    
    
