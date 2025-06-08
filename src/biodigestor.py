import time
import arrow
import threading

from abc import ABCMeta, abstractmethod
from typing import List, Dict, Tuple, Union

from utils import uuid

import event_emitter as events

emitter = events.EventEmitter()

# simulator object types
Celcius = Union[int, float]
PotentialHydrogen = Union[int, float]

class Environment:
    """Simulated environment for ESP32-controlled bio-digestor.
    """

    def __init__(self, params = {}):
        self._id = uuid()
        self._active: bool = False
        self._time = arrow.utcnow()
        self._time_step: int = params['time_step'] if params['time_step'] else 5       # minutes
        self._delta_start = self._time
        self._delta_end = params['delta'] if params['delta'] else 60 * 60 * 12
        self._elapsed_time = 0
        self._time_series = []
        
        self._starting_temperature = params['starting_temperature'] if params['starting_temperature'] else 20
        self._starting_pH = params['starting_pH'] if params['starting_pH'] else 8.8
        
        # putting these in the environment for easy updates
        # data structures and algorithms paying back dividends
        self._pump = Pump()
        self._agitator = Agitator()
        self._acid_valve = AcidValve()
        self._base_valve = BaseValve()
        self._bio_digestor = BioDigestor(self)
        self._temperature_sensor = TemperatureSensor(self)
        self._pH_sensor = PHSensor(self)
        self._micro_controller = MicroController(self)

    @property
    def elapsed_time(self):
        return self._elapsed_time
    
    def run(self, until=None):
        if until:
            self._delta_end = until
            
        self._active = True
        
        while self._active:
            self._tick()
            self._bio_digestor._update()
            self._temperature_sensor._update()
            self._pH_sensor._update()
            self._micro_controller._update()
            self._save_state()
            
        print('time series:', self._time_series)
        return self._time_series
        
    def stop(self):
        self._active = False
    
    def get_time(self, format = 'HH:mm', raw=False):
        if raw == True:
            return self._time
        
        return self._time.format(format)
    
    def _format_seconds(self, seconds):
        """Format seconds into human friendly format.

        Args:
            seconds (int): Integer seconds to be formatted

        Returns:
            str: Formatted time value.
        """
        days = int(seconds // (24 * 3600))
        hours = int((seconds % (24 * 3600)) // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds_ = int(seconds % 60)
        return f"{days} d {hours} h {minutes} m {seconds_} s"
        
    def _save_state(self):
        """Returns json representation of micro-controller state.

        Returns:
            dict: json dict of mc state.
        """
        state = {
            'time': self.get_time(),
            'elapsed_time': self._format_seconds(self.elapsed_time),
            'temperature': self._bio_digestor._temperature,
            'pH': self._bio_digestor._pH,
            'pump': self._pump.active,
            'acid_valve': self._acid_valve.active,
            'base_valve': self._base_valve.active,
            'agitator': self._agitator.active
        }
        
        self._time_series.append(state)
        print(state)
        
        return state
        
    def _tick(self):
        """Manually move the environment forward by one time step. Called internally
        or by external client.
        """
        # emitter.emit(f'tick')
        self._time = self._time.shift(minutes=self._time_step)
        delta = self._time - self._delta_start
        self._elapsed_time = delta.total_seconds()

        if self._elapsed_time > self._delta_end:   # exit condition
            self._active = False                   # deactivate on max duration
        

# todo: ensure at most one valve is open at any point in time
class MicroController:
    """Simulated ESP32 Micro-controller."""
    
    def __init__(self, env):
        self._environment: Environment = env
        self._time_series: List[dict] = []                      # records micro-controller state changes
        
        # incomming connections
        self._temperature_reading: Celcius = 0
        self._pH_reading: PotentialHydrogen = 0
        
        # outgoing connections
        self._pump: Pump = env._pump
        self._acid_valve: AcidValve = env._acid_valve
        self._base_valve: BaseValve = env._base_valve
        self._agitator: Agitator = env._agitator
        
        self._temperature_sensor = env._temperature_sensor
        self._pH_sensor = env._pH_sensor
        
        # agitator config
        self._agitation_duration: int = 15                # minutes
        self._agitation_interval: int = 240               # minutes = 4 hours
        
        # pH config
        self._pH_max: float = 7.4
        self._pH_min: float = 6.8
        
        # temperature config (+-55)
        self._temmperature_min: int = 52                 # degrees Celcius
        self._temmperature_max: int = 58                  
        
        # agitate slurry on sim start
        self._agitator.activate(self._environment.get_time(raw=True))
    
    def _set_temperature(self, value):
        """temperature sensor event handler.

        Args:
            temperature (float|int): temperature value emitted by temperature sensor.
        """
        self._temperature_reading = value
    
    def _set_pH(self, value):
        """pH sensor event handler.

        Args:
            value (float|int): pH value emitted by pH sensor.
        """
        self._pH_reading = value
        
    def _update(self):
        """Make a routine state update. Typically triggered by the environment emitting a tick.
        
        NOTES:
          - Agitation is performed on pH corrections and routinely every 4 hours for 15 minutes.
        """
        # get sensor data
        self._temperature_reading = self._temperature_sensor.get_temperature()
        self._pH_reading = self._pH_sensor.get_pH()
        
        # pH corrections
        if self._temperature_reading < self._temmperature_min and not self._pump.active:
            self._pump.activate()
            
        if self._temperature_reading >= self._temmperature_max and self._pump.active:
            self._pump.deactivate()
            
        if self._pH_reading < self._pH_min and not self._base_valve.active:
            self._base_valve.activate()
            self._agitator.activate(self._environment.get_time(raw=True))
            
        if self._pH_reading >= self._pH_min and self._base_valve.active:
            self._base_valve.deactivate()
            
        if self._pH_reading > self._pH_max and not self._acid_valve.active:
            self._acid_valve.activate()
            self._agitator.activate(self._environment.get_time(raw=True))
            
        if self._pH_reading <= self._pH_max and self._acid_valve.active:
            self._acid_valve.deactivate()

        # routine agitation
        if not self._agitator.active:
            delta = self._environment.get_time(raw=True) - self._agitator.delta_start
            elapsed_time = delta.total_seconds() / 60           # time since start of current agitation
            
            if elapsed_time >= self._agitation_interval:
                self._agitator.activate(self._environment.get_time(raw=True))
        
        if self._agitator.active:
            delta = self._environment.get_time(raw=True) - self._agitator.delta_start
            elapsed_time = delta.total_seconds() / 60           # minutes
            
            if elapsed_time >= self._agitation_duration:
                self._agitator.deactivate()
       
class BioDigestor:
    """
    Simulated bio-digestor containing slurry.
    """
    def __init__(self, env):
        self._environment = env
        # connect external components
        self._pump = env._pump
        self._acid_valve = env._acid_valve
        self._base_valve = env._base_valve
        self._agitator = env._agitator
        
        # intial conditions
        self._base_temperature = env._starting_temperature
        self._temperature = env._starting_temperature
        self._pH = env._starting_pH
    
        
    @property
    def temperature(self):
        return self._temperature
    
    @property
    def pH(self):
        return self._pH
         
    # todo: normalise pH and temperature changes, correlate to time delta
    def _update(self):
        """Perform a routine state update. Typically triggered by the environment emitting a tick.
        
        NOTES:
          - Each pH and temperature change emits an event that sensors can subscribe to.
            The emitted event includes the current value for pH or temperature.
        """
        if self._acid_valve.active:
            self._pH -= 0.2
            # emitter.emit(f'DIGESTOR_PH_CHANGE', value=self._pH)
      
        if self._base_valve.active:
            self._pH += 0.2
            # emitter.emit(f'DIGESTOR_PH_CHANGE', value=self._pH)
            
        if self._pump.active:
            self._temperature += 0.5
            # emitter.emit(f'DIGESTOR_TEMP_CHANGE', value=self._temperature)
            
        if not self._pump.active and self._temperature > self._base_temperature:
            # biodigestor contents will slowly cool to initial temperature when heat pump is off
            self._temperature -= 0.2
            # emitter.emit(f'DIGESTOR_TEMP_CHANGE', value=self._temperature)
            
        if not self._base_valve.active:
            # biodigestor contents will slowly become more acidic when base solenoid valve is closed
            self._pH -= 0.1
            # emitter.emit(f'DIGESTOR_PH_CHANGE', value=self._pH)


class TemperatureSensor:
    """
    
    """
    def __init__(self, env):
        self._environment = env
        self._bio_digestor = env._bio_digestor
        self._temperature = 0
    
        # emitter.on(f'INIT_TEMPERATURE', self._set_temperature)
        # emitter.on(f'DIGESTOR_TEMP_CHANGE', self._set_temperature)
        
    def get_temperature(self):
        return self._temperature
        
    def _update(self):
        self._temperature = self._bio_digestor.temperature


class PHSensor:
    """
    
    """
    def __init__(self, env):
        self._environment = env
        self._bio_digestor = env._bio_digestor
        self._pH = 0
        
        # emitter.on('INIT_PH', self._set_pH)
        # emitter.on('DIGESTOR_PH_CHANGE', self._set_pH)
        
    def get_pH(self):
        return self._pH
        
    def _update(self):
        self._pH = self._bio_digestor.pH


class Component(metaclass=ABCMeta):
    """Abstract base class for simple components, such as pumps and valves."""

    @abstractmethod
    def active(self):
        """"""
        
    @abstractmethod
    def activate(self):
        """"""
        
    @abstractmethod
    def deactivate(self):
        """"""


class Agitator(Component):
    """
    
    """
    def __init__(self):
        self._active = False
        self._delta_start = 0        # stores most recent agitator activation time
        
    @property
    def active(self):
        return self._active

    @property
    def delta_start(self):
        """Retrieve the agitator's most recent activation time.
        """
        return self._delta_start
    
    def activate(self, delta_start):
        self._active = True
        self._delta_start = delta_start
        
    def deactivate(self):
        self._active = False


class Pump(Component):
    """
    
    """
    def __init__(self):
        self._active = False
        
    @property
    def active(self):
        return self._active
    
    def activate(self):
        self._active = True
        
    def deactivate(self):
        self._active = False


class BaseValve(Component):
    """
    
    """
    def __init__(self):
        self._active = False
        
    @property
    def active(self):
        return self._active
    
    def activate(self):
        self._active = True
        
    def deactivate(self):
        self._active = False


class AcidValve(Component):
    """
    
    """
    def __init__(self):
        self._active = False
        
    @property
    def active(self):
        return self._active
    
    def activate(self):
        self._active = True
        
    def deactivate(self):
        self._active = False


# todo: consider how to measure energy cost then optimise

if __name__ == '__main__':    
    # init environment
    env = Environment()    
    env.run()                                    # run simulation
