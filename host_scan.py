#!/usr/bin/env python
# -*- conding:utf-8 -*-
import threading
import re,queue,requests,time

queues = queue.Queue()
info_queue = queue.Queue()
threadLock = threading.Lock()
requests.packages.urllib3.disable_warnings() #屏蔽ssl报错
threads_complete = True


class get_therad(threading.Thread):   #网络请求线程
    def __init__(self,url_ip,name):
        threading.Thread.__init__(self)
        self.url_ip = url_ip
        self.name = name

    def run(self):
        threadLock.acquire()
        print("开始线程：" + self.name)
        threadLock.release()
        while not self.url_ip.empty():
            url_ips = self.url_ip.get()
            for i in ['http://','https://']:
                url = i + url_ips[0]
                #print(url)
                headers = {
                    'host': '%s'%(url_ips[1]),
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
                    'Referer': 'http://www.baidu.com'
                }
                try:
                    response = requests.get(url=url, headers=headers,timeout=3)
                    response.encoding = 'utf-8'
                    threadLock.acquire()
                    re_handle(url,url_ips[1],response.text)
                    print(url)
                    threadLock.release()
                except:
                    threadLock.acquire()
                    print('访问url异常，url:'+url+'    host:'+url_ips[1])
                    threadLock.release()
        threadLock.acquire()
        print("退出线程：" + self.name)
        threadLock.release()

class handle_therad(threading.Thread):  #处理数据线程
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        info_list=[]
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
    with open('ip.txt','r') as f:
        with open('host.txt','r') as f1:
            for i in f1.readlines():
                i = i.strip('\n')
                ip_list.append(i)

        for host in f.readlines():
            host = host.strip('\n')
            for ip in ip_list:
                queues.put((host,ip))
    print('读取文件成功！')

def re_handle(url,host,data):    #网页返回内容处理
    try:
        title = re.search('<title>(.*)</title>',data).group(1)  # 获取标题
    except:
        title = u"获取标题失败"

    if len(data) > 0:
        info = (url,host,str(len(data)),title)
        print(info)
        info_queue.put(info)

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
