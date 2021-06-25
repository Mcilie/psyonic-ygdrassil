import threading as t
import pexpect as p



def bleComm(name):
    process = p.spawn("python3 gattProcess.py {}".format(name) )
        