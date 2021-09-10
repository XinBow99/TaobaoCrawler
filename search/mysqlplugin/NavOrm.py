from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column  # 元素/主key
from sqlalchemy import exists, update
from sqlalchemy import and_
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
DBInfo  = f"mysql+pymysql://{yamlData['userName']}:{yamlData['userPwd']}@{yamlData['ip']}/{yamlData['databaseName']}?charset=utf8mb4"
DBLink  = create_engine(DBInfo, poolclass=NullPool)
Base    = declarative_base()

print("[NavOrm]模組載入成功！")

class Navs(Base):
    __tablename__           = yamlData['navTable']
    __table_args__          = {"mysql_charset": "utf8"}
    search_key              = Column(TEXT, nullable=True)
    brand                   = Column(TEXT, primary_key=True)
    ppath                   = Column(TEXT, nullable=True)
    createAt                = Column(DATETIME)
    updateAt                = Column(DATETIME)

    def __init__(self, search_key: str, brand: str, ppath: str):
        """Navs寫入之參數

        Args:
            search_key (str): 產品名稱
            brand (str)     : 廠牌名稱
            ppath (str)     : 廠牌之金鑰
        """
        self.search_key     = search_key
        self.brand          = brand
        self.ppath          = ppath
        self.createAt       = datetime.datetime.now()


class Pagers(Base):
    __tablename__           = yamlData['pagerTable']
    __table_args__          = {"mysql_charset": "utf8"}
    _id                     = Column(INTEGER, primary_key=True)
    brand                   = Column(TEXT)
    pageSize                = Column(INTEGER)
    totalPage               = Column(INTEGER)
    currentPage             = Column(INTEGER)
    totalCount              = Column(INTEGER)
    createAt                = Column(DATETIME)

    def __init__(self, brand: str, pageSize: int, totalPage: int, currentPage: int, totalCount: int):
        """寫入Pagers資料表

        Args:
            brand (str)         : 廠牌名稱
            pageSize (int)      : 有多少樣產品
            totalPage (int)     : 共有幾頁
            currentPage (int)   : 目前頁數
            totalCount (int)    : 所有產品數量
        """
        self.brand          = brand
        self.pageSize       = pageSize
        self.totalPage      = totalPage
        self.currentPage    = currentPage
        self.totalCount     = totalCount
        self.createAt       = datetime.datetime.now()

class Items(Base):
    __tablename__           = yamlData['itemTable']
    __table_args__          = {"mysql_charset": "utf8"}
    _id                     = Column(INTEGER, primary_key=True)
    search_key              = Column(VARCHAR)
    brand                   = Column(VARCHAR)
    nid	                    = Column(VARCHAR)
    title	                = Column(VARCHAR)
    raw_title	            = Column(VARCHAR)
    detail_url	            = Column(VARCHAR)
    view_price	            = Column(FLOAT)
    view_fee	            = Column(FLOAT)
    view_sales	            = Column(VARCHAR)
    comment_count           = Column(VARCHAR)
    user_id	                = Column(VARCHAR)
    nick	                = Column(VARCHAR)
    comment_url	            = Column(VARCHAR)
    
    def __init__(self, search_key:str, brand:str, auctionOjb: dict) -> None:
        """寫入單一產品至資料庫

        Args:
            search_key (str) : 產品分類之金鑰
            brand (str)      : 品牌名稱
            auctionOjb (dict): 傳入產品的結構
        """
        def checkDict(obj,key):
            """確認key是否在dict內

            Args:
                obj (dict)): 判斷的dict物件
                key (str): 判斷的key

            Returns:
                str: 一定會回傳Str
            """
            if key in obj:
                return obj[key]
            return "Null"
        self.search_key     = search_key
        self.brand          = brand
        self.nid	        = checkDict(auctionOjb, "nid")
        self.title	        = checkDict(auctionOjb, "title")
        self.raw_title	    = checkDict(auctionOjb, "raw_title")
        self.detail_url	    = checkDict(auctionOjb, "detail_url")
        self.view_price	    = Float(checkDict(auctionOjb, "view_price"))
        self.view_fee	    = Float(checkDict(auctionOjb, "view_fee"))
        self.view_sales	    = checkDict(auctionOjb, "view_sales")
        self.comment_count  = checkDict(auctionOjb, "comment_count")
        self.user_id	    = checkDict(auctionOjb, "user_id")
        self.nick	        = checkDict(auctionOjb, "nick")
        self.comment_url	= checkDict(auctionOjb, "comment_url")

class Verifys(Base):
    __tablename__           = yamlData['verifyTable']
    __table_args__          = {"mysql_charset": "utf8"}
    _id                     = Column(INTEGER, primary_key=True)
    status                  = Column(INTEGER)
    msg                     = Column(TEXT)
    createAt                = Column(DATETIME)

    def __init__(self, status: int, msg: str):
        """存取遇到滑塊之紀錄ORM

        Args:
            status (int): 寫入之狀態，以int作為表示
            msg (str)   : 單純作為紀錄訊息用
        """
        self.status         = status
        self.msg            = msg
        self.createAt       = datetime.datetime.now()
