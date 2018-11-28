import socket,queue,threading,time,json
from packetHead import packetHead,generateBitFromDict
from udpUtil import *


mainport = 9999
appPortNum = 10000
s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind(('127.0.0.1',mainport))
serverConnected = True
while serverConnected:
    data,addr = s.recvfrom(1024)
    print("Main thread receive data",data)
    packet = packetHead(data)
    if packet.dict["FIN"] == b'1':
        break
    
    jsonOptions = packet.dict["Options"].decode("utf-8")
    jsonOptions = json.loads(jsonOptions)
    filename = jsonOptions["filename"]
    operation = jsonOptions["operation"]
    cacheMax = packet.dict["RecvWindow"]
    print("Main thread receive filename: ",filename)
    transferQueue = queue.Queue()
    rec_thread = threading.Thread(target = TransferReceiver,args = (appPortNum,transferQueue,))
    send_thread = threading.Thread(target = TransferSender,args = (appPortNum+1,transferQueue,filename,addr,cacheMax,))
    appPortNum += 2
    rec_thread.start()
    send_thread.start()
    print("Thread start")

s.close()