import argparse
import sys
import threading
from PublicFunctions import VerifyUnlocker
from mysqlplugin import NavOrm


class taobaoCrawlerByAPI:
    def __init__(self, key: str, sendMailTitle: str, ip: str, port: int) -> None:
        """初始化淘寶API爬蟲

        Args:
            key (str): 於資料庫搜尋之search_key
            sendMailTitle (str): 完成後所送的email
            ip (str): 遠程chrome ip
            port (int): 遠程chrome port
        """
        ##############
        # 下方程式碼可用於 API用
        ##############
        # 先載入一隻佛祖
        NoBugBuddha = open(file="./arts/buddha.art",
                           mode="r", encoding="utf-8")
        print("{}\n".format(NoBugBuddha.read()))
        NoBugBuddha.close()
        del NoBugBuddha
        self.sendMailTitle = sendMailTitle
        ###############
        self.key = key
        print('[__init__]key初始化完畢')
        print('[__init__]瀏覽器初始化中..')
        # 打開Chrome
        chromeThreading = None
        if ip == "127.0.0.1":
            # 需創建Threading
            print("[創建Session]For Chrome")
            chromeThreading = threading.Thread(target=self.createChromeBrowser)
            chromeThreading.start()
        # 初始化Browser
        self.ip = ip
        self.port = port
        self.driver = None
        self.initBrowser()
        # 設定解鎖所需之參數
        VerifyUnlocker.driver = self.driver
        VerifyUnlocker.key = self.key
        print('[__init__]資料庫初始化中..')
        NavDBSession = NavOrm.sessionmaker(bind=NavOrm.DBLink)
        self.NavDBSession = NavDBSession()
        print('[__init__]瀏覽器測試中..')
        self.TestUrl()
        print('[__init__]初始化完畢！')
        print('==============================')
        self.getFirstPageNavService()
        if ip == "127.0.0.1":
            self.closeDriver()
            chromeThreading.join()
        else:
            self.TestUrl()


if __name__ == "__main__":
    # 讀取啟動參數
    CrawlerArgsParser = argparse.ArgumentParser()
    CrawlerArgsParser.add_argument(
        "-k",
        "--key",
        type=str,
        help="爬取之關鍵字"
    )
    CrawlerArgsParser.add_argument(
        "-t",
        "--EmailTitle",
        type=str,
        help="設置該程序的EmailTitle",
        default="[淘寶爬蟲]品牌更新作業"
    )
    CrawlerArgsParser.add_argument(
        "-ip",
        "--ip",
        type=str,
        help="遠程控制需要用到的chrome"
    )
    CrawlerArgsParser.add_argument(
        "-p",
        "--port",
        type=int,
        help="設置爬蟲之CHROME控制通訊埠",
    )

    def checkArgsParserNone(arg):
        if arg == None:
            sys.exit("請確認輸入參數是否正確")
    CrawlerArgs = CrawlerArgsParser.parse_args()
    checkArgsParserNone(CrawlerArgs.key)
    checkArgsParserNone(CrawlerArgs.EmailTitle)
    checkArgsParserNone(CrawlerArgs.ip)
    checkArgsParserNone(CrawlerArgs.port)
    gTaobaoSession = taobaoCrawlerByAPI(
        key=CrawlerArgs.key,
        sendMailTitle=CrawlerArgs.EmailTitle,
        ip=CrawlerArgs.ip,
        port=CrawlerArgs.port
    )
