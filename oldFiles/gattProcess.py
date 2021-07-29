#!/usr/bin/python

import _thread

import asyncio
import sys
import sys
from bleak import BleakScanner, BleakClient
from bleak.backends.scanner import AdvertisementData
from bleak.backends.device import BLEDevice
import sys
UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

UART_SAFE_SIZE = 20



#print("Scanning...")
sys.stdout.flush()

async def connect():
    
    devices = await BleakScanner.discover()

    i = 0        
    for d in devices:
        if sys.argv[1].strip() == d.name:
            return devices[i]
        i += 1 
    
    return 0
        

async def run():
    def handle_rx(_: int, data: bytearray):
        print("received:", data)
        sys.stdout.flush()

    device = await connect()
    if not device:
        print("failed to connect to device: ", end='')
        print(device)
        return
    else:
        #print("connnecting to: ", end='')
        #print(device) 
        #sys.stdout.flush()   
        pass    
    
    
    async with BleakClient(device) as client:
        
        
        await client.start_notify(UART_TX_CHAR_UUID, handle_rx)

        #print("Connected!")
        #sys.stdout.flush()
        
        '''svcs = await client.get_services()
        print("Services:")
        for service in svcs:
            print(service)'''

    
        linein = ""
        while 1:
            linein = sys.stdin.readline().strip()
            if linein == "exit":
                print("exiting...")
                break
            if linein:
                data = bytearray(linein, 'utf-8')
                linein = ""
                await client.write_gatt_char(UART_RX_CHAR_UUID, data)
                print("sent:", data)
                sys.stdout.flush()
                await asyncio.sleep(0.25)

try:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
except:
    print("gperror")

