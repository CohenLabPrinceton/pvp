import xmlrpc.client
import vent.controller.control_module
from xmlrpc.server import SimpleXMLRPCServer
import pickle

default_addr = 'localhost'
default_port = 9533

remote_controller = None


def get_sensors():
    return pickle.dumps(remote_controller.get_sensors())


def get_active_alarms():
    return pickle.dumps(remote_controller.get_active_alarms())


def get_logged_alarms():
    return pickle.dumps(remote_controller.get_logged_alarms())


def set_control(control_setting):
    remote_controller.set_control(pickle.loads(control_setting.data))


def get_control(control_setting_name):
    return pickle.dumps(remote_controller.get_control(pickle.loads(control_setting_name.data)))


def rpc_server_main(sim_mode, addr=default_addr, port=default_port):
    global remote_controller
    if addr != default_addr:
        raise NotImplementedError
    if port != default_port:
        raise NotImplementedError
    remote_controller = vent.controller.control_module.get_control_module(sim_mode)
    server = SimpleXMLRPCServer((addr, port), allow_none=True, logRequests=False)
    server.register_function(get_sensors, "get_sensors")
    server.register_function(get_active_alarms, "get_active_alarms")
    server.register_function(get_logged_alarms, "get_logged_alarms")
    server.register_function(set_control, "set_control")
    server.register_function(get_control, "get_control")
    server.register_function(remote_controller.start, "start")
    server.register_function(remote_controller.is_running, "is_running")
    server.register_function(remote_controller.stop, "stop")
    server.serve_forever()


def get_rpc_client():
    proxy = xmlrpc.client.ServerProxy(f"http://{default_addr}:{default_port}/")
    return proxy