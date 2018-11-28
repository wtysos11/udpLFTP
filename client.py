import socket,random,json
from packetHead import packetHead,generateBitFromDict 

FileReceivePackMax = 1024 #客户端接受数据包的长度最大为1024bytes
FileReceivePackNumMax = 50 #最多能够接受50个这样的数据包

s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind(('127.0.0.1',9990))
jsonOptions = bytes(json.dumps({'filename':"test.txt","operation":"download"}),encoding='utf-8')
s.sendto(generateBitFromDict({"optLength":len(jsonOptions),"Options":jsonOptions,"RecvWindow":FileReceivePackNumMax*FileReceivePackMax}),('127.0.0.1',9999))
expectedSeqValue = 1
'''
GBN接受方逻辑
不断收包
    如果收到的包符合expectedSeqValue，输出，并expectedSeqValue += 1
返回ACK expectedSeqValue
'''
while True:
    data,addr = s.recvfrom(FileReceivePackMax)
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
        s.sendto(generateBitFromDict({"ACKvalue":expectedSeqValue,"ACK":b'1',"RecvWindow":FileReceivePackMax*FileReceivePackNumMax}),('127.0.0.1',int(addr[1])-1))
        expectedSeqValue += 1
    else:#收到了不对的包
        #print("Wrong data.",expectedSeqValue)
        s.sendto(generateBitFromDict({"ACKvalue":0,"ACK":b'1',"RecvWindow":FileReceivePackMax*FileReceivePackNumMax}),('127.0.0.1',int(addr[1])-1))
#s.sendto(generateBitFromDict({"FIN":b'1'}),('127.0.0.1',9999))