#!/usr/bin/env python
import sys, socket, time, threading
import struct
import selectors
import lib.ConnTool as ConnTool
sel = selectors.DefaultSelector()




class Frpc():
    def __init__(self, serverhost,serverport, targethost,targetport):
        self.targethost=targethost
        self.targetport=targetport
        self.serverhost=serverhost
        self.serverport=serverport
        self.server_fd = socket.create_connection((self.serverhost,self.serverport))
        self.server_fd.sendall(struct.pack('i', 1))  # 启动时 首次发送心跳包 1
        self.server_fd.setblocking(False)
        sel.register(self.server_fd,selectors.EVENT_READ,self.handle_controller_data)

        self.workConnPool = []
        threading.Thread(target=self.maitainConPool).start()
        threading.Thread(target=self.heartbeat).start()

    def heartbeat(self):
        while True:
            if self.server_fd is not None:
                self.server_fd.send(struct.pack('i', 1))
            time.sleep(9)

    # 提前把 workConn和targetConn连接起来，需要的时候直接用workConn targetConn不需要缓存
    def maitainConPool(self):
        print("启动tcp连接池")
        pool_size = 0
        while True:
            if len(self.workConnPool)<pool_size:
                workConn = socket.create_connection((self.serverhost,self.serverport))
                targetConn = socket.create_connection((self.targethost, self.targetport))
                ConnTool.join(targetConn,workConn)
                self.workConnPool.append(workConn)


    def handle_controller_data(self,server_fd, mask):
        try:
            data= server_fd.recv(4)  # data 长度
            if data:
                cmd = struct.unpack('i',data)[0]
                print('cmd:',cmd)
                if cmd ==2:  # 要求frpc建立的工作tcp
                    print('收到frps控制指令')
                    # 直接从池子里获取
                    if len(self.workConnPool)>0:
                        workConn = self.workConnPool.pop()
                    else:
                        targetConn = socket.create_connection((self.targethost, self.targetport))
                        workConn = socket.create_connection((self.serverhost,self.serverport))
                        ConnTool.join(targetConn,workConn)
                    workConn.sendall(struct.pack('i',2)) # 1 心跳包
                    print("建立工作tcp")
        except IOError as err:  # 非阻塞模式下调用 阻塞操作recv 如果没有数据会抛出异常
            # sel.unregister(conn)
            # conn.close()
            # print(err)
            pass

    def run(self):
        while True:
            events = sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)
        print("frpc started!")


if __name__ == '__main__':
    print('Starting frpc...')
    try:
        remothost = sys.argv[1]
        targethost = sys.argv[3]
        remoteport = int(sys.argv[2])
        targetport = int(sys.argv[4])
    except (ValueError, IndexError):
        print('Usage: %s remothost [remoteport] targethost [targetport]' % sys.argv[0])
        sys.exit(1)

    sys.stdout = open('forwaring.log', 'w')
    Frpc(remothost,remoteport, targethost,targetport).run()
    print('success started! remote is  %s:%d \t target is %s:%d' % (remothost,remoteport, targethost,targetport))
    # Frpc('192.168.1.101',7000, 'localhost',3389).run()
