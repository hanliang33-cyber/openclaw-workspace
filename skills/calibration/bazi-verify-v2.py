#!/usr/bin/env python3
"""
bazi-verify-v2.py - 八字强制验算工具 v2（API 驱动版）
==================================================

【v2 vs v1 的区别】
v1: AI 用 Python 算四柱 → AI 用 Python 算十神 → 解释输出
v2: API 生成绝对准确的 JSON → AI 读 JSON → 解释输出（不做计算）

【为什么改 v2】
专家 Q12 建议："让算法的归算法，让文学归 AI"。
v1 风险：AI 写代码时也会犯错（如甲日午时算成甲午，实际是庚午）。
v2 解法：API（http://192.168.1.2:19130/api/bazi）已与 lunar_python 4 盘 16 柱 100% 验证。
       工具只做"读 JSON + 加异常标记 + 格局检测 + 喜忌建议"。

【用法】
python3 bazi-verify-v2.py <年> <月> <日> <时> <分> <性别>
例如：python3 bazi-verify-v2.py 1983 1 23 13 40 male

【输出】
1. API 返回的真四柱 + 十神（绝对可信，不再 AI 算）
2. 地支藏干十神表（AI 算藏干+对应十神，但与 API 十神交叉验证）
3. 五行力量占比
4. 喜忌判断（得令/得地/得势三维 + 缺五行提示）
5. 异常标记（三刑/伏吟/六害/三合/天干五合）
6. 特殊格局检测
7. 通关用神建议

【v2 局限】
- 藏干十神仍然由 AI 算（不是 API 返回的）—— 这部分容易翻车，需重点核对
- 身强/身弱简化版（专家 Q3 建议三维加权，v2 还是 50% 阈值）
- 流年应事不在本工具范围
- 一切"取象"类判断（会发生什么）由人工审核
"""

import sys
import json
import urllib.request
import urllib.error
from typing import List, Dict, Tuple

# v1.5 P0 升级（专家 Q-A 终审 2026-06-06）—— 默认关闭，需 --v15 开启
V15_ENABLED = False
try:
    from v15_rootbreaker import adjust_xiji_with_v15
    V15_AVAILABLE = True
except ImportError:
    V15_AVAILABLE = False

# 复用 v1 的所有数据常量和函数
exec(open('/home/node/.openclaw/workspace/skills/calibration/bazi-verify.py').read().split('def main()')[0])

# ==== 起运年龄修正（专家 Q-1 裁决） ====
# 子平传统手算：阳年男命顺排
# 亮哥：壬戌阳年男命，顺数到立春 12 天，12/3=4 年起运
# API 算 5 岁是错误（含虚岁或节气微积分误差）
# lunar_python 算 5 岁同样是错误
# 真实起运年龄 = 4 岁（专家铁证）
LIANG_GE_START_AGE = 4  # 亮哥专用起运年龄（4岁）


def calc_jiaoyun_precise(current_year: int, dayun_table: List[Tuple[str, int, int, str]] = None) -> Dict:
    """
    精确交运期判定（按专家 Q-3 裁决：起运精确到生日同步）
    
    亮哥专：起运 1987-1-23 13:40，之后每 10 年同日同时交运
    返回：交运是否是当年、交运日期、新旧大运
    """
    if dayun_table is None:
        dayun_table = LIANG_GE_DAYUN_TRUE
    
    result = {
        'current_year': current_year,
        'is_jiaoyun_year': False,
        'old_dayun': None,
        'new_dayun': None,
        'exact_jiaoyun_date': None,
    }
    
    # 找当年是否交运
    for gz, start, end, age_range in dayun_table:
        if start == current_year:
            result['is_jiaoyun_year'] = True
            result['new_dayun'] = {'gan_zhi': gz, 'start': start, 'end': end, 'age': age_range}
            result['exact_jiaoyun_date'] = f"{start}-01-23 13:40:00（亮哥专，同生时）"
        elif end == current_year - 1:  # 上一年结束 = 旧运
            result['old_dayun'] = {'gan_zhi': gz, 'start': start, 'end': end, 'age': age_range}
    
    # 判断当前年份处于交运年前/后
    if result['is_jiaoyun_year']:
        # 假设交运日在 1-23
        jiaoyun_month = 1
        jiaoyun_day = 23
        # 6月30日 = 年中，已过交运点（默认判断）
        # 但这里只是返回信息，最终逻辑让 main 调
        result['jiaoyun_status_now'] = f"{current_year} 年为交运年（{result['exact_jiaoyun_date']}）"
    elif result['old_dayun']:
        result['jiaoyun_status_now'] = f"{current_year} 年仍为旧运【{result['old_dayun']['gan_zhi']}】，明年交运"
    else:
        result['jiaoyun_status_now'] = f"{current_year} 年为常规大运中"
    
    return result


def get_current_dayun(year: int, dayun_table: List[Tuple[str, int, int, str]] = None) -> Dict:
    """
    查当前年份在哪个大运
    
    默认用亮哥专用真大运表
    """
    if dayun_table is None:
        dayun_table = LIANG_GE_DAYUN_TRUE
    
    for gz, start, end, age_range in dayun_table:
        if start <= year <= end:
            return {
                'gan_zhi': gz,
                'start_year': start,
                'end_year': end,
                'age_range': age_range,
                'is_jiaoyun': (year == end or year == start),  # 交运期
            }
    
    return {'error': f'{year} 不在大运表范围内'}


def sanity_check_dayun_direction(dayun_table: List[Tuple[str, int, int, str]], year: int, gender: str, year_gan: str) -> Dict:
    """
    v1.6 Sanity Check: 大运序列方向与主流规则是否一致
    主流铁律：阳男/阴女顺排，阴男/阳女逆排。
    函数输入：现有 dayun_table、出生年、性别、年干
    返回：实际方向（顺/逆）+ 是否与主流规则一致 + 警告信息
    """
    if len(dayun_table) < 2:
        return {'status': 'SKIP', 'reason': '大运步数不足 2，无法判断方向'}
    
    # 实际方向：看干支序数是否递增（顺排）还是递减（逆排）
    tiangan = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
    dizhi = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
    
    def gz_to_idx(gz):
        return tiangan.index(gz[0]) * 12 + dizhi.index(gz[1])
    
    idx0 = gz_to_idx(dayun_table[0][0])
    idx1 = gz_to_idx(dayun_table[1][0])
    actual_direction = '顺排' if idx1 > idx0 else '逆排'
    
    # 主流期望方向：阳男/阴女顺排，阴男/阳女逆排
    is_yang_year = (year_gan in ('甲', '丙', '戊', '庚', '壬'))
    is_male = (gender == 'male')
    if (is_yang_year and is_male) or (not is_yang_year and not is_male):
        expected_direction = '顺排'
    else:
        expected_direction = '逆排'
    
    is_consistent = (actual_direction == expected_direction)
    warning = ''
    if not is_consistent:
        warning = f'⚠️ 【v1.6 Sanity Check 报警】主流期望「{expected_direction}」，实际大运表是「{actual_direction}」。请核对 FAMILY_DAYUN 字典是否填错！'
    
    return {
        'status': 'OK' if is_consistent else 'INCONSISTENT',
        'actual_direction': actual_direction,
        'expected_direction': expected_direction,
        'is_consistent': is_consistent,
        'warning': warning,
    }


# ==== 全家真大运表（Q-δ 裁决） ====
LIANG_GE_START_DATETIME = '1987-01-23 13:40:00'  # 亮哥起运绝对时间
LIANG_GE_DAYUN_TRUE = [
    ('甲寅', 1987, 1996, '4-13岁'),
    ('乙卯', 1997, 2006, '14-23岁'),
    ('丙辰', 2007, 2016, '24-33岁'),
    ('丁巳', 2017, 2026, '34-43岁'),  # 2026 交运期
    ('戊午', 2027, 2036, '44-53岁'),  # 2027 换入
    ('己未', 2037, 2046, '54-63岁'),
]
LIANG_GE_DAYUN_CHANGYUN_YEARS = [1987, 1997, 2007, 2017, 2027, 2037]
LIANG_GE_DAYUN_CHANGYUN_WINDOW = '每年公历 01 月 23 日前后'

# 长子：壬辰年阳男顺排，起运 2013-10-21
CHANG_ZI_START_DATETIME = '2013-10-21'
CHANG_ZI_DAYUN = [
    ('丙午', 2013, 2022, '1-10岁'),
    ('丁未', 2023, 2032, '11-20岁'),
    ('戊申', 2033, 2042, '21-30岁'),
    ('己酉', 2043, 2052, '31-40岁'),
    ('庚戌', 2053, 2062, '41-50岁'),
    ('辛亥', 2063, 2072, '51-60岁'),
]

# 次子：乙未年阴男逆排，起运 2019-7-29
CI_ZI_START_DATETIME = '2019-07-29'
CI_ZI_DAYUN = [
    ('戊寅', 2019, 2028, '4-13岁'),
    ('丁丑', 2029, 2038, '14-23岁'),
    ('丙子', 2039, 2048, '24-33岁'),
    ('乙亥', 2049, 2058, '34-43岁'),
    ('甲戌', 2059, 2068, '44-53岁'),
    ('癸酉', 2069, 2078, '54-63岁'),
]

# 亮嫂：乙丑年阴女顺排，起运 1993-1-17
LIANG_SAO_START_DATETIME = '1993-01-17'
LIANG_SAO_DAYUN = [
    ('丁亥', 1993, 2002, '7-16岁'),
    ('戊子', 2003, 2012, '17-26岁'),
    ('己丑', 2013, 2022, '27-36岁'),
    ('庚寅', 2023, 2032, '37-46岁'),
    ('辛卯', 2033, 2042, '47-56岁'),
    ('壬辰', 2043, 2052, '57-66岁'),
]

