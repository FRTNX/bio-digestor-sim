import time
import arrow
import threading

from abc import ABCMeta, abstractmethod
from typing import List, Dict, Tuple, Union

import event_emitter as events

emitter = events.EventEmitter()

# simulator object types
Celcius = Union[int, float]
PotentialHydrogen = Union[int, float]

class Environment:
    """Simulated environment for ESP32-controlled bio-digestor.
    
    NOTES:
    - Any component that needs to run every time step can simply subscribe
      to the `tick` event emitted by this class.
    """
    
    def __init__(self):
        self._active: bool = False
        self._time = arrow.utcnow()
        self._time_step: int = 5                       # minutes
        self._update_interval: float = 0.1
        self._delta_start = self._time
        self._delta_end = 60 * 60 * 24 * 3             # seconds * mins * hours * days; default 3 days
        self._elapsed_time = 0                         # seconds
        
        # self._temperature: Celcius = params.temperature
        # self._season = params.season
    
    @property
    def elapsed_time(self):
        return self._elapsed_time
    
    def get_time(self, format = 'HH:mm:ss', raw=False):
        if raw == True:
            return self._time
        
        return self._time.format(format)
            
    def run(self, until=self._delta_end):
        self._delta_end = until
        self._active = True
        update_thread = threading.Thread(target=self._tick)
        update_thread.start()
        
    def stop(self):
        self._active = False
    
    def _tick(self):
        """
        The simulator's progression function. Iterates the environment and everything in it 
        forward by 1 time step.
        """
        while self._active:
            emitter.emit('tick')
            self._time = self._time.shift(minutes=self._time_step)
            delta = self._time - self._delta_start
            self._elapsed_time = delta.total_seconds()
            time.sleep(self._update_interval)
            
            if self._elapsed_time > self._delta_end:   # exit condition
                self._active = False                   # deactivate on max duration
            

# todo: ensure at most one valve is open at any point in time
class MicroController:
    """Simulated ESP32 Micro-controller."""
    
    def __init__(self, env, pump, acid_valve, base_valve, agitator):
        self._environment: Environment = env
        self._time_series: List[dict] = []                      # records micro-controller state changes
        
        # incomming connections
        self._temperature_reading: Celcius = 0
        self._pH_reading: PotentialHydrogen = 0
        
        # outgoing connections
        self._pump: Pump = pump
        self._acid_valve: AcidValve = acid_valve
        self._base_valve: BaseValve = base_valve
        self._agitator: Agitator = agitator
        
        # agitator config
        self._agitation_duration: int = 15                # minutes
        self._agitation_interval: int = 240               # minutes = 4 hours
        
        # pH config
        self._pH_max: float = 7.4
        self._pH_min: float = 6.8
        
        # temperature config
        self._target_temperature: int = 55                # degrees Celcius
        
        # agitate slurry on sim start
        self._agitator.activate(env.get_time(raw=True))
        
        # register event handlers
        emitter.on('tick', self._update)
        # sensor event handlers
        emitter.on('TEMPERATURE_CHANGE', self._set_temperature)
        emitter.on('PH_CHANGE', self._set_pH)
    
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
        
    def _state(self):
        """Returns json representation of micro-controller state.

        Returns:
            dict: json dict of mc state.
        """
        state = {
            'time': self._environment.get_time(),  # technically a hack, but sihamba ngejubane
            'elapsed_time': self._format_seconds(self._environment.elapsed_time),
            'temperature': self._temperature_reading,
            'pH': self._pH_reading,
            'pump': 'on' if self._pump.active else 'off',
            'acid_valve': 'on' if self._acid_valve.active else 'off',
            'base_valve': 'on' if self._base_valve.active else 'off',
            'agitator': 'on' if self._agitator.active else 'off'
        }
        
        self._time_series.append(state)
        print(state)
        
        return state
        
    def _update(self):
        """Make a routine state update. Typically triggered by the environment emitting a tick.
        
        NOTES:
          - Agitation is performed on pH corrections and routinely every 4 hours for 15 minutes.
        """
        # pH corrections
        if self._temperature_reading < self._target_temperature and not self._pump.active:
            self._pump.activate()
            
        if self._temperature_reading >= self._target_temperature and self._pump.active:
            self._pump.deactivate()
            
        if self._pH_reading < self._pH_min and not self._base_valve.active:
            self._base_valve.activate()
            self._agitator.activate(env.get_time(raw=True))
            
        if self._pH_reading >= self._pH_min and self._base_valve.active:
            self._base_valve.deactivate()
            
        if self._pH_reading > self._pH_max and not self._acid_valve.active:
            self._acid_valve.activate()
            self._agitator.activate(env.get_time(raw=True))
            
        if self._pH_reading <= self._pH_max and self._acid_valve.active:
            self._acid_valve.deactivate()

        # routine agitation
        if not self._agitator.active:
            delta = self._environment.get_time(raw=True) - self._agitator.delta_start
            elapsed_time = delta.total_seconds() / 60           # time since start of current agitation
            
            if elapsed_time >= self._agitation_interval:
                self._agitator.activate(env.get_time(raw=True))
        
        if self._agitator.active:
            delta = self._environment.get_time(raw=True) - self._agitator.delta_start
            elapsed_time = delta.total_seconds() / 60           # minutes
            
            if elapsed_time >= self._agitation_duration:
                self._agitator.deactivate()

        self._state()                                           # capture current mc state        
            
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
       
