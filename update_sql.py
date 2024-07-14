import sqlite3
import os

# 获取环境变量
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
db_path = os.path.join(BASE_DIR, 'db', 'weibo.db')

def update_database():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 示例更新语句，可以根据需要修改
    sql = "UPDATE weibo SET summary = ? WHERE link = ?"
    cursor.execute(sql, ('Updated summary', 'http://example.com'))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    update_database()
