#!/usr/bin/env python
# -*- conding:utf-8 -*-
import threading
import re,queue,requests,time

queues = queue.Queue()
info_queue = queue.Queue()
threadLock = threading.Lock()
requests.packages.urllib3.disable_warnings() #屏蔽ssl报错
threads_complete = True
queues_size = 0


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
                url = i + url_ips[1]
                host = url_ips[0]
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
                    print('\n访问正常：url:'+url+'    host:'+host+'    进度:'+str(queues_size-queues.qsize()*2)+'/'+str(queues_size))
                    threadLock.release()
                except Exception as e:
                    threadLock.acquire()
                    #print(e)
                    print('\n访问url异常，url:'+url+'    host:'+host+'    进度:'+str(queues_size-queues.qsize()*2)+'/'+str(queues_size))
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

def read_file():#读取host.txt和ip.txt
    ip_list=[]
    with open('ip.txt', 'r') as f1:#把ip添加到ip_list中
        for i in f1.readlines():
            i = i.strip('\n')
            ip_list.append(i)
    with open('host.txt','r') as f:#匹配循环ip和host对应
        for host in f.readlines():
            host = host.strip('\n')
            for ip in ip_list:
                queues.put((host,ip))

    global queues_size
    queues_size =queues.qsize()*2
    print('读取文件成功！一共需要碰撞'+str(queues_size)+'次！')
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
            print(info, code)
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
    threads = []
    for i in range(num):
        thread = get_therad(queues,i)
        thread.start()
        threads.append(thread)

    handle_therads = handle_therad()
    handle_therads.start()

    for t in threads:
        t.join()
    print('=====结 束 匹 配=====')
    global threads_complete
    threads_complete = False
    handle_therads.join()



if __name__ == "__main__":
    read_file()
    print("=====开 始 匹 配=====")
    time.sleep(3)
    run_therad(20) #线程数量
    print( "已处理完成，匹配成功的保存在ok.txt！！！！！" )