class BioDigestor:
    """
    Simulated bio-digestor containing slurry.
    """
    def __init__(self, env, pump, acid_valve, base_valve, agitator):
        # connect external components
        self._pump = pump
        self._acid_valve = acid_valve
        self._base_valve = base_valve
        self._agitator = agitator
        
        # intial conditions
        self._base_temperature = 37      # todo: correlate to environment
        self._temperature = 37
        self._pH = 7.9                   # require acid dose on simulation start
        
        # register event handlers
        emitter.on('tick', self._update)
        
        # emit initial state
        emitter.emit('INIT_TEMPERATURE', value=self._base_temperature)
        emitter.emit('INIT_PH', value=self._pH)
        
    # todo: normalise pH and temperature changes, correlate to time delta
    def _update(self):
        """Perform a routine state update. Typically triggered by the environment emitting a tick.
        
        NOTES:
          - Each pH and temperature change emits an event that sensors can subscribe to.
            The emitted event includes the current value for pH or temperature.
        """
        if self._acid_valve.active:
            self._pH -= 0.2
            emitter.emit('DIGESTOR_PH_CHANGE', value=self._pH)
      
        if self._base_valve.active:
            self._pH += 0.2
            emitter.emit('DIGESTOR_PH_CHANGE', value=self._pH)
            
        if self._pump.active:
            self._temperature += 0.5
            emitter.emit('DIGESTOR_TEMP_CHANGE', value=self._temperature)
            
        if not self._pump.active and self._temperature > self._base_temperature:
            # biodigestor contents will slowly cool to initial temperature when heat pump is off
            self._temperature -= 0.2
            emitter.emit('DIGESTOR_TEMP_CHANGE', value=self._temperature)
            
        if not self._base_valve.active:
            # biodigestor contents will slowly become more acidic when base solenoid valve is closed
            self._pH -= 0.1
            emitter.emit('DIGESTOR_PH_CHANGE', value=self._pH)


class TemperatureSensor:
    """
    
    """
    def __init__(self):
        self._temperature = 0
    
        emitter.on('INIT_TEMPERATURE', self._set_temperature)
        emitter.on('DIGESTOR_TEMP_CHANGE', self._set_temperature)
        
    def get_temperature(self):
        return self._temperature
    
    def _set_temperature(self, value):
        self._temperature = value
        emitter.emit('TEMPERATURE_CHANGE', value=self._temperature)


class PHSensor:
    """
    
    """
    def __init__(self):
        self._pH = 0
        
        emitter.on('INIT_PH', self._set_pH)
        emitter.on('DIGESTOR_PH_CHANGE', self._set_pH)
        
    def get_pH(self):
        return self._pH
    
    def _set_pH(self, value):
        self._pH = value
        emitter.emit('PH_CHANGE', value=self._pH)


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
    # init components
    p = Pump()
    a = Agitator()
    av = AcidValve()
    bv = BaseValve()
    ps = PHSensor()
    ts = TemperatureSensor()
    
    # init environment
    env = Environment()
    
    # init core components
    mc = MicroController(env, p, av, bv, a)      # connect components to ESP32 micro-controller
    bd = BioDigestor(env, p, av, bv, a)          # connect components to bio-digestor
    
    env.run()                                    # run simulation
