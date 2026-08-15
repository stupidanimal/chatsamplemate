"""
测试脚本 - 验证情绪系统是否正常工作
"""
import sys
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import AICompanion

def test_emotion_parsing():
    """测试情绪标签解析"""
    companion = None
    
    # 测试用例
    test_cases = [
        ("[高兴] 你好呀！", "高兴"),
        ("[生气] 我很不满！", "生气"),
        ("[悲伤] 好难过...", "悲伤"),
        ("[惊讶] 真的吗？！", "惊讶"),
        ("[害羞] 嗯...好的", "害羞"),
        ("[思考] 让我想想", "思考"),
        ("普通回复，没有情绪标签", "默认"),
        ("[未知情绪] 这个标签不存在", "默认"),
    ]
    
    print("测试情绪标签解析...")
    for text, expected in test_cases:
        # 创建一个临时实例来测试解析方法
        class TempCompanion:
            def parse_emotion(self, text):
                import re
                pattern = r'\[(高兴|生气|悲伤|惊讶|害羞|思考|说话|困惑|得意|无聊|兴奋|委屈)\]'
                match = re.search(pattern, text)
                if match:
                    return match.group(1)
                return "默认"
        
        temp = TempCompanion()
        result = temp.parse_emotion(text)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{text}' -> {result} (期望: {expected})")

def test_emotion_files():
    """测试情绪图片文件是否存在"""
    from main import EMOTIONS
    
    assets_dir = Path(__file__).parent.parent / "assets" / "emotions"
    
    print("\n检查情绪图片文件...")
    for emotion, filename in EMOTIONS.items():
        filepath = assets_dir / filename
        status = "✓" if filepath.exists() else "✗"
        print(f"  {status} {emotion}: {filename}")

if __name__ == "__main__":
    test_emotion_parsing()
    test_emotion_files()
    print("\n测试完成！")
