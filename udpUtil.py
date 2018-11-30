import socket,queue,time,json,random,threading
from packetHead import packetHead,generateBitFromDict
from rdtPacketTransfer import rdt_send
from collections import deque
import config
#声明全局变量
config.GBNWindowMax = 100 #GBN窗口大小，意味最多等待100个未确认的包
config.senderTimeoutValue = 0.5 #下载时发送端等待超时的时间
config.TransferSenderPacketDataSize = 1400 #从文件中读取的数据的大小，发送包中数据的大小。考虑到链路层MTU为1500
config.blockWindow = 1 #阻塞窗口初始值
config.ssthresh = 10 #拥塞避免阈值
config.FileReceivePackMax = 2048 #客户端接受数据包的长度最大为1024bytes
config.FileReceivePackNumMax = 1000 #文件接受者最多能够接受500个这样的数据包
config.RcvBuffer = 1000 #文件接受者最多接受500个这样的数据包
#经常使用的常量值
GBNWindowMax = config.GBNWindowMax
senderTimeoutValue = config.senderTimeoutValue
TransferSenderPacketDataSize = config.TransferSenderPacketDataSize

blockWindow = config.blockWindow
ssthresh = config.ssthresh

### GBN接收方逻辑
# queue类q用来传递ack的值
def TransferReceiver(port,q,aimAddr,isClient):
    receiverSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    receiverSocket.bind(('',port))
    if isClient:
        rdt_send(receiverSocket,aimAddr,generateBitFromDict({"SEQvalue":0}),0)
        print("Server receive address and client get ack0 . Can transport now.")
        q.put(0)
    while True:
        data,addr = receiverSocket.recvfrom(1024)
        if addr[0] == '127.0.0.1' and addr[1] == port+1:
            print("Receiver receive end signal from local.")
            break

        packet = packetHead(data)
        #print("receiver receive ack:",packet.dict["ACKvalue"])
        q.put(data)

    receiverSocket.close()
    print("receiver close")


