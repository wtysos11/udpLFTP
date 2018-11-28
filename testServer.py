from udpUtil import *
from rdtPacketTransfer import *
from packetHead import *
import socket,queue,random

s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind(('127.0.0.1',9999))
while True:
    data,addr = s.recvfrom(1024)
    packet = packetHead(data)
    if random.random()>0.5:
        print("Drop packet")
        continue
    print("Receive with seq value ",packet.dict["SEQvalue"])
    s.sendto(generateBitFromDict({"ACK":b'1',"ACKvalue":packet.dict["SEQvalue"]}),addr)