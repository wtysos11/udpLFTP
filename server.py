from multiprocessing import Queue
import os,socket,threading,time,queue,sys

def receive_server(q):
    base = 0
    while True:
        try:
            data = q.get(timeout = 2.0)
            print(data)
        except queue.Empty:
            print("Empty")
        t = time.time()
        if t - base >10:
            base = t
            print(base)

def output_server(q,s):
    base1 = 0
    while True:
        data = s.recvfrom(1024)
        q.put(data)
        t = time.time()
        if t - base1 > 10:
            print("output")
            base1 = t

def sender():
    '''负责向客户端发送数据'''

def receiver():
    '''负责接受客户端发来的数据'''


# 主线程，默认socket，监听默认地址。对于到来的请求，进行处理，并伺机发送给sender或receiver
mainport = 9999
socketPortBase = 10001
s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind(('localhost',mainport))
while True:
    data,addr = s.recvfrom(1024)
    #收到客户端发来的连接请求，发回将要给予的发送端口和接收端口.
    if data == b'update':
        s.sendto(bytes(str(socketPortBase),encoding='utf-8'),addr)
        socketPortBase += 2
    elif data == b'download':
        s.sendto(bytes(str(socketPortBase),encoding='utf-8'),addr)
        socketPortBase += 2
    else:
        s.sendto(b'Only support update or download',addr)
'''
q = Queue()
out_thread = threading.Thread(target = output_server,args = (q,s,))
in_thread = threading.Thread(target = receive_server, args = (q,))
out_thread.start()
in_thread.start()'''