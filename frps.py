#!/usr/bin/env python
import sys, socket, time, threading
import struct
import selectors
import lib.ConnTool as ConnTool

sel = selectors.DefaultSelector()
class Frps(threading.Thread):
    def __init__(self, port, targetport):
        threading.Thread.__init__(self)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('0.0.0.0', port))
        # 设置为非阻塞模式
        self.sock.setblocking(False)
        self.sock.listen(100)
        sel.register(self.sock,selectors.EVENT_READ,self.accept_connection)

        frpc_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        frpc_sock.bind(('0.0.0.0', targetport))
        frpc_sock.setblocking(False)
        frpc_sock.listen(100)
        sel.register(frpc_sock,selectors.EVENT_READ,self.accept_frp_connection)


        self.frpc_cmd_conn =None
        self.userConns = []


    def heartbeat(self):
        while True:
            if self.frpc_cmd_conn is not None:
                self.frpc_cmd_conn.send(struct.pack('i', 1))
            time.sleep(9)

    # 收到用户tcp 先不接收 向frpc发送指令 让其建立工作tcp
    def accept_connection(self,sock, mask):
        userConn, addr = self.sock.accept()
        userConn.setblocking(True)
        self.userConns.append(userConn)
        print('收到用户请求')
        if self.frpc_cmd_conn is None:
            # print(1)
            return
            # time.sleep(0.5)
        print(2)
        try:
            self.frpc_cmd_conn.send(struct.pack('i',2)) # 2建立新的tcp
        except IOError as err:  # 非阻塞模式下调用 阻塞操作recv 如果没有数据会抛出异常
            print(err)
            pass


    def accept_frp_connection(self,sock, mask):
        frpc_conn, addr = sock.accept()
        frpc_conn.setblocking(False)
        # 注册为可读套接字
        sel.register(frpc_conn, selectors.EVENT_READ, self.handle_controller_data)

    def handle_controller_data(self,frpc_conn, mask):
        # print('frpc',frpc_conn,mask,self.userConns)
        try:
            data = frpc_conn.recv(4)  # Should be ready
            if data:
                cmd = struct.unpack('i',data)[0]
                print("cmd:",cmd)
                if cmd ==2:  # 是建立的工作tcp
                    sel.unregister(frpc_conn) # 不再监听
                    userConn = self.userConns.pop() # 从队列中选一个用户线程来处理
                    frpc_conn.setblocking(True)
                    # print(userConn)
                    # print('cmd 2')
                    # userConn, addr  = self.sock.accept()
                    # self.frpc_conn.setblocking(True)
                    # print(userConn)
                    ConnTool.join(userConn,frpc_conn)
                elif cmd ==1 and self.frpc_cmd_conn!=frpc_conn: # 说明是首次收到1
                    self.frpc_cmd_conn = frpc_conn
                    threading.Thread(target=self.heartbeat).start()
        except IOError as err:  # 非阻塞模式下调用 阻塞操作recv 如果没有数据会抛出异常
            pass

    def run(self):
        while True:
            events = sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)


if __name__ == '__main__':
    try:
        frpsport = int(sys.argv[1])
        userport = int(sys.argv[2])
    except (ValueError, IndexError):
        print('Usage: %s frpsport userport' % sys.argv[0])
        sys.exit(1)

    print('Starting...')
    Frps(userport, frpsport).start()
    print('frps server listen at 0.0.0.0:%d ,user port is %d' % (frpsport,userport))
    # Frps(8080, 7000).start()
