#!/usr/bin/env python3
"""
bazi_common.py - 八字验算公共数据与核心算法

从 bazi-verify.py 提取的所有常量和非 main 函数。
被 bazi-verify.py 和 bazi-verify-v2.py 使用。
"""

from typing import List, Dict, Tuple

# ════════════════════════════════════════════════════════
# 基础数据
# ════════════════════════════════════════════════════════

TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

GAN_WUXING = {
    '甲': '木', '乙': '木',
    '丙': '火', '丁': '火',
    '戊': '土', '己': '土',
    '庚': '金', '辛': '金',
    '壬': '水', '癸': '水',
}

GAN_YINYANG = {
    '甲': '阳', '乙': '阴',
    '丙': '阳', '丁': '阴',
    '戊': '阳', '己': '阴',
    '庚': '阳', '辛': '阴',
    '壬': '阳', '癸': '阴',
}

ZHI_WUXING = {
    '子': '水', '亥': '水',
    '寅': '木', '卯': '木',
    '巳': '火', '午': '火',
    '申': '金', '酉': '金',
    '辰': '土', '戌': '土', '丑': '土', '未': '土',
}

ZHI_CANGAN = {
    '子': ['癸'],
    '丑': ['己', '癸', '辛'],
    '寅': ['甲', '丙', '戊'],
    '卯': ['乙'],
    '辰': ['戊', '乙', '癸'],
    '巳': ['丙', '戊', '庚'],
    '午': ['丁', '己'],
    '未': ['己', '丁', '乙'],
    '申': ['庚', '壬', '戊'],
    '酉': ['辛'],
    '戌': ['戊', '辛', '丁'],
    '亥': ['壬', '甲'],
}

CANGAN_WEIGHT = [1.0, 0.5, 0.2]

SHENG = {
    '木': '火', '火': '土', '土': '金', '金': '水', '水': '木',
}
KE = {
    '金': '木', '木': '土', '土': '水', '水': '火', '火': '金',
}

YUELING_WANGSHUAI = {
    '寅': {'木': 1.0, '火': 0.5, '土': 0.3, '金': 0.2, '水': 0.3},
    '卯': {'木': 1.0, '火': 0.5, '土': 0.3, '金': 0.2, '水': 0.3},
    '辰': {'土': 1.0, '水': 0.4, '木': 0.4, '金': 0.4, '火': 0.3},
    '巳': {'火': 1.0, '土': 0.5, '金': 0.3, '木': 0.3, '水': 0.2},
    '午': {'火': 1.0, '土': 0.5, '金': 0.3, '木': 0.3, '水': 0.2},
    '未': {'土': 1.0, '火': 0.4, '木': 0.4, '金': 0.4, '水': 0.3},
    '申': {'金': 1.0, '水': 0.4, '土': 0.4, '木': 0.3, '火': 0.2},
    '酉': {'金': 1.0, '水': 0.4, '土': 0.4, '木': 0.3, '火': 0.2},
    '戌': {'土': 1.0, '火': 0.4, '金': 0.4, '木': 0.4, '水': 0.3},
    '亥': {'水': 1.0, '木': 0.5, '金': 0.3, '火': 0.2, '土': 0.3},
    '子': {'水': 1.0, '木': 0.5, '金': 0.3, '火': 0.2, '土': 0.3},
    '丑': {'土': 1.0, '水': 0.4, '金': 0.4, '木': 0.4, '火': 0.3},
}

TIAOHOU = {
    '寅': [('丙', '主'), ('壬', '辅')],
    '卯': [('壬', '主'), ('甲', '辅')],
    '辰': [('壬', '主'), ('甲', '辅')],
    '巳': [('癸', '主'), ('丙', '辅')],
    '午': [('壬', '主'), ('癸', '辅')],
    '未': [('壬', '主'), ('癸', '辅')],
    '申': [('丁', '主'), ('壬', '辅')],
    '酉': [('丁', '主'), ('甲', '辅')],
    '戌': [('甲', '主'), ('壬', '辅')],
    '亥': [('戊', '主'), ('甲', '辅')],
    '子': [('戊', '主'), ('丙', '辅')],
    '丑': [('丙', '主'), ('壬', '辅')],
}

