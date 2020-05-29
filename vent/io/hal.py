""" Module for interacting with physical and/or simulated devices installed on the ventilator.

"""
import pickle
from abc import abstractmethod
from functools import partial
from importlib import import_module
from ast import literal_eval
import socket
from itertools import count

import trio

from .devices import AsyncSMBus
from .devices.sensors import Sensor
from .devices.base import PigpioConnection

import vent.io.devices.valves as valves
import configparser
import multiprocessing
import time


class HalBase:
    def __init__(self, config_file):
        self._setpoint_in = 0.0  # setpoint for inspiratory side
        self._setpoint_ex = 0.0  # setpoint for expiratory side
        self._adc = object
        self._inlet_valve = object
        self._control_valve = object
        self._expiratory_valve = object
        self._pressure_sensor = object
        self._aux_pressure_sensor = object
        self._flow_sensor_in = object
        self._flow_sensor_ex = object
        self.config = configparser.RawConfigParser()
        self.config.optionxform = lambda option: option
        self.config.read(config_file)
        self._config = {}
        self._parse_config()

    @property
    @abstractmethod
    def pressure(self) -> float:
        """ Returns the pressure from the primary pressure sensor."""

    @property
    @abstractmethod
    def aux_pressure(self) -> float:
        """ Returns the pressure from the auxiliary pressure sensor, if so equipped."""

    @property
    @abstractmethod
    def flow_in(self) -> float:
        """ The measured flow rate inspiratory side."""

    @property
    @abstractmethod
    def flow_ex(self) -> float:
        """ The measured flow rate expiratory side."""

    @property
    @abstractmethod
    def setpoint_in(self) -> float:
        """ The currently requested flow for the inspiratory proportional control valve as a proportion of maximum."""

    @property
    @abstractmethod
    def setpoint_ex(self) -> float:
        """ The currently requested flow on the expiratory side as a proportion of the maximum."""

    def _parse_config(self):
        for section in self.config.sections():
            sdict = dict(self.config[section])
            class_ = {key: sdict[key] for key in ('module', 'type',)}
            opts = {key: sdict[key] for key in sdict.keys() - ('module', 'type',)}
            for key in opts.keys():
                opts[key] = literal_eval(opts[key])
            self._config['_' + section] = {'class_': class_, 'opts': opts}


