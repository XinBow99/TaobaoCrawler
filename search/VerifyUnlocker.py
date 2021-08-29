from selenium.webdriver.common.action_chains import ActionChains
# 自動化控制
from selenium import webdriver
import time
port = 10001


def initBrowser():
    """初始化爬蟲所需的webdriver
    """
    # 設定給予瀏覽器的options
    options = webdriver.ChromeOptions()
    # 設置控制通訊埠
    options.add_experimental_option(
        "debuggerAddress", "127.0.0.1:{}".format(port))
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
    driver = webdriver.Chrome(
        executable_path="drivers/chromedriver.exe",
        chrome_options=options
    )
    # 攔截webdriver之檢測代碼
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
                })
                """
        }
    )
    return driver


def Unlocker(driver=None):
    """負責解搜尋頁面的店小二

    Args:
        driver (webdriver): 目前正在使用的driver
    """
    SuccessFlag = False
    SuccessMessage = "解除成功"
    if not driver:
        driver = initBrowser()
    try:
        # verifySpan: 獲取滑塊
        verifySpan = driver.find_element_by_xpath(
            '//*[@id="nc_1__scale_text"]/span')
        # verifySpanSize: 滑塊的大小
        verifySpanSize = verifySpan.size
        print("[獲取滑塊]", verifySpanSize)
        # 擷取滑塊按鈕>>
        button = driver.find_element_by_xpath('//*[@id="nc_1_n1z"]')
        buttonLocation = button.location
        print("[滑塊位置]", buttonLocation)
        # 設定拖曳結束位置
        EndXlocation = verifySpanSize['width']
        dragAction = ActionChains(driver)
        dragSource = driver.find_element_by_xpath('//*[@id="nc_1_n1z"]')
        # 按住按鈕
        dragAction.click_and_hold(dragSource)
        dragAction.move_by_offset(EndXlocation, 0)
        # 放鬆按鈕
        dragAction.release().perform()
        # 給Flag
        SuccessFlag = True
    except Exception as e:
        SuccessMessage = str(e)
    return (SuccessFlag, SuccessMessage)


def TmallUnlock():
    """負責解除商品以及評論之Function

    Args:
        driver (webdriver): 目前正在使用的driver
    """
    driver = initBrowser()
    # 該頁面有嵌入iframe，必須要先進行切換
    iframe = driver.find_element_by_xpath('//*[@id="J_sufei"]/iframe')
    # main->iframe
    driver.switch_to.frame(iframe)
    time.sleep(2)
    return Unlocker(driver)
