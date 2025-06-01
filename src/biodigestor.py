# POC Code. These embryo classes will gradually be built into modules

class Environment:
    """Simulated environment for bio-digestor."""
    
    def __init__(self, params):
        self._time = 0;
        self._temperature = params.temperature
        self._season = params.season
        
    def tick(self):
        """"""
        if self._time == 24:
            self._time = 0
        else:
            self._time += 1
        

class MicroController:
    """Simulated ESP32 Micro-controller."""
    def __init__(self, temperature_sensor, pH_sensor, pump, acid_valve, base_valve, agitator):
        self._time_series = []
        self._optimum_temperature = 55
        self._optimum_pH_range = [6.6, 7.2]
        self._temperature_sensor = temperature_sensor
        self._pH_sensor = pH_sensor
        self._pump = pump
        self._base_valve = base_valve
        self._acid_valve = acid_valve
    
    def get_temperature(self):
        """"""
        return self._temperature_sensor.get_temperature()
    
    def get_pH(self):
        """"""
        return self._pH_sensor.get_pH()
    
    def agitate(self):
        """"""
        self._agitator.agitate()
        
    def acidify(self):
        """"""

    def deacidify(self):
        """"""
        

class BioDigistor:
    """"""
    def __init__(self, temperature_sensor, pH_sensor, agitator):
        self._temperature_sensor = temperature_sensor
        self._pH_sensor = pH_sensor
        self._agitator = agitator
        self._time_series = []
    

class Agitator:
    """"""
    def __init__(self):
        self._dc_motor_active = False
        self._time_series = []
        
    def agitate(self):
        """Agitate for 15 (simulated) minutes."""
        self._dc_motor_active = True
        
    def stop(self):
        """Stop agitator DC motor."""
        self._dc_motor_active = False


class Pump:
    """"""
    def __init__(self):
        self._active = False
        self._time_series = []
        
    def activate(self):
        self._active = True
        
    def stop(self):
        self._active = False


class BaseValve:
    """"""


class AcidValve:
    """"""


class TemperatureSensor:
    """"""
    def __init__(self):
        self._temperature = 0
        self._time_series = []
        
    def get_temperature(self):
        return self._temperature
    
    def set_temperature(self, value):
        self._temperature = value


class pHSensor:
    """"""
    def __init__(self):
        self._pH = 0
        self._time_series = []
        
    def get_pH(self):
        return self._pH
    
    def set_pH(self, value):
        self._pH = value
