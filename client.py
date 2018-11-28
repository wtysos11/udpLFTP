import socket,random,json,threading
from packetHead import packetHead,generateBitFromDict 
from udpUtil import *

s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind(('127.0.0.1',9990))
jsonOptions = bytes(json.dumps({'filename':"test.txt","operation":"download"}),encoding='utf-8')
s.sendto(generateBitFromDict({"optLength":len(jsonOptions),"Options":jsonOptions,"RecvWindow":FileReceivePackNumMax*FileReceivePackMax}),('127.0.0.1',9999))

'''
GBN接受方逻辑
不断收包
    如果收到的包符合expectedSeqValue，输出，并expectedSeqValue += 1
返回ACK expectedSeqValue
'''
receiver_thread = threading.Thread(target = fileReceiver,args = (s,))
receiver_thread.start()
receiver_thread.join()
#接受s