SANXING = [
    ('子卯', '无礼之刑', ['子', '卯']),
    ('寅巳申', '恃势之刑', ['寅', '巳', '申']),
    ('丑戌未', '无恩之刑', ['丑', '戌', '未']),
    ('辰午酉亥', '自刑', ['辰', '午', '酉', '亥']),
]

LIUHAI = [
    ('子未', '子未相害'),
    ('丑午', '丑午相害'),
    ('寅巳', '寅巳相害'),
    ('卯辰', '卯辰相害'),
    ('申亥', '申亥相害'),
    ('酉戌', '酉戌相害'),
]

SANHE = [
    ('申子辰', '水局三合', '水'),
    ('亥卯未', '木局三合', '木'),
    ('寅午戌', '火局三合', '火'),
    ('巳酉丑', '金局三合', '金'),
]

TIANGAN_WUHE = {
    '甲': '己', '己': '甲',
    '乙': '庚', '庚': '乙',
    '丙': '辛', '辛': '丙',
    '丁': '壬', '壬': '丁',
    '戊': '癸', '癸': '戊',
}

LU_SHEN = {
    '甲': '寅', '乙': '卯',
    '丙': '巳', '丁': '午',
    '戊': '巳', '己': '午',
    '庚': '申', '辛': '酉',
    '壬': '亥', '癸': '子',
}

TAOHUA = {
    '申子辰': '酉', '寅午戌': '卯',
    '亥卯未': '子', '巳酉丑': '午',
}

YIMA = {
    '申子辰': '寅', '寅午戌': '申',
    '亥卯未': '巳', '巳酉丑': '亥',
}


# ════════════════════════════════════════════════════════
# 核心算法
# ════════════════════════════════════════════════════════

def get_shishen(day_gan: str, other_gan: str) -> str:
    """核心十神算法"""
    if day_gan == other_gan:
        return '日主'
    
    me_wx = GAN_WUXING[day_gan]
    me_yy = GAN_YINYANG[day_gan]
    other_wx = GAN_WUXING[other_gan]
    other_yy = GAN_YINYANG[other_gan]
    
    same_yy = (me_yy == other_yy)
    
    if me_wx == other_wx:
        return '比肩' if same_yy else '劫财'
    if SHENG[other_wx] == me_wx:
        return '偏印（枭神）' if same_yy else '正印'
    if SHENG[me_wx] == other_wx:
        return '食神' if same_yy else '伤官'
    if KE[other_wx] == me_wx:
        return '七杀' if same_yy else '正官'
    if KE[me_wx] == other_wx:
        return '偏财' if same_yy else '正财'
    
    return '???'


def parse_ganzhi(gz: str) -> Tuple[str, str]:
    if len(gz) != 2:
        raise ValueError(f"干支 '{gz}' 长度错误（应为 2）")
    gan, zhi = gz[0], gz[1]
    if gan not in TIANGAN:
        raise ValueError(f"非法天干 '{gan}'")
    if zhi not in DIZHI:
        raise ValueError(f"非法地支 '{zhi}'")
    return gan, zhi


def calc_wuxing_force(bazi: List[Tuple[str, str]]) -> Dict[str, float]:
    force = {'金': 0.0, '木': 0.0, '水': 0.0, '火': 0.0, '土': 0.0}
    month_zhi = bazi[1][1]
    month_boost = YUELING_WANGSHUAI.get(month_zhi, {})
    
    for col_idx, (gan, zhi) in enumerate(bazi):
        wx = GAN_WUXING[gan]
        weight = 1.0
        if col_idx == 1:
            weight *= month_boost.get(wx, 1.0) * 1.2
        force[wx] += weight
        
        cangans = ZHI_CANGAN[zhi]
        for i, cg in enumerate(cangans):
            cg_wx = GAN_WUXING[cg]
            cg_weight = CANGAN_WEIGHT[i] if i < len(CANGAN_WEIGHT) else 0.1
            if col_idx == 1:
                cg_weight *= month_boost.get(cg_wx, 1.0)
            force[cg_wx] += cg_weight
    
    return force


def check_sanxing(bazi: List[Tuple[str, str]]) -> List[str]:
    zhis = [zhi for _, zhi in bazi]
    found = []
    for name, desc, members in SANXING:
        if all(m in zhis for m in members):
            found.append(f"{name}（{desc}）: {' '.join([f'{m}{zhis.count(m)}' for m in members])}")
    return found


