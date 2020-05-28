from functools import partial
from itertools import count
from vent.io.devices import AsyncSMBus
import trio
import time
import pickle


DAEMON_CMNDS = {
    'echo': b'\x00',
    'get_all': b'\x01',
    'get_pressure': b'\x02',
    'get_aux_pressure': b'\x03',
    'get_flow_in': b'\x04',
    'get_flow_ex': b'\x05',
    'setup': b'\x06',
    'aclose': b'\xff'
}


def enter_async_loop(*args, **kwargs):
    """ Gateway to the asynchronous
    Args:
        pipe (multiprocessing.connection.Connection):
        commands (dict):
    """
    func = partial(async_main_loop, *args, **kwargs)
    trio.run(func)


async def async_main_loop(port):
    """                             'The Loading-screen of the Asynchronous World'

        Technically not an enduring loop because its technically not a loop. It is enduring though, at least from the
    perspective of the people who live here. Not so much to everyone else. Our lives are like candle flames to them, so
    bright - yet so brief
    """
    asb = AsyncBackend()
    async with trio.open_nursery() as nursery:
        func = partial(asb.watch_the_port, main_nursery=nursery)
        nursery.start_soon(trio.serve_tcp, func, port)
        # start sensor sampling coroutines


class AsyncBackend:
    """                                         'The Criminal Underground'

        A collection of variables & coroutines, some of which are enduring, some of which are servants that are
    constantly dieing and being resurrected byt their overlords, the Enduring Loops

    """
    CMND_COROUTINES = dict(map(reversed, DAEMON_CMNDS.items()))
    CONNECTION_COUNTER = count()

    def __init__(self):
        self.is_running = True
        self._config = None
        self._smbus = AsyncSMBus()
        self.watcher_send_channel, self.watcher_receive_channel = trio.open_memory_channel(1)

    async def aclose(self, *args):
        self.is_running = False
        async with self.watcher_send_channel as chnl:
            await chnl.send("END")

    async def watch_the_port(self, server_stream, main_nursery):
        """ TCP listener/server/command interpreter. One of the Enduring Loops"""
        ident = next(self.CONNECTION_COUNTER)
        print("::daemon {}: started".format(ident))
        try:
            async for data in server_stream:
                if len(data) > 1:
                    cmd, payload = (data[0].to_bytes(1, 'big'), data[1:])
                    print(
                        "::watch_the_port {}: received command {!r} len(data): {}".format(
                            ident,
                            cmd,
                            len(payload)
                        )
                    )
                else:
                    cmd, payload = (data, None)
                    print("::watch_the_port {}: received command {!r}".format(ident, cmd))
                if cmd in self.CMND_COROUTINES:
                    print("::-->watch_the_port {}: running command {}".format(ident, self.CMND_COROUTINES[cmd]))
                    command = partial(getattr(self, self.CMND_COROUTINES[cmd]), payload)
                else:
                    command = partial(
                        getattr(self, 'echo'),
                        payload
                    )
                main_nursery.start_soon(command)
                response_data = pickle.dumps(await self.watcher_receive_channel.receive())
                await server_stream.send_all(response_data)
                if not self.is_running:
                    break
            print("::watch_the_port {}: connection closed".format(ident))
        except Exception as exc:
            print("::watch_the_port {}: crashed: {!r}".format(ident, exc))

    async def echo(self, data=None):
        """ This is a dummy coroutine that just acts like an echo server if called as a response"""
        data = 0 if data is None else pickle.loads(data)
        async with self.watcher_send_channel.clone() as chnl:
            await chnl.send(data)

    async def setup(self, subcommand):
        if subcommand is None:
            await self.echo()
        else:
            self._config = pickle.loads(subcommand)
            for section, sdict in self._config.items():
                if section == '_adc':
                    setattr(self, section, sdict['class_'](smbus=self._smbus, **sdict['opts']))
            async with self.watcher_send_channel.clone() as chnl:
                await chnl.send(type(self._adc))

    async def get_all(self, *args):
        response_data = {
            'pressure': (20, time.time()),
            'aux_pressure': (10, time.time()),
            'flow_in': (5, time.time()),
            'flow_ex': (4, time.time())
        }
        async with self.watcher_send_channel.clone() as chnl:
            await chnl.send(response_data)

    async def get_pressure(self, *args):
        async with self.watcher_send_channel.clone() as chnl:
            await chnl.send(20)

    async def get_aux_pressure(self, *args):
        async with self.watcher_send_channel.clone() as chnl:
            await chnl.send(10)

    async def get_flow_in(self, *args):
        async with self.watcher_send_channel.clone() as chnl:
            await chnl.send(5)

    async def get_flow_ex(self, *args):
        async with self.watcher_send_channel.clone() as chnl:
            await chnl.send(4)
