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


ACTIVE_ENVIRONMENT = []


def get_environment(environment_id):
    for env in ACTIVE_ENVIRONMENTS:
        if env._id == environment_id:
             return env
    raise ValueError('Environment not found.')


@app.get('/bd/init')
def create_simulation():
    """Create a new ESP32-controlled bio-digestor."""
    try:
        env = Environment()    
        data = env.run()
        
        return { 'data': data }
    except Exception as e:
        return { 'error': str(e) }
    

@app.get('/bd/tick')
def start_simulation(environment_id: str):
    """Start bio-digestor simulator."""
    try:
        env = active_env
        data = env.tick()
        return { 'data': data }
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

