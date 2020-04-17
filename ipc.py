import threading
import time


class IPC:
    # Class for communicating between processes either by sockets
    # or named-pipes
    #   Functions:
    def __init__(self, listen=False):
        # init as either listener or connector
        self.thread = threading.Thread(target=self.start)
        self.thread.start()

    def __del__(self):
        self.thread.join()

    def sendMsg(self, msg):
        pass

    def recvMsg(self, timeout=None):
        # set timeout=0 for non-blocking
        pass

    def start(self):
        while True:
            time.sleep(10)

# Variables:
