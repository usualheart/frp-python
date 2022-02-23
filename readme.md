# frp-python

> frp 是一个专注于内网穿透的高性能的反向代理应用，支持 TCP、UDP、HTTP、HTTPS 等多种协议。可以将内网服务以安全、便捷的方式通过具有公网 IP 节点的中转暴露到公网。

frp-python是基于frp原理实现的轻量级python版frp，frp-python具有非常简洁的设计，在速度方面甚至优于frp。如果你愿意，只需稍加修改frpc的代码，甚至可以在esp-32上部署一个frpc客户端！

关于frp原理，可以参考[内网穿透工具frp核心架构原理分析](https://blog.csdn.net/usualheart/article/details/123032372)

### frp-python 使用方法示例

假设服务端ip是110.110.110.1，要穿透本机的远程桌面端口3389，则分别在服务端和本机如下启动：

**服务端**

```shell
frps.py 7000 8001
```

**客户端**

```
frpc.py 110.110.110.1 7000 localhost 3389
```

然后通过110.110.110.1:8001就可以远程访问本机了！