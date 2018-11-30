import socket,queue,threading,time,json
from packetHead import packetHead,generateBitFromDict
from udpUtil import *
from rdtPacketTransfer import rdt_send
import config
FileReceivePackMax = config.FileReceivePackMax
FileReceivePackNumMax = config.FileReceivePackNumMax

mainport = 9999
appPortNum = 20000
s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind(('',mainport))
serverConnected = True
print("Server start to work on port",mainport)
while serverConnected:
    data,addr = s.recvfrom(1024)
    print("Main thread receive link request from",addr)
    packet = packetHead(data)
    print(packet.dict)
    if packet.dict["FIN"] == b'1':
        break
        
    elif packet.dict["SEQvalue"]>0:
        s.sendto(generateBitFromDict({"ACK":b'1',"ACKvalue":packet.dict["SEQvalue"]}),addr)
    
    jsonOptions = packet.dict["Options"].decode("utf-8")
    jsonOptions = json.loads(jsonOptions)
    filename = jsonOptions["filename"]
    operation = jsonOptions["operation"]
    cacheMax = packet.dict["RecvWindow"]
    receiverPort = jsonOptions["ReceiverPort"]#收到的端口是无效的
    print("Main thread receive filename: ",filename," with operation ",operation)
    backJson = bytes(json.dumps({"serverReceiverPort":appPortNum}),encoding = 'utf-8')
    rdt_send(s,addr,generateBitFromDict({"SEQvalue":2,"optLength":len(backJson),"Options":backJson,"RecvWindow":FileReceivePackNumMax}),2)
    s.sendto(generateBitFromDict({"SEQvalue":2,"optLength":len(backJson),"Options":backJson,"RecvWindow":FileReceivePackNumMax}),addr)
    if operation == "download":
        transferQueue = queue.Queue()
        rec_thread = threading.Thread(target = TransferReceiver,args = (appPortNum,transferQueue,(addr[0],receiverPort),False,))#isClient = False
        send_thread = threading.Thread(target = TransferSender,args = (appPortNum+1,transferQueue,filename,(addr[0],receiverPort),cacheMax,False,))
        appPortNum += 2
        rec_thread.start()
        send_thread.start()
    elif operation == "upload":
        print("Receive upload backup port:",receiverPort)    
        rec_thread = threading.Thread(target = fileReceiver , args = (appPortNum,(addr[0],receiverPort),(addr[0],receiverPort+1),filename,False,))#isClient = False
        rec_thread.start()
        appPortNum += 1
    print("Server working Thread start")

print("Server close.")
s.close()