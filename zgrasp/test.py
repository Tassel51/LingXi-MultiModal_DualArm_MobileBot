import os
import fitz  # PyMuPDF
from tkinter import filedialog, Tk, messagebox


def pdf_to_images_fitz():
    # 1. 初始化 Tkinter 并隐藏主窗口
    root = Tk()
    root.withdraw()

    # 2. 弹出文件选择对话框
    file_path = filedialog.askopenfilename(
        title="请选择要转换的 PDF 文件",
        filetypes=[("PDF files", "*.pdf")]
    )

    if not file_path:
        print("未选择任何文件")
        return

    try:
        # 3. 设置输出目录
        pdf_dir = os.path.dirname(file_path)
        pdf_name = os.path.splitext(os.path.basename(file_path))[0]
        output_folder = os.path.join(pdf_dir, f"{pdf_name}_images")

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # 4. 打开 PDF 文件
        pdf_document = fitz.open(file_path)

        print(f"正在转换: {pdf_name}, 共 {len(pdf_document)} 页")

        # 5. 逐页转换
        for page_index in range(len(pdf_document)):
            page = pdf_document[page_index]

            # 设置缩放比例，提高清晰度 (2.0 表示放大 2 倍，约等同于 144 DPI)
            # 如果需要更高清，可以改为 3.0 或 4.0
            zoom = 4.0
            mat = fitz.Matrix(zoom, zoom)

            # 渲染页面为位图
            pix = page.get_pixmap(matrix=mat)

            # 保存图片
            image_path = os.path.join(output_folder, f"page_{page_index + 1}.png")
            pix.save(image_path)
            print(f"已保存: {image_path}")

        pdf_document.close()
        messagebox.showinfo("成功", f"转换完成！图片保存在：\n{output_folder}")

    except Exception as e:
        messagebox.showerror("错误", f"转换失败：{str(e)}")
    finally:
        root.destroy()


if __name__ == "__main__":
    pdf_to_images_fitz()