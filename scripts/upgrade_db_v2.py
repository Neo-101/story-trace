import sqlite3
import os

def upgrade_database():
    db_path = "storytrace.db"
    
    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在，无需升级。新创建的数据库将自动包含新字段。")
        return

    print(f"正在检查数据库 {db_path} ...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. 检查 chapter 表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chapter'")
        if not cursor.fetchone():
            print("Chapter 表不存在，跳过。")
            return

        # 2. 获取现有的列
        cursor.execute("PRAGMA table_info(chapter)")
        columns = [info[1] for info in cursor.fetchall()]
        
        # 3. 检查并添加 volume_title
        if 'volume_title' not in columns:
            print("检测到缺失字段 'volume_title'，正在添加...")
            cursor.execute("ALTER TABLE chapter ADD COLUMN volume_title TEXT")
            print("✅ 'volume_title' 字段添加成功。")
        else:
            print("字段 'volume_title' 已存在。")

        conn.commit()
        print("数据库结构升级完成！您可以直接运行程序而无需重新导入小说。")
        
    except Exception as e:
        print(f"升级失败: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    upgrade_database()