class Hal(HalBase):
    """ Hardware Abstraction Layer for ventilator hardware.
    Defines a common API for interacting with the sensors & actuators on the ventilator. The types of devices installed
    on the ventilator (real or simulated) are specified in a configuration file.
    """
    def __init__(self, config_file='vent/io/config/devices.ini'):
        """ Initializes HAL from config_file.
            For each section in config_file, imports the class <type> from module <module>, and sets attribute
            self.<section> = <type>(**opts), where opts is a dict containing all of the options in <section> that are
            not <type> or <section>. For example, upon encountering the following entry in config_file.ini:

                [adc]
                type   = ADS1115
                module = devices
                i2c_address = 0x48
                i2c_bus = 1

            The Hal will:
                1) Import vent.io.devices.ADS1115 (or ADS1015) as a local variable:
                        class_ = getattr(import_module('.devices', 'vent.io'), 'ADS1115')

                2) Instantiate an ADS1115 object with the arguments defined in config_file and set it as an attribute:
                        self._adc = class_(pig=self.-pig,address=0x48,i2c_bus=1)

            Note: RawConfigParser.optionxform() is overloaded here s.t. options are case sensitive (they are by default
            case insensitive). This is necessary due to the kwarg MUX which is so named for consistency with the config
            registry documentation in the ADS1115 datasheet. For example, A P4vMini pressure_sensor on pin A0 (MUX=0)
            of the ADC is passed arguments like:

            analog_sensor = AnalogSensor(
                pig=self._pig,
                adc=self._adc,
                MUX=0,
                offset_voltage=0.25,
                output_span = 4.0,
                conversion_factor=2.54*20
            )

            Note: ast.literal_eval(opt) interprets integers, 0xFF, (a, b) etc. correctly. It does not interpret strings
            correctly, nor does it know 'adc' -> self._adc; therefore, these special cases are explicitly handled.
        Args:
            config_file (str): Path to the configuration file containing the definitions of specific components on the
                ventilator machine. (e.g., config_file = "vent/io/config/devices.ini")
        """
        self._pig = PigpioConnection(show_errors=False)
        super().__init__(config_file=config_file)
        self._init_attr()

    # TODO: Need exception handling whenever inlet valve is opened

    @property
    def pressure(self) -> float:
        """ Returns the pressure from the primary pressure sensor.
        """
        return self._pressure_sensor.get()

    @property
    def aux_pressure(self) -> float:
        """ Returns the pressure from the auxiliary pressure sensor, if so equipped.
        If a secondary pressure sensor is not defined, raises a RuntimeWarning.
        """
        if isinstance(self._aux_pressure_sensor, Sensor):
            return self._aux_pressure_sensor.get()
        else:
            raise RuntimeWarning('Secondary pressure sensor not instantiated. Check your "devices.ini" file.')

    @property
    def flow_in(self) -> float:
        """ The measured flow rate inspiratory side."""
        return self._flow_sensor_in.get()

    @property
    def flow_ex(self) -> float:
        """ The measured flow rate expiratory side."""
        return self._flow_sensor_ex.get()

    @property
    def setpoint_in(self) -> float:
        """ The currently requested flow for the inspiratory proportional control valve as a proportion of maximum."""
        return self._setpoint_in

    @setpoint_in.setter
    def setpoint_in(self, value: float):
        """ Sets the openness of the inspiratory valve to the requested value.

        Args:
            value: Requested flow, as a proportion of maximum. Must be in [0, 1].
        """
        if not 0 <= value <= 100:
            raise ValueError('setpoint must be a number between 0 and 100')
        if value > 0 and not self._inlet_valve.is_open:
            self._inlet_valve.open()
        elif value == 0 and self._inlet_valve.is_open:
            self._inlet_valve.close()
        self._control_valve.setpoint = value
        self._setpoint_in = value

    @property
    def setpoint_ex(self) -> float:
        """ The currently requested flow on the expiratory side as a proportion of the maximum."""
        return self._setpoint_ex

    @setpoint_ex.setter
    def setpoint_ex(self, value):
        """ Sets the openness of the expiratory valve to the requested value.

        Args:
            value (float): Requested flow, as a proportion of maximum. Must be either 0 or 1 for OnOffValve, and between
                0 and 1 for a (proportional) control valve.
        """
        if (
                isinstance(self._expiratory_valve, valves.OnOffValve) or
                isinstance(self._expiratory_valve, valves.SimOnOffValve)
        ):
            if value not in (0, 1):
                raise ValueError('setpoint must be either 0 or 1 for an On/Off expiratory valve')
            elif value == 1:
                self._expiratory_valve.open()
            else:
                self._expiratory_valve.close()
        elif (
                isinstance(self._expiratory_valve, valves.PWMControlValve) or
                isinstance(self._expiratory_valve, valves.SimControlValve)
        ):
            if not 0 <= value <= 100:
                raise ValueError('setpoint must be between 0 and 100 for an expiratory control valve')
            else:
                self._expiratory_valve.setpoint = value
        self._setpoint_ex = value

    def _init_attr(self):
        """ Pigpio-specific attribute initialization. """
        for section, sdict in self._config.items():
            if 'adc' in sdict['opts']:
                sdict['opts']['adc'] = self._adc
            class_ = getattr(import_module('.' + sdict['class_']['module'], 'vent.io'), sdict['class_']['type'])
            print("hal.{device_name} = {class_} opts={device_options}".format(
                device_name=section,
                class_=class_.__name__,
                device_options=sdict['opts']
            ))  # debug

            setattr(self, section, class_(pig=self._pig, **sdict['opts']))
            print(getattr(self, section))


class AsyncHal(HalBase):
    DAEMON_CMNDS = {
        'echo': b'\x00',
        # 'get_all': b'\x01',
        'pressure': b'\x02',
        'aux_pressure': b'\x03',
        'flow_in': b'\x04',
        'flow_ex': b'\x05',
        'info': b'\x06',
        'aclose': b'\xff'
    }

    @property
    def setpoint_in(self) -> float:
        pass

    @property
    def setpoint_ex(self) -> float:
        pass

    def __init__(self, config_file='vent/io/config/async-devices.ini', port=12377):
        super().__init__(config_file=config_file)
        self.socket = None
        self.port = port
        self.connected = False
        self.async_process = self.async_process = multiprocessing.Process(
            target=AsyncBackend.enter_async_loop,
            kwargs={'port': port, 'config_file': config_file},
            daemon=True
        )

    def __enter__(self):
        self.async_process.start()
        while not self.connected:
            try:
                self.socket = socket.create_connection(("127.0.0.1", self.port))
                self.connected = True
            except ConnectionRefusedError:
                time.sleep(0.005)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.socket()
        except:
            self.async_process.terminate()
        finally:
            self.async_process.join()
            self.async_process.close()

    @property
    def pressure(self) -> float:
        return self._get_from_backend('pressure')

    @property
    def aux_pressure(self) -> float:
        return self._get_from_backend('aux_pressure')

    @property
    def flow_in(self) -> float:
        return self._get_from_backend('flow_in')

    @property
    def flow_ex(self) -> float:
        return self._get_from_backend('flow_ex')

    def _get_from_backend(self, cmd):
        self.socket.send(self.DAEMON_CMNDS[cmd])
        header = self.socket.recv(3)
        assert header[0] == self.DAEMON_CMNDS[cmd][0]
        if len(header) > 1:
            response = self.socket.recv(int.from_bytes(header[1:], 'big'))
            data = pickle.loads(response)
        else:
            data = None
        return data


