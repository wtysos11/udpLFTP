
def int2Bit(value,length):
    return bytes(bin(value)[2:].zfill(length),encoding='utf-8')

def Hex2Bit(heximal):
    '''对于16进制bytes，转换为01bytes'''
    bit = b''
    for hex in heximal:
        bit += int2Bit(hex,8)
    return bit

def originBin2Hex(bStr):
    '''对于二进制01字符串，转换为16进制存储'''
    point = 0
    result = b''
    while point < len(bStr):
        hex1,hex2 = '',''
        if point+8 >= len(bStr):
            if point+4 >= len(bStr):
                hex1 = bStr[point:]
                while len(hex1) < 4:
                    hex1 +='0'
                hex2 = '0000'
            else:
                hex1 = bStr[point:point+4]
                hex2 = bStr[point+4:]
                while len(hex2) < 4:
                    hex2+='0'
        else:
            hex1 = bStr[point:point+4]
            hex2 = bStr[point+4:point+8]
        hex1 = hex(int(hex1,2))[2:]
        hex2 = hex(int(hex2,2))[2:]
        cache = bytes.fromhex(hex1+hex2)
        result += cache
        point += 8
    return result

def generateHead(mydict):
    '''接受一个字典，返回二进制流'''
    bitStream = b''
    if "SYNvalue" in mydict:
        bitStream += int2Bit(mydict["SYNvalue"],32)
    else:
        bitStream += int2Bit(0,32)
    
    if "ACKvalue" in mydict:
        bitStream += int2Bit(mydict["ACKvalue"],32)
    else:
        bitStream += int2Bit(0,32)

    if "RecvWindow" in mydict:
        bitStream += int2Bit(mydict["RecvWindow"],16)
    else:
        bitStream += int2Bit(0,16)
    
    if "FIN" in mydict:
        bitStream += mydict["FIN"]
    else:
        bitStream += b'0'
    
    if "SYN" in mydict:
        bitStream += mydict["SYN"]
    else:
        bitStream += b'0'    
    
    if "ACK" in mydict:
        bitStream += mydict["ACK"]
    else:
        bitStream += b'0'

    bitStream += b'00000'
    

    if "optLength" in mydict:
        bitStream += int2Bit(mydict["optLength"],8)
    else:
        bitStream += int2Bit(0,8)
    #前面有96个二进制字符，24个16进制字符
    bitStream = originBin2Hex(bitStream)

    if "Options" in mydict:
        bitStream += mydict["Options"]
    
    if "Data" in mydict:
        bitStream += mydict["Data"]

    return bitStream

class packetHead:
    def __init__(self,bitStream):
        '''接受一个压缩位流，返回包的各个信息'''
        bitStream = Hex2Bit(bitStream[:12])+bitStream[12:]
        self.dict = {}
        self.dict["SYNvalue"] = int(bitStream[0:32],2)
        self.dict["ACKvalue"] = int(bitStream[32:64],2)
        self.dict["RecvWindow"] = int(bitStream[64:80],2)
        self.dict["FIN"] = bytes(str(bitStream[80] - 48),encoding='utf-8')
        self.dict["SYN"] = bytes(str(bitStream[81] - 48),encoding='utf-8')
        self.dict["ACK"] = bytes(str(bitStream[82] - 48),encoding='utf-8')
        self.dict["optLength"] = int(bitStream[88:96],2)
        self.dict["Options"] = bitStream[96:96+self.dict["optLength"]]
        self.dict["Data"] = bitStream[96+self.dict["optLength"]:]


def DefaultPackWithOptionsStr(optStr):
    d = {}
    optStr = bytes(optStr,encoding='utf-8')
    d["optLength"] = len(optStr)
    d["Options"] = optStr
    return packetHead(generateHead(d))