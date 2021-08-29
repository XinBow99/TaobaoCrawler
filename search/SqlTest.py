from mysqlplugin import NavOrm
NavDBSession = NavOrm.sessionmaker(bind=NavOrm.DBLink)
navDBSession = NavDBSession()

navDBSession.query(
    # 查詢Navs的資料表
    NavOrm.Navs
).filter_by(
    # 用廠牌進行filter
    brand=""
)
