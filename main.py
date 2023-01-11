# import os
# import requests
# import re
# from bs4 import BeautifulSoup as BS
# from functools import reduce
# import schedule

# from email.mime.text import MIMEText
# from email.header import Header
# import smtplib

# import logging

# logger = logging.getLogger()
# logger.setLevel(logging.INFO)

# mail_host = os.environ['MAIL_HOST']
# mail_user = os.environ['USER']  # 此处填你的邮箱
# mail_girl = os.environ['TO']  # 另一个邮箱的邮箱
# mail_pass = os.environ['PASS']  # 邮箱密码
# name_girl = "刘喂喂"  # 名字
# mail_port = 465  # smtp端口号
# headers = {
#     'cookie': 'JSESSIONID=MR5Yj7ZR1hrNzDnQp3knNRhYYRnh4h5F2BkQYZJQBLGxcy8xy1Rj!569010957',
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
# }

# buildingID = os.environ['BUILDING_ID']
# url = f'http://124.95.133.164:7003/newbargain/download/findys/showPrice.jsp?buildingID=595784E1-2976-4971-8191-D875F50C1D89'
# room_list = []


# def sendMail():
#     smtpObj = smtplib.SMTP_SSL(mail_host, mail_port)
#     try:
#         smtpObj.login(mail_user, mail_pass)
#     except smtplib.SMTPException as e:
#         logger.info(e)
#     content = buildingInfo()
#     if content == "":
#         content += '\n数据无变化'
#     message = MIMEText(content, 'plain', 'utf-8')
#     message['From'] = mail_user
#     message['To'] = mail_girl
#     message['Subject'] = f'今日数据汇总 \n '
#     try:
#         smtpObj.sendmail(mail_user, [mail_girl], message.as_string())
#         logger.info("send email success")
#     except smtplib.SMTPException as e:
#         logger.info(e)
#         logger.info("Error: send email fail")
#         logger.info("无法发送邮件")
#     finally:
#         # 关闭服务器
#         smtpObj.quit()
#     logger.info("邮件发送成功")


# def buildingInfo():
#     print('进入方法')
#     change_room = ''
#     response = requests.get(url=url, headers=headers)
#     html_data = response.text
#     print('html_data:''html_data')
#     soup = BS(html_data, "lxml")
#     divs = soup.find_all(xxx=re.compile("可售"))

#     for div in divs:
#         td_x = div['xxx']
#         re_b = re.compile("<%s.*?>(.+?)<%s>" % ("/b", "br"), re.I | re.S)
#         # re_b = re.compile("</b.*?>(.+?)<br>", re.I | re.S)
#         # re_b = re.compile("(?<=<B>).*?(?=<br>)", re.I | re.S)
#         # ['房屋状态：', '房屋地址：', '房屋结构：', '房屋用途：', '建筑面积：', '户型：', '单价：', '总价：', '预售许可证号：']
#         room = re.findall(re_b, td_x)
#         room_json = {'room_number': re.findall('[(](.*?)[)]', room[1])[0],
#                      'area': room[4],
#                      'unit_price': room[5],
#                      'total_price': room[6]}
#         ret = reduce(lambda pre, cur: cur if cur['room_number'] == room_json['room_number'] else pre, room_list, None)
#         if ret:
#             if ret['unit_price'] != room_json['unit_price']:
#                 change_room += f'{ret["room_number"]}：原价为{ret["unit_price"]}调价位{room_json["unit_price"]}\n' \
#                                f'原总价{ret["total_price"]}调价位{room_json["total_price"]}\n'
#         else:
#             room_list.append(room_json)
#         return change_room


# if __name__ == '__main__':
#     print(buildingInfo())




# encoding:utf-8
import time
import struct
import socket
import select
 
 
def chesksum(data):
    n = len(data)
    m = n % 2
    sum = 0
    for i in range(0, n - m ,2):
        sum += (data[i]) + ((data[i+1]) << 8)#传入data以每两个字节（十六进制）通过ord转十进制，第一字节在低位，第二个字节在高位
    if m:
        sum += (data[-1])
    #将高于16位与低16位相加
    sum = (sum >> 16) + (sum & 0xffff)
    sum += (sum >> 16) #如果还有高于16位，将继续与低16位相加
    answer = ~sum & 0xffff
    #  主机字节序转网络字节序列（参考小端序转大端序）
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer
 
def request_ping(data_type,data_code,data_checksum,data_ID,data_Sequence,payload_body):
    #  把字节打包成二进制数据
    icmp_packet = struct.pack('>BBHHH32s',data_type,data_code,data_checksum,data_ID,data_Sequence,payload_body)
    icmp_chesksum = chesksum(icmp_packet)  #获取校验和
    #  把校验和传入，再次打包
    icmp_packet = struct.pack('>BBHHH32s',data_type,data_code,icmp_chesksum,data_ID,data_Sequence,payload_body)
    return icmp_packet
 
 
