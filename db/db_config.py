# MySQL连接设置
import pymysql

conn = pymysql.connect(
    host='10.7.100.245',
    user='root',
    password='gempoll',
    database="gempoll_tips",
    port=3306,
    charset='utf8mb4',
)

