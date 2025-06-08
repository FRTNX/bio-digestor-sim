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

class EnvConfig(TypedDict):
    time_step: int
    delta: int
    starting_temperature: Union[float, int]
    starting_pH: Union[int, float]

ACTIVE_ENVIRONMENTS = []


def get_environment(environment_id):
    for env in ACTIVE_ENVIRONMENTS:
        if env._id == environment_id:
             return env
    raise ValueError('Environment not found.')


@app.post('/bd/init')
def create_simulation(data: EnvConfig):
    """Create a new ESP32-controlled bio-digestor."""
    print('params:', data)
    try:
        params = {
            'time_step': data['time_step'],
            'delta': data['delta'],
            'starting_temperature': data['starting_temperature'],
            'starting_pH': data['starting_pH']
        }
        
        env = Environment(params)
 
        data = env.run()
        
        return { 'data': data }                
    except Exception as e:
        return { 'error': str(e) }
    

@app.get('/bd/ping')
def run_simulation():
    """Ping the server."""
    try:
        return { 'message': 'pong' }
    except Exception as e:
        return { 'error': str(e) }
