import socket

s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
print("socket start to work on 9999 port on localhost")
s.bind(('localhost',9999))
print("Bind successful")

while True:
    data,addr = s.recvfrom(4096)
    print(data)
    print(addr)
    s.sendto(b'Hello,%s!'%data,addr)