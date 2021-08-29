# 自動化控制
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
import time


def initBrowser():
    """初始化爬蟲所需的webdriver
    """
    # 設定給予瀏覽器的options
    options = webdriver.ChromeOptions()
    # 設置控制通訊埠
    options.add_experimental_option(
        "debuggerAddress", "127.0.0.1:10001")
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
    iframe = driver.find_element_by_xpath('//*[@id="J_sufei"]/iframe')
    print(iframe)
    driver.switch_to.frame(iframe)
    time.sleep(2)
    # 滑塊POC
    span_background = driver.find_element_by_xpath(
        '//*[@id="nc_1__scale_text"]/span')
    span_background_size = span_background.size
    print("[ScaleSize]", span_background_size)
    # 获取滑块的位置
    button = driver.find_element_by_xpath('//*[@id="nc_1_n1z"]')
    button_location = button.location
    print(button_location)
    # 模擬拖拉
    x_location = span_background_size["width"]
    y_location = button_location["y"]
    print(x_location, y_location)
    action = ActionChains(driver)
    source = driver.find_element_by_xpath('//*[@id="nc_1_n1z"]')
    action.click_and_hold(source).perform()
    action.move_by_offset(300, 0)
    action.release().perform()
    time.sleep(1)


initBrowser()
