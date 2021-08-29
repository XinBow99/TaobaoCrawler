from mysqlplugin import NavOrm
import argparse
import re
import sys
import getpass
import json
import gmail
# 自動化控制
from selenium import webdriver


def get_g_page_config(content: str) -> list:
    """抓取網頁原始碼內的g_page_config，並針對Nav進行抓取

    Args:
        content (str): 搜尋部分的淘寶網頁原始碼
    Returns:
        list: 回傳顯示於NAV的所有品牌
    """
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
    GpcNav = checkNode(GpcNav, 'nav')
    GpcNav = checkNode(GpcNav, 'data')
    GpcNav = checkNode(GpcNav, 'common')
    for i, common in enumerate(GpcNav):
        if common['text'] == '品牌':
            GpcNav = checkNode(GpcNav[i], 'sub')
            break
    return GpcNav


class taobao:
    def __init__(self, key: str, sendMailTitle: str) -> None:
        """初始化對於NAV的抓取

        Args:
            key (str): 針對何種產品進行抓取
            sendMailTitle (str): 抓取完畢所寄送之標題為何
        """
        self.key = key
        self.sendMailTitle = sendMailTitle
        print('[__init__]key初始化完畢')
        print('[__init__]瀏覽器初始化中..')
        # 負責初始化瀏覽器的部分
        self.driver = None
        self.initBrowser()
        print('[__init__]資料庫初始化中..')
        NavDBSession = NavOrm.sessionmaker(bind=NavOrm.DBLink)
        self.NavDBSession = NavDBSession()
        print('[__init__]瀏覽器測試中..')
        self.TestUrl()
        print('[__init__]初始化完畢！')
        print('==============================')
        self.getFirstPageNavService()
        self.closeDriver()

    def initBrowser(self):
        """初始化爬蟲所需的webdriver
        """
        # 設定給予瀏覽器的options
        options = webdriver.ChromeOptions()
        # 獲取本地的User名稱
        ServerUserName = getpass.getuser()
        # 給予chromedriver需要讀取的資料
        OriginChromePath = "C:\\Users\\{}\\AppData\\Local\\Google\\Chrome\\User Data".format(
            ServerUserName)
        # 加入arg
        options.add_argument("user-data-dir={}".format(OriginChromePath))
        # options.add_argument('--headless')
        # options.add_argument('--no-sandbox')
        # options.add_argument('--disable-gpu')
        # options.add_argument('--disable-dev-shm-usage')
        # 創建一個driver
        self.driver = webdriver.Chrome(
            executable_path="drivers/chromedriver.exe",
            chrome_options=options
        )

    def TestUrl(self):
        """進行driver的網頁測試是否正常
        """
        self.driver.get("https://www.google.com")

    def getFirstPageNavService(self):
        """
        - 獲取需儲存之品牌Nav
        - https://s.taobao.com/search?q=%E5%B0%BF%E8%A4%B2
        - 並將結果儲存至DB內
        - 同時傳送完畢的Email訊息
        """
        print("[getFirstPageNavService]載入關鍵字 {}".format(self.key))
        # 將chrome切換至search的頁面
        self.driver.get("https://s.taobao.com/search?q={}".format(self.key))
        # 取得搜尋的原始碼
        pageSource = self.driver.page_source
        # 獲取顯示於上列的所有廠商
        brands = get_g_page_config(pageSource)
        # 看有多少列被更新
        newRows = []
        #
        updates = 0
        for brand in brands:
            print(brand['text'])
            exists = self.NavDBSession.query(
                # 查詢Navs的資料表
                NavOrm.Navs
            ).filter_by(
                # 用廠牌進行filter
                brand=brand['text']
            ).update(
                # 更新ppath這個參數
                {"ppath": brand['value']}
            )
            # 如果找不到brand
            if not exists:
                # 使用添加
                self.NavDBSession.add(
                    NavOrm.Navs(
                        brand['text'], brand['value']
                    )
                )
                newRows.append(brand['text'])
            else:
                updates += exists
        self.NavDBSession.commit()
        self.NavDBSession.close()
        MailString = open("./config/NavStrings.txt",
                          "r", encoding="utf-8").read()
        MailString = MailString.format(
            len(brands),
            len(newRows),
            "、".join(newRows),
            updates
        )
        # 發送Email
        gmail.GInit().sendMsg(
            self.sendMailTitle,
            MailString
        )

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

    def checkArgsNone(arg):
        if arg == None:
            sys.exit("請確認輸入參數是否正確")
    CrawlerArgs = CrawlerArgsParser.parse_args()
    checkArgsNone(CrawlerArgs.key)
    checkArgsNone(CrawlerArgs.EmailTitle)
    taobao(CrawlerArgs.key, CrawlerArgs.EmailTitle)
