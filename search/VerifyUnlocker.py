from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import random
# 儲存DRIVER
driver = None
key = None
lastUrl = None

print("[VerifyUnlocker]模組載入成功！")

def freshPageToSearch(driver):
    """針對超過一次無法進行解鎖而設計之

    Args:
        driver (chromedrive): 瀏覽器控制權
    """
    driver.refresh()
    driver.get("https://s.taobao.com/")
    time.sleep(1)
    # 找搜尋的框框
    driver.find_element_by_xpath('//*[@id="q"]').send_keys(key, Keys.ENTER)
    time.sleep(1)


def Unlocker():
    """負責解搜尋頁面的店小二

    Args:
        driver (webdriver): 目前正在使用的driver
    """
    SuccessFlag = False
    SuccessMessage = "解除成功"
    print("[窗口狀態]最大化")
    driver.maximize_window()
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
        dragAction = ActionChains(driver)
        dragSource = driver.find_element_by_xpath('//*[@id="nc_1_n1z"]')
        # 按住按鈕
        dragAction.click_and_hold(dragSource)
        offsetSum = 0
        while True:
            x = random.randint(0, 10)
            dragAction.move_by_offset(x, 0)
            time.sleep((random.randint(1, 2))/10)
            offsetSum += x
            if offsetSum >= 280:
                break
        # 放鬆按鈕
        dragAction.release().perform()
        time.sleep(random.randint(5, 15))
        # 檢查是否確實消除
        if '"action": "captcha"' in driver.page_source:
            driver.refresh()
            Unlocker()
        # 給Flag
        driver.get(lastUrl)
        time.sleep(5)
        SuccessFlag = True
    except Exception as e:
        SuccessMessage = str(e)
    return (SuccessFlag, SuccessMessage)


def TmallUnlock():
    """負責解除商品以及評論之Function

    Args:
        driver (webdriver): 目前正在使用的driver
    """
    # 該頁面有嵌入iframe，必須要先進行切換
    iframe = driver.find_element_by_xpath('//*[@id="J_sufei"]/iframe')
    # main->iframe
    driver.switch_to.frame(iframe)
    time.sleep(2)
    return Unlocker()
