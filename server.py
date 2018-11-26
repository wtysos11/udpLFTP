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

if __name__ == '__main__':
    if len(sys.argv)>3:
        operation = sys.argv[1]
        hostaddr = sys.argv[2]
        filename = sys.argv[3]
s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind(('localhost',9999))
q = Queue()
out_thread = threading.Thread(target = output_server,args = (q,s,))
in_thread = threading.Thread(target = receive_server, args = (q,))
out_thread.start()
in_thread.start()