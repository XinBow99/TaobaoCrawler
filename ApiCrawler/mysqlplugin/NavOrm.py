from typing import Dict
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column  # 元素/主key
# 創接口/建立關系relationship(table.ID)
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy import create_engine
# sqlalchemy 查詢前連結，结束後，調用 session.close() 關閉連結
from sqlalchemy.pool import NullPool
from sqlalchemy.sql.sqltypes import DATETIME, INTEGER, TEXT, VARCHAR, FLOAT, Float
import yaml
import datetime

yamlData = None
with open("./config/mysql.yaml", "r", encoding="utf-8") as stream:
    yamlData = yaml.load(stream, Loader=yaml.FullLoader)
    stream.close()
yamlData = yamlData['Database']


# DB的資訊
DBInfo = f"mysql+pymysql://{yamlData['userName']}:{yamlData['userPwd']}@{yamlData['ip']}/{yamlData['databaseName']}?charset=utf8mb4"
DBLink = create_engine(DBInfo, poolclass=NullPool)
Base = declarative_base()


def checkDict(obj, key):
    """確認key是否在dict內

    Args:
        obj (dict)): 判斷的dict物件
        key (str): 判斷的key

    Returns:
        str: 一定會回傳Str
    """
    if not obj:
        return "0"
    if key in obj:
        return obj[key]
    return "0"


class Items(Base):
    __tablename__ = yamlData['itemTable']
    __table_args__ = {"mysql_charset": "utf8"}
    _id = Column(INTEGER, primary_key=True)
    search_key = Column(VARCHAR)
    brand = Column(VARCHAR)
    nid = Column(VARCHAR)
    title = Column(VARCHAR)
    raw_title = Column(VARCHAR)
    detail_url = Column(VARCHAR)
    view_price = Column(FLOAT)
    view_fee = Column(FLOAT)
    view_sales = Column(VARCHAR)
    comment_count = Column(VARCHAR)
    user_id = Column(VARCHAR)
    nick = Column(VARCHAR)
    comment_url = Column(VARCHAR)
    status = Column(INTEGER)
    createAt = Column(DATETIME)

    def __init__(self, search_key: str, brand: str, auctionOjb: dict) -> None:
        """寫入單一產品至資料庫

        Args:
            search_key (str) : 產品分類之金鑰
            brand (str)      : 品牌名稱
            auctionOjb (dict): 傳入產品的結構
        """
        self.search_key = search_key
        self.brand = brand
        self.nid = checkDict(auctionOjb, "nid")
        self.title = checkDict(auctionOjb, "title")
        self.raw_title = checkDict(auctionOjb, "raw_title")
        self.detail_url = checkDict(auctionOjb, "detail_url")
        self.view_price = (checkDict(auctionOjb, "view_price"))
        self.view_fee = (checkDict(auctionOjb, "view_fee"))
        self.view_sales = checkDict(auctionOjb, "view_sales")
        self.comment_count = checkDict(auctionOjb, "comment_count")
        self.user_id = checkDict(auctionOjb, "user_id")
        self.nick = checkDict(auctionOjb, "nick")
        self.comment_url = checkDict(auctionOjb, "comment_url")
        self.createAt = datetime.datetime.now()


class Verifys(Base):
    __tablename__ = yamlData['verifyTable']
    __table_args__ = {"mysql_charset": "utf8"}
    _id = Column(INTEGER, primary_key=True)
    status = Column(INTEGER)
    msg = Column(TEXT)
    createAt = Column(DATETIME)

    def __init__(self, status: int, msg: str):
        """存取遇到滑塊之紀錄ORM

        Args:
            status (int): 寫入之狀態，以int作為表示
            msg (str)   : 單純作為紀錄訊息用
        """
        self.status = status
        self.msg = msg
        self.createAt = datetime.datetime.now()


class Comments(Base):
    __tablename__ = yamlData['commentTable']
    __table_args__ = {"mysql_charset": "utf8"}
    _id = Column(INTEGER, primary_key=True)
    nid = Column(INTEGER)
    cid = Column(INTEGER)
    displayUserNick = Column(VARCHAR)
    items           = Column(INTEGER)
    sellerId        = Column(INTEGER)
    lastPage        = Column(INTEGER)
    page            = Column(INTEGER)
    picNum          = Column(INTEGER)
    total           = Column(INTEGER)
    used            = Column(INTEGER)
    currentMilles   = Column(INTEGER)
    intervalMilles  = Column(INTEGER)
    # append comment
    apc_commentTime = Column(DATETIME)
    apc_content     = Column(VARCHAR)
    apc_reply       = Column(VARCHAR)
    apc_days        = Column(INTEGER)
    # Normal comment
    rateContent     = Column(VARCHAR)
    rateDate        = Column(DATETIME)
    createAt        = Column(DATETIME)

    def __init__(self, nid: int, paginator: dict, rateCount: dict,rateDanceInfo: dict,rateObjects: dict) -> None:
        """[儲存留言資訊所用]

        Args:
            nid (int): [產品的id]
            paginator (dict): [該留言的頁數數據]
            rateCount (dict): [留言數量]
            rateDanceInfo (dict): [留言追蹤]
            rateObjects (dict): [rateList內的東西]
        """
        self.nid = nid
        # paginator
        self.items          = checkDict(paginator, "items")  
        self.lastPage       = checkDict(paginator, "lastPage")
        self.page           = checkDict(paginator, "page")
        # rateCount
        self.picNum         = checkDict(rateCount, "picNum")
        self.total          = checkDict(rateCount, "total")
        self.used           = checkDict(rateCount, "used")
        # rateDanceInfo
        self.currentMilles  = checkDict(rateDanceInfo, "currentMilles")
        self.intervalMilles = checkDict(rateDanceInfo, "intervalMilles")
        # rateObjects
        # append comment 追評
        self.apc_commentTime= checkDict(checkDict(rateObjects, "appendComment"), "commentTime")
        self.apc_content    = checkDict(checkDict(rateObjects, "appendComment"), "content")
        self.apc_reply      = checkDict(checkDict(rateObjects, "appendComment"), "reply")
        self.apc_days       = checkDict(checkDict(rateObjects, "appendComment"), "days")
        # Normal comment 原評
        self.sellerId       = checkDict(rateObjects, "sellerId")
        self.displayUserNick= checkDict(rateObjects, "displayUserNick")
        self.cid            = checkDict(rateObjects, "id")
        self.rateContent    = checkDict(rateObjects, "rateContent")
        self.rateDate       = checkDict(rateObjects, "rateDate")
        self.createAt = datetime.datetime.now()


print("[NavOrm]模組載入成功！")
