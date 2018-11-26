import socket,sys

myport = 10000
mainport = 9999

if __name__ == '__main__':
    if len(sys.argv)>3:
        operation = sys.argv[1]
        hostaddr = sys.argv[2]
        filename = sys.argv[3]
        s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.bind(('localhost',myport))
        if operation == "lget":
            s.sendto(b'download',(hostaddr,mainport))
        elif operation == 'lsend':
            s.sendto(b'update',(hostaddr,mainport))
        else:
            raise Exception("Only support operation:lget/lsend")
        while True:
            data,addr = s.recvfrom(1024) #接受是阻塞的
            portNumber = data.decode('utf-8')
            if portNumber < 10000:
                

    else:
        raise Exception("Please enter: LFTP operation hostaddr filename.")
    
    mainport = 9999
s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.sendto(b'Hello world',('localhost',9999))