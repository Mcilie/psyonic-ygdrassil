#!/usr/bin/python3

import _thread
from pympler import summary,muppy
import objgraph
import atexit
import asyncio
import sys
from packing import *
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
import PySimpleGUI as sg
from bleak import BleakScanner, BleakClient
from bleak.backends.scanner import AdvertisementData
from bleak.backends.device import BLEDevice
from concurrent.futures import ThreadPoolExecutor, thread
import threading
import gc
from guppy import hpy
isFsrPlotting = False
isPeuPlotting = False
fingersGoingBrrr = False
UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

UART_SAFE_SIZE = 20

'''
|
|
|
|
|
'''


class fsrQueue:
    def __init__(self):
        self.tVar = [0 for i in range(35)]
        self.pVar = [[0 for k in range(6)] for l in range(35)]
    def add(self,timeStart,bytearr):
        self.tVar = self.tVar[1:] + [time.time()-timeStart]
        self.pVar = self.pVar[1:] + [bytearr]
    def get(self):
        return [self.tVar,self.pVar]
fsrQ = fsrQueue()

class BT_ThreadAsync:
    def __init__(self):
        self.pool = ThreadPoolExecutor(max_workers=2)
        self.loop = asyncio.get_event_loop()
        self.start_loop()
        self.devs = {}
        self.c = None 
        self.win = None
        self.mode = "not editing"
        self.ts = 0
        self.buffCache = []
        self.fsr_finger = 0 
        '''
        index, middle, ring, pinky, thumb
        each finger is 6 datapoints in one array. 

        0 is index thumb is 4
        arr = [1,2,3,4...30]
        indexSensors = arr[bThread.fsr_finger * 6 : ]
        '''
        

    def runAsyncCmd(self,cmd):
        asyncio.run_coroutine_threadsafe(cmd(),self.loop)

    def racWarg(self,cmd,arg):
        asyncio.run_coroutine_threadsafe(cmd(arg),self.loop)

    def racWargTime(self,cmd,arg,timev,times):
        asyncio.run_coroutine_threadsafe(cmd(arg,timeout=timev,timestall=times),self.loop)

    def start_loop(self):
        thr = threading.Thread(target=self.loop.run_forever)
        thr.daemon = True
        thr.start()
    
    async def handle_rx(self, a, b):
        
        #print(b)
        global isFsrPlotting
        global fsrQ
        if isFsrPlotting:
            #print(b)
            dta = unpack_8bit_into_12bit(copy_bytearray_to_np_uint16(b),30)
            findex  = self.fsr_finger
            fsrQ.add(self.ts,dta[findex*6:(findex*6)+6])
            del dta
            
            '''
            if len(self.buffCache) >3:

                
                fsrQ.add(self.ts, sum(self.buffCache)/4)
                self.buffCache= []
                self.buffCache.append(dta)
            else:
                self.buffCache.append(dta)'''

            #print(dta)
            #print(dta[:6])
            
            #global isFsrPlotting
            #while isFsrPlotting:
            #self.win.write_event_value('-THREAD-', 'done.')
            return 
        
        #global isFsrPlotting
        global isPeuPlotting
        b =str(b)[2:-1]
        if "q[" in b and ( not (isFsrPlotting or isPeuPlotting)):
            self.win.write_event_value("q[",float(b.replace("'",'').split("=")[-1]))
            #self.win.FindElement("angleVal").Update(value=float(b.split("=")[-1]))
        elif "p=" in b and ( not (isFsrPlotting or isPeuPlotting)):
            self.win.write_event_value("p=",int(b.replace("'",'').split("p=")[-1].split(",")[0]))
            #self.win.FindElement("priorityVal").Update(value=)
        

    async def searchForDevices_async(self, window):
        l = [i for i in await BleakScanner.discover() if "PSYONIC" in i.name]
        self.devs = {i.name: i for i in l}
        window.write_event_value("thrd",self.devs)
    
    def searchForDevices(self,window):
        self.racWarg(self.searchForDevices_async, window)

    async def connectToDevice_async(self,device):
        client = BleakClient(device)
        await client.connect();
        #await asyncio.sleep(0.1); sdlkalsdklk With thb that dsds

        await client.start_notify(UART_TX_CHAR_UUID, self.handle_rx)
        self.c = client
    
    def connectToDevice(self,device):
        self.racWarg(self.connectToDevice_async,device)
    
    async def sendCommandToHand_async(self,command ,timeout=0.25,timestall=0):
        await asyncio.sleep(timestall)
        byteData = bytearray(command, 'utf-8')
        await self.c.write_gatt_char(UART_RX_CHAR_UUID, byteData)
        print("written " + command)
        await asyncio.sleep(timeout)
        if command == "m":
            self.mode="editing"
        elif command == "me":
            self.mode = "not editing"
    
    
    def sendCommandToHand(self,command,timeout=0.25,timestall=0):
        
        self.racWargTime(self.sendCommandToHand_async,command,timeout,timestall)
    
    
