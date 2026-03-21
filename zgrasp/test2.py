
# tBLW_d6j5370852cal848ir80

import fitz  # PyMuPDF
import requests
import random
import json
import hashlib
import time
import os

# =================配置区域=================
# 请替换为你自己的百度翻译 API 信息
BAIDU_APP_ID = '122122'
BAIDU_SECRET_KEY = 'tBLW_d6j5370852cal848ir80'

# 中文字体路径 (必须设置，否则翻译后的中文无法显示)
# Windows 常见路径: "C:/Windows/Fonts/simsun.ttc" (宋体) 或 "msyh.ttf"
# Linux/Mac 请指定有效的 .ttf/.otf 文件路径
FONT_PATH = "C:/Windows/Fonts/simsun.ttc"
FONT_NAME = "song"  # 给字体起个别名


# =========================================

class BaiduTranslator:
    def __init__(self, app_id, secret_key):
        self.app_id = app_id
        self.secret_key = secret_key
        self.api_url = "http://api.fanyi.baidu.com/api/trans/vip/translate"

    def translate(self, text, from_lang='en', to_lang='zh'):
        if not text or not text.strip():
            return ""

        salt = random.randint(32768, 65536)
        sign = self.app_id + text + str(salt) + self.secret_key
        sign = hashlib.md5(sign.encode()).hexdigest()

        params = {
            'q': text,
            'from': from_lang,
            'to': to_lang,
            'appid': self.app_id,
            'salt': salt,
            'sign': sign
        }

        try:
            response = requests.get(self.api_url, params=params)
            result = response.json()
            if "trans_result" in result:
                # 拼接多段翻译结果
                return '\n'.join([item['dst'] for item in result['trans_result']])
            else:
                print(f"翻译API错误: {result}")
                return text  # 出错返回原文
        except Exception as e:
            print(f"请求异常: {e}")
            return text


def is_formula_or_code(text):
    """
    简单的启发式判断：如果文本块包含大量非字母字符或过短，可能是公式或标号，建议跳过翻译。
    """
    if len(text.strip()) < 3:  # 太短的如页码
        return True
    # 计算特殊符号比例 (简单判断，防止破坏复杂公式)
    symbol_count = sum(1 for char in text if not char.isalnum() and char not in ' ,.():-')
    if symbol_count / len(text) > 0.4:
        return True
    return False


def translate_pdf_keep_layout(input_path, output_path):
    print(f"正在处理文件: {input_path}")

    # 打开 PDF
    doc = fitz.open(input_path)
    translator = BaiduTranslator(BAIDU_APP_ID, BAIDU_SECRET_KEY)

    # 注册中文字体
    try:
        fitz.Font(fontname=FONT_NAME, fontfile=FONT_PATH)
    except Exception as e:
        print(f"字体加载失败，请检查 FONT_PATH: {e}")
        return

    total_pages = len(doc)

    for page_num, page in enumerate(doc):
        print(f"正在处理第 {page_num + 1}/{total_pages} 页...")

        # 获取页面上的所有文本块 (blocks)
        # get_text("blocks") 返回格式: (x0, y0, x1, y1, "text", block_no, block_type)
        blocks = page.get_text("blocks")

        # 收集需要绘制的翻译任务，避免在迭代中修改页面导致坐标错乱
        replacements = []

        for block in blocks:
            x0, y0, x1, y1, text, block_no, block_type = block

            # block_type=0 是文本，1 是图片。我们只处理文本。
            if block_type != 0:
                continue

            # 去除换行符，合并成一段话进行翻译
            clean_text = text.replace('\n', ' ').strip()

            # 过滤掉可能是公式或页眉页脚的内容 (可选)
            if is_formula_or_code(clean_text):
                continue

            # 调用翻译
            # 注意：免费版API有QPS限制，这里加个微小延时
            time.sleep(0.1)
            trans_text = translator.translate(clean_text)

            if trans_text and trans_text != clean_text:
                replacements.append({
                    "rect": fitz.Rect(x0, y0, x1, y1),
                    "text": trans_text,
                    "original": text
                })

        # 开始在页面上应用修改
        shape = page.new_shape()

        for item in replacements:
            rect = item["rect"]
            trans_text = item["text"]

            # 1. 用白色矩形覆盖原文 (相当于涂改液)
            # 稍微扩大一点覆盖区域，确保盖住原来的英文字母
            cover_rect = fitz.Rect(rect.x0 - 2, rect.y0 - 2, rect.x1 + 2, rect.y1 + 2)
            shape.draw_rect(cover_rect)
            shape.finish(color=(1, 1, 1), fill=(1, 1, 1))  # 白色填充，白色边框
            shape.commit()

            # 2. 写入中文
            # insert_textbox 会自动换行以适应矩形框
            # 我们通过 fontsize 动态调整大小，或者设定一个固定的较小字号（如9或10）
            try:
                # 尝试写入，如果文字太多，textbox可能会截断，这里简化处理
                # fontsize 可以设为自动，或者根据原文框高度估算
                page.insert_textbox(
                    rect,
                    trans_text,
                    fontname=FONT_NAME,
                    fontsize=9,  # 设置基础字号
                    align=0  # 左对齐
                )
            except Exception as e:
                print(f"写入文字出错: {e}")

    # 保存文件
    doc.save(output_path)
    print(f"翻译完成！已保存至: {output_path}")


# =================使用示例=================
if __name__ == "__main__":
    # 假设你的原始文件名为 report.pdf
    input_file = "report.pdf"
    output_file = "report_cn.pdf"

    # 确保文件存在
    if not os.path.exists(input_file):
        # 为了演示，这里如果没有文件会报错
        print(f"错误：找不到文件 {input_file}")
    else:
        translate_pdf_keep_layout(input_file, output_file)