class AsyncBackend(HalBase):
    """                                         'The Criminal Underground'

        A collection of variables & coroutines, some of which are enduring, some of which are servants that are
    constantly dieing and being resurrected byt their overlords, the Enduring Loops

    """
    CMND_COROUTINES = dict(map(reversed, AsyncHal.DAEMON_CMNDS.items()))
    CONNECTION_COUNTER = count()

    @staticmethod
    def enter_async_loop(*args, **kwargs):
        """ Gateway to the asynchronous
        Args:
            pipe (multiprocessing.connection.Connection):
            commands (dict):
        """
        func = partial(AsyncBackend.async_main_loop, *args, **kwargs)
        trio.run(func)

    @staticmethod
    async def async_main_loop(port, config_file):
        """                             'The Loading-screen of the Asynchronous World'

            Technically not an enduring loop because its technically not a loop. It is enduring though, at least from
        the perspective of the people who live here. Not so much to everyone else. Our lives are like candle flames to
        them, so bright - yet so brief...

        """
        asb = AsyncBackend(config_file=config_file)
        await asb.aopen()
        async with trio.open_nursery() as nursery:
            func = partial(asb.server, main_nursery=nursery)
            nursery.start_soon(trio.serve_tcp, func, port)
            # start sensor sampling coroutines

    def __init__(self, config_file):
        super().__init__(config_file=config_file)
        self.is_running = True
        self._smbus = AsyncSMBus()
        self.watcher_send_channel, self.watcher_receive_channel = trio.open_memory_channel(1)

    async def aopen(self):
        for section, sdict in self._config.items():
            if 'adc' in sdict['opts']:
                sdict['opts']['adc'] = self._adc
            class_ = getattr(import_module('.' + sdict['class_']['module'], 'vent.io'), sdict['class_']['type'])
            setattr(self, section, class_(**sdict['opts']))
            if section == '_adc':
                await self._adc.aopen()

    async def aclose(self, *args):
        self.is_running = False
        async with self.watcher_send_channel as chnl:
            await chnl.send("END")

    async def server(self, server_stream, main_nursery):
        """                                  'Bureaucracy: The Inexorable Machine'

            Worst movie ever. Also a TCP listener/server/command interpreter, and one of the Enduring Loops.

        """
        ident = next(self.CONNECTION_COUNTER)
        print(":: daemon {}: started".format(ident))
        try:
            async for cmd in server_stream:
                if cmd in self.CMND_COROUTINES:
                    print(":: server {}: running command {}".format(ident, self.CMND_COROUTINES[cmd]))
                    command = partial(getattr(self, self.CMND_COROUTINES[cmd]))
                else:
                    command = partial(getattr(self, 'echo'))
                main_nursery.start_soon(command)
                response_data = pickle.dumps(await self.watcher_receive_channel.receive())
                response_data = cmd + len(response_data).to_bytes(2, 'big') + response_data
                await server_stream.send_all(response_data)
                if not self.is_running:
                    break
            print(":: server {}: connection closed".format(ident))
        except Exception as exc:
            print(":: server {}: crashed: {!r}".format(ident, exc))

    async def get_all(self, *args):
        response_data = {
            'pressure': (20, time.time()),
            'aux_pressure': (10, time.time()),
            'flow_in': (5, time.time()),
            'flow_ex': (4, time.time())
        }
        async with self.watcher_send_channel.clone() as chnl:
            await chnl.send(response_data)

    @property
    def setpoint_in(self) -> float:
        pass

    @property
    def setpoint_ex(self) -> float:
        pass

    async def pressure(self, *args):
        response_data = await self._pressure_sensor.get()
        async with self.watcher_send_channel.clone() as chnl:
            await chnl.send(response_data)

    async def aux_pressure(self, *args):
        response_data = await self._aux_pressure_sensor.get()
        async with self.watcher_send_channel.clone() as chnl:
            await chnl.send(response_data)

    async def flow_in(self, *args):
        response_data = await self._flow_sensor_in.get()
        async with self.watcher_send_channel.clone() as chnl:
            await chnl.send(response_data)

    async def flow_ex(self, *args):
        response_data = await self._flow_sensor_ex.get()
        async with self.watcher_send_channel.clone() as chnl:
            await chnl.send(response_data)

    async def echo(self, data=None):
        """ This is a dummy/testing coroutine that just acts like an echo server if called as a response"""
        data = 0 if data is None else pickle.loads(data)
        async with self.watcher_send_channel.clone() as chnl:
            await chnl.send(data)

    async def info(self, *args):
        """ Also kind of a dummy/testing coroutine that just sends back a string with some info about attributes"""
        attributes = str()
        for section, sdict in self._config.items():
            if section == '_adc':
                await self._adc.aopen()
            attributes += '\n    ' + str(type(getattr(self, section)))
        async with self.watcher_send_channel.clone() as chnl:
            await chnl.send(attributes)