#
#
#
#
#

def brrThreadBackend():
    global bThread
    global fingersGoingBrrr
    doneOneOnce = False
    while fingersGoingBrrr:
        bThread.sendCommandToHand("G1þ",timeout =0)
        time.sleep(1.4)
        bThread.sendCommandToHand("G0þ",timeout=0)
        time.sleep(1.4)
        '''
        T=int(time.time())%6
        
        if T == 0 and doneOneOnce==False:
            bThread.sendCommandToHand("G1þ",timeout=0)
            doneOneOnce = True
        elif T == 3 and doneOneOnce == True:
        #time.sleep(1)
            bThread.sendCommandToHand("G0þ",timeout=0)
            doneOneOnce = False'''

def brrThread():
    ttt = threading.Thread(target= brrThreadBackend,args=())
    ttt.start()

def peuPlot():
    layoutPEU= [
        [sg.Canvas(size=(500,500), key='canvas')],
        [sg.Button("Make fingers\ngo brrrrr", key="fgb")]
    ]
    peu_window =sg.Window("FSR Plotting",layoutPEU,finalize=True)
    global fingersGoingBrrr
    global isPeuPlotting
    isPeuPlotting = True
    global bThread
    bThread.win = peu_window
    bThread.sendCommandToHand("P6")

    while True:
        
        event, values = peu_window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            bThread.sendCommandToHand("P1",timestall=0.25)
            isPeuPlotting = False
            fingersGoingBrrr = False
            break
        if event == "fgb":
            '''all_objects = muppy.get_objects()
            sum1 = summary.summarize(all_objects)
            summary.print_(sum1)'''

            #objgraph.show_growth()
            if fingersGoingBrrr:
                peu_window.FindElement("fgb").Update("Make fingers\ngo brrrrr")
                fingersGoingBrrr = False
            elif not fingersGoingBrrr:
                peu_window.FindElement("fgb").Update("Make fingers\nstop brrring")
                fingersGoingBrrr = True
                brrThread()



def oneGrip(gripID):
    global bThread

    #while bThread.mode == "editing":
    #    nullVar = 0 
    #    pass
    
    gripList = gripID.split(".")
    for i in gripList:
        
        bThread.sendCommandToHand(i,timeout=0.35)
        
    #bThread.sendCommandToHand("m",timestall=3,timeout=0.3)
    #while bThread.mode == "not editing":
    #    nullVar = 0 
    #    pass

    iq = ["Index","Middle", "Ring","Pinky","Flexor","Rotator"]
    layoutOneGrip = [
        [sg.Radio(i,"RADIO1", enable_events=True, key='F' + str(iq.index(i))) for i in iq[0:3]],
        [sg.Radio(i, "RADIO1",enable_events=True, key='F' + str(iq.index(i))) for i in iq[3:]],
        #[sg.Radio("pressMe","RADIO1",enable_events=True, key="blah",default=True)],
        [sg.Text("   ")],
        [sg.Text("   ")],
        [sg.Text("Adjust finger anlge measure (degrees)",font=("Helvetica", 16 ))],
        [
            sg.Text("0 <",font=("Helvetica", 16 )),
            sg.Input(0, size=(5 , 1),font=("Helvetica", 20 ), key="angleVal", enable_events=True),
            sg.Text("< 100",font=("Helvetica", 16 ))
            ],
        [
            sg.Button("-n",size=(2, 1), font=("Helvetica", 14 )),
            sg.Text("n=", size=(2,1)) , sg.Input(3,size=(4, 1), key ="nVar", font=("Helvetica", 16 ) ),
            sg.Button("+n",size=(2, 1),font=("Helvetica", 14 ))
            ],
        [sg.Button("Set Angle",key="setA",size=(6, 1),font=("Helvetica", 14 ))],
        [sg.Text("                                    ")],
        [sg.Text("Finger Priority: ",font=("Helvetica", 16 ) ), sg.Input(0, size=(3 , 1),font=("Helvetica", 16), key="priorityVal", enable_events=True), sg.Button("Set Priority",key="setP",size=(6, 1),font=("Helvetica", 14 ))],
        [sg.Text("‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾")],
        [sg.Button("Save & Exit", key = "sne",size=(6, 1),font=("Helvetica", 14 )),sg.Button("Exit w/o Saving", key = "exwos",size=(15, 1),font=("Helvetica", 14 )) ]

    ]
    
    oneGrip_window = sg.Window("Select a grip",layoutOneGrip , element_justification='c', finalize=True)
    bThread.win = oneGrip_window
    firstTime= True
    choice = None
    while True:
        
        event, values = oneGrip_window.read()
        if firstTime:
            bThread.sendCommandToHand("mf0")
            bThread.sendCommandToHand("mr")
            bThread.sendCommandToHand("mR")
            firstTime = False 
        #print(event)
        if event == "Exit" or event == sg.WIN_CLOSED:
            bThread.sendCommandToHand("me",timestall=0.25)
            break
        if event.startswith("F"):
            #if not (bThread.mode == "editing"):
            #    bThread.sendCommandToHand("m",timeout=0.3)
            #    bThread.sendCommandToHand("mf0")
            #    print("sent M")
            #bThread.sendCommandToHand("mf" + event[-1])
            #bThread.sendCommandToHand("mf" + str( int(event[-1]) +1 %6),timeout=0.4)
            bThread.sendCommandToHand("mf" + event[-1])
            bThread.sendCommandToHand("mr")
            bThread.sendCommandToHand("mR")
        if event == "+n" : 
            angl = float(values["angleVal"]) + float(values["nVar"])
            bThread.sendCommandToHand("mq" + str(angl))
            oneGrip_window.Element("angleVal").Update(value=angl)
        if event == "-n" : 
            angl = float(values["angleVal"]) - float(values["nVar"])
            bThread.sendCommandToHand("mq" + str(angl))
            oneGrip_window.Element("angleVal").Update(value=angl)
        if event == "sne":
            bThread.sendCommandToHand("ms")
            bThread.sendCommandToHand("me")
            oneGrip_window.Close()
            break
        if event == "p=":
            print(values[event])
            oneGrip_window.FindElement("priorityVal").Update(value=values[event])
            
        if event == "q[":
            oneGrip_window.FindElement("angleVal").Update(value=values[event])
        if event == "setP":
            bThread.sendCommandToHand("mp" + values["priorityVal"])
        if event == "setA":
            bThread.sendCommandToHand("mq" + values["angleVal"])
        if event =="exwos":
            bThread.sendCommandToHand("me")
            oneGrip_window.Close()
            break

            





