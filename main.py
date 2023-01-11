import os
import requests
import re
from bs4 import BeautifulSoup as BS
from functools import reduce
import schedule

from email.mime.text import MIMEText
from email.header import Header
import smtplib

import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

mail_host = os.environ['MAIL_HOST']
mail_user = os.environ['USER']  # 此处填你的邮箱
mail_girl = os.environ['TO']  # 另一个邮箱的邮箱
mail_pass = os.environ['PASS']  # 邮箱密码
name_girl = "刘喂喂"  # 名字
mail_port = 465  # smtp端口号
headers = {
    'cookie': 'JSESSIONID=MR5Yj7ZR1hrNzDnQp3knNRhYYRnh4h5F2BkQYZJQBLGxcy8xy1Rj!569010957',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Connection': 'close',
}

buildingID = os.environ['BUILDING_ID']
url = f'http://124.95.133.164:7003/newbargain/download/findys/showPrice.jsp?buildingID={buildingID}'
room_list = []

requests.DEFAULT_RETRIES = 5  # 增加重试连接次数
s = requests.session()
s.keep_alive = False  # 关闭多余连接
s.proxies = {"https": "111.225.153.216:8089", "http": "111.225.152.186:8089", }


def buildingInfo():
    change_room = ''
    try:
        print("进入")
        response = s.get(url=url, headers=headers, timeout=300)
        print("请求成功")
        html_data = response.text
        soup = BS(html_data, "lxml")
        divs = soup.find_all(xxx=re.compile("可售"))
        for div in divs:
            td_x = div['xxx']
            re_b = re.compile("<%s.*?>(.+?)<%s>" % ("/b", "br"), re.I | re.S)
            # re_b = re.compile("</b.*?>(.+?)<br>", re.I | re.S)
            # re_b = re.compile("(?<=<B>).*?(?=<br>)", re.I | re.S)
            # ['房屋状态：', '房屋地址：', '房屋结构：', '房屋用途：', '建筑面积：', '户型：', '单价：', '总价：', '预售许可证号：']
            room = re.findall(re_b, td_x)
            room_json = {'room_number': re.findall('[(](.*?)[)]', room[1])[0],
                         'area': room[4],
                         'unit_price': room[5],
                         'total_price': room[6]}
            ret = reduce(lambda pre, cur: cur if cur['room_number'] == room_json['room_number'] else pre, room_list, None)
            if ret:
                if ret['unit_price'] != room_json['unit_price']:
                    change_room += f'{ret["room_number"]}：原价为{ret["unit_price"]}调价位{room_json["unit_price"]}\n' \
                                   f'原总价{ret["total_price"]}调价位{room_json["total_price"]}\n'
            else:
                room_list.append(room_json)
            return change_room
    except smtplib.SMTPException as e:
        print("请求失败")
        return "失败"
    

def sendMail():
    smtpObj = smtplib.SMTP_SSL(mail_host, mail_port)
    try:
        smtpObj.login(mail_user, mail_pass)
    except smtplib.SMTPException as e:
        logger.info(e)
    content = buildingInfo()
#     content = '123'
    if content == "":
        content += '\n数据无变化'
    message = MIMEText(content, 'plain', 'utf-8')
    message['From'] = mail_user
    message['To'] = mail_girl
    message['Subject'] = f'今日数据汇总 \n '
    try:
        smtpObj.sendmail(mail_user, [mail_girl], message.as_string())
        logger.info("send email success")
    except smtplib.SMTPException as e:
        logger.info(e)
        logger.info("Error: send email fail")
        logger.info("无法发送邮件")
    finally:
        # 关闭服务器
        smtpObj.quit()
    logger.info("邮件发送成功")
    
    
if __name__ == "__main__":
    sendMail()
