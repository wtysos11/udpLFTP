from udpUtil import *
from rdtPacketTransfer import *
from packetHead import *

s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
host = '123.207.228.157'
portNum = 9999
sAddr = (host,portNum)
s.bind(('',10000))#if add this, then it can't send to remote server
s.sendto(b'Hello',sAddr)
