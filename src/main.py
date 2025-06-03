from typing import List, Union
from typing_extensions import TypedDict

from datetime import datetime

import time
import threading
import fastapi

from starlette.middleware.cors import CORSMiddleware

from biodigestor import (Environment, MicroController, BioDigestor,
    Pump, Agitator, BaseValve, AcidValve, PHSensor, TemperatureSensor)


app = fastapi.FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)


ACTIVE_ENVIRONMENTS = []


def get_environment(environment_id):
    for env in ACTIVE_ENVIRONMENTS:
        if env.id == environment_id:
             return env
    raise Error('Environment fnot found.')


@app.get('/bd/init')
def create_simulation(system_id: str):
    """Create a new ESP32-controlled bio-digestor."""
    try:
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
        bd = BioDigestor(env, p, av, bv, a) 
        
        ACTIVE_ENVIRONMENTS.append(env)
        
        # todo: return env, mc, and bd identifers
        return { 'result': 'SUCCESS' }
    except Exception as e:
        return { 'error': str(e) }
    

@app.get('/bd/start')
def start_simulation(environment_id: str):
    """Start bio-digestor simulator."""
    try:
        env = get_environment(environment_id)
        env.run()
        return { 'result': 'SUCCESS' }
    except Exception as e:
        return { 'error': str(e) }


@app.get('/bd/stop')
def stop_simulation(environment_id: str):
    """Stop bio-digestor simulation."""
    try:
        env = get_environment(environment_id)
        env.stop()
        return { 'result': 'SUCCESS' }
    except Exception as e:
        return { 'error': str(e) }


@app.get('/bd/test')
def create_simulation(environment_id: str):
    """Run component tests."""
    try:   
        return { 'result': 'SUCCESS' }
    except Exception as e:
        return { 'error': str(e) }
