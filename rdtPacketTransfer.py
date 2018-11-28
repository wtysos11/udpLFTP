import queue,threading
from packetHead import packetHead,generateBitFromDict
import config

def rdt_listener(s,q,expectedACK):
    '''监听端口，检查是否有ACK，如果有，则放入队列中'''
    receivePacket = False
    while not receivePacket:
        data,addr = s.recvfrom(config.FileReceivePackMax)
        packet = packetHead(data)
        if packet.dict["ACKvalue"] == expectedACK:
            q.put(expectedACK)
            receivePacket = True


def rdt_send(s,addr,bitStream,expectedACK):
    '''
    目标：
    1.向特定端口发送可靠的信息
    实现：
    1.发送包之后，开一个线程等待，使用队列进行通信。
    2.如果接受超时，则重传。如果收到，则返回。
    3.如果超时超过一定次数，则认定出现问题，抛出异常。
    '''
    q = queue.Queue()
    listener_thread = threading.Thread(target=rdt_listener,args = (s,q,expectedACK,))
    listener_thread.start()
    s.sendto(bitStream,addr)
    ackGet = False
    counter = 1
    while not ackGet:
        try:
            ack = q.get(timeout = config.senderTimeoutValue)
            if ack == expectedACK:
                ackGet = True
        except queue.Empty:
            print("RDT time out.")
            counter += 1
            if counter > 5:
                s.sendto(generateBitFromDict({"ACK":b'1',"ACKvalue":expectedACK}),s.getsockname())
                #raise Exception("Network Error in rdt_send.")
                break
            s.sendto(bitStream,addr)

