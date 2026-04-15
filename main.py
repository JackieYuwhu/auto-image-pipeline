import os
import logging
from scripts.generator import generate_batch_images  # 假设你把生成逻辑封装成了函数
from scripts.processor import process_images        # 假设你把处理逻辑封装成了函数
from scripts.uploader import upload_to_oss          # 假设你把上传逻辑封装成了函数

# 1. 配置日志，让过程可视化
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    logging.info("🚀 AI 图像自动化处理流水线启动...")

    # 第一步：准备阶段 (Configuration/Setup)
    # 检查 API Key 是否存在
    if not os.getenv("DASHSCOPE_API_KEY") or not os.getenv("OPENAI_API_KEY"):
        logging.error(" 缺失 API Key，请检查环境变量配置！")
        return

    try:
        # 第二步：调用 AI 生成图片 (Generation)
        logging.info("🎨 正在调用 DashScope/OpenAI 批量生成图片...")
        raw_images_dir = generate_batch_images(prompt_count=10)

        # 第三步：图片后期处理 (Processing)
        logging.info("⚙️ 正在对图片进行自动化处理（裁剪/超分/增强）...")
        processed_images_dir = process_images(raw_images_dir)

        # 第四步：上传云端存储 (Storage)
        logging.info("☁️ 正在同步至阿里云 OSS...")
        upload_to_oss(processed_images_dir)

        logging.info("✅ 全流程处理完成！所有素材已就绪。")

    except Exception as e:
        logging.error(f"⚠️ 运行过程中出现错误: {e}")

if __name__ == "__main__":
    main()