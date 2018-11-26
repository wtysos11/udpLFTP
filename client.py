import socket

s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind(('127.0.0.1',9990))
s.sendto(b'test.txt',('127.0.0.1',9999))
while True:
    data,addr = s.recvfrom(1024)
    print(data,addr)
    s.sendto(b'ack',('127.0.0.1',int(addr[1])-1))