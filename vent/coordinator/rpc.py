import logging
import pickle
import socket
import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer

import vent.controller.control_module
from vent.common.logging import init_logger

default_addr = 'localhost'
default_port = 9533
default_timeout = 10
socket.setdefaulttimeout(default_timeout)

remote_controller = None


def get_sensors():
    # left as example of how to get loggers within these callbacks
    #logger = logging.getLogger(__name__)
    #logger.info('remote runnnnnnn')
    res = remote_controller.get_sensors()
    return pickle.dumps(res)


# def get_active_alarms():
#     res = remote_controller.get_active_alarms()
#     return pickle.dumps(res)
#
#
# def get_logged_alarms():
#     res = remote_controller.get_logged_alarms()
#     return pickle.dumps(res)


def set_control(control_setting):
    args = pickle.loads(control_setting.data)
    remote_controller.set_control(args)


def get_control(control_setting_name):
    args = pickle.loads(control_setting_name.data)
    res = remote_controller.get_control(args)
    return pickle.dumps(res)


def rpc_server_main(sim_mode, serve_event, addr=default_addr, port=default_port):
    logger = init_logger(__name__)
    logger.info('controller process init')
    global remote_controller
    if addr != default_addr:
        raise NotImplementedError
    if port != default_port:
        raise NotImplementedError
    remote_controller = vent.controller.control_module.get_control_module(sim_mode)
    server = SimpleXMLRPCServer((addr, port), allow_none=True, logRequests=False)
    server.register_function(get_sensors, "get_sensors")
    # server.register_function(get_active_alarms, "get_active_alarms")
    # server.register_function(get_logged_alarms, "get_logged_alarms")
    server.register_function(set_control, "set_control")
    server.register_function(get_control, "get_control")
    server.register_function(remote_controller.start, "start")
    server.register_function(remote_controller.is_running, "is_running")
    server.register_function(remote_controller.stop, "stop")
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