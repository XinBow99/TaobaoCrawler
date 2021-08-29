from selenium.webdriver.common.action_chains import ActionChains
import time
# 儲存DRIVER
driver = None


def Unlocker():
    """負責解搜尋頁面的店小二

    Args:
        driver (webdriver): 目前正在使用的driver
    """
    SuccessFlag = False
    SuccessMessage = "解除成功"
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
    # 該頁面有嵌入iframe，必須要先進行切換
    iframe = driver.find_element_by_xpath('//*[@id="J_sufei"]/iframe')
    # main->iframe
    driver.switch_to.frame(iframe)
    time.sleep(2)
    return Unlocker(driver)
