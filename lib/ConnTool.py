# -*- coding: utf-8 -*-
# tcp mapping 

import sys
import socket
import logging
import threading

# 接收数据缓存大小
PKT_BUFF_SIZE = 10240

logger = logging.getLogger("Proxy Logging")
formatter = logging.Formatter('%(name)-12s %(asctime)s %(levelname)-8s %(lineno)-4d %(message)s', '%Y %b %d %a %H:%M:%S',)

stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)

# 单向流数据传递
def tcp_mapping_worker(conn_receiver, conn_sender):
    logger.info("start ")
    while True:
        try:
            data = conn_receiver.recv(PKT_BUFF_SIZE)
        except Exception as e:
            logger.debug(e)
            logger.debug('Connection closed.')
            break

        if not data:
            logger.info('No more data is received.') # 正常情况下不会到这，一般是某个连接断了
            break

        try:
            conn_sender.sendall(data)
        except Exception:
            logger.error('Failed sending data.')
            break

        # logger.info('Mapping data > %s ' % repr(data))
        # logger.info('Mapping > %s -> %s > %d bytes.' % (conn_receiver.getpeername(), conn_sender.getpeername(), len(data)))

    conn_receiver.close()
    conn_sender.close()

    return


# 端口映射请求处理
def join(connA, connB):
    threading.Thread(target=tcp_mapping_worker, args=(connA, connB)).start()
    threading.Thread(target=tcp_mapping_worker, args=(connB, connA)).start()
    return

if __name__ == '__main__':
    # 测试
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('0.0.0.0', 8080))
    # sock.setblocking(False)
    sock.listen(100)
    conn1,addr1 =sock.accept()

    sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock2.bind(('0.0.0.0', 7000))
    sock2.listen(100)

    # 类似frpc
    server_conn = socket.create_connection(('localhost', 7000))

    conn2,addr2 =sock2.accept()
    join(conn1,conn2)

    target_conn = socket.create_connection(('192.168.1.101', 3389))
    join(server_conn,target_conn)
