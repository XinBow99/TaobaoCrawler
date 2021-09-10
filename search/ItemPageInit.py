from mysqlplugin import NavOrm
import argparse
import re
import sys
import subprocess
import threading
import json
from datetime import datetime, timedelta
import time
import gmail
from PublicFunctions import VerifyUnlocker, checkVerify
# 自動化控制
from selenium import webdriver
# 進度條測試
from tqdm import tqdm
##########################################################################################
#                                                    __----~~~~~~~~~~~------___
#                                   .  .   ~~//====......          __--~ ~~
#                   -.            \_|//     |||\\  ~~~~~~::::... /~
#                ___-==_       _-~o~  \/    |||  \\            _/~~-
#        __---~~~.==~||\=_    -_--~/_-~|-   |\\   \\        _/~
#    _-~~     .=~    |  \\-_    '-~7  /-   /  ||    \      /
#  .~       .~       |   \\ -_    /  /-   /   ||      \   /
# /  ____  /         |     \\ ~-_/  /|- _/   .||       \ /
# |~~    ~~|--~~~~--_ \     ~==-/   | \~--===~~        .\
#          '         ~-|      /|    |-~\~~       __--~~
#                      |-~~-_/ |    |   ~\_   _-~            /\
#                           /  \     \__   \/~                \__
#                       _--~ _/ | .-~~____--~-/                  ~~==.
#                      ((->/~   '.|||' -_|    ~~-/ ,              . _||
#                                 -_     ~\      ~~---l__i__i__i--~~_/
#                                 _-~-__   ~)  \--______________--~~
#                               //.-~~~-~_--~- |-------~~~~~~~~
#                                      //.-~~~--\
#                  神獸保佑
#                程式碼永無BUG!
##########################################################################################


def get_g_page_config(content: str) -> list:
    """抓取網頁原始碼內的g_page_config，並針對item進行抓取

    Args:
        content (str): 搜尋部分的淘寶網頁原始碼
    Returns:
        dict: 回傳auction參數
    """
    # 先判斷是否被阻擋
    content = checkVerify.do(content)
    if "g_page_config" not in content:
        return {
            'status': 0,
            'function': 'get_g_page_config',
            'msg': '網頁內容不正確'
        }
    gpcRe = re.findall(pattern=r'g_page_config \= (.*)\;',
                       string=content.strip().strip("\n"))[0]
    GpcNav = json.loads(gpcRe)

    def checkNode(jsonContent, checkKey):
        if checkKey in jsonContent:
            return jsonContent[checkKey]
        # 未來需放try catch
        return jsonContent
    GpcNav = checkNode(GpcNav, 'mods')
    GpcNav = checkNode(GpcNav, 'itemlist')
    GpcNav = checkNode(GpcNav, 'auctions')
    return GpcNav


