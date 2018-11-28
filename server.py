import socket,queue,threading,time,json
from packetHead import packetHead,generateBitFromDict

#经常使用的常量值
GBNWindowMax = 5 #GBN窗口大小，意味最多等待1000个未确认的包
senderTimeoutValue = 1.0 #下载时发送端等待超时为1.0s
TransferSenderPacketDataSize = 50 #从文件中读取的数据的大小，发送包中数据的大小。

blockWindow = 1 #阻塞窗口初始值
ssthresh = 10 #拥塞避免值

### GBN接收方逻辑
# queue类q用来传递ack的值
def TransferReceiver(port,q):
    receiverSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    receiverSocket.bind(('127.0.0.1',port))
    while True:
        data,addr = receiverSocket.recvfrom(1024)
        if addr[0] == '127.0.0.1' and addr[1] == port+1:
            print(data)
            print("Receiver receive end signal.")
            break

        packet = packetHead(data)
        print("receiver receive ack:",packet.dict["ACKvalue"])
        q.put(data)

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
def TransferSender(port,q,fileName,addr,cacheMax):
    global blockWindow,ssthresh
    print("Enter sender with filename",fileName)
    senderSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    senderSocket.bind(('127.0.0.1',port))
    f = open(filename,"rb")
    #待确认的包的数量nextseqnum - baseSEQ <= GBNWindowMax
    baseSEQ = 1
    nextseqnum = 1
    GBNtimer = 0
    GBNcache = {}
    sendValueable = True
    senderClose = False
    sendOver = False
    ClientBlock = False
    blockStatus = 1#1意味着处于指数增长；2意味着线性增长

    senderSendDataSize = 0 #记录当前已经发送的数据量，这个量不能超过对面缓存区的大小
    #拥塞控制相关：
    # 正常情况下，发送端收到ACK后双倍发送（拥塞窗口倍增）
    # 如果超时，拥塞窗口变为1，并开始线性增长。更新ssthresh = 当前拥塞窗口的一半
    # 如果收到3个ACK，拥塞窗口等于阈值ssthresh，然后开始线性增长
    #流控制相关：
    #如果客户端上传的数据包超过对面的缓存区，则说明对面缓存区已经满了。这时候，将会暂停发送和重传直到缓存区再次清空
    while not senderClose:
        while sendValueable:#如果可以读入数据

            data = f.read(TransferSenderPacketDataSize)
            print("sender read file with data: ",data)
            if data == b'':#文件读入完毕
                print("File read end.")
                sendValueable = False
                sendOver = True
            #缓存并发送
            if nextseqnum == baseSEQ:
                GBNtimer = time.time()
            GBNcache[nextseqnum] = generateBitFromDict({"SEQvalue":nextseqnum,"Data":data})
            senderSocket.sendto(GBNcache[nextseqnum],addr)
            print("Sender send",data)
            nextseqnum += 1
            senderSendDataSize = TransferSenderPacketDataSize * (nextseqnum - baseSEQ)
            if nextseqnum - baseSEQ >=GBNWindowMax or nextseqnum - baseSEQ >= blockWindow:
                sendValueable = False
                print("Up to limit ",nextseqnum - baseSEQ,GBNWindowMax,blockWindow)
            elif senderSendDataSize > cacheMax:
                sendValueable = False
                ClientBlock = True
                print("Client cache full.")

        #等待接收ACK
        receiveACK = False
        counter = 0
        while not receiveACK:
            try:
                receiveData = q.get(timeout = senderTimeoutValue)
                receivePacket = packetHead(receiveData)

                ack = receivePacket.dict["ACKvalue"]
                cacheMax = receivePacket.dict["RecvWindow"]

                if senderSendDataSize <= cacheMax:
                    ClientBlock = False
                else:
                    ClientBlock = True
                
                if ack >= baseSEQ:
                    print("update baseSEQ to ",ack+1," with nextseqnum",nextseqnum)
                    baseSEQ = ack+1
                    senderSendDataSize = (nextseqnum-baseSEQ)*senderSendDataSize#更新流控制未确定名单
                    receiveACK = True #收到ACK，脱离超时循环
                    GBNtimer = time.time()#更新计时器
                    if baseSEQ == nextseqnum:#前一阶段发送完毕
                        sendValueable = True
                        if blockStatus == 1:
                            blockWindow *= 2
                        else:
                            blockWindow += 1
                        #阻塞避免，如果达到阈值，则状态转换
                        if blockWindow > ssthresh and blockStatus == 1:
                            blockWindow = ssthresh
                            blockStatus = 2
                        if sendOver:
                            senderClose = True
                        break
                elif ack == 0:
                    counter += 1
                    if counter >=3:#收到三次重复的ACK
                        counter = 0
                        if blockWindow>ssthresh:
                            blockWindow = ssthresh
                        else:
                            ssthresh = blockWindow
                        blockStatus = 2
                        raise queue.Empty
                    continue


                currentTime = time.time()
                if currentTime - GBNtimer > senderTimeoutValue and not ClientBlock:
                    print("Time out and output from",baseSEQ)
                    GBNtimer = time.time()#更新计时器
                    for i in range(baseSEQ,nextseqnum):
                        senderSocket.sendto(GBNcache[i],addr)
                    blockStatus = 2
                    ssthresh = int(blockWindow)/2
                    blockWindow = 1
                elif currentTime - GBNtimer > senderTimeoutValue and ClientBlock:
                    GBNtimer = time.time()
                    senderSocket.sendto(generateBitFromDict({}),addr)
            except queue.Empty: #超时，发包
                if not ClientBlock:
                    print("Time out and output from",baseSEQ)
                    GBNtimer = time.time()#更新计时器
                    for i in range(baseSEQ,nextseqnum):
                        senderSocket.sendto(GBNcache[i],addr)
                    blockStatus = 2
                    ssthresh = int(blockWindow)/2
                    blockWindow = 1
                else:
                    GBNtimer = time.time()
                    senderSocket.sendto(generateBitFromDict({}),addr)
        print("sender receive ack")
    #关闭接受端与客户端
    senderSocket.sendto(generateBitFromDict({"optLength":3,"Options":b"eof","FIN":b'1'}),addr)
    receiveFIN = False
    counter = 0
    overCount = 0
    # 如果反复收到ACK = 0
    while not receiveFIN:
        try:
            ack = q.get(timeout = senderTimeoutValue)
            print("Sender try to close but receive unproper ack:",ack)
            if ack == nextseqnum or ack == 0:
                counter+=1
                if counter >= 3:
                    counter = 0
                    raise queue.Empty
        except queue.Empty:
            print("Sender resend FIN")
            overCount += 1
            if overCount > 3:
                break
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