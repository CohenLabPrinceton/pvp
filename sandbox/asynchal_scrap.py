from vent.io import AsyncHal
import time
import random
import pickle


hal = AsyncHal()
with hal:
    print("    <sync> hal.pressure = {}".format(hal.pressure))
    print("    <sync> hal.aux_pressure = {}".format(hal.aux_pressure))
    print("    <sync> hal.flow_in = {}".format(hal.flow_in))
    print("    <sync> hal.flow_ex = {}".format(hal.flow_ex))

"""
    keepgoing = True
    while keepgoing:
        for cmd in AsyncHal.DAEMON_CMNDS.values():
            hal.socket.send(cmd)
            # time.sleep(0.001)  # Not needed?
            # Protocol: first byte is an echo of the command; 2nd and 3rd (if present) repr an int that is the length
            # of the response
            header = hal.socket.recv(3)
            if header:
                assert header[0] == cmd[0]
                if len(header) > 1:
                    response = hal.socket.recv(int.from_bytes(header[1:], 'big'))
                data = pickle.loads(response)
            if data == 'END':
                keepgoing = False
            else:
                print('<>SyncSide got a {} that looks like: {}'.format(type(data), data))
"""