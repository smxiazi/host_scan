#!/usr/bin/env python
# -*- conding:utf-8 -*-
import threading
import re,queue,requests,time

queues = queue.Queue()
info_queue = queue.Queue()
threadLock = threading.Lock()
requests.packages.urllib3.disable_warnings() #屏蔽ssl报错
threads_complete = True
queues_size = 0 #存放总的数量
now_size = 0 #现在进度
switch = 1 #开关

port_list = [80,443,8080,8888,8000] #端口配置

class get_therad(threading.Thread):   #网络请求线程
    def __init__(self,url_ip,name):
        threading.Thread.__init__(self)
        self.url_ip = url_ip
        self.name = name

    def run(self):
        threadLock.acquire()
        print("线程" + self.name+'启动')
        threadLock.release()
        while not self.url_ip.empty():
            url_ips = self.url_ip.get()
            for i in ['http://','https://']:
                url = i + url_ips[1] +":"+ str(url_ips[2])
                host = url_ips[0]+":"+str(url_ips[2])
                port = url_ips[2]
                headers = {
                    'host': '%s'%(host),
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
                    'Referer': 'http://www.baidu.com',
                    'Connection': 'close'
                }
                try:
                    response = requests.get(url=url, headers=headers,timeout=3,verify=False,allow_redirects=False)#忽略ssl问题和禁止302、301跳转
                    response.encoding = 'utf-8'
                    threadLock.acquire()
                    re_handle(url,host,response.text,response.headers,response.status_code)#url、host、响应体、响应头、响应码
                    print('\n访问正常：url:'+url+'    host:'+host+'    port:'+str(port)+'    进度:'+str((now_size-queues.qsize())*2)+'/'+str(queues_size))
                    threadLock.release()
                except Exception as e:
                    threadLock.acquire()
                    #print(e)
                    print('\n访问url异常，url:'+url+'    host:'+host+'    port:'+str(port)+'    进度:'+str((now_size-queues.qsize())*2)+'/'+str(queues_size))
                    threadLock.release()
        threadLock.acquire()
        print("退出线程：" + self.name)
        threadLock.release()

class handle_therad(threading.Thread):  #独立线程 处理数据线程
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        info_list=[] #
        while threads_complete:
            info_complete =True
            try:
                if len(info_list) == 0:
                    info = info_queue.get(timeout=3)
                    info_list.append(info)
                    with open('ok.txt', 'a', encoding='utf-8') as f:
                        f.write(str(info) + '\n')
                else:
                    info = info_queue.get(timeout=3)

                    for i in info_list:
                        if info[0] == i[0] and info[2] == i[2] and info[3] == i[3]:
                            info_complete = False
                            break
                    if info_complete:
                        info_list.append(info)
                        with open('ok.txt','a',encoding='utf-8') as f:
                            f.write(str(info)+'\n')

            except Exception as e:
                print(e)

class read_file_data(threading.Thread):  #独立线程 加载数据，防止内存爆炸
    def __init__(self,num):
        threading.Thread.__init__(self)
        self.num = num

    def run(self):#读取host.txt和ip.txt
        ip_list=[]
        host_list=[]

        with open('ip.txt', 'r') as f1:#把ip添加到ip_list中
            for i in f1.readlines():
                i = i.strip('\n')
                ip_list.append(i)
        with open('host.txt','r') as f:#匹配循环ip和host对应
            for host in f.readlines():
                host = host.strip('\n')
                host_list.append(host)

        global queues_size
        queues_size = (len(ip_list) * len(host_list)) * 2 * len(port_list)
        print('读取文件成功！一共需要碰撞' + str(queues_size) + '次！')


        for host in host_list:
            for ip in ip_list:
                for i in port_list:
                    queues.put((host, ip,i))
                    global now_size
                    now_size += 1
            while True:
                if queues.qsize() > self.num*4:
                    global switch
                    switch = 0
                else:
                    break
        switch = 0


        #queues.get()=('www.baidu.com', '127.0.0.1')

def re_handle(url,host,data,head,code):    #网页返回内容处理
    try:
        title = re.search('<title>(.*)</title>',data).group(1)  # 获取标题
    except:
        title = u"获取标题失败"

    #只要响应码200、301、302的，其他的都不要
    if code == 302 or code == 301:
        if 'Location' in head:
            info = (url, host, str(len(data)), str(code) + ':' + head['Location'])
            print("\n",info, code)
            if '//cas.baidu.com' not in head['location'] and '//www.baidu.com' not in head['location'] and '//m.baidu.com' not in head['location']:
                info_queue.put(info)

    elif '百度一下' in title:
        info = (url, host, str(len(data)), title)
        print('无效数据' + str(info),code)

    elif code == 200:
        info = (url, host, str(len(data)), title)
        print(info,code)
        if len(data) > 20:  # 去除掉一些无用数据
            info_queue.put(info)

    else:
        info = (url, host, str(len(data)), title)
        print(info,code)

def run_therad(num):# 创建新线程

    read_file_data_therads = read_file_data(num)
    read_file_data_therads.start()

    while switch:
        continue

    threads = []
    for i in range(num):
        thread = get_therad(queues,i)
        thread.start()
        threads.append(thread)


    handle_therads = handle_therad()
    handle_therads.start()

    read_file_data_therads.join()
    for t in threads:
        t.join()
    print('=====结 束 匹 配=====')
    global threads_complete
    threads_complete = False
    handle_therads.join()




if __name__ == "__main__":
    print("=====开 始 匹 配=====")
    run_therad(20) #线程数量
    print( "已处理完成，匹配成功的保存在ok.txt！！！！！" )
