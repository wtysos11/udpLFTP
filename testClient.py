from udpUtil import *
from rdtPacketTransfer import *
from packetHead import *

s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind(('127.0.0.1',10000))
for i in range(10):
    rdt_send(s,('127.0.0.1',9999),generateBitFromDict({"SEQvalue":i}),i)
    print(i)