def raw_socket(dst_addr,icmp_packet):
    '''
       连接套接字,并将数据发送到套接字
    '''
    #实例化一个socket对象，ipv4，原套接字，分配协议端口
    rawsocket = socket.socket(socket.AF_INET,socket.SOCK_RAW,socket.getprotobyname("icmp"))
    #记录当前请求时间
    send_request_ping_time = time.time()
    #发送数据到网络
    rawsocket.sendto(icmp_packet,(dst_addr,80))
    #返回数据
    return send_request_ping_time,rawsocket,dst_addr
 
 
def reply_ping(send_request_ping_time,rawsocket,data_Sequence,timeout = 2):
    while True:
        #开始时间
        started_select = time.time()
        #实例化select对象，可读rawsocket，可写为空，可执行为空，超时时间
        what_ready = select.select([rawsocket], [], [], timeout)
        #等待时间
        wait_for_time = (time.time() - started_select)
        #没有返回可读的内容，判断超时
        if what_ready[0] == []:  # Timeout
            return -1
        #记录接收时间
        time_received = time.time()
        #设置接收的包的字节为1024
        received_packet, addr = rawsocket.recvfrom(1024)
        #获取接收包的icmp头
        #print(icmpHeader)
        icmpHeader = received_packet[20:28]
        #反转编码
        type, code, checksum, packet_id, sequence = struct.unpack(
            ">BBHHH", icmpHeader
        )
 
        if type == 0 and sequence == data_Sequence:
            return time_received - send_request_ping_time
 
        #数据包的超时时间判断
        timeout = timeout - wait_for_time
        if timeout <= 0:
            return -1
def dealtime(dst_addr,sumtime,shorttime,longtime,accept,i,time):
    sumtime += time
    print(sumtime)
    if i == 4:
        print("{0}的Ping统计信息：".format(dst_addr))
        print("数据包：已发送={0},接收={1}，丢失={2}（{3}%丢失），\n往返行程的估计时间（以毫秒为单位）：\n\t最短={4}ms，最长={5}ms，平均={6}ms".format(i+1,accept,i+1-accept,(i+1-accept)/(i+1)*100,shorttime,longtime,sumtime))
def ping(host):
    send, accept, lost = 0, 0, 0
    sumtime, shorttime, longtime, avgtime = 0, 1000, 0, 0
    #TODO icmp数据包的构建
    data_type = 8 # ICMP Echo Request
    data_code = 0 # must be zero
    data_checksum = 0 # "...with value 0 substituted for this field..."
    data_ID = 0 #Identifier
    data_Sequence = 1 #Sequence number
    payload_body = b'abcdefghijklmnopqrstuvwabcdefghi' #data
 
    # 将主机名转ipv4地址格式，返回以ipv4地址格式的字符串，如果主机名称是ipv4地址，则它将保持不变
    dst_addr = socket.gethostbyname(host)
    print("正在 Ping {0} [{1}] 具有 32 字节的数据:".format(host,dst_addr))
    for i in range(0,4):
        send = i + 1
        #请求ping数据包的二进制转换
        icmp_packet = request_ping(data_type,data_code,data_checksum,data_ID,data_Sequence + i,payload_body)
        #连接套接字,并将数据发送到套接字
        send_request_ping_time,rawsocket,addr = raw_socket(dst_addr,icmp_packet)
        #数据包传输时间
        times = reply_ping(send_request_ping_time,rawsocket,data_Sequence + i)
        if times > 0:
            print("来自 {0} 的回复: 字节=32 时间={1}ms".format(addr,int(times*1000)))
 
            accept += 1
            return_time = int(times * 1000)
            sumtime += return_time
            if return_time > longtime:
                longtime = return_time
            if return_time < shorttime:
                shorttime = return_time
            time.sleep(0.7)
        else:
            lost += 1
            print("请求超时。")
 
        if send == 4:
            print("{0}的Ping统计信息:".format(dst_addr))
            print("\t数据包：已发送={0},接收={1}，丢失={2}（{3}%丢失），\n往返行程的估计时间（以毫秒为单位）：\n\t最短={4}ms，最长={5}ms，平均={6}ms".format(
                i + 1, accept, i + 1 - accept, (i + 1 - accept) / (i + 1) * 100, shorttime, longtime, sumtime/send))
 
 
 
if __name__ == "__main__":
    ping('124.95.133.164')
