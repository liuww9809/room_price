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
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
}

buildingID = os.environ['BUILDING_ID']

def sendMail():
    smtpObj = smtplib.SMTP_SSL(mail_host, mail_port)
    try:
        smtpObj.login(mail_user, mail_pass)
    except smtplib.SMTPException as e:
        logger.info(e)
#     content = buildingInfo()
    content = '123'
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
