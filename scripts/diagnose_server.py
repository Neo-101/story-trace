import socket
import sys
import time
import urllib.request
import urllib.error
import json

def check_port(host, port):
    """检查端口是否开放"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

def check_api(url):
    """检查 API 是否响应"""
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print(f"✅ API 请求成功: {url}")
                data = json.loads(response.read().decode())
                print(f"   返回数据条数: {len(data)}")
                return True
            else:
                print(f"⚠️ API 返回状态码: {response.status}")
                return False
    except urllib.error.URLError as e:
        print(f"❌ API 请求失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")
        return False

def main():
    print("=== StoryTrace 后端诊断工具 ===")
    
    # 从 .env 读取端口
    import os
    env_port = "8000"
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if line.strip().startswith("API_PORT="):
                    env_port = line.split("=")[1].strip()
                    break
    
    port = int(env_port)
    host = "127.0.0.1" 
    
    print(f"\n1. 检查当前配置端口 {host}:{port} ...")
    if check_port(host, port):
        print(f"✅ 端口 {port} 已开放")
        check_api(f"http://{host}:{port}/api/novels")
    else:
        print(f"❌ 端口 {port} 未开放")
        
    print("\n------------------------------------------------")
    print("如果端口未开放，请确保你已经运行了: python app/main.py serve")

if __name__ == "__main__":
    main()
