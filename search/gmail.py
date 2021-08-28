import smtplib
from email.mime.text import MIMEText
import yaml


def GInit():
    g = Gmail()
    return g


class Gmail:
    def __init__(self):
        self.yamlData = None
        with open("./gmail.yaml", "r", encoding="utf-8") as stream:
            self.yamlData = yaml.load(stream, Loader=yaml.FullLoader)
            stream.close()
        # 寄件者帳號
        self.gmail_user = self.yamlData['Sender']['account']
        # 寄件者密碼(GOOGLE 應用程式密碼)
        self.gmail_password = self.yamlData['Sender']['key']

    def sendMsg(self, subject="ErrorMsg", content="content"):
        msg = MIMEText(content)
        msg['Subject'] = subject
        msg['From'] = self.gmail_user
        msg['To'] = ",".join(self.yamlData['Receiver'])
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(self.gmail_user, self.gmail_password)
        Logo = '''
        <p align="center">
            <a href="" rel="noopener">
                <img width=200px height=200px src="https://raw.githubusercontent.com/XinBow99/TaobaoCrawler/main/search/crawler.png" alt="Project logo"></a>
            </p>
        <h3 align="center">TaobaoCrawler</h3><br>
        '''
        server.send_message(Logo + msg)
        server.quit()
