GBNWindowMax = 5 #GBN窗口大小，意味最多等待1000个未确认的包
senderTimeoutValue = 1.0 #下载时发送端等待超时为1.0s
TransferSenderPacketDataSize = 50 #从文件中读取的数据的大小，发送包中数据的大小。
blockWindow = 1 #阻塞窗口初始值
ssthresh = 10 #拥塞避免值
FileReceivePackMax = 1024 #客户端接受数据包的长度最大为1024bytes
FileReceivePackNumMax = 50 #最多能够接受50个这样的数据包