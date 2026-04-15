import json
import os
import time
import re
import requests
import dashscope
from dashscope import ImageSynthesis
from openai import OpenAI
import logging

# --- 1. 基础配置 ---
OUTPUT_DIR = "cosplay_results"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 密钥配置 - 建议从环境变量或配置文件读取
SUPERCOMPUTING_API_KEY = os.getenv("SUPERCOMPUTING_API_KEY", "")
DASH_SCOPE_API_KEY = os.getenv("DASH_SCOPE_API_KEY", "\[]")
dashscope.api_key = DASH_SCOPE_API_KEY

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 定义模型名称
BRAIN_MODEL_NAME = "" # 超算大脑，用于极致翻译与规划
PAINTER_MODEL = "" # 画家,调用的ai必须可以生成图片

# 初始化大脑客户端
client_brain = OpenAI(
    api_key=" ",#
    base_url= ""#
)

# --- 待生成角色列表 ---
# 在这里添加你想要生成写实全身图的角色和特征
character_list = [
    {"name": "神里凌华", "features": "浅蓝长发，高马尾，折扇，蓝色武士铠甲元素"},
    {"name": "雷电将军", "features": "紫色长发，紫瞳，和服，雷元素，长刀，威严气质"},
    {"name": "八重神子", "features": "粉色长发，巫女服，狐狸元素，优雅神秘"},
    {"name": "胡桃", "features": "棕色双马尾，中式服装，红色调，古灵精怪"},
    {"name": "甘雨", "features": "浅蓝长发，红角，紧身服饰，冰元素，温柔"},
    {"name": "刻晴", "features": "紫色双马尾，猫耳发型，雷元素，干练气质"},
    {"name": "优菈", "features": "银蓝长发，骑士装，冰元素，冷艳"},
    {"name": "夜兰", "features": "黑色短发，蓝色渐变，紧身衣，特工风"},
    {"name": "申鹤", "features": "白色长发，红绳装饰，仙气飘逸"},
    {"name": "芙宁娜", "features": "蓝白短发，异色瞳，礼服，戏剧风"},
    {"name": "宵宫", "features": "金发马尾，浴衣风，烟花元素，活泼"},
    {"name": "珊瑚宫心海", "features": "粉蓝渐变长发，水元素，海洋风，温柔"},
    {"name": "莫娜", "features": "紫发，魔法师帽，紧身衣，占星元素"},
    {"name": "琴", "features": "金发马尾，骑士团制服，干练优雅"},
    {"name": "丽莎", "features": "紫发卷发，魔女帽，成熟慵懒"},
    {"name": "罗莎莉亚", "features": "白发，修女风，冷酷气质"},
    {"name": "烟绯", "features": "粉发，律法师风格，红色元素"},
    {"name": "妮露", "features": "红发，舞娘装，异域风情"},
    {"name": "莱依拉", "features": "蓝发，星空元素，学者气质"},
    {"name": "卡芙卡", "features": "紫发，风衣，蜘蛛元素，御姐"},
    {"name": "银狼", "features": "灰紫短发，街机风，未来科技"},
    {"name": "布洛妮娅", "features": "银发，军装风，冷静理性"},
    {"name": "三月七", "features": "粉发，少女感，摄影元素"},
    {"name": "姬子", "features": "红发，礼服，成熟优雅"},
    {"name": "黑天鹅", "features": "紫黑长发，神秘占卜风"},
    {"name": "花火", "features": "粉发，面具，戏剧感强"},
    {"name": "符玄", "features": "紫发，道袍风，预言者气质"},
    {"name": "镜流", "features": "白发，冰冷剑士，肃杀气质"},
    {"name": "爱莉希雅", "features": "粉色长发，精灵感，华丽甜美"},
    {"name": "雷电芽衣", "features": "紫发，剑士，和风元素"},
    {"name": "琪亚娜", "features": "白发，战斗服，元气少女"},
    {"name": "布洛妮娅（崩坏）", "features": "银发双马尾，机械风"},
    {"name": "希儿", "features": "黑紫发，双重人格，暗黑风"},
    {"name": "初音未来", "features": "双马尾，青绿色头发，虚拟偶像"},
    {"name": "镜音铃", "features": "金发短发，大蝴蝶结，活泼"},
    {"name": "巡音流歌", "features": "粉发，御姐气质，成熟优雅"},
    {"name": "蕾姆", "features": "蓝发，女仆装，温柔"},
    {"name": "拉姆", "features": "粉发，女仆装，傲娇"},
    {"name": "艾米莉亚", "features": "银发紫瞳，精灵耳，长裙"},
    {"name": "约尔·福杰", "features": "黑长发，红瞳，杀手礼服"},
    {"name": "阿尼亚", "features": "粉发双角，可爱表情丰富"},
    {"name": "2B", "features": "白发短发，眼罩，战斗裙"},
    {"name": "A2", "features": "白发凌乱，战斗破损风"},
    {"name": "明日香", "features": "红发，紧身战斗服，傲娇"},
    {"name": "绫波丽", "features": "蓝短发，冷淡气质"},
    {"name": "宝多六花", "features": "黑发短发，JK制服，清纯"},
    {"name": "五更琉璃", "features": "黑长发，哥特萝莉"},
    {"name": "时崎狂三", "features": "黑红双马尾，哥特风，病娇"},
    {"name": "远坂凛", "features": "黑长发，红衣，魔术师"},
    {"name": "间桐樱", "features": "紫发，温柔，暗黑气质"},
    {"name": "阿尔托莉雅", "features": "金发，骑士铠甲，王者气质"},
    {"name": "尼禄", "features": "金发，红礼服，皇帝气质"},
    {"name": "伊蕾娜", "features": "灰发，魔女帽，旅行者"},
    {"name": "莉可丽丝千束", "features": "金发，制服，元气少女"},
    {"name": "井之上泷奈", "features": "黑长发，冷静，制服风"},
    {"name": "喜多川海梦", "features": "金发，辣妹风，coser属性"},
    {"name": "后藤一里", "features": "粉发，社恐少女"},
    {"name": "早坂爱", "features": "金发，女仆+辣妹双形态"},
    {"name": "四宫辉夜", "features": "黑长发，大小姐气质"},
    {"name": "白银御行", "features": "黑发，学生会长，理性气质"}
]



