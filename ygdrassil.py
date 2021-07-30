#!/usr/bin/python3

"""
To the poor soul that has to debug this shit after I'm gone,
Good luck
Rewrite this in rust if youre smart....
Literally anything but this cursed POS script
mcilie@icloud.com if you need me 
240 817 6154 if urgent

"""

#TODO i dont use like 40% of these imports
# IMPORTAnt, PACKING.PY IS NECESSARY
#import _thread
#from pympler import summary,muppy
#import objgraph
#import atexit
import asyncio
#import sys
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
import struct
import gc
#from guppy import hpy


"""
These are some global variables 
"""
isFsrPlotting = False #Global vars for the 2 diff plotting methods
isPeuPlotting = False
fingersGoingBrrr = False
UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E" #Some weird ID's for some bluetooth shit
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

UART_SAFE_SIZE = 20


"""
Below are 2 different Queue classes that are actually identical
Why did I do this? I initially thought there were gonna be two different data shapes...
Even so, I couldve made the queue array shape parametric, but oh well  ¯\_(ツ)_/¯
fsrQueue is for FSR plotting and so on and so forth
"""

class fsrQueue: 
    def __init__(self):
        self.tVar = [0 for i in range(35)]
        self.pVar = [[0 for k in range(6)] for l in range(35)]
    def add(self,timeStart,bytearr):
        self.tVar = self.tVar[1:] + [time.time()-timeStart]
        self.pVar = self.pVar[1:] + [bytearr]
    def get(self):
        return [self.tVar,self.pVar]

class peuQueue:
    def __init__(self):
        self.tVar = [0 for i in range(35)]
        self.pVar = [[0.0 for k in range(6)] for l in range(35)]
    def add(self,timeStart,bytearr):
        self.tVar = self.tVar[1:] + [time.time()-timeStart]
        self.pVar = self.pVar[1:] + [bytearr]
    def get(self):
        return [self.tVar,self.pVar]

# Oh yeah more global variables.
# I like these, they work        
peuQ = peuQueue()
fsrQ = fsrQueue()


