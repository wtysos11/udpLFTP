import socket,queue,threading,time
from packetHead import packetHead,generateBitFromDict

#经常使用的常量值
GBNWindowMax = 1000 #GBN窗口大小，意味最多等待1000个未确认的包
senderTimeoutValue = 1.0 #下载时发送端等待超时为1.0s
senderPacketDataSize = 50 #从文件中读取的数据的大小，发送包中数据的大小。

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

'''
GBN发送方逻辑
尝试从文件中读取数据
    是否能够进行发送
        如果当前发送的包没有超过数量或是阻塞控制上限，则打包、缓存，并进行发送。
        如果已经满了，则置sendValuable = False
    发送完之后，检查是否接受到ACK并判断超时。
    对于接受到的ACK，baseSEQ进行更新。
    如果baseSEQ = nextseqnum，则解除置位,sendValuable = True
'''
def sender(port,q,fileName,addr):
    print("Enter sender with filename",fileName)
    senderSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    senderSocket.bind(('127.0.0.1',port))
    f = open(filename,"rb")
    #待确认的包的数量nextseqnum - baseSEQ <= GBNWindowMax
    baseSEQ = 0
    nextseqnum = 0
    GBNtimer = 0
    GBNcache = {}
    sendValueable = True
    senderClose = False
    while not senderClose:
        while sendValueable:#如果可以读入数据
            data = f.read(senderPacketDataSize)
            print("sender read file with data: ",data)
            data = f.read(senderPacketDataSize)
            if data == b'':#文件读入完毕
                print("File read end.")
                sendValueable = False
                senderClose = True
            #缓存并发送
            if nextseqnum == baseSEQ:
                GBNtimer = time.time()
            GBNcache[nextseqnum] = generateBitFromDict({"SEQvalue":nextseqnum,"Data":data})
            senderSocket.sendto(GBNcache[nextseqnum],addr)
            print("Sender send",data)
            nextseqnum += 1
            if nextseqnum - baseSEQ >=GBNWindowMax:
                sendValueable = False

        #等待接收ACK
        receiveACK = False
        while not receiveACK:
            try:
                ack = q.get(timeout = senderTimeoutValue)
                if ack >= baseSEQ:
                    baseSEQ = ack+1
                    receiveACK = True #收到ACK，脱离超时循环
                    GBNtimer = time.time()#更新计时器
                    if baseSEQ == nextseqnum:#前一阶段发送完毕
                        sendValueable = True
                        break
                    
                currentTime = time.time()
                if currentTime - GBNtimer > senderTimeoutValue:
                    GBNtimer = time.time()#更新计时器
                    for i in range(baseSEQ,nextseqnum):
                        senderSocket.sendto(GBNcache[i],addr)
            except queue.Empty: #超时，发包
                print("Time out")
                GBNtimer = time.time()#更新计时器
                for i in range(baseSEQ,nextseqnum):
                    senderSocket.sendto(GBNcache[i],addr)
        print("sender receive ack")
    #关闭接受端与客户端
    senderSocket.sendto(generateBitFromDict({"optLength":3,"Options":b"eof","FIN":b'1'}),addr)
    senderSocket.sendto(generateBitFromDict({"optLength":3,"Options":b"end","FIN":b'1'}),('127.0.0.1',port-1))
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
    print("Main thread receive filename: ",filename)
    transferQueue = queue.Queue()
    rec_thread = threading.Thread(target = receiver,args = (appPortNum,transferQueue,))
    send_thread = threading.Thread(target = sender,args = (appPortNum+1,transferQueue,filename,addr,))
    appPortNum += 2
    rec_thread.start()
    send_thread.start()
    print("Thread start")

s.close()