#!/usr/bin/python

import _thread

import asyncio
import sys

from bleak import BleakScanner, BleakClient
from bleak.backends.scanner import AdvertisementData
from bleak.backends.device import BLEDevice

UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

UART_SAFE_SIZE = 20

print("Scanning...")

async def connect():
    
    devices = await BleakScanner.discover()
    i = 0        
    for d in devices:
        if d.name and "PSYONIC" in d.name:
            print("[%d]: " % i, end='')
            print(d.name)
        i = i + 1
    instr = input("Enter idx to connect to (number)")
    idx = int(instr)
    if idx >= 0 and idx < i:
        return devices[idx]
    else:
        return 0
        

async def run():
    def handle_rx(_: int, data: bytearray):
        print("received:", data)

    device = await connect()
    if not device:
        print("failed to connect to device: ", end='')
        print(device)
        return
    else:
        print("connnecting to: ", end='')
        print(device)        
    
    
    async with BleakClient(device) as client:
        
        await client.start_notify(UART_TX_CHAR_UUID, handle_rx)

        print("Connected!")
        
        svcs = await client.get_services()
        print("Services:")
        for service in svcs:
            print(service)

    
        linein = ""
        while 1:
            linein = input(":")
            if linein == "exit":
                print("exiting...")
                break
            if linein:
                data = bytearray(linein, 'utf-8')
                linein = ""
                await client.write_gatt_char(UART_RX_CHAR_UUID, data)
                print("sent:", data)
                await asyncio.sleep(0.25)

loop = asyncio.get_event_loop()
loop.run_until_complete(run())
