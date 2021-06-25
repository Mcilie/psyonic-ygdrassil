import PySimpleGUI as sg
import asyncio
import nest_asyncio
nest_asyncio.apply()
from PySimpleGUI.PySimpleGUI import Btn
from packing import *
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time
from concurrent.futures import ThreadPoolExecutor
from bleak import BleakScanner, BleakClient
from bleak.backends.scanner import AdvertisementData
from bleak.backends.device import BLEDevice
import threading
from sarge import Command, run, Capture
from subprocess import PIPE
UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
readVar = []

commStack = []
recvStack = []

proc = 0 

def sendms(arg):
    global proc
    proc.stdin.write(arg.encode() + b"\n")
    proc.stdin.flush()
    retList = []
    qet = 0
    while True:
        time.sleep(0.05)
        qe = proc.stdout.readline().decode()
        print("ms "+ qe)
        if "Saved" in qe:
            for i in range(20):
                qe = proc.stdout.readline().decode()
            return qe
        else :
            pass

def sendme(arg):
    global proc
    proc.stdin.write(arg.encode() + b"\n")
    proc.stdin.flush()
    retList = []
    qet = 0
    while True:
        time.sleep(0.05)
        qe = proc.stdout.readline().decode()
        print("me:"+qe)
        if "Exiting" in qe:
            return qe
        else :
            pass

def sendmr(arg):
    global proc
    proc.stdin.write(arg.encode() + b"\n")
    proc.stdin.flush()
    retList = []
    qet = 0
    while True:
        time.sleep(0.05)
        qe = proc.stdout.readline().decode()
        if "q[" in qe:
            return qe
        else :
            pass
def readPriority(arg):
    global proc
    proc.stdin.write(arg.encode() + b"\n")
    proc.stdin.flush()
    retList = []
    qet = 0
    while True:
        time.sleep(0.05)
        qe = proc.stdout.readline().decode()
        if "p=" in qe:
            print("PRIORITY "+qe)
            return qe.split("=")[-1].replace("'","")
        else :
            pass

def setPriority(arg,timestop = 5):
    global proc
    proc.stdin.write(arg.encode() + b"\n")
    proc.stdin.flush()
    retList = []
    qet = 0
    tet = time.time()
    while True:
        time.sleep(0.05)
        qe = proc.stdout.readline().decode()
        if "Set" in qe:
            return qe.split("=")[-1].replace("'","")
        else:
            pass
        if time.time()-tet > timestop:
            break



def sendCommandWithResponse(arg,timediff = 10):
    ta = time.time()
    global proc
    proc.stdin.write(arg.encode() + b"\n")
    proc.stdin.flush()
    retList = []
    qet = 0
    while True:
        time.sleep(0.05)
        qe = proc.stdout.readline().decode()
        qet += (qe == "")
        if time.time()- ta >timediff:
            retList.append("ERR")
            print("No Bueno")
            break
        if len(retList)>0:
            break
        if "idx" in qe: 
            pass
        elif "sent:" in qe:
            pass
        elif qe == "":
            pass
        else:
            retList.append(qe)
    return retList

def sendCommandWithOutResponse(arg):

    global proc
    proc.stdin.write(arg.encode() + b"\n")
    proc.stdin.flush()
    
    while True:
        time.sleep(0.05)
        qe = proc.stdout.readline().decode()
        if qe == "":
            break
def sendCommandEatingRespones(arg):
    global proc
    proc.stdin.write(arg.encode() + b"\n")
    proc.stdin.flush()
    voidList = []
    while True:
        time.sleep(0.05)
        qe = proc.stdout.readline().decode()
        if qe == "" and len(voidList) > 0:
            break
        elif qe == "" and len(voidList) == 0:
            pass
        else:
            voidList.append(qe)

        
    


devices = {}
connected = False 
device = 0
client = 0


def handle_rx(a,b):
    print("MESSASGE:" + str(b))
    
