from mitmproxy import http


def request(flow: http.HTTPFlow) -> None:
    # 將請求新增了一個查詢參數
    if 'tmall' in flow.request.url:
        print(flow.request.headers['cookie'])


def response(flow: http.HTTPFlow) -> None:
    # 將響應頭中新增了一個自定義頭字段
    flow.response.headers["newheader"] = "foo"
    print(flow.response.text)
