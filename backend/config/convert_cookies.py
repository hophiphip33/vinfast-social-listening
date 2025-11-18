import json
from pathlib import Path

# Đường dẫn file JSON gốc và file đích dạng .txt
json_path = Path("backend/config/facebook_cookies.txt")  # file JSON bạn xuất từ trình duyệt
txt_path = Path("backend/config/facebook_cookies_parsed.txt")

def convert_json_to_txt(json_file, txt_file):
    with open(json_file, "r", encoding="utf-8") as f:
        cookies_json = json.load(f)

    # Chuyển mỗi cookie thành "name=value"
    cookie_line = "; ".join([f"{c['name']}={c['value']}" for c in cookies_json])

    # Ghi ra file .txt dạng dòng đơn
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write(cookie_line)

    print(f"✅ Đã chuyển thành công -> {txt_file}")
    print(f"👉 Nội dung: \n{cookie_line[:200]}...")

if __name__ == "__main__":
    convert_json_to_txt(json_path, txt_path)
