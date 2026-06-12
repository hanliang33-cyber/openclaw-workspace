#!/usr/bin/env python3
"""
bazi-verify.py - 八字强制验算工具
=================================

【为什么有这个工具】
阿pin 之前犯的最大错误：跳过基础十神验证，直接拼结论。
这个工具强制跑完"基础十神表 + 五行力量 + 喜忌 + 异常标记"四步，
不跑完不许出推算结论。

【用法】
python3 bazi-verify.py <年干支> <月干支> <日干支> <时干支>

例如（亮哥命盘）：
python3 bazi-verify.py 壬戌 辛丑 辛亥 辛未

【输出】
1. 天干十神表
2. 地支藏干十神表
3. 五行力量占比
4. 喜忌判断（调候→扶抑→月令三步法）
5. 异常标记（三刑、伏吟、六害、三合、五合）
6. 特殊格局检测
7. 通关用神建议
"""

import sys
from bazi_common import *

# ════════════════════════════════════════════════════════
# 主函数
# ════════════════════════════════════════════════════════

def main():
    if len(sys.argv) != 5:
        print(__doc__)
        print("\n【错误】需要 4 个干支参数（年月日时）")
        print("示例：python3 bazi-verify.py 壬戌 辛丑 辛亥 辛未")
        sys.exit(1)
    
    bazi_str = sys.argv[1:5]
    try:
        bazi = [parse_ganzhi(gz) for gz in bazi_str]
    except ValueError as e:
        print(f"【错误】{e}")
        sys.exit(1)
    
    output = format_output(bazi_str, bazi)
    print(output)


if __name__ == '__main__':
    main()