"""
This, now this is Hell...
This class right here is the reason the app was rewritten 3 FUCKING TIMES in 6 FUCKING weeks.
Async programming in python is AIDS 
The only competent BLE library that had all the features we wanted works ONLY
with async, and trying to circumvent that makes problems with the GUI.
You cant just fire and forget commands like REAL async programming in JS
So i made this class (stolen from some SO post) that manages Async calls in a diff thread
Its meant to be initialized once as an object, return BLE devices, connect to one and store the client object
and then it lets you fire and forget commands (with delays if desired)

"""
class BT_ThreadAsync:
    def __init__(self):
        self.pool = ThreadPoolExecutor(max_workers=2) #dual core opmtimization
        #TODO , parametrize core optimization. This is supposed to run on an RPI (4 cores), so I should
        #probably make this 4 cores but ya know what, its my last day and Im terrified of breaking this
        self.loop = asyncio.get_event_loop()
        self.start_loop()
        self.devs = {} #List of devices
        self.c = None  # I **think** this is the client variable
        self.win = None #Window variable. GUI programming is weird. 
        '''
        Quick warranted explanation for the above variable: 
            self.win is a settable variable that lets you tell the object what window you want it to currently communicate with
            PySimple gui lets you send events to windows. I am under the current impression that this works and doesnt break the GUI
            So far it works. Previously I used this variable to directly modify the window (No bueno on Windows:(   ) 

        '''
        self.mode = "not editing" #useless probably
        self.ts = 0 #i think ts stands for 'time start', not sure tho
        self.buffCache = [] # unused?
        self.fsr_finger = 0  # Stores what finger is used by FSR plotting
        '''
        index, middle, ring, pinky, thumb
        each finger is 6 datapoints in one array. 

        0 is index thumb is 4
        arr = [1,2,3,4...30]
        indexSensors = arr[bThread.fsr_finger * 6 : ]
        '''
        

    def runAsyncCmd(self,cmd): # runs async command 
        asyncio.run_coroutine_threadsafe(cmd(),self.loop)

    def racWarg(self,cmd,arg): #RacWarg stands for Run A Command WIth Argument
        asyncio.run_coroutine_threadsafe(cmd(arg),self.loop)

    def racWargTime(self,cmd,arg,timev,times): #Run A Command with Arguments and Time delays 
        asyncio.run_coroutine_threadsafe(cmd(arg,timeout=timev,timestall=times),self.loop)

    def start_loop(self): 
        thr = threading.Thread(target=self.loop.run_forever)
        thr.daemon = True
        thr.start()


    '''
    Oh boy, this is the main callback that handles like *everything* relating to *recieving* bluetooth data
    This is where the Bitchiness of python async, specifically the bleak library, really materializes into tangibility.
    Unlike in JS where you can set a specific call back for each async call (usually), you cant do that here, hence the If statements 
    and need for global vars. 
    This call back needs to figrue out what its calling back from (to?)
    '''
    async def handle_rx(self, a, b):
        
        #print(b)
        global isFsrPlotting
        global isPeuPlotting
        global fsrQ
        global peuQ
        if isFsrPlotting: #fsr p
            #print(b)
            dta = unpack_8bit_into_12bit(copy_bytearray_to_np_uint16(b),30) #bit fuckery, it works. See BLE CLI document for details 
            findex  = self.fsr_finger
            fsrQ.add(self.ts,dta[findex*6:(findex*6)+6])
            del dta #may help with memory
            #TODO haha so turns out that one of my previous iterations of this had a MAJOR Memory leak problem (FSR Plotting drawing canvas over and over again)
            #You will find commented out memory optimizations.
            #Its my last day so do me a favor and do memory leak testing for this, ~sometime~ in the near future. Im sure its fine
            
            '''
            if len(self.buffCache) >3:

                
                fsrQ.add(self.ts, sum(self.buffCache)/4)
                self.buffCache= []
                self.buffCache.append(dta)
            else:
                self.buffCache.append(dta)'''
            #Aha so more peculiarities. IDK if its something to do with Python, Pysimplegui, Ble(ak), Matplotlib/pyplot
            #But for some reason there is occasional lag and stutter in the graphing
            #THis "buffer" feature was meant to buffer some datapoints and average them out or some bullshit like that
            #TODO Fix the fucking stutter and lag in graphing. I tried fuck all else but nothing works 

            #print(dta)
            #print(dta[:6])
            
            #global isFsrPlotting
            #while isFsrPlotting:
            #self.win.write_event_value('-THREAD-', 'done.')
            return 
        elif isPeuPlotting: 
            tee= [struct.unpack("f",b[i:i+4])[0] for i in [  #Data parsing fuckery for peu
                0,
                4,
                8,
                12,
                16,
                20

            ]]
            #print(tee)
            peuQ.add(self.ts, tee)

            
            return
        
        
        #global isFsrPlotting
        #global isPeuPlotting

        #Okay so past this point weve eliminated the possibility of handling plotting data,
        #now its just handling normal data. q[ i believe is for the angle value of some window
        #p= is priority value
        b =str(b)[2:-1] 
        if "q[" in b and ( not (isFsrPlotting or isPeuPlotting)):
            self.win.write_event_value("q[",float(b.replace("'",'').split("=")[-1]))
            #self.win.FindElement("angleVal").Update(value=float(b.split("=")[-1]))
        elif "p=" in b and ( not (isFsrPlotting or isPeuPlotting)):
            self.win.write_event_value("p=",int(b.replace("'",'').split("p=")[-1].split(",")[0])) #parsing fuckery 
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
        #await asyncio.sleep(0.1); 

        await client.start_notify(UART_TX_CHAR_UUID, self.handle_rx)  #REmember that weird ID var i mentioned? 
        self.c = client
    
    def connectToDevice(self,device):
        self.racWarg(self.connectToDevice_async,device) 
    
    async def sendCommandToHand_async(self,command ,timeout=0.25,timestall=0): 
        ''' 
        This is the function that sends commands to hand 
        
        '''
        await asyncio.sleep(timestall) #pause before
        byteData = bytearray(command, 'latin-1') #See commment below
        '''
        THIS!!!! 2 WEEKS. 2 FUCKING WEEKS BECAUSE PYTHON 3 got dropped on its head as a baby, 
        and cant handle UTF-8 like a real prorgamming language. Instead I had to encode to latin-1 to 
        get a character's REAL ascii value.
        '''

        print("About to Write " + command + "  " + str(time.time() % 60)) #debug 
        await self.c.write_gatt_char(UART_RX_CHAR_UUID, byteData, response=True)
        print("written " + command + "  " + str(time.time() % 60))#debug
        await asyncio.sleep(timeout)#pause after 

        #legacy code? I used to care if the hand was in edit mode, but idt its necessary anymore 
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

    #brr == something is moving
    #Brr like the sound a car or a machine of any sort makes when its operating
    global bThread
    global fingersGoingBrrr #Global var to see if peu finger movement is desired
    doneOneOnce = False #No idea what this was for 
    while fingersGoingBrrr:
        print("brring")
        bThread.sendCommandToHand("G1ë",timeout =0) #Close
        print("Sent G1b " + str(time.time() %60))

        #TODO This time might cause the PEU plotting to not work depending on the hand. Change as needed. 
        #James, yourwelcome, I shaved off 1 second off of the time i initially promised you
        time.sleep(1)
        bThread.sendCommandToHand("G0ë",timeout=0) #open
        print("Sent G0b " + str(time.time() %60))
        time.sleep(1)
    

        #Forget this code below
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
    #start the brrThread function 
    ttt = threading.Thread(target= brrThreadBackend,args=())
    ttt.start()

def triggerFramePeu(win):
    #loop that runs peu plotting at 7 fps
    #TODO should probably make fps a global/config var
    global isPeuPlotting
    while isPeuPlotting:
        win.write_event_value('-THREAD-', 'done.')
        time.sleep(1/7)

