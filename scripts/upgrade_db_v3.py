import sqlite3
import os

def upgrade_database():
    db_path = "storytrace.db"
    
    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在，新创建的数据库将自动包含新表。")
        return

    print(f"正在检查数据库 {db_path} ...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if plotsegment table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='plotsegment'")
        if not cursor.fetchone():
            print("正在创建 PlotSegment 表...")
            # Create table manually (matching the SQLModel definition)
            cursor.execute("""
            CREATE TABLE plotsegment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                volume_title VARCHAR,
                title VARCHAR NOT NULL,
                synopsis TEXT,
                start_chapter_index INTEGER NOT NULL,
                end_chapter_index INTEGER NOT NULL,
                avg_intensity FLOAT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES analysisrun (id)
            )
            """)
            cursor.execute("CREATE INDEX ix_plotsegment_run_id ON plotsegment (run_id)")
            print("✅ PlotSegment 表创建成功。")
        else:
            print("PlotSegment 表已存在，跳过。")

        # Check if plotarc table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='plotarc'")
        if not cursor.fetchone():
            print("正在创建 PlotArc 表...")
            cursor.execute("""
            CREATE TABLE plotarc (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                volume_title VARCHAR,
                title VARCHAR NOT NULL,
                synopsis TEXT,
                start_chapter_index INTEGER NOT NULL,
                end_chapter_index INTEGER NOT NULL,
                FOREIGN KEY (run_id) REFERENCES analysisrun (id)
            )
            """)
            cursor.execute("CREATE INDEX ix_plotarc_run_id ON plotarc (run_id)")
            print("✅ PlotArc 表创建成功。")
        else:
            print("PlotArc 表已存在，跳过。")
            
        conn.commit()
        
    except Exception as e:
        print(f"升级失败: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    upgrade_database()