def TransferSender(port,q,fileName,addr,cacheMax,isClient):
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
    global blockWindow,ssthresh
    senderSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    senderSocket.bind(('',port))
    if isClient:
        ack = q.get(block = True)
        print("Client get ack from server. Addr transport success.")
    else:
        data,addr = senderSocket.recvfrom(FileReceivePackMax)
        senderSocket.sendto(generateBitFromDict({"ACKvalue":0,"ACK":b'1'}),addr)
        print("Server receive client receiver addr",addr)

    f = open(fileName,"rb")
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
    senderSendPacketNum = 0 #记录当前已经发送的数据量，这个量不能超过对面缓存区的大小

    loss_time = 0
    #拥塞控制相关：
    # 正常情况下，发送端收到ACK后双倍发送（拥塞窗口倍增）
    # 如果超时，拥塞窗口变为1，并开始线性增长。更新ssthresh = 当前拥塞窗口的一半
    # 如果收到3个ACK，拥塞窗口等于阈值ssthresh，然后开始线性增长
    #流控制相关：
    #如果客户端上传的数据包超过对面的缓存区，则说明对面缓存区已经满了。这时候，将会暂停发送和重传直到缓存区再次清空
    while not senderClose:
        while sendValueable:#如果可以读入数据

            data = f.read(TransferSenderPacketDataSize)
            if data == b'':#文件读入完毕
                print("File read end.")
                sendValueable = False
                sendOver = True
            #缓存并发送
            if nextseqnum == baseSEQ:
                GBNtimer = time.time()
            GBNcache[nextseqnum] = generateBitFromDict({"SEQvalue":nextseqnum,"Data":data})
            senderSocket.sendto(GBNcache[nextseqnum],addr)
            nextseqnum += 1
            senderSendPacketNum = nextseqnum - baseSEQ
            if nextseqnum - baseSEQ >=GBNWindowMax or nextseqnum - baseSEQ >= blockWindow:
                sendValueable = False
                #print("Up to limit ",nextseqnum - baseSEQ,GBNWindowMax,blockWindow)
            elif senderSendPacketNum > cacheMax:
                sendValueable = False
                ClientBlock = True
                print("待确认包的数量：",senderSendPacketNum,"最大缓存：",cacheMax)
                print("Client cache full.")

        #等待接收ACK
        previousACK = 0 #重复接受ACK计数器
        receiveACK = False
        counter = 0
        ForceTime = 0
        while not receiveACK:
            try:
                receiveData = q.get(timeout = senderTimeoutValue)
                receivePacket = packetHead(receiveData)

                ack = receivePacket.dict["ACKvalue"]
                cacheMax = receivePacket.dict["RecvWindow"]

                if senderSendPacketNum <= cacheMax:
                    ClientBlock = False
                else:
                    ClientBlock = True
                
                if ack >= baseSEQ:
                    baseSEQ = ack+1
                    senderSendPacketNum = nextseqnum-baseSEQ#更新流控制未确定名单
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
                elif ack == previousACK:
                    counter += 1
                    if counter >=3:#收到三次重复的ACK
                        print("Three times duplicated ACK",previousACK," ,resend now!")
                        counter = 0
                        if blockWindow>ssthresh:
                            blockWindow = ssthresh
                        else:
                            ssthresh = blockWindow
                        blockStatus = 2
                        raise queue.Empty
                    continue
                else:
                    previousACK = ack
                    counter = 1


                currentTime = time.time()
                if currentTime - GBNtimer > senderTimeoutValue and not ClientBlock:
                    loss_time += 1
                    print("Time out and output current sequence number",baseSEQ)
                    GBNtimer = time.time()#更新计时器
                    for i in range(baseSEQ,nextseqnum):
                        packet = packetHead(GBNcache[i])
                        #print("Check resend packet SEQ:",packet.dict["SEQvalue"])
                        senderSocket.sendto(GBNcache[i],addr)
                    blockStatus = 1
                    ssthresh = int(blockWindow/2)
                    if ssthresh<=0:
                        ssthresh = 1
                    blockWindow = 1
                elif currentTime - GBNtimer > senderTimeoutValue and ClientBlock:
                    GBNtimer = time.time()
                    senderSocket.sendto(generateBitFromDict({}),addr)#向目标发送空包以更新recvWindow
                    senderSendPacketNum = nextseqnum - baseSEQ
                    if senderSendPacketNum <= cacheMax:
                        ClientBlock = False
                    else:
                        ClientBlock = True
            except queue.Empty: #超时，发包
                if not ClientBlock:
                    loss_time += 1
                    print("Time out and output current sequence number",baseSEQ)
                    GBNtimer = time.time()#更新计时器
                    for i in range(baseSEQ,nextseqnum):
                        packet = packetHead(GBNcache[i])
                        #print("Check resend packet SEQ:",packet.dict["SEQvalue"])
                        senderSocket.sendto(GBNcache[i],addr)
                    blockStatus = 1
                    ssthresh = int(blockWindow/2)
                    if ssthresh<=0:
                        ssthresh = 1
                    blockWindow = 1
                else:
                    print("Update flow control value.")
                    GBNtimer = time.time()
                    senderSocket.sendto(generateBitFromDict({}),addr)
                    senderSendPacketNum = nextseqnum - baseSEQ
                    if senderSendPacketNum <= cacheMax:
                        ClientBlock = False
                    else:
                        ClientBlock = True
    #关闭接受端与客户端
    senderSocket.sendto(generateBitFromDict({"optLength":3,"Options":b"eof","FIN":b'1'}),addr)
    receiveFIN = False
    counter = 0
    overCount = 0
    # 如果反复收到ACK = 0
    while not receiveFIN:
        try:
            data = q.get(timeout = senderTimeoutValue)
            packet = packetHead(data)
            ack = packet.dict["ACKvalue"]
            print("Sender try to close but receive unproper ack:",ack)
            if ack == nextseqnum:
                receiveFIN = True
            elif ack == nextseqnum-1:
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
    print("sender closes,丢包率计算",loss_time/(nextseqnum-1))


#文件接收方
FileReceivePackMax = config.FileReceivePackMax
FileReceivePackNumMax = config.FileReceivePackNumMax
FileWriteInterval = 0.5#磁盘每1s进行一次写操作
RcvBuffer = config.RcvBuffer
fileWriterEnd = False
LastByteRcvd = 0
LastByteRead = 0

def fileWriter(filename,d,q):
    '''使用双端队列作为缓存，如果队列不为空，则取出数据包并输出到磁盘中'''
    global fileWriterEnd,LastByteRead
    with open(filename,"ab+") as f:
        while not fileWriterEnd:
            try:
                da = q.get(timeout = FileWriteInterval)
            except queue.Empty:
                while len(d)>0:
                    data = d.popleft()
                    packet = packetHead(data)
                    LastByteRead = packet.dict["SEQvalue"]
                    f.write(packet.dict["Data"])
                #print("fileWriter")


