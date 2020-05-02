import threading
import time
from enum import Enum, auto
import pickle
import socket

socket_port = 9998
buffer_size = 65536


class IPCCommand(Enum):
    START = auto()
    STOP = auto()
    GET_SENSORS = auto()
    GET_CONTROL = auto()
    SET_CONTROL = auto()
    GET_ACTIVE_ALARMS = auto()
    GET_LOGGED_ALARMS = auto()
    CLEAR_LOGGED_ALARMS = auto()


class IPCMessage:
    def __init__(self, command, args=None):
        """
        :param command: ENUM in IPCCommand
        """
        self.command = command
        # TODO: current only assume one arg
        self.args = args


class IPC:
    # Class for communicating between processes either by sockets
    # or named-pipes
    #   Functions:
    def __init__(self, listen):
        self.listen = listen
        self.s = socket.socket()
        if listen:
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.bind(('localhost', socket_port))
            self.s.listen()
            self.conn, self.addr = self.s.accept()
        else:
            self.s.connect(('localhost', socket_port))
        # init as either listener or connector
        # self.thread = threading.Thread(target=self.start)
        # self.thread.start()
        # two msg queue

    def __del__(self):
        if self.listen:
            self.conn.close()
        else:
            self.s.close()

    def send_msg(self, msg: IPCMessage):
        pickled_msg = pickle.dumps(msg)
        if self.listen:
            self.conn.sendall(pickled_msg)
        else:
            self.s.sendall(pickled_msg)

    def recv_msg(self, timeout=None) -> IPCMessage:
        # set timeout=0 for non-blocking
        if timeout is not None:
            raise NotImplementedError
        if self.listen:
            data = self.conn.recv(buffer_size)
        else:
            data = self.s.recv(buffer_size)
        unpicked_msg = pickle.loads(data)
        return unpicked_msg
    # def start(self):
    #     while True:
    #         time.sleep(10)

# Variables:
