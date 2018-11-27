import socket,queue,threading
from packetHead import packetHead,generateBitFromDict

senderTimeoutValue = 1.0 #下载时发送端等待超时为1.0s

# queue类q用来传递ack的值
def receiver(port,q):
    receiverSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    receiverSocket.bind(('127.0.0.1',port))
    while True:
        data,addr = receiverSocket.recvfrom(1024)
        if addr[0] == '127.0.0.1' and addr[1] == port+1:
            print(data)
            print("Receiver receive end signal.")
            break

        packet = packetHead(data)
        print("receiver receive",packet.dict["ACKvalue"])
        print(addr)
        q.put(packet.dict["ACKvalue"])

    receiverSocket.close()
    print("receiver close")

def sender(port,q,fileName,addr):
    senderSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    senderSocket.bind(('127.0.0.1',port))
    f = open(filename,"rb")
    SYNvalue = 1
    hopeACKvalue = 1
    while True:
        data = f.read(50)
        print("sender read",data)
        if data == b'':
            print("File read end.")
            senderSocket.sendto(generateBitFromDict({"optLength":3,"Options":b"end","FIN":b'1'}),('127.0.0.1',port-1))
            senderSocket.sendto(generateBitFromDict({"optLength":3,"Options":b"eof","FIN":b'1'}),addr)
            break
        
        senderSocket.sendto(generateBitFromDict({"SYNvalue":SYNvalue,"SYN":b'1',"Data":data}),addr)
        receiveCurrentACK = False
        while not receiveCurrentACK:
            try:
                ack = q.get(timeout = senderTimeoutValue)
                if ack == hopeACKvalue:
                    receiveCurrentACK = True
                    hopeACKvalue = int(not bool(hopeACKvalue))
                    SYNvalue = hopeACKvalue
                else: #收到了不正确的ACK
                    print("Receive wrong ack",ack," and hope for ack",hopeACKvalue)
                    senderSocket.sendto(generateBitFromDict({"SYNvalue":SYNvalue,"SYN":b'1',"Data":data}),addr)
            except queue.Empty: #超时，发包
                print("Time out")
                senderSocket.sendto(generateBitFromDict({"SYNvalue":SYNvalue,"SYN":b'1',"Data":data}),addr)
        print("sender receive ack")
    senderSocket.close()
    f.close()
    print("sender closes")


mainport = 9999
appPortNum = 10000
s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind(('127.0.0.1',mainport))
serverConnected = True
while serverConnected:
    data,addr = s.recvfrom(1024)
    print("Main thread receive data",data)
    packet = packetHead(data)
    filename = packet.dict["Options"].decode("utf-8")
    transferQueue = queue.Queue()
    rec_thread = threading.Thread(target = receiver,args = (appPortNum,transferQueue,))
    send_thread = threading.Thread(target = sender,args = (appPortNum+1,transferQueue,filename,addr,))
    appPortNum += 2
    rec_thread.start()
    send_thread.start()
    print("Thread start")

s.close()