async def getDevs():
    global devices
    print("Ereee", devices)
    devices = [i  for i in await BleakScanner.discover() if "PSYONIC" in i.name]
    #print(devices)
    return "ree"

async def write(data):
    global client
    global readVar
    print(data + "reeeee")
    await client.write_gatt_char(UART_RX_CHAR_UUID, bytearray(data,"utf-8"))
    print("done writing pog?!?!?!")
    #readVar.append(await client.read_gatt_char(UART_TX_CHAR_UUID))
    await asyncio.sleep(0.000000001)
    return  readVar

async def asyncConFunc():
    global client
    await client.connect()

def getReadvar():
    global readVar
    ooga = "booga"
    while len(readVar)==0:
        ooga = "booga"
    return readVar.pop()

async def susGatChar():
    global client
    await client.start_notify(UART_TX_CHAR_UUID, handle_rx) 
    
def sendCMD(d, reading=False):
    print("Heyo")
    btt2 =  BT_ThreadAsync()
    btt2.start_loop()
    btt2.racWarg(write,d)
    #ree = asyncio.run(write(d))
    print("wsendcmd")
    """ print("oy mate")
    if reading:
        return getReadvar()
    else:
        try:
            global readVar
            readvar.pop()
        except:
            pass
        return "empty" """

class BT_ThreadAsync:
    def __init__(self):
        self.pool = ThreadPoolExecutor(max_workers=2)
        self.loop = asyncio.get_event_loop()

    
    
    async def calculate(self):
        result = await self.loop.run_in_executor(self.pool,  getDevs)
        

    def run(self):
        asyncio.run_coroutine_threadsafe(getDevs(), self.loop)

    def runAsyncCmd(self,cmd):
        asyncio.run_coroutine_threadsafe(cmd(),self.loop)

    def racWarg(self,cmd,arg):
        asyncio.run_coroutine_threadsafe(cmd(arg),self.loop)

    def start_loop(self):
        thr = threading.Thread(target=self.loop.run_forever)
        thr.daemon = True
        thr.start()

def connFunc():
    #time.sleep(2)
    btt =  BT_ThreadAsync()
    btt.start_loop()
    btt.runAsyncCmd(asyncConFunc)
    btt.runAsyncCmd(susGatChar)
    #asyncio.run(asyncConFunc())
    

def open_windowOneFinger(finger):
    terp = time.time()
    sendCommandWithOutResponse("m")
    sendCommandWithResponse("mf" + finger.split("_")[-1])
    currAngle = sendmr("mr")
    print(currAngle)
    currAngle  = float(currAngle.split("=")[-1].strip().replace("'",""))
    pri = readPriority("mR")
    print(pri)
    layout5 = [
        [sg.Text("Adjust finger anlge measure (degrees)",font=("Helvetica", 16 ))],
        [sg.Text("‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾")],
        [
            sg.Text("0 <",font=("Helvetica", 16 )),
            sg.Input(currAngle, size=(5 , 1),font=("Helvetica", 20 ), key="angleVal", enable_events=True),
            sg.Text("< 100",font=("Helvetica", 16 ))
            ],
        [
            sg.Button("-n",size=(2, 1), font=("Helvetica", 14 )),
            sg.Text("n=", size=(3,1)) , sg.Input(3,size=(4, 1), key ="nVar", font=("Helvetica", 14 ) ),
            sg.Button("+n",size=(2, 1),font=("Helvetica", 14 ))
            ],
        [sg.Button("Apply",size=(6, 1),font=("Helvetica", 14 ))],
        [sg.Text("                                    ")],
        [sg.Text("Finger Priority: ",font=("Helvetica", 16 ) ), sg.Input(pri, size=(3 , 1),font=("Helvetica", 16), key="priorityVal", enable_events=True)],
        [sg.Text("‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾")],
        [sg.Button("Save & Exit", key = "sne",size=(6, 1),font=("Helvetica", 14 )),sg.Button("Exit w/o Saving", key = "swne",size=(15, 1),font=("Helvetica", 14 )) ]
    ]

    window4 =sg.Window("Finger",layout5,element_justification='c')
    #Read  values entered by user
    while True:
        event, values = window4.read()
        print(event)
        if event == "Exit" or event == sg.WIN_CLOSED or event =="swne":
            
            time.sleep(0.75)
            sendme("me")
            print("saved")
            break
            
        if event == "+n" and currAngle <=100:
            terp2 = time.time()
            if terp2-terp >= 0.3:
                currAngle += int(values["nVar"])
                time.sleep(0.03)
                sendCommandWithResponse("mq" + str(currAngle),timediff=2)
                window4.Element("angleVal").Update(value=currAngle)
            terp = time.time()
        if event == "-n":
            terp2 = time.time()
            if terp2-terp >= 0.3 and currAngle >=10:
                currAngle -=int(values["nVar"])
                time.sleep(0.03)
                sendCommandWithResponse("mq" + str(currAngle),timediff=2)
                window4.Element("angleVal").Update(value=currAngle)
            terp = time.time()
        if event == "Apply":
            sendCommandWithResponse("mq" + str(values["angleVal"]),timediff=2)
            time.sleep(0.5)
            setPriority("mp" + str(values["priorityVal"]))
            print(str(values["priorityVal"]))
            print("applied")
            
        if event == "sne":
            sendms("ms")
            time.sleep(0.75)
            sendme("me")
            print("saved")
            break
    

    #access all the values and if selected add them to a string
    window4.close()  

        
