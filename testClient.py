from udpUtil import *
from rdtPacketTransfer import *
from packetHead import *

s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
#host = '123.207.228.157'
host = '127.0.0.1'
portNum = 9999
sAddr = (host,portNum)
s.bind(('',10000))#if add this, then it can't send to remote server
dataList = [b'He',b'el',b'lo']
for i in dataList:
    s.sendto(i,(host,portNum))
    data,addr = s.recvfrom(1024)
    print(data,addr)
