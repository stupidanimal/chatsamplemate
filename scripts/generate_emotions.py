"""
生成占位情绪图片（用于测试）
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def create_emotion_image(emotion, color, filename):
    """创建带文字的情绪占位图"""
    img = Image.new('RGBA', (150, 150), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # 画圆形背景
    draw.ellipse([10, 10, 140, 140], fill=color)
    
    # 尝试添加文字
    try:
        font = ImageFont.truetype("msyh.ttc", 24)
    except:
        font = ImageFont.load_default()
    
    # 居中绘制文字
    text = emotion
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (150 - text_width) // 2
    y = (150 - text_height) // 2
    draw.text((x, y), text, fill="white", font=font)
    
    img.save(filename)
    print(f"Created: {filename}")

def main():
    output_dir = Path(__file__).parent / "assets" / "emotions"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    emotions = {
        "default": ("默认", "#4A90D9"),
        "happy": ("高兴", "#FFD700"),
        "angry": ("生气", "#FF4444"),
        "sad": ("悲伤", "#4169E1"),
        "surprised": ("惊讶", "#FF69B4"),
        "shy": ("害羞", "#FFB6C1"),
        "thinking": ("思考", "#9370DB"),
        "speaking": ("说话", "#98FB98"),
        "confused": ("困惑", "#DDA0DD"),
        "proud": ("得意", "#FFA500"),
        "bored": ("无聊", "#808080"),
        "excited": ("兴奋", "#FF1493"),
        "wronged": ("委屈", "#87CEEB"),
    }
    
    for filename, (emotion, color) in emotions.items():
        filepath = output_dir / f"{filename}.png"
        create_emotion_image(emotion, color, filepath)

if __name__ == "__main__":
    main()
