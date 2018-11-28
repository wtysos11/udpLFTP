import socket,random,json,threading,queue
from packetHead import packetHead,generateBitFromDict 
from udpUtil import *

filename = "test.txt"
destUrl = '127.0.0.1'
operation = "download"

appPortNum = 8000
s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind(('127.0.0.1',9990))
jsonOptions = bytes(json.dumps({'filename':filename,"operation":operation,"ReceiverPort":appPortNum}),encoding='utf-8')
s.sendto(generateBitFromDict({"optLength":len(jsonOptions),"Options":jsonOptions,"RecvWindow":FileReceivePackNumMax*FileReceivePackMax}),('127.0.0.1',9999))
receiveServerReceiverPort = False
while not receiveServerReceiverPort:
    data,addr = s.recvfrom(FileReceivePackMax)
    packet = packetHead(data)
    try:
        jsonOptions = json.loads(packet.dict["Options"].decode("utf-8"))
        if "serverReceiverPort" in jsonOptions:
            serverReceiverPort = jsonOptions["serverReceiverPort"]
            cacheMax = packet.dict["RecvWindow"]
            receiveServerReceiverPort = True
    except:#如果接受到空包的话，loads会抛出异常
        pass

if operation == "download":
    receiver_thread = threading.Thread(target = fileReceiver,args = (appPortNum,(destUrl,serverReceiverPort),))
    receiver_thread.start()
    receiver_thread.join()
elif operation == "upload":
    transferQueue = queue.Queue()
    rec_thread = threading.Thread(target = TransferReceiver,args = (appPortNum,transferQueue,))
    send_thread = threading.Thread(target = TransferSender,args = (appPortNum+1,transferQueue,filename,(destUrl,serverReceiverPort),cacheMax,))
    rec_thread.start()
    send_thread.start()
    rec_thread.join()
    send_thread.join()