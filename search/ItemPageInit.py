from mysqlplugin import NavOrm
import argparse
import re
import sys
import subprocess
import threading
import json
import gmail
import time
import VerifyUnlocker
# 自動化控制
from selenium import webdriver

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
##########################################################################################
# 通用型程式碼


def checkVerify(content: str) -> str:
    """判斷網頁原始碼是被阻擋

    Args:
        content (str): 網頁原始碼

    Raises:
        VerifyError: 驗證失敗
        VerifyError: 遇到登入

    Returns:
        str: 成功解鎖之網頁
    """
    # msg: '霸下通用 web 页面-验证码',
    DBSession = NavOrm.sessionmaker(bind=NavOrm.DBLink)
    dbSession = DBSession()
    if '"action": "captcha"' in content:
        # 寫入遇到滑塊時間，記錄之
        dbSession.add(
            NavOrm.Verifys(
                status=0,
                msg="遇到滑塊"
            )
        )
        HOST = re.findall(r'"HOST": "(.*?)",', content)[0]
        PATH = re.findall(r'"PATH": "(.*?)",', content)[0]
        MSG = re.findall(r"msg: '(.*?)',", content)[0]
        # 先嘗試進行解塊，若出現False，則拋出錯誤
        UnlockResult = VerifyUnlocker.Unlocker()
        if not UnlockResult[0]:
            dbSession.add(
                NavOrm.Verifys(
                    status=2,
                    msg=MSG + "\n" + UnlockResult[1]
                )
            )
            dbSession.commit()
            dbSession.close()
            raise VerifyError({
                "HOST": HOST,
                "PATH": PATH,
                "MSG": MSG + "\n" + UnlockResult[1]
            })
        dbSession.add(
            NavOrm.Verifys(
                status=1,
                msg=UnlockResult[1]
            )
        )
        dbSession.commit()
        dbSession.close()
        return VerifyUnlocker.driver.page_source
    elif '/newlogin/login.do' in content:
        dbSession.add(
            NavOrm.Verifys(
                status=4,
                msg="尚未登入淘寶！"
            )
        )
        dbSession.commit()
        dbSession.close()

        raise VerifyError({
            "HOST": "login.taobao.com",
            "PATH": "member/login.jhtml",
            "MSG": "尚未登入淘寶！"
        })
    return content


def get_g_page_config(content: str) -> list:
    """抓取網頁原始碼內的g_page_config，並針對pager進行抓取

    Args:
        content (str): 搜尋部分的淘寶網頁原始碼
    Returns:
        dict: 回傳pager參數
    """
    # 先判斷是否被阻擋
    content = checkVerify(content)
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


###############
# 通用型Class
###############
class VerifyError(Exception):
    """認證錯誤

    Args:
        Exception (Taobao): 因為解鎖失敗所以拋錯
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        MailString = open("./config/GetVerify.txt",
                          "r", encoding="utf-8").read()
        MailString = MailString.format(
            args[0]['HOST'],
            args[0]['PATH'],
            args[0]['MSG']
        )
        # 發送Email
        gmail.GInit().sendMsg(
            "[淘寶爬蟲]驗證攔截",
            MailString
        )


class chromeDriverInformation:
    """chrome driver的設定參數
    """
    ip = None
    port = None
    drive = None

# 通用型程式碼結束
##########################################################################################


class taobao:
    def __init__(self, key: str, ip: str, port: int) -> None:
        """初始化針對產品進行的抓取

        Args:
            key (str): 針對何種產品進行抓取
            ip (str): Driver之IP
            port (int): Driver之PORT
        """
        # 先載入一隻神獸
        NoBugDragon = open(file="./arts/Nobug.art", mode="r", encoding="utf-8")
        print("{}\n".format(NoBugDragon.read()))
        NoBugDragon.close()
        del NoBugDragon
        ##############
        self.key = key
        print('[__init__]key初始化完畢')
        print('[__init__]瀏覽器初始化中..')
        # 負責初始化瀏覽器的部分
        chromeDriverInformation.ip = ip
        chromeDriverInformation.port = port
        # 打開Chrome
        if ip == "127.0.0.1":
            # 需創建Threading
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
        try:
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
        except Exception as e:
            sys.exit("[Chrome初始化失敗]{}".format(e))

    def TestUrl(self):
        """進行driver的網頁測試是否正常
        """
        chromeDriverInformation.drive.get("https://www.google.com")

    def getNavItemsService(self):
        """
        - 獲取需品牌底下的產品
        - https://s.taobao.com/search?q=%E5%B0%BF%E8%A4%B2&tab=mall&sort=sale-desc&ppath={}&s= 44 * p
        - 並將結果儲存至DB內
        - 同時傳送完畢的Email訊息
        """
        print("[getNavItemsService]載入關鍵字 {}".format(self.key))
        # 將chrome切換至search的頁面
        # q     : key
        # tab   : 標籤
        # sort  : 排序方式
        # ppath : 品牌
        # s     : 顯示頁面. s = 44 * p
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
        help="遠程控制需要用到的chrome",
        default="127.0.0.1"
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
        ip=CrawlerArgs.key,
        port=CrawlerArgs.port
    )
