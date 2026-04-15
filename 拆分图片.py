import os
import re
import time
from pathlib import Path
import requests
import dashscope
from dashscope import Application
import oss2  # 阿里云对象存储 SDK
import uuid

# ==========================================
# ⚙️ 全局配置 (请必须替换为你自己的真实信息)
# ==========================================
# 1. 百炼 API Key
dashscope.api_key = ""
# 2. 阿里云 OSS 配置
# 强烈建议在阿里云控制台创建一个专门的 Bucket，并将其读写权限设置为“公共读”
OSS_ACCESS_KEY_ID = ""
OSS_ACCESS_KEY_SECRET = ""
OSS_ENDPOINT = ""
OSS_BUCKET_NAME = ""

# 初始化 OSS 实例
auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)


# ==========================================
#  第 1 部分：你的百炼应用调用核心函数
# ==========================================
def upload_image_to_oss(local_path):
    """将本地图片上传到 OSS，返回公网 URL"""
    print(f"   ☁️  正在将图片上传至阿里云 OSS...")
    
    # 构造云端文件路径，加入了时间戳防止同名文件覆盖
    # 专门建立一个 cosplay_app_assets 目录来存放这些临时处理的资产图片
    object_name = f"cosplay_app_assets/{int(time.time())}_{local_path.name}"
    
    try:
        bucket.put_object_from_file(object_name, str(local_path))
        # 拼接公网 URL
        image_url = f"https://{OSS_BUCKET_NAME}.{OSS_ENDPOINT}/{object_name}"
        print(f"   🔗 OSS 上传成功: {image_url}")
        return image_url
    except Exception as e:
        raise Exception(f"OSS 上传失败: {e}")
    

def download_image(url, save_path):
    """
    根据给定的 URL 下载图片，并保存到本地绝对路径
    """
    print(f"   ⬇️ 正在从网络下载处理结果...")
    # stream=True 保证大图片也能平稳下载，不会撑爆内存
    response = requests.get(url, stream=True, timeout=30)
    
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
    else:
        raise Exception(f"图片下载失败，HTTP状态码: {response.status_code}")

def your_application_process_func(input_image_local_path, output_image_local_path):
    # 1. 先把本地图片传到云端 OSS，拿到公网 URL
    image_url = upload_image_to_oss(input_image_local_path)
    
    print(f"   🧠 正在请求专属百炼应用处理任务... ")
    APP_ID = '9e2f43042de441368ebe958b97010861' 
    
    # 2. 将工作流变量放入字典
    # 注意：如果你上一条采纳了我的 Plan B 建了自定义变量 my_image，这里就改成 'my_image': image_url
    workflow_params = {
        'my_image_url': image_url
    }
    
    # 发起调用：【终极修复】使用官方指定的 biz_params 传参！
    response = Application.call(
        app_id=APP_ID,
        prompt='提取图中的商品,生成的商品之间不要相互遮挡',  
        biz_params=workflow_params  # <--- 关键修复：必须用 biz_params！
    )
    
    if response.status_code == 200:
        print("   ✅ 应用处理完成！")
        result_text = response.output.text
        
        # 3. 提取返回的图片 URL
        url_match = re.search(r'https?://[^\s\)]+', result_text)
        if url_match:
            result_url = url_match.group(0)
            print(f"   ✨ 成功提取到结果链接: {result_url}")
            
            # 4. 下载保存回本地
            download_image(result_url, output_image_local_path)
        else:
            raise Exception(f"模型回复中没找到链接，原始回复: {result_text}")
    else:
        raise Exception(f"应用调用失败: {response.code} - {response.message}")
    
    


# ==========================================
# 🚀 第 2 部分：自动化流水线核心逻辑
# ==========================================
def automated_batch_pipeline_in_place(root_folder_path):
    base_dir = Path(root_folder_path)
    
    # 定义你认为的“照片”的后缀名
    valid_extensions = '.png'
    
    # 定义处理结果文件名的后缀，防止重复处理
    result_suffix = "_processed"

    success_count = 0
    error_count = 0
    skip_count = 0

    print(f"🚀 开始自动化处理流水线...")
    print(f"📂 根目录: {base_dir.resolve()}\n")

    # 递归查找大文件夹及其子文件夹下的所有照片
    for image_file_path in base_dir.rglob('*'):
        
        # 排除不是文件或者后缀不符的项目
        if not image_file_path.is_file() or image_file_path.suffix.lower() not in valid_extensions:
            continue

        # 排除已经是处理结果的照片 (根据文件名后缀)
        if result_suffix in image_file_path.stem:
            skip_count += 1
            continue

        # =======================================================
        # 🔑 路径重组逻辑：实现“结果放在原照片文件夹里” 🔑
        # =======================================================
        # image_file_path.parent: 拿到原照片的文件夹路径
        # image_file_path.stem:   拿到原照片的文件名(不带后缀，如 "photo01")
        # image_file_path.suffix: 拿到原照片的后缀(如 ".jpg")
        
        parent_folder = image_file_path.parent
        original_name = image_file_path.stem
        file_ext = image_file_path.suffix
        
        # 拼接出新的文件名，并生成完整的输出路径对象
        new_filename = f"{original_name}{result_suffix}{file_ext}"
        output_file_path = parent_folder / new_filename
        
        # 检查是否已经存在同名处理结果，如果存在则跳过（防止重复 API 调用）
        if output_file_path.exists():
            print(f"ℹ [跳过] {new_filename} 已存在.")
            skip_count += 1
            continue
            
        # =======================================================
        
        # 4. 执行核心处理逻辑，并加上错误捕获
        try:
            print(f"⏳ [处理中] 照片: {image_file_path.name}")
            print(f"📂 [将保存至]: {output_file_path.name}")

            #  真正调用处理函数 
            your_application_process_func(image_file_path, output_file_path)

            print(f"✅ [成功]\n")
            success_count += 1
            # 建议加上短暂休眠，防止并发请求过快触发阿里云的频率限制 (Rate Limit)
            time.sleep(1) 
            
        except Exception as e:
            print(f"❌ [失败] 处理 {image_file_path.name} 时发生错误: {e}\n")
            error_count += 1

    print(f"--------------------------------------------------")
    print(f"🎉 自动化处理流水线已完成.")
    print(f"📊 总结: 成功 {success_count} 张, 失败 {error_count} 张, 跳过 {skip_count} 张.")

# ==========================================
# ▶️ 第 3 部分：设置 并 运行
# ==========================================
if __name__ == '__main__':
    your_data_folder_path = r""#这里放你图片的地址
    
    automated_batch_pipeline_in_place(your_data_folder_path)
