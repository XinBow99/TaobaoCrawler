# 淘寶爬蟲-資料庫處理

## 目錄

- [關於](#about)
- [基本架構](#getting_started)
- [使用套件](#usage)

## 關於 <a name = "about"></a>

該資料夾用於存放資料庫處理之相關程式
- 資料庫架設
- sqlalchemy撰寫
    - https://s.taobao.com/search 
    - items: https://detail.tmall.com/
    - comment: https://rate.tmall.com/list_detail_rate.htm


## 基本架構 <a name = "getting_started"></a>

本資料庫將淘寶分為兩大部分及三小節
- PC
    - 商品主頁面
    - 單一商品顯示頁面
    - 單一商品留言頁面
- Mobile App
    - 商品主頁面
    - 單一商品顯示頁面
    - 單一商品留言頁面

### PC網頁分析

商品主頁面之各項商品變數，`g_page_config`僅會在`https://s.taobao.com/search?`出現一次，並在切換頁數時進行變更，故為1~100頁獨立變數。

#### s.taobao.com之API分析
REST Api url: `https://s.taobao.com/search`
method: `GET` 

| Parameters  | Required | Default value | Mark                              |
|:----------- |:-------- |:------------- |:--------------------------------- |
| q           | ✅       | 尿褲          | 搜尋產品名稱                      |
| bcoffset    |          | 1             | 於第二頁之參數                    |
| ntoffset    |          | 1             | 於第二頁之參數                    |
| p4ppushleft |          | 2,48          | 於第二頁之參數                    |
| s           |          | 44            | 於第二頁之參數，往後推了多少商品  |
| tab         |          | mall          | Should be mall                    |
| sort        |          |               | Should be sale-desc(销量从高到低) |
| ppath       |          |               | 分類器                            |

Page1
```json=
//q=%E5%B0%BF%E8%A4%B2&bcoffset=4&ntoffset=4&p4ppushleft=2%2C48&s=0
{
    "q": "尿褲",
    "bcoffset": 4,
    "ntoffset": 4,
    "p4ppushleft": "2,48"
    "s": 0
}
```
Page2
```json=
//q=%E5%B0%BF%E8%A4%B2&bcoffset=1&ntoffset=1&p4ppushleft=2%2C48&s=44
{
    "q": "尿褲",
    "bcoffset": 1,
    "ntoffset": 1,
    "p4ppushleft": "2,48",
    "s": 44
}
```
Summary(可行)
- pageNum - 1
    - Assume `p` as `pageNum - 1`
    - And `s` = 44 * p

https://s.taobao.com/search?q=%E5%B0%BF%E8%A4%B2&s=`s`&tab=`mall`&sort=`sale-desc`&ppath=`Classifier`#

#### g_page_config分析

#### `Level1️⃣`
| Parameters | Mark                          |
| ---------- |:----------------------------- |
| pageName   | 呼叫頁面之名稱                |
| mods       | 網頁各項Component之初始化參數 |
| mainInfo   | 呼叫各項產品之URL參數         |
| feature    | 不清楚                        |

`Level2️⃣ *mods` 
| Parameters | Mark                   |
| ---------- |:---------------------- |
| itemlist   | 各項產品資訊           |
| related    | 修正搜尋｜您是不是想找 |
| pager      | 目前頁面資訊           |
| nav        | 品牌                   |

#### `Level3️⃣` 
`*itemlist->data`
| Parameters | Mark             |
| ---------- |:---------------- |
| auctions   | 該頁面之所有產品 |

`*related->data`
| Parameters | Mark     |
| ---------- |:-------- |
| words      | 修正搜尋 |

`*pager->data`
| Parameters  | Mark              |
| ----------- |:----------------- |
| pageSize    | 頁面產品數量      |
| totalPage   | 共有多少頁        |
| currentPage | 目前在第幾頁      |
| totalCount  | 關於q有多少樣產品 |

`*nav->data`
| Parameters | Mark           |
| ---------- |:-------------- |
| common     | 頁籤顯示之文字 |

#### `Level4️⃣` 
`*auctions->[0]`
| Parameters    | Mark               |
| ------------- |:------------------ |
| nid           | 產品編號           |
| category      | 產品分類，不清楚   |
| title         | 產品名稱，有編碼   |
| raw_title     | 產品編號，正確名稱 |
| detail_url    | 詳細頁面           |
| view_price    | 產品價格           |
| view_fee      | 產品運費           |
| view_sales    | 購買人數           |
| comment_count | 評論數量           |
| user_id       | 刊登者             |
| nick          | 刊登者名稱         |
| comment_url   | 評論連結           |

`*words->[0]`
| Parameters | Mark           |
| ---------- |:-------------- |
| text       | 修正之搜尋名稱 |

`*common->[0]`
| Parameters | Mark    |
| ---------- |:------- |
| text       | nav名稱 |
| sub        | 分類    |

#### `Level5️⃣` 
`*sub->[0]`
| Parameters | Mark                                          |
| ---------- |:--------------------------------------------- |
| text       | 廠牌名稱                                      |
| value      | Classifier |

### 爬取該總產品頁面之流程
1. Get
    * https://s.taobao.com/search?q=%E5%B0%BF%E8%A4%B2&tab=mall&sort=sale-desc
    * 取得g_page_config
    * 寫入mods->nav->data->common->sub
    * 注意`"text":"品牌"`
2. 以寫入之ppath value進行爬取
3. Get
    * https://s.taobao.com/search?q=%E5%B0%BF%E8%A4%B2&tab=mall&sort=sale-desc&ppath=20000%3A1973598548
    * 取得g_page_config
    * 判斷total_page
4. 如果TP>1，添加s

## Usage <a name = "usage"></a>

Add notes about how to use the system.