def gripCtl():
    global bThread
    grips = [
        ["Power\nClosed|G1þ", "Power\nOpen|G1þ.G0þ",     "Key\nClosed|G2þ", "Key\nOpen|G2þ.G0þ" ],
        ["Pinch\nClosed|G3þ", "Pinch\nOpen|G3þ.G0þ",     "Chuck\nClosed|G4þ", "Chuck\nOpen|G4þ.G0þ" ],
        ["RockNRoll\nClosed|G5þ", "RockNRoll\nOpen|G5þ.G0þ",     "Point\nClosed|G9þ", "Point\nOpen|G9þ.G0þ" ],
        ["Rude\nClosed|GAþ", "Rude\nOpen|GAþ.G0þ",     "Relax\nClosed|GCþ", "Relax\nOpen|GCþ.G0þ" ],
        ["Chuck OK\nClosed|GFþ", "Chuck OK\nOpen|GFþ.G0þ",     "Custom\nClosed|GVþ", "Custom\nOpen|GVþ.G0þ" ],
        ]
    layoutGripCtl = [
        [sg.Button(grip.split("|")[0],size=(9,3), key=grip.split("|")[1],font=("Helvetica", 16) )for grip in row] for row in grips
    ]

    gripCtl_window = sg.Window("Select a grip",layoutGripCtl , element_justification='c')

    choice = None
    while True:
        event, values = gripCtl_window.read()
        #print(event)
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        if event.startswith("G"):
            gripCtl_window.Disappear()
            oneGrip(event)
            gripCtl_window.Reappear()
    gripCtl_window.close()

def triggerFrame(win):
   
    global isFsrPlotting
    while isFsrPlotting:
        win.write_event_value('-THREAD-', 'done.')
        time.sleep(1/24)
    '''
    if False:
        time.sleep(1/24) '''




def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg



