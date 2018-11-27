import socket
from packetHead import packetHead,generateBitFromDict 

s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.bind(('127.0.0.1',9990))
s.sendto(generateBitFromDict({"optLength":8,"Options":b"test.txt"}),('127.0.0.1',9999))
ackValue = 1
hopeSEQvalue = 1
drop = 0
while True:
    data,addr = s.recvfrom(1024)
    packet = packetHead(data)
    print(packet.dict["Data"],addr)
    drop = int(not bool(drop))
    if drop == 1:
        print("Drop packet")
        continue

    if packet.dict["FIN"] == b'1':
        print("receive eof, client over.")
        break
    elif packet.dict["SEQvalue"] != hopeSEQvalue:
        print("receive not receive hope SEQvalue",packet.dict["SEQvalue"])
        print("Hope for ",hopeSEQvalue)
        s.sendto(generateBitFromDict({"ACKvalue":int(not bool(ackValue)),"ACK":b'1'}),('127.0.0.1',int(addr[1])-1))
    else:
        s.sendto(generateBitFromDict({"ACKvalue":ackValue,"ACK":b'1'}),('127.0.0.1',int(addr[1])-1))
        ackValue = int(not bool(ackValue))
        hopeSEQvalue = ackValue