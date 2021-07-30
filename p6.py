#!/usr/bin/python3

import _thread

import atexit
import asyncio
import sys
from packing import *
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time

from bleak import BleakScanner, BleakClient
from bleak.backends.scanner import AdvertisementData
from bleak.backends.device import BLEDevice

UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

UART_SAFE_SIZE = 20

ylower = 0
yupper = 5000
numlines = 30
bufwidth = 50
unpacked = [0]*30
run = True

async def connect():
    devices = await BleakScanner.discover()
    i = 0        
    for d in devices:
        if d.name:
            print("[%d]: " % i, end='')
            print(d.name)
        i = i + 1
    instr = input("Enter idx to connect to (number)")
    idx = int(instr)
    if idx >= 0 and idx < i:
        return devices[idx]
    else:
        return 0



async def main():
    
    fig, ax = plt.subplots()
    ax.set_ylim(ylower,yupper)
    line, = ax.plot([], [], lw = 2) # lw is line width
    lines = [] # lines holds line objects for ploting
    data = [] # data holds data points to plot
    plotlays, plotcols = [numlines], ["black","red","blue","green","yellow","purple","orange"]
    t = [0]*bufwidth
    

    for index in range(numlines):
        # create line object
        lineobj = ax.plot([], [], lw = 2, color=plotcols[index%7])[0]
        lines.append(lineobj)
        # create data object
        dataobj = [0]*bufwidth
        data.append(dataobj)

    def init():  # only required for blitting to give a clean slate.
        for line in lines:
            line.set_data([],[])
        return lines

    async def handle_rx(_: int, data: bytearray):
        #print(len(data));
        arr = copy_bytearray_to_np_uint16(data)
       # print("-")
        #print(len(arr));
        global unpacked
        unpacked = unpack_8bit_into_12bit(arr, 30)
        #print(len(unpacked))
        print(unpacked)
        
    
    def animate(i):
        # delete first entry in each list
        #plt.pause(1)
        print("bruh")
        del t[0]
        for index in range(numlines):
            del (data[index])[0]

        t.append(time.time()-start_time)
        for index in range(numlines):
            data[index].append(unpacked[index]) 

        #rescale plot
        ax.relim()
        ax.autoscale_view()

        # set line data
        for lnum, line in enumerate(lines):
            line.set_data(t, data[lnum])
        return lines
    
    

    device = await connect()
    if not device:
        print("Device name %s not found" % scanname)
        return
    async with BleakClient(device) as client:
        print(client)
        
        await client.start_notify(UART_TX_CHAR_UUID, handle_rx)

        print("Connected...")

        async def BTdisconnect():
            print("hey")
            try:
                await client.stop_notify(UART_TX_CHAR_UUID)
                await client.disconnect()
            except:
                print('error')
            #print("Disconnected from %s" % device.name)

        def thingy(event):
            global run
            run = False
            print("DFJDLK")
            asyncio.ensure_future(BTdisconnect())
            print('fdfdf')
            

        """  @atexit.register
        def shutdown():

            loop.run_until_complete(BTdisconnect()) """
        
        svcs = await client.get_services()
        print("Services:")
        for service in svcs:
            print(service)

        print('statement1')

        linein = "P4"
        byteData = bytearray(linein, 'utf-8')
        #await client.write_gatt_char(UART_RX_CHAR_UUID, byteData)
        start_time = time.time()

        print('fdhshkd')
        plt.show(block=False)
        cidclose = fig.canvas.mpl_connect('close_event', thingy)
        ani = animation.FuncAnimation(fig, animate, init_func=init, interval=200, blit=False, save_count=0)
        
        while run: 
            #print("fsdfjsdlkfj")
            t1 = time.time()
            print("About to write G1ÿ "+str(t1%60))
            byteData = bytearray("G1",'utf-8')+bytearray([254])
            print(byteData)
            await client.write_gatt_char(UART_RX_CHAR_UUID, byteData)
            t2 = time.time()
            print("Wrote G1ÿ " +str(t2%60))
            print(t2-t1)
            print()

            await asyncio.sleep(1.7)
            #print('12310293')
            t3 = time.time()
            print("About to write G0ÿ "+str(t3%60))
            byteData = bytearray("G0",'utf-8')+bytearray([254])
            print(byteData)
            await client.write_gatt_char(UART_RX_CHAR_UUID, byteData)
            t4 = time.time()
            print("Wrote G0ÿ " +str(t4%60))
            print(t4-t3)
            print()
            print(t4-t1)
            await asyncio.sleep(1.7)
        
        
        

        
loop = asyncio.get_event_loop()

try:        
    loop.run_until_complete(main())
except KeyboardInterrupt as e:

    print("Caught keyboard interrupt. Quitting Program...")

