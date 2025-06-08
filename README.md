# Bio-Digestor Simulator
A bio-digestor simulator for Kudzai Makotore

## Dependencies

The codebase is written in Python 3.10 and and utilises the FastAPI library to expose simulator methods to a React.js web client. This code is designed to run in a  cloud environment but can be run on any machine with Python 3 installed. Depencies can be installed with the following command:

```
pip install -r requirements.txt
```

This will install everything you need to run the simulator. Once installed you can then run:

```
uvicorn main:app --port 8002
```
