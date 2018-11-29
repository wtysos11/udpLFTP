from udpUtil import *
from rdtPacketTransfer import *
from packetHead import *
import socket,queue,random

s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind(('',9999))
while True:
    data,addr = s.recvfrom(1024)
    print("Receive data")
    s.sendto(b'Hello',addr)