# --- [核心功能函数] ---

def clean_file_name(name):
    """清理文件名，移除非法字符"""
    if not name:
        return "unnamed"
    return re.sub(r'[\\/:*?"<>|]', '', str(name)).strip()

def save_image(image_url, char_name, scene_type):
    """下载并保存图片"""
    if not image_url:
        logger.warning("图片URL为空，跳过保存")
        return None
    
    char_path = os.path.join(OUTPUT_DIR, clean_file_name(char_name))
    os.makedirs(char_path, exist_ok=True)
    
    file_path = os.path.join(char_path, f"{clean_file_name(scene_type)}.png")
    
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        with open(file_path, "wb") as f:
            f.write(response.content)
        logger.info(f" 成功保存: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f" 下载或保存图片异常 ({scene_type}): {e}")
    return None

# --- 阶段 1: 超算大脑规划 (全身图硬约束版) ---

def get_optimized_prompts_from_brain(char_info):
    """
    大脑规划 (极致硬约束版)：
    专注于生成带有强制全身构图的写实 Prompt。彻底去除了复杂的资产审计任务。
    """
    logger.info(f"\n [超算大脑] 正在为 {char_info['name']} 规划写实级视觉任务...")

    # 通过“开头强制”的 Prompt Engineering，锁死 AI 的发挥空间
    prompt_task = f"""
    作为顶级的影视级 Cosplay 视觉统筹，请为以下角色规划视觉生成任务。
    
    目标角色: {char_info['name']}
    设定特征: {char_info['features']}
    
    请严格以 JSON 格式输出规划，必须包含以下两个纯英文字段：
    
    1. "char_name_en": 角色的纯英文名称（如 "Nahida"）。
    
    2. "full_body_photo_prompt": 用于生成第一张图（极致写实全身照）的纯英文提示词。
       【致命约束 - 构图】：必须严格以这句话开头："An ultra-detailed wide-angle full body shot, head to toe, entire body visible including shoes, standing on solid physical ground, holding full signature weapons, "
       【致命约束 - 画风】：严禁使用 anime, stylized, 3d render。必须将角色特征翻译为真实的物理材质（例如: heavy velvet, textured linen, leather, realistic skin pores, cinematic volumetric lighting, 35mm lens）。

    请严格返回合法的 JSON 结构（直接输出 JSON 文本，不要用 markdown 代码块包裹）：
    {{
      "char_name_en": "English Name",
      "full_body_photo_prompt": "An ultra-detailed wide-angle full body shot, head to toe, entire body visible including shoes, standing on solid physical ground, holding full signature weapons, [在此处继续写实材质描述]..."
    }}
    """
    
    try:
        response = client_brain.chat.completions.create(
            model=BRAIN_MODEL_NAME,
            messages=[{"role": "user", "content": prompt_task}],
            temperature=0 
        )
        
        content = response.choices[0].message.content.strip()
        
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            plan = json.loads(json_match.group(0))
            logger.info(" 大脑规划成功，已注入全身构图硬约束。")
            return plan
        else:
            raise ValueError(f"未能从回复中提取到 JSON，原始回复: {content[:100]}...")
            
    except Exception as e:
        logger.error(f" 大脑规划解析失败: {e}")
        return None

# --- 阶段 2: 千问画家生成全身图 (纯净版) ---

def draw_with_ali(prompt, char_features="", max_retries=2):
    """专注于生成极致写实的人物全身图"""
    
    base_instruction = (
        "hyper-realistic cosplay photography, RAW photo, 8k resolution, "
        "cinematic volumetric lighting, 35mm lens, f/2.8, "
        "full body shot, head to toe, standing on ground, "
        "real human skin texture, visible pores, "
    )

    negative_prompt = (
        "anime style, cartoon, stylized, 3d render, generic character, "
        "incorrect design, missing details, bad anatomy"
    )

    final_prompt = (
        f"{prompt}, {char_features}, "
        f"{base_instruction}, "
        f"must accurately match original character design, "
        f"--no {negative_prompt}"
    )
    for attempt in range(max_retries):
        try:
            response = ImageSynthesis.call(
                model=PAINTER_MODEL,  
                prompt=final_prompt[:1000], 
                n=1,
                size="1024*1024"
            )

            if response.status_code == 200:
                if hasattr(response, 'output') and hasattr(response.output, 'results') and response.output.results:
                    return response.output.results[0].url
                elif hasattr(response, 'output') and hasattr(response.output, 'images') and response.output.images:
                    return response.output.images[0].url
                elif hasattr(response, 'url'):
                    return response.url
                    
            logger.error(f" 画家创作失败: HTTP {response.status_code}")
            time.sleep(5)

        except Exception as e:
            logger.error(f" 画家调用异常: {e}")
            time.sleep(5)
            
    return None

# --- 主程序控制 ---

def main_optimized():
    logger.info("[系统启动] 开始批量执行精简版写实全身照生成流水线...")
    
    for char in character_list:
        char_display_name = char.get('name', '未知角色')
        print(f"\n{'='*40}")
        print(f"当前目标角色: {char_display_name}")
        print(f"{'='*40}")

        try:
            # 1. 大脑规划
            plan = get_optimized_prompts_from_brain(char)
            if not plan or 'full_body_photo_prompt' not in plan:
                logger.warning(f"[跳过] 角色 {char_display_name} 规划数据不完整。")
                continue

            char_name_en = plan.get('char_name_en', char_display_name)
            char_name_folder = clean_file_name(char_display_name)
            
            # 2. 生成极度写实全身照
            logger.info(f"\n[画家生成] 正在为 {char_display_name} 创作参考级全身照...")
            char_photo_url = draw_with_ali(plan['full_body_photo_prompt'])
            
            if not char_photo_url:
                logger.error(f"❌ [中断] {char_display_name} 的全身照生成失败。")
                continue

            local_file_path = save_image(char_photo_url, char_name_folder, "01_极致写实参考全身照")
            if local_file_path:
                logger.info(f"✅ {char_display_name} 的全身照已就绪！")
            
        except Exception as e:
            logger.error(f"❌ [严重异常] 处理角色 {char_display_name} 发生未捕获错误: {e}")
            
        finally:
            # 冷却时间：保护 API 额度
            logger.info("⏳ 进入 API 冷却期...")
            time.sleep(8)

    logger.info("\n🎉 [系统停机] 所有角色生成任务完成！")

if __name__ == "__main__":
    main_optimized()