def check_fuyin(bazi: List[Tuple[str, str]]) -> List[str]:
    fuyin = []
    for i in range(4):
        for j in range(i+1, 4):
            if bazi[i] == bazi[j]:
                fuyin.append(f"第{['年','月','日','时'][i]}柱与第{['年','月','日','时'][j]}柱伏吟: {bazi[i][0]}{bazi[i][1]}")
    return fuyin


def check_liuhai(bazi: List[Tuple[str, str]]) -> List[str]:
    zhis = [z for _, z in bazi]
    found = []
    for pair, name in LIUHAI:
        if all(c in zhis for c in pair):
            found.append(name)
    return found


def check_sanhe(bazi: List[Tuple[str, str]]) -> List[str]:
    zhis = [z for _, z in bazi]
    found = []
    for combo, name, wx in SANHE:
        if all(c in zhis for c in combo):
            found.append(f"{name}（{wx}势成）")
    return found


def check_wuhe(bazi: List[Tuple[str, str]], day_gan: str) -> List[str]:
    tgs = [g for g, _ in bazi]
    found = []
    seen = set()
    for g in tgs:
        if g == day_gan:
            continue
        other = TIANGAN_WUHE.get(g)
        if other and other in tgs:
            pair_key = tuple(sorted([g, other]))
            if pair_key in seen:
                continue
            seen.add(pair_key)
            marks = []
            if g == day_gan or other == day_gan:
                marks.append("涉日主")
            found.append(f"{g}与{other}相合{'（'+'、'.join(marks)+'）' if marks else ''}")
    return found


def check_special_geju(force: Dict[str, float], day_gan: str, day_wx: str, bazi: List[Tuple[str, str]]) -> List[Dict]:
    total = sum(force.values())
    pct = {k: v/total*100 for k, v in force.items()}
    findings = []
    
    if day_wx == '金' and pct.get('土', 0) >= 30 and pct.get('金', 0) + pct.get('土', 0) >= 55 and pct.get('土', 0) >= pct.get('金', 0) * 0.9:
        findings.append({
            'name': '土多金埋',
            'desc': f'日主金被厚土盖住（金{pct["金"]:.0f}%，土{pct["土"]:.0f}%，合计{pct["金"]+pct["土"]:.0f}%）',
            'xi': '水（泄秀）＋木（疏土）',
            'ji': '土（加埋）＋金（被埋更深）',
            'yong': '水、木（以水为先）',
            'note': '与普通「身强」不同。身强是金本强、土助强；土多金埋是金被压出不来',
        })
    
    if day_wx == '水' and pct.get('金', 0) >= 35:
        findings.append({
            'name': '金多水浊',
            'desc': f'日主水被重金生起，反而浑浊（金{pct["金"]:.0f}%）',
            'xi': '木（泄水）＋火（照水）',
            'ji': '金（加浊）＋水（泛滥）',
            'yong': '木',
        })
    
    max_wx = max(pct, key=pct.get)
    if pct[max_wx] >= 70:
        findings.append({
            'name': f'{max_wx}行得气格（候选）',
            'desc': f'{max_wx}气专旺{pct[max_wx]:.0f}%，可能为专旺格',
            'xi': f'{max_wx}（顺其气势）',
            'ji': f'克{max_wx}者（逆势）',
            'yong': f'{max_wx}',
            'note': '需看是否日主在旺气中。若日主是最大五行，可定专旺',
        })
    
    if pct[day_wx] < 15:
        lu = LU_SHEN.get(day_gan)
        has_root = lu in [b[1] for b in bazi] if lu else False
        all_cg = []
        for _, zhi in bazi:
            all_cg.extend(ZHI_CANGAN[zhi])
        has_cg_root = day_gan in all_cg
        if not has_root and not has_cg_root:
            findings.append({
                'name': '从弱格（候选）',
                'desc': f'日主{pct[day_wx]:.0f}%极弱，无禄、无藏干根',
                'xi': '克泄耗日主者（顺从弱势）',
                'ji': '生扶日主者（逆势）',
                'yong': '需进一步确认（参考月令）',
            })
    
    tgs = [g for g, _ in bazi]
    month_gan = bazi[1][0]
    hour_gan = bazi[3][0]
    he_target = TIANGAN_WUHE.get(day_gan)
    if he_target and (he_target == month_gan or he_target == hour_gan):
        if he_target == month_gan:
            target, col = month_gan, '月'
        else:
            target, col = hour_gan, '时'
        findings.append({
            'name': f'化格候选（{day_gan}{target}合）',
            'desc': f'日干与{col}干{day_gan}{target}合',
            'xi': '需师傅判断',
            'ji': '需师傅判断',
            'yong': '需师傅判断',
            'note': '化格成立需满足多个条件：月令引化、柱中无破合、地支会局。仅提示候选，不定论',
        })
    
    return findings


