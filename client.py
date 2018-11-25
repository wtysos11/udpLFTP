import socket

s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.sendto(b'Hello world',('localhost',9999))