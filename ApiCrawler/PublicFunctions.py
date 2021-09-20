
import re
import VerifyUnlocker
import gmail
from mysqlplugin import NavOrm
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

class CookieError(Exception):
    """認證錯誤

    Args:
        Exception (Taobao): 因為解鎖失敗所以拋錯
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        # 發送Email
        gmail.GInit().sendMsg(
            "[淘寶爬蟲]Cookie取值錯誤",
            args[0]['Value']
        )

class checkVerify:
    def do(content: str) -> str:
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
            return UnlockResult[2]
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

# 通用型程式碼結束
##########################################################################################