def fileReceiver(port,serverReceiverAddr,senderSenderAddr,filename,isClient):
    global fileWriterEnd,LastByteRead
    '''
    GBN接受方逻辑
    不断收包
        如果收到的包符合expectedSeqValue，输出，并expectedSeqValue += 1
    返回ACK expectedSeqValue
    '''
    s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    s.bind(('',port))
    if isClient:
        rdt_send(s,senderSenderAddr,generateBitFromDict({"SEQvalue":0}),0)
        print("Client file receiver successfully send addr.")
    else:
        data,serverReceiverAddr = s.recvfrom(FileReceivePackMax)
        s.sendto(generateBitFromDict({"ACKvalue":0,"ACK":b'1'}),serverReceiverAddr)
        print("Server file receiver successfully receive addr",serverReceiverAddr)

    d = deque()
    timeQueue = queue.Queue()#因为磁盘写入速度太快，导致文件写入线程空转。因此每隔一段时间向队列传入数据，使其运行。
    fileThread = threading.Thread(target=fileWriter,args=(filename,d,timeQueue,))
    fileThread.start()
    expectedSeqValue = 1
    LastByteRcvd = 0
    start_time = time.time()
    total_length = 0
    total_num = 0
    ac_num = 0
    local_cache = {}
    while True:
        data,addr = s.recvfrom(FileReceivePackMax)
        packet = packetHead(data)
        total_num += 1
        #随机丢包
        '''
        if random.random()>0.8:
            #print("Drop packet")
            continue
        '''
        recvWindowSize = RcvBuffer - (LastByteRcvd-LastByteRead)
        if recvWindowSize<0:
            print("Alert, recvwindowsize less than 0")
            continue

        if packet.dict["FIN"] == b'1':#如果收到FIN包，则退出
            print("receive eof, client over.")
            s.sendto(generateBitFromDict({"ACKvalue":expectedSeqValue,"ACK":b'1',"RecvWindow":recvWindowSize}),serverReceiverAddr)
            break
        elif packet.dict["SEQvalue"] == expectedSeqValue:
            #print("Receive packet with correct seq value:",expectedSeqValue)
            LastByteRcvd = packet.dict["SEQvalue"]
            d.append(data)
            total_length += len(packet.dict["Data"])
            ac_num +=1
            s.sendto(generateBitFromDict({"ACKvalue":expectedSeqValue,"ACK":b'1',"RecvWindow":recvWindowSize}),serverReceiverAddr)
            #print("Receive window now",RcvBuffer - (LastByteRcvd-LastByteRead),LastByteRcvd,LastByteRead)
            expectedSeqValue += 1
            while expectedSeqValue in local_cache:
                packet = local_cache[expectedSeqValue]
                LastByteRcvd = packet.dict["SEQvalue"]
                d.append(data)
                total_length += len(packet.dict["Data"])
                ac_num +=1
                s.sendto(generateBitFromDict({"ACKvalue":expectedSeqValue,"ACK":b'1',"RecvWindow":recvWindowSize}),serverReceiverAddr)
                #print("Receive window now",RcvBuffer - (LastByteRcvd-LastByteRead),LastByteRcvd,LastByteRead)
                expectedSeqValue += 1
        else:#收到了不对的包，则返回expectedSeqValue-1，表示在这之前的都收到了
            print("Expect ",expectedSeqValue," while receive",packet.dict["SEQvalue"]," send ACK ",expectedSeqValue-1,"to receiver ",serverReceiverAddr)
            if packet.dict["SEQvalue"] > expectedSeqValue and "SEQvalue" not in local_cache:
                local_cache[packet.dict["SEQvalue"]]=packet
            s.sendto(generateBitFromDict({"ACKvalue":expectedSeqValue-1,"ACK":b'1',"RecvWindow":recvWindowSize}),serverReceiverAddr)
    #s.sendto(generateBitFromDict({"FIN":b'1'}),('127.0.0.1',9999))#关闭服务器，调试用
    fileWriterEnd = True
    end_time = time.time()
    total_length/=1024
    total_length/=(end_time-start_time)
    print("Transfer speed",total_length,"KB/s")
    print("有效接收率",ac_num/total_num)