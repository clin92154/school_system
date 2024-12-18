import os

def print_directory_tree(start_path, prefix=""):
    # 列出目前路徑下的所有項目（檔案與資料夾）
    items = sorted(os.listdir(start_path))
    # 過濾隱藏檔案與資料夾（如 .git 等），可視需要移除
    items = [item for item in items if not item.startswith('.')]

    # 使用迴圈列印出當前層級的項目
    for index, item in enumerate(items):
        path = os.path.join(start_path, item)
        marker = "└──" if index == len(items) - 1 else "├──"

        if os.path.isdir(path):
            print(f"{prefix}{marker} {item}/")
            # 遞迴處理子資料夾
            new_prefix = prefix + ("    " if index == len(items) - 1 else "│   ")
            print_directory_tree(path, new_prefix)
        else:
            print(f"{prefix}{marker} {item}")

if __name__ == "__main__":
    # 假設你的Django專案在目前目錄下
    project_root = "."  # 你也可輸入實際的專案路徑
    print_directory_tree(project_root)