def open_windowOneGrip(gripID):
    ee = gripID.replace(".","")
 
    print(ee)
    print(sendCommandWithOutResponse(ee))
    #print(sendCMD("G0~"))
    #print(getReadvar())
    #time.sleep(0.2)
    #print(sendCMD("mf0"))
    #time.sleep(0.2)
    #print(sendCMD("mr"))
    #print(sendCMD("mg00"))
    #Do BLE things...

    iq = ["Index","Middle", "Ring","Pinky","Flexor","Rotator"]
    it = []
    #for k in iq:
    #    sendCommandWithResponse("mf" + str(iq.index(k)))
    #    it.append(sendCommandWithResponse("mr"))
    #print(iq,it)

    layout1 = [
           [sg.Button(i, font=("Helvetica", 14 ), size=(6,2),key="F_Open_"+str(iq.index(i))) for i in ["Index","Middle", "Ring"]],
           [sg.Button(i, font=("Helvetica", 14), size=(6,2),key="F_Open_"+str(iq.index(i))) for i in ["Pinky","Flexor","Rotator"]]
           
           ]
    layout2 = [
           [sg.Button(i,font=("Helvetica", 14), size=(6,2),key="F_Close_"+str(iq.index(i))) for i in ["Index","Middle", "Ring"]],
           [sg.Button(i,font=("Helvetica", 14), size=(6,2),key="F_Close_"+str(iq.index(i))) for i in ["Pinky","Flexor","Rotator"]]
           
           ]
    tabgrp = [
        [sg.TabGroup([
            [sg.Tab('Opened',  layout1,key=gripID+"|o", title_color='Black', element_justification= 'center'),
            sg.Tab('Closed', layout2,  key=gripID+"|c",title_color='Black',element_justification= 'center')
             ][::-1] ], tab_location='centertop',
                       title_color='Black', selected_title_color='Blue',
                       selected_background_color='Gray',font=("Helvetica", 25), key='tg')]]
    window3 =sg.Window("Grip Open Close Selection",tabgrp)
    #window3.bind('<FocusOut>', '+FOCUS OUT+')
    #window3.bind('<FocusIn>', '+INPUT FOCUS+')
   
    #window3['tg'].Widget.select(1)
    #Read  values entered by user
    while True:
        print("enter here maybe?")
        event,values=window3.read()
        print("ree" + str(event)+ str(values))
        if event == "Exit" or event == sg.WIN_CLOSED:
            print(event)
            break
        '''if values["tg"].endswith("|c"):
            
            print(sendCMD(ee))
            
        if values["tg"].endswith("|o"):
            print(sendCMD("G0~"))'''
        if event != None and event.startswith("F"):
            print(event)
            open_windowOneFinger(event)
        
        
            

    #access all the values and if selected add them to a string
    window3.close()  

