import socket,queue,threading

def receiver(port,q):
    receiverSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    receiverSocket.bind(('127.0.0.1',port))
    while True:
        data,addr = receiverSocket.recvfrom(1024)
        if addr[0] == '127.0.0.1' and addr[1] == port+1:
            print(data)
            print("Receiver receive end signal.")
            
            break
        print("receiver receive",data)
        print(addr)
        q.put(data)

    receiverSocket.close()
    print("receiver close")

def sender(port,q,fileName,addr):
    senderSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    senderSocket.bind(('127.0.0.1',port))
    f = open(filename,"rb")
    while True:
        data = f.read(50)
        print("sender read",data)
        if data == b'':
            print("File read end.")
            senderSocket.sendto(b'file end',('127.0.0.1',port-1))
            senderSocket.sendto(b'eof',addr)
            break
        
        senderSocket.sendto(data,addr)
        ack = q.get()
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
    filename = data.decode("utf-8")
    transferQueue = queue.Queue()
    rec_thread = threading.Thread(target = receiver,args = (appPortNum,transferQueue,))
    send_thread = threading.Thread(target = sender,args = (appPortNum+1,transferQueue,filename,addr,))
    rec_thread.start()
    send_thread.start()
    print("Thread start")

s.close()