class taobao:
    def __init__(self, key: str, sendMailTitle: str, ip: str, port: int) -> None:
        """初始化針對產品進行的抓取

        Args:
            key (str): 針對何種產品進行抓取
            ip (str): Driver之IP
            port (int): Driver之PORT
        """
        ##############
        # 下方程式碼可用於 Item, PPath, Nav
        ##############
        # 先載入一隻神獸
        NoBugDragon = open(file="./arts/Nobug.art", mode="r", encoding="utf-8")
        print("{}\n".format(NoBugDragon.read()))
        NoBugDragon.close()
        del NoBugDragon
        ###############
        # 設定該Class獨立參數
        ###############
        self.sendMailTitle = sendMailTitle
        ###############
        self.key = key
        print('[__init__]key初始化完畢')
        print('[__init__]瀏覽器初始化中..')
        # 打開Chrome
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
        self.getNavItemsService()
        self.closeDriver()
        chromeThreading.join()

    def createChromeBrowser(self):
        """以Bash的方式打開一個Chrome
        """
        try:
            subprocess.call(
                ["RunNavChrome.bat"])
        except Exception as e:
            sys.exit(f"[無法啟動Chrome]{e}")

    def initBrowser(self):
        try:
            """初始化爬蟲所需的webdriver
            """
            # 設定給予瀏覽器的options
            options = webdriver.ChromeOptions()
            # 設置控制通訊埠
            options.add_experimental_option(
                "debuggerAddress", "{}:{}".format(
                    self.ip,
                    self.port
                ))
            # 獲取本地的User名稱
            # ServerUserName = getpass.getuser()
            # 給予chromedriver需要讀取的資料
            # OriginChromePath = "C:\\Users\\{}\\AppData\\Local\\Google\\Chrome\\User Data".format(
            #    ServerUserName)
            # 加入arg
            # options.add_argument("user-data-dir={}".format(OriginChromePath))
            # options.add_argument('--headless')
            # options.add_argument('--no-sandbox')
            # options.add_argument('--disable-gpu')
            # options.add_argument('--disable-dev-shm-usage')
            # 創建一個driver
            self.driver = webdriver.Chrome(
                executable_path="drivers/chromedriver.exe",
                chrome_options=options
            )
            self.driver.implicitly_wait(30)
            # 攔截webdriver之檢測代碼
            self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                    })
                    """
                }
            )
        except Exception as e:
            sys.exit("[Chrome初始化失敗]{}".format(e))

    def TestUrl(self):
        """進行driver的網頁測試是否正常
        """
        self.driver.get("https://www.google.com")

    def getNavItemsService(self):
        """
        - 獲取需品牌底下的產品
        - https://s.taobao.com/search?q={}&tab=mall&sort=sale-desc&ppath={}&s= 44 * (p - 1)
        - 並將結果儲存至DB內
        - 同時傳送完畢的Email訊息
        """
        print("[getNavItemsService]載入關鍵字 {}".format(self.key))
        # 將chrome切換至search的頁面
        # q     : key
        # tab   : 標籤
        # sort  : 排序方式
        # ppath : 品牌
        # s     : 顯示頁面. s = 44 * (p-1)
        # 先query出所有為key的list
        now = datetime.now()
        eight_hours_ago = now - timedelta(hours=8)
        queryByKeyList = self.NavDBSession.query(
            # 查詢Navs的資料表
            NavOrm.Navs.brand,
            NavOrm.Navs.search_key,
            NavOrm.Navs.ppath,
            # 查詢Pagers
            NavOrm.Pagers.pageSize,
            NavOrm.Pagers.totalPage,
            NavOrm.Pagers.currentPage,
            NavOrm.Pagers.totalCount,
            NavOrm.Pagers.createAt
        ).join(
            NavOrm.Navs, NavOrm.Navs.brand == NavOrm.Pagers.brand
        ).filter_by(
            search_key=self.key
        ).filter(
            NavOrm.Pagers.createAt > eight_hours_ago
        ).filter(
            NavOrm.Pagers.createAt < now
        ).all()
        # 枚舉result
        # search_key
        # brand
        # ppath
        _tempPageLength = 0
        for result in queryByKeyList:
            print('[INFO]->', result.brand)
            # Save auctions
            auctions = []
            for page in tqdm(range(int(result.currentPage), int(result.totalPage) + 1)):
                # 進入網頁
                ConnentUrl = "https://s.taobao.com/search?q={}&tab=mall&sort=sale-desc&ppath={}&s={}".format(
                    self.key,
                    result.ppath,
                    44 * (page - 1)
                )
                self.driver.get(ConnentUrl)
                # 預防爆炸，並設定最後一個訪問的網址，如果解鎖則傳送之
                VerifyUnlocker.lastUrl = ConnentUrl
                print("[URL_初始化]{}".format(VerifyUnlocker.lastUrl))
                # 取得網頁原始碼
                pageSource = self.driver.page_source
                # 分析網頁 -> auction
                itemsAnalysis = get_g_page_config(pageSource)
                # 取得網頁的auction並新增到陣列
                auctions += itemsAnalysis
                time.sleep(5)
            print("[SQL]auctions寫入資料庫")
            for auction in tqdm(auctions):
                # by brand
                self.NavDBSession.add(
                    NavOrm.Items(
                        result.search_key,
                        result.brand,
                        auction
                    )
                )
                # 各項請求需休息5秒，否則會被擋下來
                self.NavDBSession.commit()
            _tempPageLength += len(auctions)
        self.NavDBSession.close()
        gmail.GInit().sendMsg(
            self.sendMailTitle,
            "產品下載完成，{}項品牌，總共：{}項產品".format(
                len(queryByKeyList), _tempPageLength)
        )

    def getCurrentDriver(self):
        """回傳正在使用的Driver

        Returns:
            Chrome: 目前正在使用的Chrome
        """
        return self.driver

    def getCurrentDBsession(self):
        """回傳正在使用的DBsession

        Returns:
            DBsession: 目前正在使用的DBsession
        """
        return self.NavDBSession

    def closeDriver(self):
        """結束Chrome driver
        """
        self.driver.close()
        self.driver.quit()
        print("[CloseDriver]結束Nav抓取")


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
    gTaobaoSession = taobao(
        key=CrawlerArgs.key,
        sendMailTitle=CrawlerArgs.EmailTitle,
        ip=CrawlerArgs.ip,
        port=CrawlerArgs.port
    )
