"""Smbus2 asyncio support."""
import trio
from vent.io.devices import AsyncADS1015
from vent.io.devices.sensors import AsyncAnalogSensor, AnalogSensor
import numpy as np
from functools import partial


async def update_cycle(snsr):
    while True:
        await snsr.update()


async def producer(snsr, send):
    async with send:
        while True:
            #await trio.sleep(0.05)
            #print("Averaged {} sensor values".format(len(snsr._data['value'])))
            val = await snsr.get(average=True)
            await send.send((snsr.MUX, val))


async def consumer(r, recv):
    async with recv:
        while True:
            mux, val = await recv.receive()
            #print('Recieved value {} on channel {}'.format(val, mux))
            r[mux].append(val)


async def heartbeat():

    async def tick(nursery):
        print('Tick... ')
        await trio.sleep(1)
        nursery.start_soon(tock, nursery)

    async def tock(nursery):
        print("Tock!")
        await trio.sleep(1)
        nursery.start_soon(tick, nursery)
    async with trio.open_nursery() as nursery:
        nursery.start_soon(tick, nursery)


async def main(DR=2400):
    ads = AsyncADS1015()
    results = [[], [], [], []]
    await ads.aopen()
    i = 0
    (send, recv) = trio.open_memory_channel(4)
    sensors = []
    with trio.move_on_after(10):
        async with trio.open_nursery() as nursery:
            nursery.start_soon(heartbeat)
            for mux in AsyncADS1015._CONFIG_VALUES[1][4:]:
                sensors.append(AsyncAnalogSensor(ads, MUX=mux, DR=DR))
                nursery.start_soon(update_cycle, sensors[-1])
                nursery.start_soon(producer, sensors[-1], send.clone())
                nursery.start_soon(consumer, results, recv)
    return results


res = trio.run(main)
n_readings = np.mean([len(x) for x in res])
print('Got readings from sensors on average {} times'.format(n_readings))
for mux in range(len(res)):
    print('    -> Sensor on MUX {} averaged {}V'.format(mux, np.mean(res[mux])))
    print('    ->                       max {}V'.format(np.max(res[mux])))
    print('    ->                       min {}V'.format(np.min(res[mux])))
