from multiprocessing import Queue
import os,socket,threading,time

def receive_server(q):
    base = 0
    while True:
        data = q.get()
        print(data)
        t = time.time()
        if t - base >10:
            base = t
            print(base)

def output_server(q,s):
    while True:
        data = s.recvfrom(1024)
        q.put(data)

s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind(('localhost',9999))
q = Queue()
out_thread = threading.Thread(target = output_server,args = (q,s,))
in_thread = threading.Thread(target = receive_server, args = (q,))
out_thread.start()
in_thread.start()