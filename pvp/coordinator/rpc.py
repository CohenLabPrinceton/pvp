import logging
import typing
import pickle
import socket
import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer

from pvp.controller import control_module
from pvp.common.loggers import init_logger

default_addr = 'localhost'
default_port = 9533
default_timeout = 10
socket.setdefaulttimeout(default_timeout)

remote_controller = None # type: typing.Union[None, control_module.ControlModuleBase]


def get_sensors():
    res = remote_controller.get_sensors()
    return pickle.dumps(res)

def get_alarms():
    res = remote_controller.get_alarms()
    return pickle.dumps(res)


def set_control(control_setting):
    args = pickle.loads(control_setting.data)
    remote_controller.set_control(args)


def get_control(control_setting_name):
    args = pickle.loads(control_setting_name.data)
    res = remote_controller.get_control(args)
    return pickle.dumps(res)

def set_breath_detection(breath_detection):
    args = pickle.loads(breath_detection.data)
    remote_controller.set_breath_detection(args)

def get_breath_detection():
    res = remote_controller.get_breath_detection()
    return pickle.dumps(res)

def get_target_waveform():
    res = remote_controller.get_target_waveform()
    return pickle.dumps(res)


def rpc_server_main(sim_mode, serve_event, addr=default_addr, port=default_port):
    logger = init_logger(__name__)
    logger.info('controller process init')
    global remote_controller
    if addr != default_addr:
        raise NotImplementedError
    if port != default_port:
        raise NotImplementedError
    remote_controller = control_module.get_control_module(sim_mode)
    server = SimpleXMLRPCServer((addr, port), allow_none=True, logRequests=False)
    server.register_function(get_sensors, "get_sensors")
    # server.register_function(get_active_alarms, "get_active_alarms")
    # server.register_function(get_logged_alarms, "get_logged_alarms")
    server.register_function(set_control, "set_control")
    server.register_function(get_control, "get_control")
    server.register_function(get_target_waveform, "get_target_waveform")
    server.register_function(remote_controller.start, "start")
    server.register_function(remote_controller.is_running, "is_running")
    server.register_function(remote_controller.stop, "stop")
    server.register_function(get_alarms, 'get_alarms')
    server.register_function(set_breath_detection, 'set_breath_detection')
    server.register_function(get_breath_detection, "get_breath_detection")
    serve_event.set()
    server.serve_forever()



def get_rpc_client():
    # https://mail.python.org/pipermail/python-bugs-list/2015-January/260126.html
    #transport = xmlrpc.client.Transport()
    #con = transport.make_connection(f"http://{default_addr}:{default_port}/")
    #con.timeout = 5
    #
    proxy = xmlrpc.client.ServerProxy(f"http://{default_addr}:{default_port}/")

    return proxy