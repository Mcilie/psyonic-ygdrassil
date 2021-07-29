import PySimpleGUI as sg
import _thread

import atexit
import asyncio
import sys
from packing import *
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time
import signal

from bleak import BleakScanner, BleakClient
from bleak.backends.scanner import AdvertisementData
from bleak.backends.device import BLEDevice

UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

layout = [[sg.Text("Hello from PySimpleGUI")], [sg.Button("OK")]]



mapFingerToNumber = {
    "Index": "0",
    "Middle": "1",
    "Ring": "2",
    "Pinky": "3",
    "Flexor": "4",
    "Rotator": "5",
}



def mainMenu():
    layoutMain = [
        [sg.Button("Hand Control", key="open", size=(30,3), font=("Helvetica", 36))],
        [sg.Button("Pressure Plotting", key="", size=(30,3),font=("Helvetica", 36))],
        [sg.Button("PEU Plotting", key="", size=(30,3),font=("Helvetica", 36))]
    ]

    return sg.Window('Main Menu', layoutMain, finalize=True)

def connectMenu():
    layoutCon =[
        [sg.Text("Select Device to Connect to")],
        [sg.Listbox(values=[], key='_listbox_', size=(60, 20))],
        [sg.Button("Connect", key="conbtn"),sg.Button("Refresh", key="refr")]
    ]

    return sg.Window('Connect', layoutCon, finalize=True)

def gripMenu():
    layoutGrip = [
        [ sg.Button("Power",size=(9,3), key="G.1.254",font=("Helvetica", 16) ),
        sg.Button("Key",size=(9,3), key="G.2.254",font=("Helvetica", 16) ),
        sg.Button("Pinch",size=(9,3), key="G.3.254",font=("Helvetica", 16) ) 
        ],
        [ sg.Button("Chuck",size=(9,3), key="G.4.254",font=("Helvetica", 16) ),
        sg.Button("RockNRoll",size=(9,3), key="G.5.254",font=("Helvetica", 16) ),
        sg.Button("Point",size=(9,3), key="G.9.254",font=("Helvetica", 16) ) 
        ],
        [ sg.Button("Rude",size=(9,3), key="G.A.254",font=("Helvetica", 16) ),
        sg.Button("Relax",size=(9,3), key="G.C.254",font=("Helvetica", 16) ),
        sg.Button("Chuck OK",size=(9,3), key="G.F.254",font=("Helvetica", 16) ) 
        ],
        []
    ]
    return sg.Window('Grips', layoutGrip, finalize=True)

def fingersMenu():
    layout1 = [
        [sg.Button(i, font=("Helvetica", 14 ), size=(6,2),key="F_Open_"+i+"_"+mapFingerToNumber[i]) for i in ["Rotator", "Flexor", "Index"]],
        [sg.Button(i, font=("Helvetica", 14), size=(6,2),key="F_Open_"+i+"_"+mapFingerToNumber[i]) for i in ["Middle", "Ring", "Pinky"]]
            
        ]
    layout2 = [
        [sg.Button(i,font=("Helvetica", 14), size=(6,2),key="F_Close_"+i+"_"+mapFingerToNumber[i]) for i in ["Rotator", "Flexor", "Index"]],
        [sg.Button(i,font=("Helvetica", 14), size=(6,2),key="F_Close_"+i+"_"+mapFingerToNumber[i]) for i in ["Middle", "Ring", "Pinky"]]
            
        ]
    tabgrp = [[sg.TabGroup([[sg.Tab('Opened', layout1, title_color='Black', element_justification= 'center'),
                    sg.Tab('Closed', layout2,title_color='Black',element_justification= 'center')]], tab_location='centertop',
                    title_color='Black', selected_title_color='Blue',
                    selected_background_color='Gray',font=("Helvetica", 25))]]  

    return sg.Window("Grip Open Close Selection",tabgrp, finalize=True)

def oneFingerMenu():
    layout5 = [
        [sg.Text("Adjust finger anlge measure (degrees)",font=("Helvetica", 16 ))],
        [sg.Text("‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾")],
        [
            sg.Text("0 <",font=("Helvetica", 16 )),
            sg.Input(50, size=(3 , 1),font=("Helvetica", 20 ), key="angleVal", enable_events=True),
            sg.Text("< 100",font=("Helvetica", 16 ))
            ],
        [
            sg.Button("-3",size=(2, 1), font=("Helvetica", 14 )),
            sg.Text("                               ", size=(10,1)),
            sg.Button("+3",size=(2, 1),font=("Helvetica", 14 ))
            ],
        [sg.Button("Apply",size=(6, 1),font=("Helvetica", 14 ))],
        [sg.Text("                                    ")],
        [sg.Text("Finger Priority: ",font=("Helvetica", 16 ) ), sg.Input(0, size=(1 , 1),font=("Helvetica", 16), key="priorityVal", enable_events=True)],
        [sg.Text("‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾")],
        [sg.Button("Save & Exit",size=(6, 1),font=("Helvetica", 14 ))]
    ]

    return sg.Window("Finger",layout5,element_justification='c', finalize=True)




async def findDevices():
    devices = [(i.name, i.address) for i in await BleakScanner.discover() if "PSYONIC" in i.name]
    return devices
# Create an event loop
#while True:

async def handle_rx(_: int, data: bytearray):
    if data == None:
        return
    #arr = copy_bytearray_to_np_uint16(data)
    #global unpacked
    #unpacked = unpack_8bit_into_12bit(arr, 30)
    print(data)

async def main():
    #devices = await findDevices();
    client = None;

    #pages
    finger = None
    fingers = None
    grips = None;
    Menu = None;
    connect = connectMenu();

    await asyncio.sleep(0.5);
    connect["_listbox_"].update(values=await findDevices())
    

    while True:
        #event, values = window.read()
        window, event, values = sg.read_all_windows()

        if event == None or event == 'Exit':
            break

        if window == connect:
            print("hey")

        if event == "refr":
            print("refresh")
            window.FindElement('_listbox_').Update(values=await findDevices())

        if event == "conbtn":
            print("connect", [i for i in values["_listbox_"]])
            print(values["_listbox_"][0][1])
            client = BleakClient(values["_listbox_"][0][1])
            await client.connect()
            await asyncio.sleep(0.1)
            await client.start_notify(UART_TX_CHAR_UUID, handle_rx)
            await asyncio.sleep(0.1)
            window.close()
            Menu = mainMenu()
        
        if event == "open":
            print("open")
            window.close()
            grips = gripMenu()
            #await client.write_gatt_char(UART_RX_CHAR_UUID, data = bytearray("mg00", 'utf-8'), response=True)
            #await asyncio.sleep(2)

        if event.startswith("G."):
            print(event)
            await client.write_gatt_char(UART_RX_CHAR_UUID, data = bytearray("mg00", 'utf-8'), response=True)
            await asyncio.sleep(2)
            window.close()
            fingers = fingersMenu();

        if event.startswith("F_"):
            print(event)
            await client.write_gatt_char(UART_RX_CHAR_UUID, data = bytearray("mf" + event[-1], 'utf-8'), response=True)
            await client.write_gatt_char(UART_RX_CHAR_UUID, data = bytearray("mr", 'utf-8'), response=True)
            await client.write_gatt_char(UART_RX_CHAR_UUID, data = bytearray("mR", 'utf-8'), response=True)
            await asyncio.sleep(2)
            window.close()
            finger = oneFingerMenu()

        

            

    
    # End program if user closes window or
    # presses the OK button
    


loop = asyncio.get_event_loop()

#try:        
loop.run_until_complete(main())

#window.close()