def find_tongguan(force: Dict[str, float], day_wx: str) -> List[str]:
    total = sum(force.values())
    pct = {k: v/total*100 for k, v in force.items()}
    findings = []
    
    water = pct.get('水', 0)
    fire = pct.get('火', 0)
    
    if water > 30 and fire < 10:
        findings.append(f"偏寒（水{water:.0f}%多，火{fire:.0f}%少）── 需丙火解寒，取用先看调候")
    if fire > 30 and water < 10:
        findings.append(f"偏燥（火{fire:.0f}%多，水{water:.0f}%少）── 需壬癸水润局")
    if pct.get('土', 0) > 40 and pct.get('木', 0) < 10:
        findings.append(f"偏燥（土{pct['土']:.0f}%多）── 燥土需水润，取水通关")
    if pct.get('土', 0) > 40 and water > 20:
        findings.append(f"土紧湿重（土{pct['土']:.0f}%+水{water:.0f}%）── 需木疏土通关")
    
    if pct.get('金', 0) > 25 and pct.get('木', 0) > 20:
        findings.append("金木交战 ── 需水通关（金生水→水生木）")
    if pct.get('水', 0) > 25 and pct.get('火', 0) > 20:
        findings.append("水火交战 ── 需木通关（水生木→木生火）")
    if pct.get('火', 0) > 25 and pct.get('金', 0) > 20:
        findings.append("火金交战 ── 需土通关（火生土→土生金）")
    
    return findings


def judge_xiji(force: Dict[str, float], day_wx: str, day_gan: str, bazi: List[Tuple[str, str]]) -> Dict:
    """
    判断身强/身弱
    
    身强信号：
    1. 日主同类（同五行）占比高
    2. 印（生我者）占比高
    3. 月令生日主或同五行（得月令之旺）─ +10% 加成
    4. 柱中有禄神 ─ +5% 加成
    
    身强力量 = 同类 + 印 + 月令加成 + 禄神加成
    """
    total = sum(force.values())
    if total == 0:
        return {'error': '力量为 0'}
    
    pct = {k: v/total*100 for k, v in force.items()}
    sheng_me_map = {'金': '土', '木': '水', '水': '金', '火': '木', '土': '火'}
    sheng_me = sheng_me_map[day_wx]
    me_help = pct[day_wx] + pct[sheng_me]
    
    # 月令是否生日主 或 同五行
    month_zhi = bazi[1][1]
    month_wx = ZHI_WUXING.get(month_zhi, '')
    month_sheng = (month_wx == day_wx) or (SHENG.get(month_wx) == day_wx)
    if month_sheng:
        me_help += 10
    
    # 禄神
    lu = LU_SHEN.get(day_gan)
    has_lu = lu and lu in [b[1] for b in bazi]
    if has_lu:
        me_help += 5
    
    is_strong = me_help > 50
    
    # 极缺五行提示
    scarce = [k for k, v in pct.items() if v < 5]
    
    return {
        'force_pct': pct,
        'day_wx': day_wx,
        'sheng_me': sheng_me,
        'is_strong': is_strong,
        'me_help': me_help,
        'month_sheng': month_sheng,
        'has_lu': has_lu,
        'scarce': scarce,
    }


# ════════════════════════════════════════════════════════
# 输出
# ════════════════════════════════════════════════════════

