import threading
import time
from enum import Enum, auto
import pickle
import socket

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
    def __init__(self, listen, addr=None, port=None):
        self.listen = listen
        self.s = socket.socket()
        if listen:
            # TODO: can start random port on testing, but deterministic port on deployment
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.bind(('', 0))
            self.addr, self.port = self.s.getsockname()
            # print(self.addr)
            # print(self.port)
            # print('listen socket created')
            self.conn = None
            self.connection_thread = threading.Thread(target=self.connect, daemon=True)
            self.connection_thread.start()
        else:
            self.s.connect((addr, port))
            # print('connect socket created')
        # init as either listener or connector
        # self.thread = threading.Thread(target=self.start)
        # self.thread.start()
        # two msg queue

    def connect(self):
        self.s.listen()
        self.conn, _ = self.s.accept()

    def __del__(self):
        if self.listen:
            self.conn.close()
        self.s.close()


    def send_msg(self, msg: IPCMessage):
        # print(f'sending IPC: {msg.command}')
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
        # print(f'received IPC: {unpicked_msg.command}')
        return unpicked_msg
    # def start(self):
    #     while True:
    #         time.sleep(10)

# Variables:
