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
import PySimpleGUI as sg
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

device = 0
connected = 0
client = None
devs = []
mWin = 0


async def sendCMD(cmd):
    global client
    #linein = "P4"
    print("fjdlskfjsdklf", client)
    byteData = bytearray(cmd, 'utf-8')
    await client.write_gatt_char(UART_RX_CHAR_UUID, data=byteData,response=True)
    await asyncio.sleep(1)


async def handle_rx(_: int, data: bytearray):
    print(data)
    #print(len(data));
    #arr = copy_bytearray_to_np_uint16(data)
    # print("-")
    #print(len(arr));
    #global unpacked
    #unpacked = unpack_8bit_into_12bit(arr, 30)
    #print(len(unpacked))
    

async def updateDeviceList(win):
    
    print("called")
    global devs
    de = [i for i in await BleakScanner.discover() if "PSYONIC" in i.name]
    de2 = [str(i).split(':')[-1] for i in de]
    devs+= [i for i in de if "PSYONIC" in i.name] 
    win.Element('fac').Update(values = de2)
    print("updated windows")
    


async def forceConnectDevice():
    sg.Popup("Click me to start scanning for devices!\nIt will take a few seconds...")
    global client
    global devs
    global connected
    de = [i for i in devs if "PSYONIC" in i.name]
    de2 = [str(i).split(':')[-1] for i in de]
    

    layoutCon =[
        [sg.Text("Select Device to Connect to")],
        [sg.Listbox(values=de2, key='fac', size=(60, 20))],
        [sg.Button("Connect", key="conbtn"),sg.Button("Refresh", key="refr")]
    ]

    windowC = sg.Window("Connect", layoutCon,finalize=True)
    await updateDeviceList(windowC)
    while not connected:
        windowC.refresh()
        #print(devices)
        event, values = windowC.read()
        #asyncio.create_task(updateDeviceList(windowC))
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        if event == "refr":
            await updateDeviceList(windowC)
        if event == "conbtn":
            for q in devs:
                if values['fac'][0].strip() in q.name:
                    device = q
                    print(device)
                    client = BleakClient(device)
                    await client.connect();
                    #await asyncio.sleep(0.1);
        
                    await client.start_notify(UART_TX_CHAR_UUID, handle_rx)
                    svcs = await client.get_services()

                    #client =   BleakClient(device)
                    #await client.start_notify(UART_TX_CHAR_UUID, handle_rx)

                    #client = BleakClient(device)#asyncio.run(BleakClient(device))
                    #print(client)

                    windowC.close()
                    #global proc 
                    
                    #global bttra
                    #del bttra
                    #^^^^^^^
                    #connFunc()
                    #time.sleep(1)
                    #print(client)
                    
                    #global bttra
                    #del bttra
            
            connected = True
            print(device)
        
        
        
    windowC.close()

async def sample():
    layoutCon =[
        [sg.Text("TEXT",key="ttt")],
        [sg.Button("Update", key="upd")]
    ]
    global client 
    global mWin
    mWin= sg.Window("Connect", layoutCon,finalize=True)
    while True:
        event, values = mWin.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        elif event == "upd":
            await sendCMD("GA~")
            time.sleep(0.5)
            #await client.write_gatt_char(UART_RX_CHAR_UUID, data = bytearray("mg00", 'utf-8'), response=True);
            #await asyncio.sleep(5)
            await sendCMD("m")
            await sendCMD("mf0")
            await sendCMD("mr")
            #time.sleep(0.5)

    
    
'''
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
'''



async def main():
    
    await forceConnectDevice()
    await sample()
    '''
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
        await client.write_gatt_char(UART_RX_CHAR_UUID, byteData)
        start_time = time.time()

        print('fdhshkd')
        plt.show(block=False)
        cidclose = fig.canvas.mpl_connect('close_event', thingy)
        ani = animation.FuncAnimation(fig, animate, init_func=init, interval=200, blit=False, save_count=0)
        
        while run: 
            #print("fsdfjsdlkfj")
            await asyncio.sleep(0.000000001)
            #print('12310293')
            plt.pause(0.000000001)
        '''
        
        
        

        
loop = asyncio.get_event_loop()

try:        
    loop.run_until_complete(main())
except KeyboardInterrupt as e:

    print("Caught keyboard interrupt. Quitting Program...")

