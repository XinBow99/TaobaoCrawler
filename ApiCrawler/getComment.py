import requests
from PublicFunctions import VerifyError, CookieError, jsonp
import argparse
import sys
import threading
from PublicFunctions import VerifyUnlocker
from mysqlplugin import NavOrm
######################
# Timeout之後 重新試試看
from retry import retry
from timeout_decorator import timeout, TimeoutError
######################
#########
# 自動化控制
from selenium import webdriver
# 通用 function
from PublicFunctions import VerifyUnlocker, checkVerify
# call bat
import subprocess
# Sign用
import time
import hashlib
# Progress
from tqdm import tqdm
# debug
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

cmtResult = []


def mutiWorks(TaobaoCommentInformation, NavDBSession, item, currentPage):
    cmtSecResult = jsonp.get(requests.get(
        url=TaobaoCommentInformation['api']['url'],
        headers=TaobaoCommentInformation['headers'],
        # cookies=self.TaobaoCommentInformation['cookies'],
        params={
            "itemId": item.nid,
            "sellerId": item.user_id,
            "currentPage": currentPage,
            "order": 3,
            "content": "1"
        },
        # Proxy 遠端方須架設
        # proxies=proxyServer,
        verify=False
    ).text)
    paginator = cmtSecResult['rateDetail']['paginator']
    rateCount = cmtSecResult['rateDetail']['rateCount']
    rateDanceInfo = cmtSecResult['rateDetail']['rateDanceInfo']
    rateList = cmtSecResult['rateDetail']['rateList']
    # 寫入資料庫
    for rateObj in rateList:
        # by cmt
        cmtResult.append(
            NavOrm.Comments(
                nid=item.nid,
                paginator=paginator,
                rateCount=rateCount,
                rateDanceInfo=rateDanceInfo,
                rateObjects=rateObj
            )
        )


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
        # TODO: 這邊修改為爬Api專用之代碼，設置初始化Self
        # T、sign、data需要額外產生
        self.TaobaoCommentInformation = {
            "api": {
                "url": "https://rate.tmall.com/list_detail_rate.htm",
                "path": "h5/mtop.taobao.rate.detaillist.get/4.0/"
            },
            "datas": {
                "itemId": None,
                "sellerId": None,
                "order": "3",
                "currentPage": None,
                "content": "1"
            },
            "headers": {
                'accept': '*/*',
                'accept-encoding': 'gzip, deflate, br',
                'referer': 'https://detail.tmall.com/item.htm?id={}',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
                'cookie': None
            },
            "cookies": {},
            "currentPid": ""
        }
        self.getCommentByApiService()
        if ip == "127.0.0.1":
            self.closeDriver()
            chromeThreading.join()
        else:
            # self.TestUrl()
            pass

    @retry(TimeoutError, tries=50)
    @timeout(20)
    def getWithRetry(self, url):
        """當瀏覽器載入不了時，需要retry

        Args:
            url (str): 指定的網址
        """
        self.driver.get(url)

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
            executable_path="drivers/chromedriver",
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

    def TestUrl(self):
        """進行driver的網頁測試是否正常
        """
        self.getWithRetry("https://www.google.com")

    def getCommentByApiService(self):
        # TODO: 添加CommentApi相關分析資訊
        """Comment相關資訊如下
        - domain: https://h5api.m.taobao.com/ 
        - path: h5/mtop.taobao.rate.detaillist.get/4.0/
        - https://rate.tmall.com/list_detail_rate.htm ?itemId=570120860221&spuId=962818326&sellerId=1770178042&currentPage=1&callback=jsonp903
        - args
        """
        print("[getCommentByApiService]載入關鍵字 {}".format(self.key))
        # 先找出第一筆Pid
        itemsResult = self.NavDBSession.query(
            NavOrm.Items
        ).filter_by(
            # 搜尋status為0的pid
            status=0)
        print("[itemsResult]載入筆數{}".format(len(list(itemsResult))))
        # 這個html用於跑第一筆init cookie用
        self.firstItemDetailHtml = 'https:' + itemsResult[0].comment_url
        # detail.tmall.com/item.htm -> m.intl.taobao.com/detail/detail.html
        # 先設定Cookie
        self.cookieGenerator()
        # 跑回圈8.8K多筆
        # 設定IP SERVER
        proxyServer = {
            'http': f"{self.ip}:8888",
            'https': f"{self.ip}:8888",
        }
        for item in tqdm(itemsResult, desc="[下載產品...]"):
            # set data
            # self.TaobaoCommentInformation['datas'][
            #    'data'] = '{"pageSize":10,"pageNo":1,"auctionNumId":"' + item.nid + '"}'
            # set sign 網頁版不用
            # self.setSign()
            # Null設定完成

            # 開始進行請求
            # TODO: 改成巢狀迴圈
            self.TaobaoCommentInformation['headers']['referer'] = self.TaobaoCommentInformation['headers']['referer'].format(
                item.nid)
            commentFirstRequest = jsonp.get(requests.get(
                url=self.TaobaoCommentInformation['api']['url'],
                headers=self.TaobaoCommentInformation['headers'],
                # cookies=self.TaobaoCommentInformation['cookies'],
                params={
                    "itemId": item.nid,
                    "sellerId": item.user_id,
                    "currentPage": 1,
                    "order": 3,
                    "content": "1"
                },
                # proxies=proxyServer,
                verify=False
            ).text)
            # 取得rateDetail資訊
            # TODO: 確認rgv587_flag 解一次解不過須重新整理
            rateDetail = commentFirstRequest['rateDetail']
            # 資料庫會用到
            paginator = rateDetail['paginator']
            rateCount = rateDetail['rateCount']
            rateDanceInfo = rateDetail['rateDanceInfo']
            rateList = rateDetail['rateList']
            lastPage = paginator['lastPage']
            # 寫入第一筆資料
            for rateObj in rateList:
                # by cmt
                self.NavDBSession.add(
                    NavOrm.Comments(
                        nid=item.nid,
                        paginator=paginator,
                        rateCount=rateCount,
                        rateDanceInfo=rateDanceInfo,
                        rateObjects=rateObj
                    )
                )
                self.NavDBSession.commit()
            # 因為先獲取第一頁了 所以從2
            mutiT = []
            for currentPage in tqdm(range(2, lastPage + 1), desc=item.nid):
                t = threading.Thread(target=mutiWorks, args=(
                    self.TaobaoCommentInformation, self.NavDBSession, item, currentPage,))

                mutiT.append(t)
                # cmtSecResult = jsonp.get(requests.get(
                #    url=self.TaobaoCommentInformation['api']['url'],
                #    headers=self.TaobaoCommentInformation['headers'],
                #    # cookies=self.TaobaoCommentInformation['cookies'],
                #    params={
                #        "itemId": item.nid,
                #        "sellerId": item.user_id,
                #        "currentPage": currentPage,
                #        "order": 3,
                #        "content": "1"
                #    },
                #    # Proxy 遠端方須架設
                #    # proxies=proxyServer,
                #    verify=False
                # ).text)
                ## TODO: 判斷flag<確認rgv587_flag
                # 處理資料庫所需要使用的部分
                #paginator = cmtSecResult['rateDetail']['paginator']
                #rateCount = cmtSecResult['rateDetail']['rateCount']
                #rateDanceInfo = cmtSecResult['rateDetail']['rateDanceInfo']
                #rateList = cmtSecResult['rateDetail']['rateList']
                # 寫入資料庫
                # for rateObj in rateList:
                #    # by cmt
                #    self.NavDBSession.add(
                #        NavOrm.Comments(
                #            nid=item.nid,
                #            paginator=paginator,
                #            rateCount=rateCount,
                #            rateDanceInfo=rateDanceInfo,
                #            rateObjects=rateObj
                #        )
                #    )
                #    self.NavDBSession.commit()
                # time.sleep(3)
                #print('cmtSecResult', cmtSecResult['rateDetail']['paginator'])
            for mt in mutiT:
                mt.start()
            for mt in tqdm(mutiT):
                mt.join()
            global cmtResult
            for cmt in cmtResult:
                self.NavDBSession.add(
                    cmt
                )
                self.NavDBSession.commit()
            #
            # print('[status]{}'.format(commentRequest.status_code))
            break
        # 然後再設定Sign
        # self.setSign()

    def cookieGenerator(self):
        """產生一組Cookie供於Api使用
        """
        # 先去產生x5key
        # self.getWithRetry(self.firstItemDetailHtml)
        # 然後判斷有沒有阻擋

        # 最後抓x5key
        self.getWithRetry(
            "chrome-extension://flldehcnleejgpingiffimidfjdcnfdi/popup.html")
        self.driver.execute_script("getX5();")
        x5Value = str(self.driver.execute_script("return x5;"))
        #cookiesList = self.driver.get_cookies()
        #cookieString = ""
        # for cookie in cookiesList:
        #    cookieString += "{}={}; ".format(cookie['name'], cookie['value'])
        #self.TaobaoCommentInformation['headers']['cookie'] = cookieString
        # self.getWithRetry(self.firstItemDetailHtml)
        self.TaobaoCommentInformation['headers']['cookie'] = x5Value
        print(x5Value)
        print("[cookieGenerator]設定完成")

    def setSign(self):
        """產生一組爬蟲所需的sign與t
        """
        token = str(self.driver.get_cookie("_m_h5_tk"))
        print(token)
        if '_' not in token:
            raise CookieError({'value': '_m_h5_tk'})
        token = token.split("_")[0]
        auctionData = self.TaobaoCommentInformation['datas']['data']
        # {"pageSize":10,"pageNo":1,"auctionNumId":"$pid"}
        t = int(time.time() * 1000)
        appkey = self.TaobaoCommentInformation['datas']['appKey']
        # 產生需要hash的資料
        hashKey = "{}&{}&{}&{}".format(token, t, appkey, auctionData)
        # 建立md5物件
        m = hashlib.md5()
        m.update(hashKey.encode("utf-8"))
        sign = m.hexdigest()
        # 寫入建立好的sign
        # TODO: 未來轉移至PublicFunction
        self.TaobaoCommentInformation["datas"]["t"] = t
        self.TaobaoCommentInformation["datas"]["sign"] = sign


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
    # python getComment.py -k -t -ip -p
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
