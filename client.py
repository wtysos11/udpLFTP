import socket,random
from packetHead import packetHead,generateBitFromDict 

clientReceivePackMax = 1024 #客户端接受数据包的长度最大为1024bytes

s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind(('127.0.0.1',9990))
s.sendto(generateBitFromDict({"optLength":8,"Options":b"test.txt"}),('127.0.0.1',9999))
expectedSeqValue = 1
'''
GBN接受方逻辑
不断收包
    如果收到的包符合expectedSeqValue，输出，并expectedSeqValue += 1
返回ACK expectedSeqValue
'''
while True:
    data,addr = s.recvfrom(clientReceivePackMax)
    packet = packetHead(data)
    #print("receive ",packet.dict["Data"]," with seq",packet.dict["SEQvalue"])
    if random.random()>0.8:
        #print("Drop packet")
        continue

    if packet.dict["FIN"] == b'1':#如果收到FIN包，则退出
        print("receive eof, client over.")
        break
    elif packet.dict["SEQvalue"] == expectedSeqValue:
        print("Output data:",packet.dict["Data"])
        s.sendto(generateBitFromDict({"ACKvalue":expectedSeqValue,"ACK":b'1'}),('127.0.0.1',int(addr[1])-1))
        expectedSeqValue += 1
    else:#收到了不对的包
        #print("Wrong data.",expectedSeqValue)
        s.sendto(generateBitFromDict({"ACKvalue":0,"ACK":b'1'}),('127.0.0.1',int(addr[1])-1))
#s.sendto(generateBitFromDict({"FIN":b'1'}),('127.0.0.1',9999))