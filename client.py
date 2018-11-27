import socket
from packetHead import packetHead,generateBitFromDict 

s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind(('127.0.0.1',9990))
s.sendto(generateBitFromDict({"optLength":8,"Options":b"test.txt"}),('127.0.0.1',9999))
while True:
    data,addr = s.recvfrom(1024)
    packet = packetHead(data)
    print(packet.dict["Data"],addr)
    if packet.dict["FIN"] == b'1':
        print("receive eof")
        break
    s.sendto(generateBitFromDict({"ACK":b'1'}),('127.0.0.1',int(addr[1])-1))