def open_windowGripCTL():
    q = []
    q = [
        [ sg.Button("Power",size=(9,3), key="G.1.~",font=("Helvetica", 16) ),
          sg.Button("Key",size=(9,3), key="G.2.~",font=("Helvetica", 16) ),
          sg.Button("Pinch",size=(9,3), key="G.3.~",font=("Helvetica", 16) ) 
        ],
        [ sg.Button("Chuck",size=(9,3), key="G.4.~",font=("Helvetica", 16) ),
          sg.Button("RockNRoll",size=(9,3), key="G.5.~",font=("Helvetica", 16) ),
          sg.Button("Point",size=(9,3), key="G.9.~",font=("Helvetica", 16) ) 
        ],
        [ sg.Button("Rude",size=(9,3), key="G.A.~",font=("Helvetica", 16) ),
          sg.Button("Relax",size=(9,3), key="G.C.~",font=("Helvetica", 16) ),
          sg.Button("Chuck OK",size=(9,3), key="G.F.~",font=("Helvetica", 16) ) 
        ],
        []
    ]

    
    layout1 =  q

    
    
    window2 = sg.Window("Second Window",layout1 , element_justification='c', modal=True)

    choice = None
    while True:
        event, values = window2.read()
        print(event)
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        if event.startswith("G."):
            window2.close()
            open_windowOneGrip(event)
            break
        
    window2.close()


def main():
    global client
    
    print(client)
    layoutMain = [
       [sg.Button("Hand Control", key="open", size=(30,3), font=("Helvetica", 36))],
       [sg.Button("Pressure Plotting", key="", size=(30,3),font=("Helvetica", 36))],
       [sg.Button("PEU Plotting", key="", size=(30,3),font=("Helvetica", 36))]
    ]
    window = sg.Window("Main Window", layoutMain)
    while True:
        event, values = window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        if event == "open":
            window.Disappear()
            open_windowGripCTL()
            window.Reappear()
        
    window.close()

def forceConnectDevice():
    global devices
    global device
    global connected
    global client
    d =[i for i in devices]

    layoutCon =[
        [sg.Text("Select Device to Connect to")],
        [sg.Listbox(values=d, key='fac', size=(60, 20))],
        [sg.Button("Connect", key="conbtn"),sg.Button("Refresh", key="refr")]
    ]

    windowC = sg.Window("Connect", layoutCon)
    while not connected:
        print(devices)
        event, values = windowC.read()
        windowC.Element('fac').Update(values=[str(i).split(':')[-1] for i in devices])
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        if event == "refr":
            global bttra
            bttra.run()
        if event == "conbtn":
            for q in devices:
                if values['fac'][0].strip() in q.name:
                    device = q
                    #client = BleakClient(device)#asyncio.run(BleakClient(device))
                    #print(client)
                    windowC.close()
                    global proc 
                    proc = Command("python3 gattProcess.py {}".format(q.name), stdout=Capture(buffer_size=1))
                    proc.run(input=PIPE, async_=True)
                    #^^^^^^^
                    #connFunc()
                    #time.sleep(1)
                    #print(client)
                    
                    #global bttra
                    #del bttra
            
            connected = True
            print(device)
        
        
        
    windowC.close()
    

try:
    bttra = BT_ThreadAsync()
    bttra.start_loop()
    bttra.run()

    forceConnectDevice()
    main()
    asyncio.run(client.disconnect())
except:
    asyncio.run(client.disconnect())

