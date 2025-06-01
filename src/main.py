from typing import List, Union
from typing_extensions import TypedDict

from datetime import datetime
from freezegun import freeze_time

import time
import threading
import fastapi

from starlette.middleware.cors import CORSMiddleware

environment = Environment()

app = fastapi.FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

ACTIVE_SIMULATIONS: List[dict] = []


class temperatureDict(TypedDict):
    unit: str
    value: Union[int, float]

@freeze_time('May 21, 2024 04:00', auto_tick_seconds=3)
def simulated_time(environment):
    """Updates an environment's time value based on specified interval."""
    while environment._active:
        environment.set_time(datetime.now())
        time.sleep(1)

sim_time_thread = threading.Thread(target=simulated_time, args=(environment,))
sim_time_thread.start()
