import sys
import os

# 将项目根目录添加到 sys.path，确保可以导入 app, core, data_protocol
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import main

if __name__ == '__main__':
    main()
