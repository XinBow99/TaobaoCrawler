from mysqlplugin import NavOrm
import argparse
import re
import sys
import subprocess
import threading
import json
import gmail
import time
from PublicFunctions import chromeDriverInformation, VerifyUnlocker, checkVerify
# 自動化控制
from selenium import webdriver


def get_g_page_config(content: str) -> list:
    """抓取網頁原始碼內的g_page_config，並針對pager進行抓取

    Args:
        content (str): 搜尋部分的淘寶網頁原始碼
    Returns:
        dict: 回傳pager參數
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
    _temp = GpcNav
    GpcNav = checkNode(GpcNav, 'pager')
    if 'status' in GpcNav:
        if GpcNav['status'] == "hide":
            pager = {}
            # 因為產品太少 所以只找一頁 故以auctions替代Size
            _temp = checkNode(GpcNav, 'itemlist')
            _temp = checkNode(GpcNav, 'data')
            _temp = checkNode(GpcNav, 'auctions')
            pager['pageSize'] = len(_temp)
            pager['totalPage'] = 1
            pager['currentPage'] = 1
            pager['totalCount'] = len(_temp)
            return pager
    GpcNav = checkNode(GpcNav, 'data')
    return GpcNav


class taobao:
    def __init__(self, key: str, sendMailTitle: str, ip: str, port: int) -> None:
        """初始化對於pager的抓取

        Args:
            key (str): 針對何種產品進行抓取
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
        self.sendMailTitl = sendMailTitle
        ###############
        self.key = key
        print('[__init__]key初始化完畢')
        print('[__init__]瀏覽器初始化中..')
        # 負責初始化瀏覽器的部分
        chromeDriverInformation.ip = ip
        chromeDriverInformation.port = port
        # 打開Chrome
        if ip == "127.0.0.1":
            # 需創建Threading
            print("[創建Session]For Chrome")
            chromeThreading = threading.Thread(target=self.createChromeBrowser)
            chromeThreading.start()
        # 初始化Browser
        self.initBrowser()
        # 設定解鎖所需之參數
        VerifyUnlocker.driver = chromeDriverInformation.drive
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
        """初始化爬蟲所需的webdriver
        """
        # 設定給予瀏覽器的options
        options = webdriver.ChromeOptions()
        # 設置控制通訊埠
        options.add_experimental_option(
            "debuggerAddress", "{}:{}".format(
                chromeDriverInformation.ip,
                chromeDriverInformation.port
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
        chromeDriverInformation.drive = webdriver.Chrome(
            executable_path="drivers/chromedriver.exe",
            chrome_options=options
        )
        chromeDriverInformation.drive.implicitly_wait(30)
        # 攔截webdriver之檢測代碼
        chromeDriverInformation.drive.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
              Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
              })
              """
            }
        )

    def TestUrl(self):
        """進行driver的網頁測試是否正常
        """
        chromeDriverInformation.drive.get("https://www.google.com")

    def getNavPagerService(self):
        """
        - 獲取需儲存之品牌pager
        - https://s.taobao.com/search?q=%E5%B0%BF%E8%A4%B2&tab=mall&sort=sale-desc&ppath={}
        - 並將結果儲存至DB內
        - 同時傳送完畢的Email訊息
        """
        print("[getNavPagerService]載入關鍵字 {}".format(self.key))
        # 將chrome切換至search的頁面
        # q     : key
        # tab   : 標籤
        # sort  : 排序方式
        # ppath : 品牌
        # 先query出所有為key的list
        queryByKeyList = self.NavDBSession.query(
            # 查詢Navs的資料表
            NavOrm.Navs
        ).filter_by(
            search_key=self.key
        ).all()
        # 枚舉result
        # search_key
        # brand
        # ppath
        for result in queryByKeyList:
            print('[INFO]->', result.brand)
            # 切換頁面
            chromeDriverInformation.drive.get(
                "https://s.taobao.com/search?q={}&tab=mall&sort=sale-desc&ppath={}".format(
                    self.key,
                    result.ppath
                )
            )
            pageSource = chromeDriverInformation.drive.page_source
            pager = get_g_page_config(pageSource)
            # 取得pager後寫入資料庫
            # by brand
            self.NavDBSession.add(
                NavOrm.Pagers(
                    brand=result.brand,
                    pageSize=pager['pageSize'],
                    totalPage=pager['totalPage'],
                    currentPage=pager['currentPage'],
                    totalCount=pager['totalCount']
                )
            )
            # 各項請求需休息5秒，否則會被擋下來
            self.NavDBSession.commit()
            time.sleep(5)
        self.NavDBSession.close()

    def getCurrentDriver(self):
        """回傳正在使用的Driver

        Returns:
            Chrome: 目前正在使用的Chrome
        """
        return chromeDriverInformation.drive

    def getCurrentDBsession(self):
        """回傳正在使用的DBsession

        Returns:
            DBsession: 目前正在使用的DBsession
        """
        return self.NavDBSession

    def closeDriver(self):
        """結束Chrome driver
        """
        chromeDriverInformation.drive.close()
        chromeDriverInformation.drive.quit()
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

    def checkArgsNone(arg):
        if arg == None:
            sys.exit("請確認輸入參數是否正確")
    CrawlerArgs = CrawlerArgsParser.parse_args()
    checkArgsNone(CrawlerArgs.key)
    checkArgsNone(CrawlerArgs.EmailTitle)
    checkArgsNone(CrawlerArgs.ip)
    checkArgsNone(CrawlerArgs.port)
    gTaobaoSession = taobao(
        key=CrawlerArgs.key,
        sendMailTitle=CrawlerArgs.EmailTitle,
        ip=CrawlerArgs.ip,
        port=CrawlerArgs.port
    )