def fsrPlot():
    layoutFSR= [
        [sg.Canvas(size=(500,500), key='canvas')],
        [sg.Button("Make fingers\ngo brrrrr", key="fgb")]
    ]
    fsr_window =sg.Window("FSR Plotting",layoutFSR,finalize=True)
    global fingersGoingBrrr
    global bThread
    global isFsrPlotting
    global fsrQ
    isFsrPlotting = True
    bThread.win = fsr_window
    bThread.sendCommandToHand("P4")
    bThread.ts = time.time()
    animThread = threading.Thread(target=triggerFrame, args=(fsr_window,))
    animThread.start()


    canvas_elem = fsr_window['canvas']
    canvas = canvas_elem.TKCanvas
    # draw the intitial scatter plot
    fig, ax = plt.subplots()
    ax.set_ylim([0,4000])
    #ax.grid(True)
    fig_agg = draw_figure(canvas, fig)
    while True:
        event, values = fsr_window.read()
      
        if event == "Exit" or event == sg.WIN_CLOSED:
            isFsrPlotting = False
            bThread.sendCommandToHand("P1")
            try:
                fig_agg.clear()
                print("yay")
            except Exception as e:
                print(e)
            del animThread
            fsr_window.close()
            del fsr_window
            
            del fig_agg
            
            gc.collect()
            break
            #exit(0)
            break
        if event == "fgb":
            '''all_objects = muppy.get_objects()
            sum1 = summary.summarize(all_objects)
            summary.print_(sum1)'''

            #objgraph.show_growth()
            if fingersGoingBrrr:
                fsr_window.FindElement("fgb").Update("Make fingers\ngo brrrrr")
                fingersGoingBrrr = False
            elif not fingersGoingBrrr:
                fsr_window.FindElement("fgb").Update("Make fingers\nstop brrring")
                fingersGoingBrrr = True

        if event == "-THREAD-":
            #cquisition: ', values[event])
            #time.sleep(1)
            try:
                if isFsrPlotting:
                    ax.cla()
                    ax.set_ylim([0,4000])
                    #ax.grid(True)
                    eee  = fsrQ.get()
                    ax.plot(eee[0],eee[1])
                    
                    fig_agg.draw()
            except Exception as e:
                print(e)
                
def fingerSelect(): 
    layountFingerSelect = [
        [
            sg.Button("Index", key="fp.0", size = (9,3), font=("Helvetica", 16)),sg.Button("Middle", key="fp.1",size = (9,3),font=("Helvetica", 16))
        ],
        [
            sg.Button("Ring", key="fp.2",size = (9,3),font=("Helvetica", 16)),sg.Button("Pinky", key="fp.3",size = (9,3),font=("Helvetica", 16))
        ],
        [
            sg.Button("Thumb", key="fp.4",size = (9,3),font=("Helvetica", 16))
        ]
    ]
    fingerSelectWindow= sg.Window("Select Finger",layountFingerSelect,finalize=True,element_justification='c')
    global bThread
    while True:
        event, values = fingerSelectWindow.read()
        print(event)
        if event == "Exit" or event == sg.WIN_CLOSED:
            fingerSelectWindow.close()
            break
        if event.startswith("fp."):
            fingerSelectWindow.close()
            bThread.fsr_finger = int(event.split(".")[-1])
            fsrPlot()
            







def connectToDevice():
    layoutCon =[
        [sg.Text("Select Device to Connect to")],
        [sg.Listbox(values=[], key='fac', size=(60, 20))],
        [sg.Button("Connect", key="conbtn"),sg.Button("Refresh", key="refr")]
    ]
    conn_window = sg.Window("Connect to a device", layoutCon, finalize=True)
    global bThread
    bThread.searchForDevices(conn_window)
    while True:
        event, values = conn_window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            conn_window.close()
            exit(0)
            break
        if event == "conbtn":
            print(values['fac'][0])
            bThread.connectToDevice(bThread.devs[values["fac"][0]])
            conn_window.close()
            break
            
        if event == "refr":
            bThread.searchForDevices(conn_window)
        if event == "thrd":
            conn_window.FindElement('fac').Update(values=values[event])
            print(values[event])

def mainMenu():
    global bThread
    layoutMain = [
       [sg.Button("Hand Control", key="handCTL", size=(30,3), font=("Helvetica", 36))],
       [sg.Button("FSR Plotting", key="fsrPlot", size=(30,3),font=("Helvetica", 36))],
       [sg.Button("PEU Plotting", key="peuPlot", size=(30,3),font=("Helvetica", 36))]
    ]
    window = sg.Window("Main Window", layoutMain)
    while True:
        event, values = window.read()
        #all_objects = muppy.get_objects()
        #sum1 = summary.summarize(all_objects)
        #summary.print_(sum1)

        #objgraph.show_growth()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break
        if event == "handCTL":
            window.Disappear()
            gripCtl()
            window.Reappear()
        if event =="fsrPlot":
            window.Disappear()
            fingerSelect()
            #fsrPlot()
            window.Reappear()
        if event == "peuPlot":
            window.Disappear()
            peuPlot()
            window.Disappear()

            
        
        
    window.close()

bThread = BT_ThreadAsync()
connectToDevice()
mainMenu()
"""
dsfasdfasdjklkosie

"""