def peuPlot():
    #PEU window 
    #TODO Add some 'save plot data per finger to file' feature. Good luck
    layoutPEU= [
        [sg.Canvas(size=(500,500), key='canvas')],
        [sg.Button("Make fingers\ngo brrrrr", key="fgb")]
    ]
    peu_window =sg.Window("PEU Plotting",layoutPEU,finalize=True)
    global fingersGoingBrrr
    global isPeuPlotting
    isPeuPlotting = True
    global bThread
    bThread.win = peu_window
    bThread.sendCommandToHand("P6") #Start spitting out peu data 
    bThread.ts = time.time() #OOOOH i think this is for keeping track of x-axis (time)
    animThread = threading.Thread(target=triggerFramePeu, args=(peu_window,))
    animThread.start()


    canvas_elem = peu_window['canvas']
    canvas = canvas_elem.TKCanvas
    # draw the intitial scatter plot
    fig, ax = plt.subplots()
    ax.set_ylim([0,80])
    #ax.grid(True)
    fig_agg = draw_figure(canvas, fig)

    while True:
        
        event, values = peu_window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            isPeuPlotting = False
            fingersGoingBrrr = False
            bThread.sendCommandToHand("P1")
            

            #TODO idk why but this window sometimes closes and the original window doesnt open back up

            try:
                #fig_agg.clear()
                print("yay")
            except Exception as e:
                print(e)
            peu_window.close()
            print("done")
            break
            
        if event == "fgb":
            #FGB stands for fingers go brr 


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


        if event == "-THREAD-":
            #That thread event comms i mentioned earlier 
            try:
                if isPeuPlotting:
                    ax.cla()
                    ax.set_ylim([0,80])
                    eee = peuQ.get()
                    ax.plot(eee[0],eee[1])
                    #update plot 
                    fig_agg.draw()

            except Exception as e:
                print(e)



def oneGrip(gripID):
    #Window for one grip 
    global bThread

    #while bThread.mode == "editing":
    #    nullVar = 0 
    #    pass
    
    gripList = gripID.split(".")
    for i in gripList:
        #Either opens or closes the hand
        bThread.sendCommandToHand(i,timeout=0.35)
        
    #bThread.sendCommandToHand("m",timestall=3,timeout=0.3)
    #while bThread.mode == "not editing":
    #    nullVar = 0 
    #    pass

    iq = ["Index","Middle", "Ring","Pinky","Flexor","Rotator"]
    layoutOneGrip = [
        [sg.Radio(i,"RADIO1", enable_events=True, key='F' + str(iq.index(i))) for i in iq[0:3]], #List comps are sexy
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
        

        """
        EXPLANATION
        so for some reason, whenever youd select one finger  on the first iteration of this
        no matter how many times you pressed the increment buttons, it would not increase or decrease the finger angle in real time 
        This only happened for the first finger selection. If you selected another finger, real time changes would work again.
        I tried to fix this the reasonable way by just silently switching to an arbitrary finger, but NOOOO for some dumbfucking reason
        even that wouldnt work. So in the end, i literally simulated a finger selection. This is why when you first select a finger on this app
        it has a mini stroke and switches the numerical values on the window very quickly. Advise users of the app not to use the app too quickly

        """
        #TODO fix above issue  
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
        if event == "sne": #SNE stands for save n' exit 
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
        if event =="exwos": #Exit with out saving, my naming is inconsistent 
            bThread.sendCommandToHand("me")
            oneGrip_window.Close()
            break

            





def gripCtl():
    #Grip selection
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
    #Animate FSR at 7 fps 
    global isFsrPlotting
    while isFsrPlotting:
        win.write_event_value('-THREAD-', 'done.')
        time.sleep(1/7)
    '''
    if False:
        time.sleep(1/24) '''




def draw_figure(canvas, figure):
    #???? what this does but it is necessary 
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg



def fsrPlot():
    #fsr window 
    layoutFSR= [
        [sg.Canvas(size=(500,500), key='canvas')],
        [sg.Button("Make fingers\ngo brrrrr", key="fgb")] # Dont know why this is here. I think lucy or james accidentally told me to do this. 
    ]
    fsr_window =sg.Window("FSR Plotting",layoutFSR,finalize=True)
    global fingersGoingBrrr
    global bThread
    global isFsrPlotting
    global fsrQ
    isFsrPlotting = True
    bThread.win = fsr_window
    bThread.sendCommandToHand("P4") #start data
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
            bThread.sendCommandToHand("P1") # Stop data
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
    #finger seelection for FSR 
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
    #connect to device 
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
    #main thing 
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
        #BTW if anyone wants it, theres a 20 hiding somewhere in 210, i think its under the iMac.
        #I left this as an incentive to come back 
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

            window.Reappear()

            
        
        
    window.close()

bThread = BT_ThreadAsync()
connectToDevice()
mainMenu()
"""
Youve made it this far.
Aditya, thank you for working with me for 6 weeks. I hope I didnt completely make you lose your sanity
"""

