from mysqlplugin import NavOrm
import argparse
import re
import sys
import getpass
import json
# 自動化控制
from selenium import webdriver


def get_g_page_config(content: str):
    '''
    取得該頁面的g_page_config
    - content: 網頁內容
    '''
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
    def __init__(self, key: str) -> None:
        '''
        該方法用於初始化淘寶搜索，必須輸入查詢之key以及使用者的headers的txt
        - key: 搜索之物品
        '''
        self.key = key
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
        self.getFirstPageNav()
        self.closeDriver()

    def initBrowser(self):
        '''
        初始化chrome的瀏覽器...
        '''
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
        '''
        測試瀏覽器是否正常運行
        '''
        self.driver.get("https://www.google.com")

    def getFirstPageNav(self):
        '''
        獲取需儲存之品牌Nav
        https://s.taobao.com/search?q=%E5%B0%BF%E8%A4%B2
        '''
        print("[getFirstPageNav]載入關鍵字 {}".format(self.key))
        self.driver.get("https://s.taobao.com/search?q={}".format(self.key))
        pageSource = self.driver.page_source
        brands = get_g_page_config(pageSource)
        for brand in brands:
            exists = self.NavDBSession.query(NavOrm.exists().filter(
                NavOrm.Navs.brand == brand['text'])).update({"value": brand['value']}).scalar()
            if not exists:
                self.NavDBSession.add(NavOrm.Navs(
                    brand['text'], brand['value']))
        self.NavDBSession.commit()
        self.NavDBSession.close()

    def closeDriver(self):
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

    def checkArgsNone(arg):
        if arg == None:
            sys.exit("請確認輸入參數是否正確")
    CrawlerArgs = CrawlerArgsParser.parse_args()
    checkArgsNone(CrawlerArgs.key)
    taobao(CrawlerArgs.key)
