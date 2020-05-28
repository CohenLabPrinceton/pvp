from vent.io import AsyncHal
from vent.io._asynchal import DAEMON_CMNDS
import time
import random
import pickle


hal = AsyncHal()
with hal:
    hal.socket.send(DAEMON_CMNDS['setup'] + pickle.dumps(hal._config))
    keepgoing = True
    while keepgoing:
        hal.socket.send(random.choice([val for val in DAEMON_CMNDS.values()]))
        time.sleep(0.1)
        response = hal.socket.recv(4096)
        data = pickle.loads(response)
        if data == 'END':
            keepgoing = False
        else:
            print('<>SyncSide got a {} that looks like: {}'.format(type(data), data))