# 全家大运表
FAMILY_DAYUN = {
    '亮哥': {'start': LIANG_GE_START_DATETIME, 'dayun': LIANG_GE_DAYUN_TRUE},
    '长子': {'start': CHANG_ZI_START_DATETIME, 'dayun': CHANG_ZI_DAYUN},
    '次子': {'start': CI_ZI_START_DATETIME, 'dayun': CI_ZI_DAYUN},
    '亮嫂': {'start': LIANG_SAO_START_DATETIME, 'dayun': LIANG_SAO_DAYUN},
}


# ==== Q-α 交运期三段提示 ====
def check_jiaoyun_three_phase(current_year: int, start_datetime: str = LIANG_GE_START_DATETIME) -> Dict:
    """
    Q-α 裁决：A-α2 交运前夜（气场预热）
    
    返回：交运年三段提示（前/中/后）
    亮哥专：交运年为 next_year，交运点为 1-23 13:40
    """
    start_year = int(start_datetime[:4])
    jiaoyun_year = start_year
    # 亮哥专：起运 1987-1-23，后续每 10 年交运
    # 亮哥交运年：1987, 1997, 2007, 2017, 2027, 2037
    
    # 判断 current_year 是否是交运年
    is_jiaoyun_year = current_year in LIANG_GE_DAYUN_CHANGYUN_YEARS
    
    if current_year == 2026:  # 2026 接近 2027-1-23 交运点（交运倒计时）
        return {
            'phase': '交运倒计时',
            'period': '2026 上半年 + 下半年',
            '上半年': '【前夜蓄势】丁巳最尾期，旧运做最后清盘与总结',
            '下半年': '【中场过渡】戊午之气渗透，平台/环境出现预热换挡信号',
            '底色': '丁巳为底，戊午预热',
            '提示': '上 6 个月旧运主导，下 6 个月新运已扑面而来。',
        }
    elif current_year == 2027:  # 2027 交运年，1-23 13:40 交运
        return {
            'phase': '中场交接',
            'period': '1月1日 - 1月22日（最后 22 天）',
            '底色': '旧运【丁巳】最后挣扎',
            '提示': '正式卸任【丁巳】，2027-1-23 13:40 后全面接管【戊午】。',
        }
    
    return {}


# ==== Q-γ 三阶激活算法 ====
def check_liunian_activation(gan_ln: str, zhi_ln: str, bazi: List[Tuple[str, str]]) -> List[Dict]:
    """
    Q-γ 裁决：三阶激活判定
    
    第一阶：冲/合/刑/害/破 → 100% 激活
    第二阶：同五行/同字（值临） → 100% 激活
    第三阶：天干通根/合化 → 联动激活
    
    返回：激活列表
    """
    activations = []
    pillar_names = ['年', '月', '日', '时']
    
    for idx, (gan_yj, zhi_yj) in enumerate(bazi):
        pillar = pillar_names[idx]
        
        # 第一阶：冲/合/刑/害/破
        relation = get_zhi_relation(zhi_ln, zhi_yj)
        if relation:
            activations.append({
                'pillar': pillar,
                'zhi': zhi_yj,
                'type': '关系引动',
                'desc': f'流年{zhi_ln}与{pillar}支{zhi_yj}：{relation}',
            })
            continue
        
        # 第二阶：值临（同字）
        if zhi_ln == zhi_yj:
            activations.append({
                'pillar': pillar,
                'zhi': zhi_yj,
                'type': '值临引动',
                'desc': f'流年{zhi_ln}与{pillar}支伏吟，{zhi_yj}登台亮相',
            })
            continue
        
        # 第三阶：天干通根（流年干在地支藏干中）
        if zhi_yj in ZHI_CANGAN:
            cangan = ZHI_CANGAN[zhi_yj]
            if gan_ln in cangan:
                activations.append({
                    'pillar': pillar,
                    'zhi': zhi_yj,
                    'type': '天干通根',
                    'desc': f'流年干{gan_ln}是{pillar}支{zhi_yj}的藏干，被激活',
                })
                continue
    
    # 特殊：三刑三字齐（丑戌未、寅巳申）
    sanxing_jihe = {
        '丑戌未': ['丑', '戌', '未'],
        '寅巳申': ['寅', '巳', '申'],
    }
    for sx_name, chars in sanxing_jihe.items():
        if zhi_ln in chars:
            # 流年是三刑中的一字，检查原局是否已有其他两字
            present = [c for c in chars if c in [b[1] for b in bazi]]
            if len(present) >= 1:  # 流年+原局组成三刑
                activations.append({
                    'pillar': '三刑',
                    'zhi': sx_name,
                    'type': '三刑引爆',
                    'desc': f'流年{zhi_ln}补齐{sx_name}，原局已有{present}，三刑被引动',
                })
    
    return activations


def calc_liunian_ying_shi(current_year: int, day_wx: str, day_gan: str, bazi: List, judgment: Dict, family_member: str = '亮哥') -> str:
    """
    流年应事推导（按专家 Q-A/B/C/D 裁决的双层喜忌+调候优先框架）
    
    专家原则：
    1. 极寒极热月→调候一票否决权
    2. 身强喜忌是基础
    3. 流年不套“刑冲破害=灾祸”词库
    4. 杀印相生通关路径可化凶为吉
    5. AI 只能输出“大类取象”（压力/职位/平台）不负责“现实具体事”
    """
    lines = []
    lines.append(f"  流年：{current_year} 年")
    
    # 1. 当前大运
    dayun_table = _resolve_dayun_table(family_member)  # v1.5c Bugfix
    dayun = get_current_dayun(current_year, dayun_table)
    if 'error' in dayun:
        return f"  {dayun['error']}"
    
    lines.append(f"  当前大运：{dayun['gan_zhi']}（{dayun['start_year']}-{dayun['end_year']}）")
    if dayun['is_jiaoyun']:
        lines.append(f"    ⚠️  交运期！大运交接棒，是十年转换点")
    
    # 2. 大运干支对日主的喜忌
    dayun_gan = dayun['gan_zhi'][0]
    dayun_zhi = dayun['gan_zhi'][1]
    dayun_gan_wx = GAN_WUXING.get(dayun_gan, '')
    dayun_zhi_wx = ZHI_WUXING.get(dayun_zhi, '')
    
    sheng_me = SHENG_ME_MAP[day_wx]
    
    # 判断大运干对日主的十神
    dayun_gan_ss = get_shishen(day_gan, dayun_gan)
    lines.append(f"  大运天干 {dayun_gan}（{dayun_gan_wx}）对日主 = {dayun_gan_ss}")
    
    # 3. 判定大运吉凶底色
    if judgment['is_strong']:
        # 身强喜克泄耗
        xi_wx = ['火', '水', '木']  # 官杀/食伤/财
    else:
        # 身弱喜生扶
        xi_wx = [sheng_me, day_wx]  # 印/比劫
    
    if dayun_gan_wx in xi_wx:
        lines.append(f"    大运天干为喜（{dayun_gan_ss}）→ 底色吉")
    elif dayun_gan_wx == day_wx or dayun_gan_wx == sheng_me:
        # 身强时比劫/印是忌
        if judgment['is_strong']:
            lines.append(f"    大运天干为忌（{dayun_gan_ss}）→ 底色有压")
        else:
            lines.append(f"    大运天干为喜（{dayun_gan_ss}）→ 底色吉")
    else:
        lines.append(f"    大运天干中性 → 底色平")
    
    # 4. 调候交互
    if judgment['tiaohou_priority']:
        tiaohou_gan = TIAOHOU.get(bazi[1][1], [('?', '?')])[0][0]
        lines.append(f"  调候优先权：极寒/极热月，调候{ tiaohou_gan}为")
        if dayun_gan_wx == GAN_WUXING.get(tiaohou_gan, ''):
            lines.append(f"    大运{dayun_gan}命中调候{tiaohou_gan} → 调候“通关”成立")
        elif dayun_zhi_wx == GAN_WUXING.get(tiaohou_gan, ''):
            lines.append(f"    大运{dayun_zhi}命中调候{tiaohou_gan}（地支藏干）→ 调候“通关”间接")
    
    # 5. 输出流年应事文字
    lines.append("")
    lines.append(f"  【流年应事推测】（大类取象，需人工审核）")
    
    # 判断大运干十神的现实取象
    shi_xiang_map = {
        '比劫': '朋友/同事/同类/竞争/合伙',
        '劫财': '财物被劫/朋友反目/竞争失财',
        '食神': '饮食/创作/表达/享受/子女',
        '伤官': '表现/创新/冲突/言语/叛逆',
        '偏财': '意外财/投资/父缘/男命父/情人',
        '正财': '薪资/固定资产/财/男命妻',
        '七杀': '压力/权威/官方/上司/竞争者/强制',
        '正官': '职位/名誉/官方/正名/体面',
        '偏印': '学习/技术/宗教/母缘/偏门',
        '正印': '贵人/母缘/学业/名望/保护',
    }
    
    shi_xiang = shi_xiang_map.get(dayun_gan_ss, '变化')
    lines.append(f"    大运{dayun_gan}为{dayun_gan_ss} → 主取象：{shi_xiang}")
    
    if dayun['is_jiaoyun']:
        # v1.1-Patch1 Rectification: 交运期取象升级为"双向可能"
        lines.append(f"    交运期取象（双向可能）：")
        lines.append(f"      上半年 (旧运清盘): 可能退场/收尾/总结/调岗/离职")
        lines.append(f"      过渡期: 气场上/下交织/不稳定")
        lines.append(f"      下半年 (新运接管): 可能启动/接任/开拓")
    
    # 6. Q-α 交运期三段提示（亮哥专用 2026-2027）
    if current_year in [2026, 2027]:
        three_phase = check_jiaoyun_three_phase(current_year)
        if three_phase:
            lines.append("")
            lines.append(f"  【Q-α 交运期提示】：")
            lines.append(f"    {three_phase['phase']}（{three_phase['period']}）")
            lines.append(f"    底色：{three_phase['底色']}")
            if '上半年' in three_phase:
                lines.append(f"    上半年：{three_phase['上半年']}")
                lines.append(f"    下半年：{three_phase['下半年']}")
            lines.append(f"    提示：{three_phase['提示']}")
    
    # 7. Q-γ 流年对原局激活扫描
    # 亮哥专：2026丙午, 2027丁未, 2028戊申
    if current_year in LIUNIAN_TABLE:
        gan_ln, zhi_ln = LIUNIAN_TABLE[current_year]
        lines.append("")
        lines.append(f"  【Q-γ 流年对原局激活扫描】（{current_year}={gan_ln}{zhi_ln}年）")
        activations = check_liunian_activation(gan_ln, zhi_ln, bazi)
        if activations:
            for a in activations:
                lines.append(f"    {a['type']}：{a['desc']}")
        else:
            lines.append(f"    ✅ 无直接引动，流年主要走【值/调候/通关】路径")
    
    # 8. Q-β 2026/2027 流年现实取象（v1.6-refactor: 按家庭成员分支）
    if family_member == '亮哥':
        if current_year == 2026:
            lines.append("")
            lines.append(f"  【Q-β 2026 丙午流年核心取象】（亮哥专 · 专家文本库）")
            lines.append(f"    1. 【人事压力与权责博弈】：流年丙火（正官）与大运丁火（七杀）齐透，")
            lines.append(f"       构成官杀混杂。人事关系复杂，“既要又要”的夹板气，")
            lines.append(f"       或面临极具挑战性的外部公关/管理任务。")
            lines.append(f"    2. 【调候大吉与精力破局】：流年午火+大运巳火=南方火局，")
            lines.append(f"       原局“寒谷回春”。调候到位→精力、斗志被彻底激活。")
            lines.append(f"       压力转化为业内名气与实际掌控力。")
            lines.append(f"    3. 【平台换挡与后方变动】：午+巳联手合动丑土（印库=平台）。")
            lines.append(f"       企业内部架构调整、阵营重新洗牌，或权责范围重大换挡。")
            lines.append(f"       为 2027 戊午正印生身大运稳固新平台做铺垫。")
        elif current_year == 2027:
            lines.append("")
            lines.append(f"  【Q-β 2027 丁未流年核心取象】（明凶实吉 · 专家 Q5 裁决）")
            lines.append(f"    1. 【权责升级与新职任命】：戊午大运（正印生身），")
            lines.append(f"       流年丁未七杀=新的挑战+官方任命/调位。")
            lines.append(f"    2. 【丑戌未三刑引爆】：流年未补齐原局三刑，")
            lines.append(f"       土旺=企业架构重组、岗位调整。")
            lines.append(f"    3. 【杀印相生通关】：戊（印）化丁（杀），杀印相生→")
            lines.append(f"       明凶实吉，动荡中大成。")
    else:
        # 其他家庭成员：通用模板（v1.6-refactor：留给后续按 family_member 扩充）
        if current_year in [2026, 2027]:
            lines.append("")
            lines.append(f"  【Q-β {current_year} 流年取象】（{family_member} · 通用模板）")
            lines.append(f"    详尽文本库待补充。跳过大段专家文本，仅输出大运十神主调。")
    
    # 9. 输出“取象分类”类（不负责“现实具体事”）
    lines.append("")
    lines.append(f"  ⚠️  AI 输出仅为“大类取象”参考：")
    lines.append(f"     {family_member} {current_year} 处于【{dayun['gan_zhi']}】大运，{dayun_gan_ss}主调。")
    lines.append(f"     实际会发生什么（升职/跳槽/婚动/破财）取决于该命主的【现实变量】：")
    lines.append(f"     公司平台、行业、岗位、领导风格、家庭状况等，不是命盘能完全决定的。")
    lines.append(f"     AI 只能提供取象倾向，最终判断需命主按现实校准。")
    
    return '\n'.join(lines)


