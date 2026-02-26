
import os

def update_env_port():
    env_path = ".env"
    if not os.path.exists(env_path):
        print("⚠️ .env file not found. Creating one with API_PORT=8001.")
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("API_PORT=8001\n")
        return

    print(f"✅ Found .env file. Checking API_PORT...")
    
    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    found = False
    for line in lines:
        if line.strip().startswith("API_PORT="):
            print(f"   - Updating existing API_PORT to 8001")
            new_lines.append("API_PORT=8001\n")
            found = True
        else:
            new_lines.append(line)
    
    if not found:
        print(f"   - Appending API_PORT=8001")
        if new_lines and not new_lines[-1].endswith('\n'):
            new_lines[-1] += '\n'
        new_lines.append("API_PORT=8001\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    
    print("🎉 .env updated successfully!")

if __name__ == "__main__":
    update_env_port()
