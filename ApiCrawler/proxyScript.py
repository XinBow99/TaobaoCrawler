from mitmproxy import http
from mysqlplugin import NavOrm
import re
# Set database
NavDBSession = NavOrm.sessionmaker(bind=NavOrm.DBLink)
navDBSession = NavDBSession()


def request(flow: http.HTTPFlow) -> None:
    # 將請求新增了一個查詢參數
    if 'https://rate.tmall.com/list_detail_rate.htm' in flow.request.url:
        print("[Proxy]->獲取Url，寫入資料庫")
        # 存入 cookie pool
        # 判斷目標存在不
        cookieValue = flow.request.headers['cookie']
        print(cookieValue)
        itemIdRe = re.findall(r'itemId\=(.*?)\&', cookieValue)
        if len(itemIdRe) > 0:
            exists = navDBSession.query(
                # 查詢CookieGet的資料表
                NavOrm.CookieGet
            ).filter_by(
                # 用id
                nid=itemIdRe[0]
            ).update(
                # 更新ppath這個參數
                {
                    "cookieValue": cookieValue,
                    "status": 0
                }
            )
            if not exists:
                # 使用添加
                navDBSession.add(
                    NavOrm.CookieGet(
                        nid=itemIdRe[0],
                        url=flow.request.url,
                        cookieValue=cookieValue,
                        status=0
                    )
                )


def response(flow: http.HTTPFlow) -> None:
    # 將響應頭中新增了一個自定義頭字段
    flow.response.headers["mit"] = "-----------------"