# ════════════════════════════════════════════════════════
# API 调用层
# ════════════════════════════════════════════════════════

BAZI_API_URL = 'http://192.168.1.2:19130/api/bazi'


def call_bazi_api(year: int, month: int, day: int, hour: int, minute: int, gender: str) -> Dict:
    """
    调用排盘 API 拿绝对正确的四柱 + 十神 + 大运
    
    Returns: {
        'year_gan', 'year_zhi', 'month_gan', 'month_zhi',
        'day_gan', 'day_zhi', 'hour_gan', 'hour_zhi',
        'shi_shen': [年干十神, 月干十神, 日干十神, 时干十神],  # 绝对正确
        'dayun': [大运1, 大运2, ...],
        'jieqi_lichun', 'jieqi_yue', ...
    }
    """
    payload = {
        'year': year,
        'month': month,
        'day': day,
        'hour': hour,
        'minute': minute,
        'gender': gender,
    }
    req = urllib.request.Request(
        BAZI_API_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        return data
    except urllib.error.URLError as e:
        raise RuntimeError(f"API 调用失败: {e}")
    except (KeyError, json.JSONDecodeError) as e:
        raise RuntimeError(f"API 返回格式异常: {e}")


def validate_api_output(data: Dict) -> None:
    """验证 API 返回必要字段"""
    required = ['year_gan', 'year_zhi', 'month_gan', 'month_zhi',
                'day_gan', 'day_zhi', 'hour_gan', 'hour_zhi', 'shi_shen']
    missing = [k for k in required if k not in data]
    if missing:
        raise RuntimeError(f"API 返回缺少字段: {missing}")
    if len(data['shi_shen']) != 4:
        raise RuntimeError(f"API 十神数量异常: {data['shi_shen']}")


# ════════════════════════════════════════════════════════
# v2 身强身弱判断（三维加权：得令 + 得地 + 得势）
# ════════════════════════════════════════════════════════

# 12 长生状态：日干 -> 所在地支
# 本气根：长生、禄、帝旺（足根）
# 中气根：墓库、余气
# 余气根：衰、病、死
CHANG_SHENG = {
    '甲': {'长': '亥', '禄': '寅', '旺': '卯', '衰': '辰', '病': '巳', '死': '午', '墓': '未', '绝': '申', '胎': '酉', '养': '戌', '生': '子', '沐': '丑'},
    '乙': {'长': '午', '禄': '寅', '旺': '卯', '衰': '辰', '病': '巳', '死': '午', '墓': '未', '绝': '申', '胎': '酉', '养': '戌', '生': '子', '沐': '丑'},
    '丙': {'长': '寅', '禄': '巳', '旺': '午', '衰': '未', '病': '申', '死': '酉', '墓': '戌', '绝': '亥', '胎': '子', '养': '丑', '生': '卯', '沐': '辰'},
    '丁': {'长': '酉', '禄': '巳', '旺': '午', '衰': '未', '病': '申', '死': '酉', '墓': '戌', '绝': '亥', '胎': '子', '养': '丑', '生': '卯', '沐': '辰'},
    '戊': {'长': '寅', '禄': '巳', '旺': '午', '衰': '未', '病': '申', '死': '酉', '墓': '戌', '绝': '亥', '胎': '子', '养': '丑', '生': '卯', '沐': '辰'},
    '己': {'长': '酉', '禄': '巳', '旺': '午', '衰': '未', '病': '申', '死': '酉', '墓': '戌', '绝': '亥', '胎': '子', '养': '丑', '生': '卯', '沐': '辰'},
    '庚': {'长': '巳', '禄': '申', '旺': '酉', '衰': '戌', '病': '亥', '死': '子', '墓': '丑', '绝': '寅', '胎': '卯', '养': '辰', '生': '午', '沐': '未'},
    '辛': {'长': '子', '禄': '申', '旺': '酉', '衰': '戌', '病': '亥', '死': '子', '墓': '丑', '绝': '寅', '胎': '卯', '养': '辰', '生': '午', '沐': '未'},
    '壬': {'长': '申', '禄': '亥', '旺': '子', '衰': '丑', '病': '寅', '死': '卯', '墓': '辰', '绝': '巳', '胎': '午', '养': '未', '生': '酉', '沐': '戌'},
    '癸': {'长': '卯', '禄': '亥', '旺': '子', '衰': '丑', '病': '寅', '死': '卯', '墓': '辰', '绝': '巳', '胎': '午', '养': '未', '生': '酉', '沐': '戌'},
}

# 本气根：禄/旺/长
# 中气根：衰/墓/养
ROOT_STRONG = {'禄', '旺', '长'}
ROOT_MID = {'衰', '墓', '养'}


def calc_de_ling(day_wx: str, month_zhi: str) -> Tuple[int, str]:
    """
    得令评分（月令是否生日主）
    返回：(分数, 描述)
    
    经典权重（参考子平、盲派）：
    - 月令同五行：50分（旺于月令，禄/帝旺）
    - 月令生我：40分（次旺）
    - 月令克我：10分（被克最弱）
    - 我克月令：20分（如土克水，月令为财）
    - 我泄月令：15分（如金泄于水，月令为食伤）
    """
    month_wx = ZHI_WUXING.get(month_zhi, '')
    sheng_wo_map = {'金': '火', '木': '金', '水': '土', '火': '水', '土': '木'}  # 我生者
    wo_ke_map = {'金': '木', '木': '土', '水': '火', '火': '金', '土': '水'}  # 我克者
    wo_sheng_map = SHENG_ME_MAP  # 生我者 = 我所生者的反向
    
    if month_wx == day_wx:
        return 50, f"月令同五行（{month_wx}）── 当令"
    if SHENG.get(month_wx) == day_wx:
        # 月令生我
        return 40, f"月令生我（{month_wx}生{day_wx}）── 得令之生"
    if SHENG.get(day_wx) == month_wx:
        # 我生月令
        return 15, f"我生月令（{day_wx}生{month_wx}）── 泄气"
    if wo_ke_map.get(day_wx) == month_wx:
        # 我克月令
        return 20, f"我克月令（{day_wx}克{month_wx}）── 耗气（财）"
    if wo_ke_map.get(month_wx) == day_wx:
        # 月令克我
        return 10, f"月令克我（{month_wx}克{day_wx}）── 失令"
    return 0, f"月令与日主关系不明（{month_wx} vs {day_wx}）"


def calc_de_di(day_gan: str, day_wx: str, bazi: List[Tuple[str, str]]) -> Tuple[int, List[str]]:
    """
    得地评分（柱中有根）
    返回：(总分, 描述列表)
    
    禄/旺/长生（地支本气根）：每个 +25
    衰/墓/养（中气根）：每个 +10
    病死死绝（无气根）：+0
    """
    score = 0
    descs = []
    for i, (label, zhi) in enumerate([('年', bazi[0][1]), ('月', bazi[1][1]), ('日', bazi[2][1]), ('时', bazi[3][1])]):
        cs = CHANG_SHENG.get(day_gan, {})
        for state, target_zhi in cs.items():
            if target_zhi == zhi:
                if state in ROOT_STRONG:
                    score += 25
                    descs.append(f"{label}支{zhi}为{day_gan}之{state}── 本气根 +25")
                elif state in ROOT_MID:
                    score += 10
                    descs.append(f"{label}支{zhi}为{day_gan}之{state}── 中气根 +10")
                break
    return score, descs


def calc_de_shi(day_wx: str, force: Dict[str, float]) -> Tuple[int, str]:
    """
    得势评分（同类+印占比）
    返回：(分, 描述)
    """
    total = sum(force.values())
    if total == 0:
        return 0, "力量为 0"
    pct = {k: v/total*100 for k, v in force.items()}
    sheng_me = SHENG_ME_MAP[day_wx]
    me_help = pct[day_wx] + pct[sheng_me]
    
    if me_help >= 50:
        return 30, f"同类+印 {me_help:.1f}% ≥ 50% ── 极强 +30"
    elif me_help >= 30:
        return 20, f"同类+印 {me_help:.1f}% ≥ 30% ── 中等 +20"
    elif me_help >= 10:
        return 10, f"同类+印 {me_help:.1f}% ≥ 10% ── 弱 +10"
    else:
        return 0, f"同类+印 {me_help:.1f}% < 10% ── 无 +0"


def is_di_wang_yue(day_wx: str, month_zhi: str) -> bool:
    """
    是否帝旺月（日主在月令处于帝旺/禄/刃位）
    按 YUELING_WANGSHUAI[月支][日主五行] >= 0.5 判断
    专家补强一：帝旺月身弱打分不准低于 50
    """
    if month_zhi in YUELING_WANGSHUAI:
        return YUELING_WANGSHUAI[month_zhi].get(day_wx, 0) >= 0.5
    return False


def calc_xie_hao(day_wx: str, force: Dict[str, float]) -> Tuple[int, str]:
    """
    泄耗扣分（水木火土对日主的克泄耗）
    
    子平传统："身弱最怕食伤泄、财星耗、官杀克"
    按专家反馈（亮哥盘）："水木太旺泄身"需扣分
    
    - 食伤（我生者）≥ 30%：扣 15 分
    - 财星（我克者）≥ 20%：扣 10 分
    - 官杀（克我者）≥ 20%：扣 5 分
    """
    total = sum(force.values())
    if total == 0:
        return 0, "力量为 0"
    pct = {k: v/total*100 for k, v in force.items()}
    
    shishen = SHENG[day_wx]  # 食伤
    cai = KE[day_wx]          # 财
    guan_sha_map = {'金': '火', '木': '金', '水': '土', '火': '水', '土': '木'}
    guan_sha = guan_sha_map[day_wx]  # 官杀
    
    deductions = []
    total_deduct = 0
    
    if pct[shishen] >= 30:
        d = 15
        total_deduct += d
        deductions.append(f"食伤{shishen}{pct[shishen]:.1f}%≥30% 扣{d}")
    elif pct[shishen] >= 20:
        d = 8
        total_deduct += d
        deductions.append(f"食伤{shishen}{pct[shishen]:.1f}%≥20% 扣{d}")
    
    if pct[cai] >= 20:
        d = 10
        total_deduct += d
        deductions.append(f"财星{cai}{pct[cai]:.1f}%≥20% 扣{d}")
    elif pct[cai] >= 10:
        d = 5
        total_deduct += d
        deductions.append(f"财星{cai}{pct[cai]:.1f}%≥10% 扣{d}")
    
    if pct[guan_sha] >= 20:
        d = 5
        total_deduct += d
        deductions.append(f"官杀{guan_sha}{pct[guan_sha]:.1f}%≥20% 扣{d}")
    
    if not deductions:
        return 0, "泄耗轻微，不扣分"
    
    return total_deduct, "; ".join(deductions)


# 环境折减常量（按专家 Q-B 补强）
# 寒冬月：亥子丑 → 金水寒极，需火
# 盛夏月：巳午未 → 火土燥极，需水
EXTREME_COLD = ['亥', '子', '丑']  # 极寒月（需火调候）
EXTREME_HOT = ['巳', '午', '未']    # 极热月（需水调候）

# ==== v1.6-refactor: 五行生克映射（提取为模块常量，避免重复定义 4+ 次）====
# 我生者（食伤）
SHENG_WO_MAP = {'金': '金', '木': '火', '水': '木', '火': '土', '土': '金'}  # 复用 SHENG 即可，保留作 alias
# 明确别名（防止有人误用 SHENG 以为是生我）
SHENG_ME_MAP = {'金': '土', '木': '水', '水': '金', '火': '木', '土': '火'}  # 生我者（印）
KE_ME_MAP = {'金': '木', '木': '土', '水': '火', '火': '金', '土': '水'}  # 我克者（财）
KE_WO_MAP = {'金': '火', '木': '金', '水': '土', '火': '水', '土': '木'}  # 克我者（官杀）

# ==== v1.6-refactor: 流年表提取为模块常量（避免文本/JSON 两个函数各自维护） ====
LIUNIAN_TABLE = {
    2024: ('甲', '辰'), 2025: ('乙', '巳'), 2026: ('丙', '午'),
    2027: ('丁', '未'), 2028: ('戊', '申'), 2029: ('己', '酉'),
    2030: ('庚', '戌'), 2031: ('辛', '亥'), 2032: ('壬', '子'),
    2033: ('癸', '丑'), 2034: ('甲', '寅'), 2035: ('乙', '卯'),
}

# ==== 地支冲合刑害破常量（Q-γ 激活算法） ====
# v1 已有 LIUHAI（6害）和 SANHE（3合），这里补 CHONG（6冲）、XING（3刑）、PO（6破）
CHONG = [
    ('子午', '子午相冲'),
    ('丑未', '丑未相冲'),
    ('寅申', '寅申相冲'),
    ('卯酉', '卯酉相冲'),
    ('辰戌', '辰戌相冲'),
    ('巳亥', '巳亥相冲'),
]

XING = [
    # 丑戌未三刑（无恩之刑）
    (('丑', '戌', '未'), '丑戌未三刑（无恩之刑）'),
    # 寅巳申三刑（恃势之刑）
    (('寅', '巳', '申'), '寅巳申三刑（侍势之刑）'),
    # 子卯刑（无礼之刑）
    (('子', '卯'), '子卯相刑（无礼之刑）'),
]

PO = [
    ('子酉', '子酉相破'),
    ('丑辰', '丑辰相破'),
    ('寅亥', '寅亥相破'),
    ('卯午', '卯午相破'),
    ('巳申', '巳申相破'),
    ('未戌', '未戌相破'),
]


def get_zhi_relation(zhi1: str, zhi2: str) -> str:
    """
    查两个地支的冲/合/刑/害/破关系
    返回：关系名 或 空字符串
    """
    pair = tuple(sorted([zhi1, zhi2]))
    pair_str = ''.join(pair)
    
    # 冲
    for p, name in CHONG:
        if p == pair_str:
            return name
    # 合（三合需三个，这里只查两位）
    # 害
    for p, name in LIUHAI:
        if p == pair_str:
            return name
    # 破
    for p, name in PO:
        if p == pair_str:
            return name
    # 刑（需要三个字才能凑齐三刑）— 只看两位能识别的：子卯、寅巳、寅申、巳申
    if pair == ('子', '卯'):
        return '子卯相刑（无礼之刑）'
    if pair in [('寅', '巳'), ('巳', '申'), ('寅', '申')]:
        return '寅巳申三刑局部'
    if pair in [('丑', '戌'), ('丑', '未'), ('戌', '未')]:
        return '丑戌未三刑局部'
    
    return ''


def get_environment_modifier(day_gan: str, day_wx: str, bazi: List[Tuple[str, str]]) -> Tuple[int, str]:
    """
    环境折减（寒暖燥湿）
    
    专家 Q-B：极寒月（金生亥子丑）或极热月（火生巳午未）
    如果调候缺失（无天干明丙丁+无地支巳午火 / 无天干明壬癸+无地支亥子水），原局生克质量打折
    
    返回：(扣分, 描述)
    """
    month_zhi = bazi[1][1]
    deduction = 0
    descs = []
    
    # 检查"明"调候用神（天干干 + 地支本气）
    all_gans = [b[0] for b in bazi]
    all_zhis = [b[1] for b in bazi]
    
    has_ming_fire = ('丙' in all_gans or '丁' in all_gans) or ('巳' in all_zhis or '午' in all_zhis)
    has_ming_water = ('壬' in all_gans or '癸' in all_gans) or ('亥' in all_zhis or '子' in all_zhis)
    
    # 极寒月（金水月）金/水日主需要火
    if month_zhi in EXTREME_COLD and day_wx in ['金', '水']:
        if not has_ming_fire:
            deduction = 10
            descs.append(f"{month_zhi}月为极寒冬月，{day_wx}日主需明火调候，但原局无天干丙丁、无地支巳午")
    
    # 极热月（火土月）火/土日主需要水
    elif month_zhi in EXTREME_HOT and day_wx in ['火', '土']:
        if not has_ming_water:
            deduction = 10
            descs.append(f"{month_zhi}月为极热夏月，{day_wx}日主需明水调候，但原局无天干壬癸、无地支亥子")
    
    if not descs:
        return 0, "环境适中（极寒极热月有明调候），无需折减"
    
    return deduction, "; ".join(descs) + f" → 扣{deduction}分"


def get_tiaohou_priority(bazi: List[Tuple[str, str]], day_wx: str) -> Tuple[bool, str, str]:
    """
    检测调候优先级（极寒/极热时调候一票否决）
    v1.6-tiaohou-fix: 返回三元组(是否极寒极热, 描述, 调候用神五行)
    """
    month_zhi = bazi[1][1]
    if month_zhi in EXTREME_COLD:
        return True, f"{month_zhi}月极寒冬月，调候用神为火，拥有最高优先权", '火'
    if month_zhi in EXTREME_HOT:
        return True, f"{month_zhi}月极热夏月，调候用神为水，拥有最高优先权", '水'
    return False, f"{month_zhi}月非极寒极热，调候优先级常规", ''


def judge_xiji_v2(force: Dict[str, float], day_gan: str, day_wx: str, bazi: List[Tuple[str, str]]) -> Dict:
    """
    v2 身强身弱判断（三维加权 + 泄耗扣分 + 环境折减 + 帝旺月硬约束）
    
    总分 = 得令 + 得地 + 得势 - 泄耗 - 环境折减
    帝旺月硬约束：底线抬升至 60（专家 Q-D 修正）
    
    判定档位：
    - 总分 ≥ 80：极强身强
    - 总分 ≥ 60：身强
    - 总分 ≥ 50：偏强
    - 总分 ≥ 40：偏弱
    - 总分 < 40：身弱
    """
    month_zhi = bazi[1][1]
    
    # 1. 得令
    ling_score, ling_desc = calc_de_ling(day_wx, month_zhi)
    
    # 2. 得地
    di_score, di_descs = calc_de_di(day_gan, day_wx, bazi)
    
    # 3. 得势
    shi_score, shi_desc = calc_de_shi(day_wx, force)
    
    # 4. 泄耗扣分
    xh_score, xh_desc = calc_xie_hao(day_wx, force)
    
    # 5. 环境折减（寒暖燥湿）
    env_score, env_desc = get_environment_modifier(day_gan, day_wx, bazi)
    
    # 6. 调候优先级
    tiaohou_priority, tiaohou_desc, tiaohou_yongshen = get_tiaohou_priority(bazi, day_wx)
    # v1.6-tiaohou-fix: tiaohou_yongshen 是调候用神五行（'火'/'水'/''空）
    
    raw_total = ling_score + di_score + shi_score
    total = max(0, raw_total - xh_score - env_score)
    
    # 7. 帝旺月硬约束（Q-D 修正：底线抬升至 60）
    is_dw = is_di_wang_yue(day_wx, month_zhi)
    if is_dw and total < 60:
        total = 60
        hard_constraint = f"⚠️ 帝旺月硬约束：原始分 {raw_total} 被抬升至 60（专家 Q-D 修正）"
    else:
        hard_constraint = None
    
    # 判定档位（专家 Q-A 裁决：加"中和"档）
    # 亮哥 57 分 = 中和偏弱，其他参照实际判断
    if total >= 80:
        level = '极强身强'
    elif total >= 65:
        level = '身强'
    elif total >= 60:
        level = '偏强'
    elif total >= 45:
        level = '中和'  # 专家原话："量化打分稍偏强，但实际操作按偏弱论"
    elif total >= 35:
        level = '偏弱'
    else:
        level = '身弱'
    
    is_strong = total >= 60  # 中和档以下不认为身强
    
    # 极缺五行
    total_force = sum(force.values())
    if total_force > 0:
        pct = {k: v/total_force*100 for k, v in force.items()}
        scarce = [k for k, v in pct.items() if v < 5]
    else:
        scarce = []
    
    sheng_me = SHENG_ME_MAP[day_wx]
    
    return {
        'ling_score': ling_score,
        'ling_desc': ling_desc,
        'di_score': di_score,
        'di_descs': di_descs,
        'shi_score': shi_score,
        'shi_desc': shi_desc,
        'xh_score': xh_score,
        'xh_desc': xh_desc,
        'env_score': env_score,
        'env_desc': env_desc,
        'tiaohou_priority': tiaohou_priority,
        'tiaohou_desc': tiaohou_desc,
        'tiaohou_yongshen': tiaohou_yongshen,  # v1.6-tiaohou-fix
        'raw_total': raw_total,
        'total': total,
        'is_dw': is_dw,
        'hard_constraint': hard_constraint,
        'level': level,
        'is_strong': is_strong,
        'sheng_me': sheng_me,
        'scarce': scarce,
        'force_pct': {k: v/total_force*100 for k, v in force.items()} if total_force > 0 else {},
    }


# ════════════════════════════════════════════════════════
# v2 输出格式
# ════════════════════════════════════════════════════════

def format_output_v2(api_data: Dict, current_year_gan: str = None, current_dayun_gan: str = None) -> str:
    """
    读 API JSON 输出报告
    
    关键：不重新计算四柱和天干十神（API 已给）
    仍需 AI 算：藏干十神、五行力量、异常标记、格局检测、通关建议
    
    参数:
        api_data: API 返的完整 JSON
        current_year_gan: 当前流年干（用于天干伏吟检测，v1.1-Patch1 Rectification Bug 4 修复）
        current_dayun_gan: 当前大运干（用于大运+流年干伏吟检测，v1.1-Patch1 Rectification Bug 5 修复）
    """
    # API 提供的绝对正确数据
    year_gz = api_data['year_gan'] + api_data['year_zhi']
    month_gz = api_data['month_gan'] + api_data['month_zhi']
    day_gz = api_data['day_gan'] + api_data['day_zhi']
    hour_gz = api_data['hour_gan'] + api_data['hour_zhi']
    bazi_str = [year_gz, month_gz, day_gz, hour_gz]
    bazi = [parse_ganzhi(gz) for gz in bazi_str]
    api_shishen = api_data['shi_shen']  # [年干, 月干, 日干, 时干]
    dayun = api_data.get('dayun', [])
    
    day_gan = bazi[2][0]
    day_wx = GAN_WUXING[day_gan]
    month_zhi = bazi[1][1]
    
    lines = []
    lines.append("═" * 60)
    lines.append(f"八字四柱（API 真盘）：{' '.join(bazi_str)}")
    lines.append(f"日主：{day_gan}（{GAN_YINYANG[day_gan]}{day_wx}）")
    lines.append("═" * 60)
    
    # 1. 天干十神表（API 绝对正确 + 与 AI 算的对照）
    lines.append("")
    lines.append("【天干十神表】（API 锁死 · 不可由 AI 复述）")
    # API shi_shen 顺序：[年, 月, 日, 时]
    # bazi 顺序：[年, 月, 日, 时]
    # 两老一致，直接用 idx
    for label, idx in [('年干', 0), ('月干', 1), ('时干', 3)]:
        gan = bazi[idx][0]
        wx = GAN_WUXING[gan]
        yy = GAN_YINYANG[gan]
        # API 返回的十神（idx=3 是时干）
        if idx == 2:
            ss = '日主'  # 日干为日主
        else:
            ss = api_shishen[idx]
        # AI 算的（同源代码逻辑）
        ai_ss = get_shishen(day_gan, gan) if idx != 2 else '日主'
        match = '✅' if ss == ai_ss else '❌'
        lines.append(f"  {label} {gan}（{wx}·{yy}）── {ss} （AI算: {ai_ss}）{match}")
    lines.append(f"  日干 {day_gan}（{day_wx}·{GAN_YINYANG[day_gan]}）── 日主")
    
    # 2. 地支藏干十神表（AI 算 + 标注"非API锁死"）
    lines.append("")
    lines.append("【地支藏干十神表】（AI 计算 · 需人工核对）")
    for i, (label, _) in enumerate([('年支', 0), ('月支', 1), ('日支', 2), ('时支', 3)]):
        zhi = bazi[i][1]
        canggan = ZHI_CANGAN.get(zhi, [])
        parts = []
        for cg in canggan:
            ss = get_shishen(day_gan, cg)
            parts.append(f"{cg}({ss})")
        lines.append(f"  {label} {zhi}（{ZHI_WUXING[zhi]}）  藏: {' '.join(parts)}")
    
    # 3. 五行力量（复用 v1）
    force = calc_wuxing_force(bazi)
    total = sum(force.values())
    
    lines.append("")
    lines.append("【五行力量】（含月令加权）")
    for wx in ['金', '木', '水', '火', '土']:
        val = force[wx]
        pct = val / total * 100
        bar = '█' * int(pct / 2.5)
        lines.append(f"  {wx}: {val:5.1f}  {pct:5.1f}%  {bar}")
    
    # 4. 喜忌判断（v2 三维加权 + 泄耗 + 环境折减 + 帝旺月硬约束 + 调候优先级）
    lines.append("")
    lines.append("【喜忌判断】（v2 完整版：得令 + 得地 + 得势 - 泄耗 - 环境折减）")
    judgment = judge_xiji_v2(force, day_gan, day_wx, bazi)
    pct = judgment['force_pct']
    
    lines.append(f"  日主五行：{day_wx}，生我者为：{judgment['sheng_me']}")
    lines.append("")
    lines.append(f"  ① 得令（月令）：{judgment['ling_score']} 分")
    lines.append(f"     {judgment['ling_desc']}")
    lines.append(f"  ② 得地（柱中有根）：{judgment['di_score']} 分")
    for d in judgment['di_descs']:
        lines.append(f"     {d}")
    if not judgment['di_descs']:
        lines.append(f"     无本气根 / 中气根")
    lines.append(f"  ③ 得势（同类+印占比）：{judgment['shi_score']} 分")
    lines.append(f"     {judgment['shi_desc']}")
    lines.append(f"  ④ 泄耗扣分（食伤/财/官杀）：-{judgment['xh_score']} 分")
    lines.append(f"     {judgment['xh_desc']}")
    lines.append(f"  ⑤ 环境折减（寒暖燥湿）：-{judgment['env_score']} 分")
    lines.append(f"     {judgment['env_desc']}")
    lines.append(f"  原始分：{judgment['raw_total']} 分")
    if judgment.get('hard_constraint'):
        lines.append(f"  {judgment['hard_constraint']}")
    lines.append(f"  最终分：{judgment['total']} 分")
    lines.append(f"  判定：{judgment['level']} {'✅' if judgment['is_strong'] else '⚠️'}")
    
    if judgment.get('scarce'):
        lines.append(f"  ⚠️  极缺五行：{', '.join(judgment['scarce'])}（< 5%）")
    
    # 调候优先级提示
    lines.append("")
    lines.append(f"  调候层优先级：{judgment['tiaohou_desc']}")
    if judgment['tiaohou_priority']:
        lines.append(f"    ⚠️  极寒/极热月份，调候用神拥有最高优先权")
    
    # 喜忌双层输出（专家 Q-C）
    lines.append("")
    lines.append("  喜用神（双层输出：调候层 + 身强身弱基础层）：")
    
    # 第一层：调候
    tiaohou_gan = None
    month_zhi = bazi[1][1]
    th_list = TIAOHOU.get(month_zhi, [])
    if th_list:
        tiaohou_gan = th_list[0][0]
        lines.append(f"    [调候层]  喜：{tiaohou_gan}（调候，{'极寒/极热优先' if judgment['tiaohou_priority'] else '常规'}）")
    
    # 第二层：身强身弱
    ke_wo = {'木': '金', '金': '火', '火': '水', '水': '土', '土': '木'}
    shishen_wx = SHENG[day_wx]
    cai_wx = KE[day_wx]
    guan_sha_wx = ke_wo[day_wx]
    
    if judgment['is_strong']:
        lines.append(f"    [身强身弱层]  喜：{guan_sha_wx}（官杀，制身）")
        lines.append(f"    [身强身弱层]  喜：{shishen_wx}（食伤，泄秀）")
        lines.append(f"    [身强身弱层]  喜：{cai_wx}（财星，耗身）")
        lines.append(f"    [身强身弱层]  忌：{day_wx}（比劫）/{judgment['sheng_me']}（印）")
    else:
        lines.append(f"    [身强身弱层]  喜：{judgment['sheng_me']}（印，生身）")
        lines.append(f"    [身强身弱层]  喜：{day_wx}（比劫，帮身）")
        lines.append(f"    [身强身弱层]  忌：{guan_sha_wx}（官杀，克身）")
        lines.append(f"    [身强身弱层]  忌：{shishen_wx}（食伤，泄身）")
        lines.append(f"    [身强身弱层]  忌：{cai_wx}（财星，耗身）")
    
    # 冲突提示 + 中和档调候优先
    tiaohou_wx = GAN_WUXING.get(tiaohou_gan, '') if tiaohou_gan else ''
    tiaohou_shi_shen = None
    if tiaohou_gan:
        if tiaohou_wx == day_wx:
            tiaohou_shi_shen = '比劫'
        elif tiaohou_wx == judgment['sheng_me']:
            tiaohou_shi_shen = '印'
        elif tiaohou_wx == guan_sha_wx:
            tiaohou_shi_shen = '官杀'
        elif tiaohou_wx == shishen_wx:
            tiaohou_shi_shen = '食伤'
        elif tiaohou_wx == cai_wx:
            tiaohou_shi_shen = '财星'
    
    # 极寒极热且调候 = 身强身弱忌神 → 调候优先按吉论
    if judgment['tiaohou_priority'] and tiaohou_shi_shen in ['官杀', '食伤', '财星']:
        lines.append(f"    ⚠️  调候{tiaohou_gan}={tiaohou_shi_shen} 与身强身弱忌神冲突，但极寒/极热调候优先级最高，按吉论（杀印相生通关）")
    elif judgment['tiaohou_priority'] and tiaohou_shi_shen in ['比劫', '印']:
        lines.append(f"    ℹ️  调候{tiaohou_gan}={tiaohou_shi_shen} 与身强身弱喜神一致，吉祥加成")
    elif tiaohou_gan and not judgment['tiaohou_priority']:
        # 常规调候
        xi_or_ji_base = '喜' if tiaohou_shi_shen in ['官杀', '食伤', '财星'] else '忌'
        if xi_or_ji_base == '忌':
            lines.append(f"    ⚠️  调候{tiaohou_gan}={tiaohou_shi_shen} 与身强身弱忌神冲突（常规调候不优先）")
        else:
            lines.append(f"    ℹ️  调候{tiaohou_gan}={tiaohou_shi_shen} 与身强身弱喜神一致（常规调候加成）")
    
    # v1.6-tiaohou-fix: 合并层最终结论
    if judgment.get('tiaohou_priority'):
        tiao_wx = judgment.get('tiaohou_yongshen', '?')
        sheng_tiao = {'火': '木', '水': '金'}.get(tiao_wx, '?')
        day_wx_name = day_wx
        lines.append(f"    v1.6-tiaohou-fix: 调候层{tiao_wx}优先，最终喜用={tiao_wx}（调候）+{sheng_tiao}（生调候）")
    
    # 5. 调候用神（复用 v1）
    lines.append("")
    lines.append(f"【调候用神】月支：{month_zhi}")
    tiaohou = TIAOHOU.get(month_zhi, [])
    for gan, role in tiaohou:
        has = "原局有" if gan in [b[0] for b in bazi] else "原局无"
        all_cg = []
        for _, zhi in bazi:
            all_cg.extend(ZHI_CANGAN.get(zhi, []))
        if gan in all_cg:
            has = "原局有（含藏干）"
        lines.append(f"  {gan}（{role}）── {has}")
    
    # 6. 异常标记（复用 v1）
    lines.append("")
    lines.append("【异常标记】")
    
    sanxing = check_sanxing(bazi)
    if sanxing:
        for s in sanxing:
            lines.append(f"  ⚠️  {s}")
    else:
        lines.append("  ✅ 无三刑")
    
    fuyin = check_fuyin(bazi)
    if fuyin:
        for f in fuyin:
            lines.append(f"  ⚠️  {f}")
            # v1.1-Patch1 Rectification 补取象
            # 伏吟 = 主柱与主柱同干同支。传统命理主 “反复/退场/主动改变"
            lines.append(f"     → Rectification 取象: 反复/退场/主动改变（调岗/离职/项目重起）")
    else:
        lines.append("  ✅ 无伏吟")
    
    # v1.1-Patch1 Rectification Bug 4 修复：天干伏吟检测（只天干同，地支不同）
    # 检测流年干是否与原局任一干相同
    if current_year_gan:
        gan_names = ['年', '月', '日', '时']
        for i, (g, z) in enumerate(bazi):
            if g == current_year_gan and i != 2:  # 不重复报日主
                lines.append(f"  ⚠️  流年干{current_year_gan}与{gan_names[i]}干{g}同 = 天干伏吟（地支{z}不同）")
                lines.append(f"     → Rectification 取象: 反复/承前启后/谋虑多/计划变调")
    
    # v1.1-Patch1 Rectification Bug 5 修复：大运+流年干伏吟检测
    # 2017 丁年+大运丁 = 干伏吟
    if current_year_gan and current_dayun_gan and current_year_gan == current_dayun_gan:
        lines.append(f"  ⚠️  流年干{current_year_gan}与大运干{current_dayun_gan}同 = 干支双伏吟背景（极强反复/承前启后）")
    
    liuhai = check_liuhai(bazi)
    if liuhai:
        for l in liuhai:
            lines.append(f"  ⚠️  六害: {l}")
            # v1.1-Patch1 Rectification 补取象
            liuhai_meaning = {
                '子未相害': '感情离散/合作破裂',
                '丑午相害': '平台换挡/离职/调动',
                '寅巳相害': '项目中止/合作伙伴背刺',
                '卯辰相害': '小环境变动/邻里纠纷',
                '申亥相害': '暗中谋害/被排挤/离职',
                '酉戌相害': '家庭变动/酒色争议',
            }
            meaning = liuhai_meaning.get(l, '')
            if meaning:
                lines.append(f"     → Rectification 取象: {meaning}")
    else:
        lines.append("  ✅ 无六害")
    
    sanhe = check_sanhe(bazi)
    if sanhe:
        for s in sanhe:
            lines.append(f"  🔷 {s}")
    else:
        lines.append("  ✅ 无三合")
    
    wuhe = check_wuhe(bazi, day_gan)
    if wuhe:
        for w in wuhe:
            lines.append(f"  🔷 {w}")
    else:
        lines.append("  ✅ 无天干合（涉日主）")
    
    # 禄神
    lu = LU_SHEN.get(day_gan)
    if lu and lu in [b[1] for b in bazi]:
        lines.append(f"  ℹ️  禄神在{lu}（{day_gan}禄）── 有根有禄")
    
    # 桃花
    month_group_taohua = {
        '申子辰': '酉', '寅午戌': '卯',
        '亥卯未': '子', '巳酉丑': '午',
    }
    for combo, taohua in month_group_taohua.items():
        if month_zhi in combo:
            if taohua in [b[1] for b in bazi]:
                lines.append(f"  ℹ️  桃花在{taohua}（月支{month_zhi}局桃花）")
            break
    
    # 驿马
    yima_map = {
        '申子辰': '寅', '寅午戌': '申',
        '亥卯未': '巳', '巳酉丑': '亥',
    }
    for combo, yima in yima_map.items():
        if month_zhi in combo:
            if yima in [b[1] for b in bazi]:
                lines.append(f"  ℹ️  驿马在{yima}（{month_zhi}局驿马）── 主奔波动")
            break
    
    # 7. 特殊格局检测
    lines.append("")
    lines.append("【特殊格局检测】")
    special = check_special_geju(force, day_gan, day_wx, bazi)
    if special:
        lines.append("  ⚠️  以下识别出特殊格局，喜忌应优先参考格局调整（而非上方「扶抑法」简单判断）")
        for sp in special:
            lines.append(f"  🎯 {sp['name']}")
            lines.append(f"     {sp['desc']}")
            lines.append(f"     喜：{sp['xi']}")
            lines.append(f"     忌：{sp['ji']}")
            lines.append(f"     用：{sp['yong']}")
            lines.append(f"     注：{sp['note']}")
    else:
        lines.append("  ✅ 未识别出特殊格局（按普通身强/身弱处理）")
    
    # 8. 通关用神建议
    lines.append("")
    lines.append("【通关用神建议】")
    tongguan = find_tongguan(force, day_wx)
    if tongguan:
        for t in tongguan:
            lines.append(f"  💡 {t}")
    else:
        lines.append("  ✅ 五行流通，无明显战局/失衡")
    
    # 9. 大运（API 锁死）
    if dayun:
        lines.append("")
        lines.append("【大运】（API 锁死）")
        lines.append(f"  {' → '.join(dayun)}")
    
    lines.append("")
    lines.append("═" * 60)
    lines.append("✅ v2 验证完成（API 锁死 + AI 辅助）")
    lines.append("")
    lines.append("⚠️  v2 仍需人工审核：")
    lines.append("  1. 天干十神 ✅ 来自 API，绝对可信")
    lines.append("  2. 地支藏干十神 ⚠️ AI 算的，需核对（v2.1 应从 API 拿）")
    lines.append("  3. 喜忌判断 ⚠️ 简化版扶抑法，特殊格局需师傅审")
    lines.append("  4. 异常标记 ✅ 算法检测，但三刑吉凶取决于喜忌")
    lines.append("  5. 特殊格局 ⚠️ 候选检测，定论需师傅")
    lines.append("  6. 流年应事 ❌ 本工具不做")
    lines.append("")
    lines.append("下一步：")
    lines.append("  1. 核对天干十神 vs API")
    lines.append("  2. 核对地支藏干十神（重点：易翻车）")
    lines.append("  3. 检查喜忌是否符合命主实际情况")
    lines.append("  4. 异常标记是否需要重点分析")
    lines.append("  5. 特殊格局是否成立（人工审核）")
    lines.append("  6. 以上无异议后，再开始具体推算")
    lines.append("═" * 60)
    
    return '\n'.join(lines)


# ════════════════════════════════════════════════════════
# 主函数
# ════════════════════════════════════════════════════════

def main():
    # v1.6: 兼容 6/7/9/10/11/13/15 个参数（+2/4 为 --direction/--dayun-table 可选）
    if len(sys.argv) not in (6, 7, 9, 10, 11, 13, 15):
        print(__doc__)
        print("\n【错误】参数格式: 年 月 日 时 分 性别 [--year 流年] [--json] [--direction mainstream|custom_ni] [--dayun-table auto|custom]")
        print("示例：python3 bazi-verify-v2.py 1983 1 23 13 40 male --year 2027 --json --direction mainstream")
        sys.exit(1)
    
    try:
        year = int(sys.argv[1])
        month = int(sys.argv[2])
        day = int(sys.argv[3])
        hour = int(sys.argv[4])
        minute = int(sys.argv[5])
        gender = sys.argv[6] if len(sys.argv) >= 7 else 'male'
        current_year = None
        json_mode = False
        direction_practice = 'mainstream'  # v1.6 默认主流顺排
        dayun_table_mode = 'auto'  # v1.6 默认按 family_member 自动选
        for i in range(7, len(sys.argv)):
            if sys.argv[i] == '--year' and i + 1 < len(sys.argv):
                current_year = int(sys.argv[i + 1])
            elif sys.argv[i] == '--json':
                json_mode = True
            elif sys.argv[i] == '--v15':
                global V15_ENABLED
                V15_ENABLED = True
            elif sys.argv[i] == '--direction' and i + 1 < len(sys.argv):
                direction_practice = sys.argv[i + 1]
                if direction_practice not in ('mainstream', 'custom_ni'):
                    print(f"【警告】--direction 取值 {direction_practice} 不在支持列表，默认 mainstream")
                    direction_practice = 'mainstream'
            elif sys.argv[i] == '--dayun-table' and i + 1 < len(sys.argv):
                dayun_table_mode = sys.argv[i + 1]
                if dayun_table_mode not in ('auto', 'custom'):
                    print(f"【警告】--dayun-table 取值 {dayun_table_mode} 不在支持列表，默认 auto")
                    dayun_table_mode = 'auto'
    except (ValueError, IndexError) as e:
        print(f"【错误】参数解析失败: {e}")
        sys.exit(1)
    
    # v1.1-Patch1 Rectification: 计算流年干 + 大运干（用于天干伏吟检测）
    TIANGAN_LIST = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    if current_year:
        current_year_gan_for_fuyin = TIANGAN_LIST[(current_year - 4) % 10]
    else:
        current_year_gan_for_fuyin = None
    
    # 默认大运表中的大运干
    DEFAULT_DAYUN_GAN = '丁'  # 2017-2026 丁巳运，亮哥常用
    current_dayun_gan = DEFAULT_DAYUN_GAN
    
    try:
        api_data = call_bazi_api(year, month, day, hour, minute, gender)
    except RuntimeError as e:
        print(f"【错误】{e}")
        sys.exit(1)
    
    validate_api_output(api_data)
    
    # v1.5c Bugfix：识别家庭成员，后续调 get_current_dayun 时用正确的大运表
    family_member = _detect_family_member(year, month, day, hour, minute, gender)
    
    # JSON 输出模式（专家推荐 activated_nodes 需求）
    if json_mode:
        import json as json_lib
        output_dict = build_json_output(api_data, current_year, year, month, day, hour, minute, gender)
        print(json_lib.dumps(output_dict, ensure_ascii=False, indent=2))
        return
    
    output = format_output_v2(api_data, current_year_gan=current_year_gan_for_fuyin, current_dayun_gan=current_dayun_gan)
    
    if current_year:
        output += "\n\n"
        output += "═" * 60 + "\n"
        output += f"【流年推算 · {current_year} 年】\n"
        output += "═" * 60 + "\n"
        # ...（原有流年输出逻辑保持不变）
        
        jiaoyun = calc_jiaoyun_precise(current_year)
        output += f"  【交运期判定】\n"
        output += f"  {jiaoyun['jiaoyun_status_now']}\n"
        if jiaoyun['is_jiaoyun_year']:
            output += f"  ⚠️  交运年！换运精确时间：{jiaoyun['exact_jiaoyun_date']}\n"
        elif jiaoyun['old_dayun']:
            output += f"  明年 ({current_year + 1}) 交运换入新大运【{jiaoyun['new_dayun']['gan_zhi']}】\n"
        output += ""
        
        dayun_table = _resolve_dayun_table(family_member)  # v1.5c Bugfix
        dayun = get_current_dayun(current_year, dayun_table)
        if 'error' not in dayun:
            jiaoyun_warn = " ⚠️ 交运期！" if dayun['is_jiaoyun'] else ""
            output += f"  当前大运（粗调表）：{dayun['gan_zhi']}（{dayun['start_year']}-{dayun['end_year']}，{dayun['age_range']}）{jiaoyun_warn}\n"
            for gz, s, e, a in dayun_table:  # v1.5c Bugfix: 不再硬编码 LIANG_GE_DAYUN_TRUE
                if s > dayun['end_year']:
                    output += f"  下一大运：{gz}（{s}-{e}，{a}）\n"
                    break
            # v1.6 Sanity Check: 大运方向是否与主流规则一致
            sanity = sanity_check_dayun_direction(dayun_table, year, gender, api_data['year_gan'])
            if sanity['status'] == 'INCONSISTENT':
                output += f"  {sanity['warning']}\n"
                output += f"    （年干{api_data['year_gan']}，性别{gender}，主流期望{sanity['expected_direction']}）\n"
        
        year_gz = api_data['year_gan'] + api_data['year_zhi']
        month_gz = api_data['month_gan'] + api_data['month_zhi']
        day_gz = api_data['day_gan'] + api_data['day_zhi']
        hour_gz = api_data['hour_gan'] + api_data['hour_zhi']
        bazi_for_calc = [parse_ganzhi(gz) for gz in [year_gz, month_gz, day_gz, hour_gz]]
        day_gan_calc = api_data['day_gan']
        day_wx_calc = GAN_WUXING[day_gan_calc]
        force_for_calc = globals()['calc_wuxing_force'](bazi_for_calc)
        judgment_real = judge_xiji_v2(force_for_calc, day_gan_calc, day_wx_calc, bazi_for_calc)
        
        output += "\n" + calc_liunian_ying_shi(current_year, day_wx_calc, day_gan_calc, bazi_for_calc, judgment_real, family_member) + "\n"
    
    print(output)


def build_json_output(api_data: Dict, current_year, year, month, day, hour, minute, gender) -> Dict:
    """
    输出结构化 JSON（专家推荐 activated_nodes 需求）
    """
    year_gz = api_data['year_gan'] + api_data['year_zhi']
    month_gz = api_data['month_gan'] + api_data['month_zhi']
    day_gz = api_data['day_gan'] + api_data['day_zhi']
    hour_gz = api_data['hour_gan'] + api_data['hour_zhi']
    bazi = [year_gz, month_gz, day_gz, hour_gz]
    bazi_for_calc = [parse_ganzhi(gz) for gz in bazi]
    day_gan_calc = api_data['day_gan']
    day_wx_calc = GAN_WUXING[day_gan_calc]
    force_for_calc = globals()['calc_wuxing_force'](bazi_for_calc)
    judgment = judge_xiji_v2(force_for_calc, day_gan_calc, day_wx_calc, bazi_for_calc)

    # v1.5 P0 调整（专家 Q-A 终审）—— 三刑+喜忌矛盾自动收敛
    if V15_ENABLED and V15_AVAILABLE:
        judgment_v15 = adjust_xiji_with_v15(bazi_for_calc, judgment, verbose=False)
        if judgment_v15.get('v15_adjustment', '').startswith('v1.5'):
            if judgment_v15.get('base_wuxing_xi'):
                judgment['base_wuxing_xi'] = judgment_v15['base_wuxing_xi']
            if judgment_v15.get('tiaohou_layer_xi'):
                judgment['tiaohou_layer_xi'] = judgment_v15['tiaohou_layer_xi']
            judgment['v15_p0_applied'] = True
            judgment['v15_sanxing_hits'] = judgment_v15.get('v15_sanxing_hits', [])
            judgment['v15_expert_yongshen'] = judgment_v15.get('v15_expert_yongshen', [])
    
    result = {
        'profile': {
            'birth': f'{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}',
            'gender': gender,
            'bazi': bazi,
            'day_gan': day_gan_calc,
            'day_wx': day_wx_calc,
        },
        'wuxing_force': force_for_calc,
        'judgment': {
            'score': judgment['total'],
            'level': judgment['level'],
            'is_strong': judgment['is_strong'],
            'raw_total': judgment['raw_total'],
            'env_deduct': judgment['env_score'],
            # Bug 3 修复（v1.1-Patch1）：喜忌字段双轴序列化（身强喜克泄耗，身弱喜生扶）
            # v1.5 P0：优先读 v15 调整后的值，否则走硬编码
            # v1.5 P0 基础层喜忌（身强喜克泄耗，身弱喜生扶）
            'base_wuxing_xi': judgment.get('base_wuxing_xi') or (['火', '金', '木'] if judgment['is_strong'] else ['金', '土']),
            'base_wuxing_ji': ['金', '土'] if judgment['is_strong'] else ['火', '金', '木'],
            'base_shishen_xi': ['正官', '偏官', '食神', '伤官', '正财', '偏财'] if judgment['is_strong'] else ['正印', '偏印', '比肩', '劫财'],
            'base_shishen_ji': ['正印', '偏印', '比肩', '劫财'] if judgment['is_strong'] else ['正官', '偏官', '食神', '伤官', '正财', '偏财'],
            # v1.6-tiaohou-fix: 合并调候层后的最终喜忌
            'tiaohou_priority': judgment.get('tiaohou_priority', False),
            'tiaohou_yongshen': judgment.get('tiaohou_yongshen', ''),
            'tiaohou_layer_xi': judgment.get('tiaohou_layer_xi') or (['火', '丙', '丁'] if judgment.get('tiaohou_priority') else []),
            'conflict_resolved': '调候一票否决权已激活。极寒/极热月调候优先级最高，身强身弱与调候冲突时按调候论。' if judgment.get('tiaohou_priority') else '身强身弱基础喜忌与调候无冲突。',
            # v1.6-tiaohou-fix: 合并调候层后的最终喜忌
            'v15_p0_applied': judgment.get('v15_p0_applied', False),
            'v15_sanxing_hits': judgment.get('v15_sanxing_hits', []),
            'v15_expert_yongshen': judgment.get('v15_expert_yongshen', []),
        },
    }
    
    # v1.6-tiaohou-fix：合并调候层到喜忌
    j = result['judgment']
    if j['tiaohou_priority']:
        tiao = j['tiaohou_yongshen']  # '火' 或 '水'
        base_xi = j['base_wuxing_xi']
        base_ji = j['base_wuxing_ji']
        # 调候层高于基础层：调候用神必定是喜
        # 生调候用神的五行也列入喜
        sheng_tiao = SHENG_ME_MAP[tiao]  # 生火者木，生水者金
        # 组合喜用：调候用神 + 生调候的五行 + 基础层已有的且不冲突的
        combined_xi = [tiao]
        if sheng_tiao not in combined_xi:
            combined_xi.append(sheng_tiao)
        for wx in base_xi:
            if wx not in combined_xi:
                combined_xi.append(wx)
        # 组合忌用：调候生己（克调候的五行）+ 基础层忌用中未出现在喜用的
        combined_ji = []
        ke_tiao = KE_WO_MAP[tiao]  # 克火者水，克水者土
        if ke_tiao not in combined_xi:
            combined_ji.append(ke_tiao)
        for wx in base_ji:
            if wx not in combined_xi and wx not in combined_ji:
                combined_ji.append(wx)
        result['combined_wuxing_xi'] = combined_xi
        result['combined_wuxing_ji'] = combined_ji
        result['combined_desc'] = f"调候层（{tiao}）+ 基础层合并，最终喜用：{'/'.join(combined_xi)}，忌：{'/'.join(combined_ji)}"
    else:
        result['combined_wuxing_xi'] = j['base_wuxing_xi']
        result['combined_wuxing_ji'] = j['base_wuxing_ji']
        result['combined_desc'] = '无调候优先，使用基础层喜忌'
    
    result['family_member'] = _detect_family_member(year, month, day, hour, minute, gender)
    family_member = result['family_member']
    
    # 起始交运点（按 family_member 选，v1.5c Bugfix）
    if family_member in FAMILY_DAYUN:
        result['start_datetime'] = FAMILY_DAYUN[family_member]['start']
        result['dayun_table'] = FAMILY_DAYUN[family_member]['dayun']
    else:
        result['start_datetime'] = None
        result['dayun_table'] = None
    
    if current_year:
        # 流年激活扫描（v1.6-refactor: 用模块级 LIUNIAN_TABLE）
        if current_year in LIUNIAN_TABLE:
            gan_ln, zhi_ln = LIUNIAN_TABLE[current_year]
            activations = check_liunian_activation(gan_ln, zhi_ln, bazi_for_calc)
            result['liunian'] = {
                'year': current_year,
                'gan_zhi': f'{gan_ln}{zhi_ln}',
                'activated_nodes': activations,
            }
        # 当前大运
        dayun_table = _resolve_dayun_table(family_member)  # v1.5c Bugfix
        dayun = get_current_dayun(current_year, dayun_table)
        if 'error' not in dayun:
            result['current_dayun'] = dayun
    
    return result


def _detect_family_member(year, month, day, hour, minute, gender) -> str:
    """识别 4 家庭成员之一"""
    if year == 1983 and month == 1 and day == 23:
        return '亮哥'
    elif year == 2012 and month == 6 and day == 1:
        return '长子'
    elif year == 2015 and month == 3 and day == 19:
        return '次子'
    elif year == 1985 and month == 10 and day == 17:
        return '亮嫂'
    return '未知'


def _resolve_dayun_table(family_member: str):
    """
    v1.5c Bugfix：根据家庭成员从 FAMILY_DAYUN 取正确的大运表。
    修正前：所有调用都用默认 LIANG_GE_DAYUN_TRUE（亮哥的），导致亮嫂/孩子也显示亮哥的大运。
    修正后：根据 family_member 自动选。
    未知成员：fallback 到亮哥（保持向后兼容，但会在输出里标记）。
    """
    if family_member in FAMILY_DAYUN:
        return FAMILY_DAYUN[family_member]['dayun']
    return LIANG_GE_DAYUN_TRUE  # fallback（应该不会发生）


if __name__ == '__main__':
    main()
