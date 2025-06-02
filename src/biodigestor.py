import time
import arrow
from abc import ABCMeta, abstractmethod
import threading

import event_emitter as events

emitter = events.EventEmitter()

class Environment:
    """Simulated environment for ESP32-controlled bio-digestor."""
    
    def __init__(self):
        self._active = False
        self._time = arrow.utcnow();
        self._time_step = 20                       # minutes
        self._update_interval = 0.2
        
        # self._temperature = params.temperature
        # self._season = params.season
    
    def get_time(self, format = 'HH:mm:ss'):
        return self._time.format(format)
            
    def run(self):
        self._active = True
        update_thread = threading.Thread(target=self._tick)
        update_thread.start()
        
    def stop(self):
        self._active = False
    
    def _tick(self):
        """
        
        """
        while self._active:
            emitter.emit('tick')
            self._time = self._time.shift(minutes=self._time_step)
            print(self.get_time())
            time.sleep(self._update_interval)
            

# todo: ensure at most one valve is open at any point in time
class MicroController:
    """Simulated ESP32 Micro-controller."""
    
    def __init__(self, env, pump, acid_valve, base_valve, agitator):
        self._environment = env
        self._time_series = []
        
        self._temperature_reading = 0
        self._pH_reading = 0
        
        self._pump = pump
        self._acid_valve = acid_valve
        self._base_valve = base_valve
        self._agitator = agitator
        
        emitter.on('tick', self._update)
        emitter.on('temperature_change', self._set_temperature)
        emitter.on('pH_change', self._set_pH)
    
    def _set_temperature(self, temperature):
        """temperature sensor event handler.

        Args:
            temperature (float|int): temperature value emitted by temperature sensor.
        """
        self._temperature_reading = temperature
    
    def _set_pH(self, value):
        """pH sensor event handler

        Args:
            value (float|int): pH value emitted by pH sensor.
        """
        set._pH_reading = value
        
    def _state(self):
        """Returns json representation of micro-controller state.

        Returns:
            dict: json dict of mc state.
        """
        state = {
            'time': self._environment.get_time(),  # technically a hack, but sihamba ngejubane
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
        """
        print('Micro controller captured tick event')
        if self._temperature_reading < 55 and not self._pump.active:
            self._pump.activate()
            
        if self._temperature_reading >= 55 and self._pump.active:
            self._pump.deactivate()
            
        if self._pH_reading < 6.6 and not self._base_valve.active:
            self._base_valve.activate()
            
        if self._pH_reading >= 6.6 and self._base_valve.active:
            self._base_valve.deactivate()
            
        if self._pH_reading > 7.2 and not self._acid_valve.active:
            self._acid_valve.activate()
            
        if self._pH_reading <= 7.2 and self._acid_valve.active:
            self._acid_valve.deactivate()
            
        # todo: add more conditions

       
class BioDigestor:
    """
    
    """
    def __init__(self, env, pump, acid_valve, base_valve, agitator):
        self._pump = pump
        self._acid_valve = acid_valve
        self._base_valve = base_valve
        self._self_agitator = agitator
        
        self._base_temperature = 37      # todo: lookup required   
        self._temperature = 37
        self._pH = 0                     # todo: lookup required
        
        self._time_series = []
        
        emitter.on('tick', self._update)
        
        # emit initial state
        emitter.emit('temperature', value=self._base_temperature)
        emitter.emit('pH', value=self._pH)
        
    def _update(self):
        """Perform a routine state update. Typically triggered by the environment emitting a tick.
        """
        if self._acid_valve.active:
            self._pH -= 0.2
            emitter.emit('digestor_pH_change', value=self._pH)
      
        if self._base_valve.active:
            self._pH += 0.2
            emitter.emit('digestor_pH_change', value=self._pH)
            
        if self._pump.active:
            self._temperature += 0.5
            emitter.emit('digestor_temperature_change', value=self._temperature)
            
        if not self._pump.active and self._temperature > self._base_temperature:
            # biodigestor contents will slowly cool to initial temperature when heat pump is off
            self._temperature -= 0.2
            emitter.emit('digestor_temperature_change', value=self._temperature)
            
        if not self._base_valve.active:
            # biodigestor contents will slowly become more acidic when base solenoid valve is closed
            self._pH -= 0.1
            emitter.emit('digestor_pH_change', value=self._pH)
            
        # todo: add agitator conditions


class TemperatureSensor:
    """
    
    """
    def __init__(self):
        self._temperature = 0
    
        emitter.on('temperature', self._set_temperature)
        emitter.on('digestor_temperature_change', self._set_temperature)
        
    def get_temperature(self):
        return self._temperature
    
    def _set_temperature(self, value):
        self._temperature = value
        emitter.emit('temperature_change', value=self._pH)


class pHSensor:
    """
    
    """
    def __init__(self):
        self._pH = 0
        
        emitter.on('pH', self._set_pH)
        emitter.on('digestor_pH_change', self._set_pH)
        
    def get_pH(self):
        return self._pH
    
    def set_pH(self, value):
        self._pH = value
        emitter.emit('pH_change', value=self._pH)
        

class Agitator():
    """
    wip
    """
    # def __init__(self):
    #     self._dc_motor_active = False
    #     self._agitation_duration = 15
        
    # def agitate(self):
    #     """Agitate for 15 (simulated) minutes."""
    #     self._dc_motor_active = True
    #     self._agitation_duration = 15
        
    # def stop(self):
    #     """Stop agitator DC motor."""
    #     self._dc_motor_active = False
        
    # def json(self):
    #     """Return agitator state"""
        
    # def _tick(self):
    #     if self._dc_motor_active:
    #         if self._agitation_duration > 0:
    #             self._agitation_duration -= 1
    #         else:
    #             # agitation complete, switch off dc motor
    #             self._dc_motor_active = False



class Component(metaclass=ABCMeta):
    """Base class for simple components, such as pumps and valves."""

    @abstractmethod
    def active(self):
        """"""
        
    @abstractmethod
    def activate(self):
        """"""
        
    @abstractmethod
    def deactivate(self):
        """"""


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



if __name__ == '__main__':
    av = AcidValve()
    bv = BaseValve()
    p = Pump()
    ps = pHSensor()
    ts = TemperatureSensor()
    a = Agitator()
    env = Environment()
    mc = MicroController(env, p,av, bv, a)
    bd = BioDigestor(env, p, av, bv, a)
    
    env.run()                     # run simulation
