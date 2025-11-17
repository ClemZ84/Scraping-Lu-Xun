import requests
from bs4 import BeautifulSoup
import os
import re
import time
import random

# --- 配置区域 ---
HEADERS = {
    "User-Agent": "" #配置user-agent
}

# 书信和日记ID范围 (根据实际情况修改)
SHUXIN_IDS = range(2913, 4355) #书信
RIJI_IDS = range(4395, 4677) #日记

# 使用 os.path.join 或原始字符串 r"" 避免路径转义问题
BASE_DIR = r"" #配置输出目录
SHUXIN_DIR = os.path.join(BASE_DIR, "shuxin") #配置书信输出目录
RIJI_DIR = os.path.join(BASE_DIR, "riji") #配置日记输出目录


# --- 通用工具函数 ---

def fetch_html(url, retry=3):
    """
    通用爬取函数：包含随机等待和重试机制
    """
    for i in range(retry):
        try:
            # 反爬虫检测随机等待
            sleep_time = random.uniform(0, 3) #设置随即等待时间，目前是0~3秒
            print(f"[{i + 1}/{retry}] 防反爬虫检测，随机等待 {sleep_time:.2f}秒后请求: {url}")
            time.sleep(sleep_time)

            response = requests.get(url, headers=HEADERS, timeout=10)  # 设置超时时间
            if response.status_code == 200:
                return response.text
            else:
                print(f"请求失败，状态码: {response.status_code}")
        except requests.RequestException as e:
            print(f"网络请求出现错误: {e}")

    return None  # 重试都失败后返回 None


def save_to_file(directory, filename, content):
    """通用保存文件函数"""
    if not os.path.exists(directory):
        os.makedirs(directory)

    # 清洗文件名中可能的非法字符
    safe_filename = re.sub(r'[\\/:*?"<>|]', '_', filename)
    full_path = os.path.join(directory, f"{safe_filename}.txt")

    try:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ 保存成功: {filename}.txt")
    except Exception as e:
        print(f"❌ 保存失败 {filename}: {e}")


# --- 核心逻辑 ---

def process_shuxin():
    print("=== 开始处理书信 ===")
    for id in SHUXIN_IDS:
        url = f"http://www.luxunmuseum.com.cn/cx/content.php?id={id}"

        # 1. 爬取
        html = fetch_html(url)
        if not html: continue  # 如果爬取失败，跳过当前ID

        # 2. 解析
        soup = BeautifulSoup(html, "html.parser")

        # 提取标题
        p_tag = soup.find("p", attrs={"align": "CENTER"})
        if not p_tag:
            print(f"跳过 ID {id}: 未找到标题")
            continue

        original_title = p_tag.string.strip().replace(" ", "")

        # 正则格式化标题
        match = re.match(r'^(\d{4})(\d{2})(\d{2})致(.+)$', original_title)
        if match:
            year, month, day, person = match.groups()
            final_title = f"{year}.{month}.{day}_{person}"
        else:
            final_title = original_title

        # 提取正文
        body_list = soup.find_all("blockquote")
        clean_body = [t.get_text(strip=True).replace('\u3000', '') for t in body_list]
        final_body = "\n".join(clean_body)

        # 3. 保存
        save_to_file(SHUXIN_DIR, final_title, final_body)


def process_riji():
    print("\n=== 开始处理日记 ===")

    current_year = 1912
    seen_december = False

    month_map = {
        "正月": "01", "一月": "01", "二月": "02", "三月": "03",
        "四月": "04", "五月": "05", "六月": "06", "七月": "07",
        "八月": "08", "九月": "09", "十月": "10", "十一月": "11", "十二月": "12"
    }

    for id in RIJI_IDS:
        url = f"http://www.luxunmuseum.com.cn/cx/content.php?id={id}&tid=3"

        # 1. 爬取
        html = fetch_html(url)
        if not html: continue

        # 2. 解析
        soup = BeautifulSoup(html, "html.parser")
        content_div = soup.find("div", attrs={"class": "ctcontent"})

        if not content_div:
            print(f"跳过 ID {id}: 未找到日记内容")
            continue

        full_text = content_div.get_text(separator="\n", strip=True)
        parts = full_text.split("\n")

        # 标题处理
        raw_month_title = parts[0].strip().replace(" ", "")

        # --- 年份判断 ---
        if "正月" in raw_month_title and seen_december:
            current_year += 1
            seen_december = False
        if "十二月" in raw_month_title:
            seen_december = True
        # -------------------------------

        # 映射月份数字
        month_num = month_map.get(raw_month_title, raw_month_title)
        final_title = f"{current_year}.{month_num}"

        # 正文处理
        final_body = "\n".join(parts[1:])

        # 保存
        save_to_file(RIJI_DIR, final_title, final_body)


# --- 主程序入口 ---
if __name__ == "__main__":
    # 检查输出目录
    if not os.path.exists(SHUXIN_DIR): os.makedirs(SHUXIN_DIR)
    if not os.path.exists(RIJI_DIR): os.makedirs(RIJI_DIR)

    # 运行任务
    process_shuxin()
    process_riji()
    print("\n全部任务完成！")