def format_output(bazi_str: List[str], bazi: List[Tuple[str, str]]):
    day_gan = bazi[2][0]
    day_wx = GAN_WUXING[day_gan]
    month_zhi = bazi[1][1]
    
    lines = []
    lines.append("═" * 60)
    lines.append(f"八字四柱：{' '.join(bazi_str)}")
    lines.append(f"日主：{day_gan}（{GAN_YINYANG[day_gan]}{day_wx}）")
    lines.append("═" * 60)
    
    # 1. 天干十神表
    lines.append("")
    lines.append("【天干十神表】")
    positions = ['年干', '月干', '日干', '时干']
    for i, (gan, _) in enumerate(bazi):
        if i == 2:
            continue
        ss = get_shishen(day_gan, gan)
        me_yy = GAN_YINYANG[day_gan]
        other_yy = GAN_YINYANG[gan]
        same = '同性' if me_yy == other_yy else '异性'
        lines.append(f"  {positions[i]} {gan}（{GAN_WUXING[gan]}·{other_yy}）── {ss}（{same}）")
    lines.append(f"  日干 {day_gan}（{day_wx}·{GAN_YINYANG[day_gan]}）── 日主")
    
    # 2. 地支藏干十神表
    lines.append("")
    lines.append("【地支藏干十神表】")
    zhi_positions = ['年支', '月支', '日支', '时支']
    for i, (_, zhi) in enumerate(bazi):
        cangans = ZHI_CANGAN[zhi]
        cg_strs = []
        for cg in cangans:
            ss = get_shishen(day_gan, cg)
            cg_strs.append(f"{cg}({ss})")
        zhi_wx = ZHI_WUXING[zhi]
        lines.append(f"  {zhi_positions[i]} {zhi}（{zhi_wx}）  藏: {' '.join(cg_strs)}")
    
    # 3. 五行力量
    force = calc_wuxing_force(bazi)
    total = sum(force.values())
    lines.append("")
    lines.append("【五行力量】（含月令加权）")
    for wx in ['金', '木', '水', '火', '土']:
        pct_v = force[wx] / total * 100
        bar = '█' * int(pct_v / 2)
        lines.append(f"  {wx}: {force[wx]:5.1f}  {pct_v:5.1f}%  {bar}")
    
    # 4. 喜忌判断
    lines.append("")
    lines.append("【喜忌判断】")
    judgment = judge_xiji(force, day_wx, day_gan, bazi)
    pct = judgment['force_pct']
    
    lines.append(f"  日主五行：{day_wx}，生我者为：{judgment['sheng_me']}")
    
    # 身强身弱详细判定
    me_help = judgment.get('me_help', pct[day_wx] + pct[judgment['sheng_me']])
    base_pct = pct[day_wx] + pct[judgment['sheng_me']]
    signals = []
    if judgment.get('month_sheng'):
        signals.append("得月令之旺")
    if judgment.get('has_lu'):
        signals.append("有禄神")
    signal_str = f"（含 {'+'.join(signals)} 加成）" if signals else ""
    lines.append(f"  身强/身弱：{'身强' if judgment['is_strong'] else '身弱'}（{day_wx}+{judgment['sheng_me']} 合计 {base_pct:.1f}% + 加成 {me_help-base_pct:.0f}% = {me_help:.1f}%{signal_str}）")
    
    # 极缺五行提示
    if judgment.get('scarce'):
        lines.append(f"  ⚠️  极缺五行：{', '.join(judgment['scarce'])}（< 5%）")
    
    lines.append("")
    lines.append("  喜用神（扶抑法）：")
    if judgment['is_strong']:
        ke_wo = {'木': '金', '金': '火', '火': '水', '水': '土', '土': '木'}
        guan_sha_wx = ke_wo[day_wx]
        shishen_wx = SHENG[day_wx]
        cai_wx = KE[day_wx]
        lines.append(f"    喜：{guan_sha_wx}（官杀，制身）")
        lines.append(f"    喜：{shishen_wx}（食伤，泄秀）")
        lines.append(f"    喜：{cai_wx}（财星，耗身）")
        lines.append(f"    忌：{day_wx}（比劫，帮身太重）")
        lines.append(f"    忌：{judgment['sheng_me']}（印，生身太重）")
    else:
        lines.append(f"    喜：{judgment['sheng_me']}（印，生身）")
        lines.append(f"    喜：{day_wx}（比劫，帮身）")
        lines.append(f"    忌：克我者（官杀，克身）")
        lines.append(f"    忌：{SHENG[day_wx]}（食伤，泄身）")
        lines.append(f"    忌：{KE[day_wx]}（财星，耗身）")
    
    # 5. 调候
    lines.append("")
    lines.append(f"【调候用神】月支：{month_zhi}")
    tiaohou = TIAOHOU.get(month_zhi, [])
    for gan, role in tiaohou:
        has = "原局有" if gan in [b[0] for b in bazi] else "原局无"
        all_cg = []
        for _, zhi in bazi:
            all_cg.extend(ZHI_CANGAN[zhi])
        if gan in all_cg:
            has = "原局有（含藏干）"
        lines.append(f"  {gan}（{role}调候）── {has}")
    
    # 6. 异常标记（扩展版）
    lines.append("")
    lines.append("【异常标记】")
    
    sanxing = check_sanxing(bazi)
    if sanxing:
        for sx in sanxing:
            lines.append(f"  ⚠️  {sx} 成局")
    else:
        lines.append("  ✅ 无三刑")
    
    fuyin = check_fuyin(bazi)
    if fuyin:
        for fy in fuyin:
            lines.append(f"  ⚠️  {fy}")
    else:
        lines.append("  ✅ 无伏吟")
    
    liuhai = check_liuhai(bazi)
    if liuhai:
        for lh in liuhai:
            lines.append(f"  ⚠️  {lh}")
    else:
        lines.append("  ✅ 无六害")
    
    sanhe = check_sanhe(bazi)
    if sanhe:
        for sh in sanhe:
            lines.append(f"  🔷 {sh}")
    else:
        lines.append("  ✅ 无三合")
    
    wuhe = check_wuhe(bazi, day_gan)
    if wuhe:
        for wh in wuhe:
            lines.append(f"  🔷 {wh}")
    else:
        lines.append("  ✅ 无天干合（涉日主）")
    
    # 禄神
    lu = LU_SHEN.get(day_gan)
    if lu and lu in [b[1] for b in bazi]:
        lines.append(f"  ℹ️  禄神在{lu}（{day_gan}禄）── 有根有禄")
    
    # 桃花
    for combo, t in TAOHUA.items():
        if month_zhi in combo and t in [b[1] for b in bazi]:
            lines.append(f"  ℹ️  桃花在{t}（{month_zhi}局桃花）")
    
    # 驿马
    for combo, y in YIMA.items():
        if month_zhi in combo and y in [b[1] for b in bazi]:
            lines.append(f"  ℹ️  驿马在{y}（{month_zhi}局驿马）── 主奔波动")
    
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
            if 'note' in sp:
                lines.append(f"     注：{sp['note']}")
    else:
        lines.append("  ✅ 未识别出特殊格局（按普通身强/身弱处理）")
    
    # 8. 通关用神
    lines.append("")
    lines.append("【通关用神建议】")
    tongguan = find_tongguan(force, day_wx)
    if tongguan:
        for tg in tongguan:
            lines.append(f"  💡 {tg}")
    else:
        lines.append("  ✅ 五行流通，无明显战局/失衡")
    
    lines.append("")
    lines.append("═" * 60)
    lines.append("✅ 验证完成。下一步：")
    lines.append("  1. 核对十神阴阳是否与你预期一致")
    lines.append("  2. 检查喜忌是否符合命主实际情况")
    lines.append("  3. 异常标记是否需要重点分析")
    lines.append("  4. 特殊格局是否成立（人工审核）")
    lines.append("  5. 通关建议是否合理")
    lines.append("  6. 以上无异议后，再开始具体推算")
    lines.append("")
    lines.append("⚠️  本工具的局限（v2 仍需人工审核）：")
    lines.append("  - 特殊格局仅做候选检测，定论需师傅判断")
    lines.append("  - 化格成立需月令引化+无破合+地支会局")
    lines.append("  - 通关用神基于战局模式，特殊格局的取用仍需师傅拍板")
    lines.append("  - 不解决「算对但解读错」问题（这个靠真命例校准）")
    lines.append("  - 流年应事、神煞、本命事件不在本工具范围")
    lines.append("═" * 60)
    
    return '\n'.join(lines)
