import socket,random,json,threading
from packetHead import packetHead,generateBitFromDict 
from udpUtil import *

s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind(('127.0.0.1',9990))
jsonOptions = bytes(json.dumps({'filename':"test.txt","operation":"download"}),encoding='utf-8')
s.sendto(generateBitFromDict({"optLength":len(jsonOptions),"Options":jsonOptions,"RecvWindow":FileReceivePackNumMax*FileReceivePackMax}),('127.0.0.1',9999))
receiveServerReceiverPort = False
while not receiveServerReceiverPort:
    data,addr = s.recvfrom(FileReceivePackMax)
    packet = packetHead(data)
    jsonOptions = json.loads(packet.dict["Options"].decode("utf-8"))
    if "serverReceiverPort" in jsonOptions:
        serverReceiverPort = jsonOptions["serverReceiverPort"]
        receiveServerReceiverPort = True

receiver_thread = threading.Thread(target = fileReceiver,args = (s,('127.0.0.1',serverReceiverPort),))
receiver_thread.start()
receiver_thread.join()
#接受s
