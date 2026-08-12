#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mark questions whose stored answer is likely a SOURCE ERROR.
For high-confidence cases: correct the answer AND add a `flag` note.
For lower-confidence: add a `flag` note only (answer unchanged).
Idempotent: skips lines that already have `,flag:`.
"""
import re, sys

PATH = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
content = open(PATH, encoding='utf-8').read()
lines = content.split('\n')

def esc(s):
    return s.replace('\\', '\\\\').replace("'", "\\'")

# (unique q-text snippet, new_a or None, flag message)
ENTRIES = [
    # ---- high confidence: correct the answer + flag ----
    ('测度数据集中趋势的指标有（）。', '[1,2]',
     '源站答案疑似错误：方差、标准差是离散程度指标而非集中趋势；正确为众数、均值（BC）'),
    ('下列各项中，属于企业所有者权益的有（）。', '[1,2,3]',
     '源站答案疑似错误：预付款项属流动资产而非所有者权益；正确为BCD'),
    ('在资产负债表中，根据总账科目期末余额与其备抵科目抵消后的数据填列的项目有（）。', '[1,2,3]',
     '源站答案疑似错误：实收资本按总账余额直接填列，不按备抵抵消；正确为BCD'),
    ('下列关于担保物权的表述中，正确的有（）。', '[1,2,3]',
     '源站答案疑似错误：担保物权是从物权而非主权利，A项错；正确为BCD'),
    ('我国政府预算体系包括（）。', '[1,2,3]',
     '源站答案疑似错误：我国政府预算体系不含“税收支出预算”；正确为BCD'),
    ('深化预算管理制度改革的主要内容包括（）。', '[1,2,3]',
     '源站答案疑似错误：“推进中央与地方财政事权划分”属现代财政制度，非深化预算改革内容；正确为BCD'),
    ('根据《中华人民共和国预算法》，各级人民政府的预算管理职权有（）。', '[0,1,2]',
     '源站答案疑似错误：审批本级预算调整方案属人大常委会职权，D项错；正确为ABC'),
    ('关于合理划分中央与地方财政事权和支出责任原则，下列描述正确的有（）。', '[0,1,2]',
     '源站答案疑似错误：信息困难的基本公共服务优先作为地方事权，D项说反了；正确为ABC'),
    ('合理划分中央与地方财政事权和支出责任的总体要求包括（）。', '[0,1,2]',
     '源站答案疑似错误：总体要求不含“加强中央对微观事务的直接管理”，D项错；正确为ABC'),
    ('关于美国金融监管体制的说法，正确的有（）。', '[0,1,2]',
     '源站答案疑似错误：监管联邦注册银行的是货币监理署而非美联储，D项错；正确为ABC'),
    ('下列关于各类型金融危机之间相互关系的说法，正确的有（）。', '[1,2,3]',
     '源站答案疑似错误：危机可同时爆发，A项错；正确为BCD'),
    ('商业银行在办理境外直接投资人民币结算业务时应履行的义务包括（）。', '[1,2,3]',
     '源站答案疑似错误：应“事后管理”而非“事前管理”，A项错；正确为BCD'),
    ('关于数据科学的说法，正确的有（）。', '[1,2,3]',
     '源站答案疑似错误：数据科学不止涉及统计学，A项错；正确为BCD'),
    ('关于大数据多样性的说法，正确的有（）。', '[1,2,3]',
     '源站答案疑似错误：大数据含结构化/半结构化/非结构化，A项“只包括结构化”错；正确为BCD'),
    ('关于增长量与平均增长量的说法，正确的有（）。', '[0,1,2]',
     '源站答案疑似错误：平均增长量是逐期增长量而非累计增长量的序时平均，D项错；正确为ABC'),
    ('在经济法调整对象中，对宏观经济管理关系的说法正确的有（）。', '[1,2,3]',
     '源站答案疑似错误：宏观经济管理关系是经济关系而非行政关系，A项错；正确为BCD'),
    # ---- medium / ambiguous: flag only (answer unchanged) ----
    ('根据经济周期理论，导致经济波动的因素有（）。', None,
     '答案存疑：解析所列波动因素不含“通货膨胀率”，疑为BCD，建议对照教材核实'),
    ('市场并不总是有效率的，政府经济活动范围主要集中在（）。', None,
     '答案存疑：政府经济活动范围不含“保证绝对公平”，疑为BCD，建议对照教材核实'),
    ('合理划分中央与地方财政事权和支出责任的原则，包括（）。', None,
     '答案存疑：划分原则应为“支出责任与财政事权相适应”，而非“中央统筹、地方协助”，疑为ABC，建议核实'),
    ('关于统计报表填报要求的说法，正确的有（）。', None,
     '答案存疑：统计报表要求为统一表式/指标/报送时间/报送程序，疑不含“填表人统一”，建议核实'),
    ('会计要素的确认计量原则包括（）。', None,
     '答案存疑：确认计量原则不含“实质重于形式”（属信息质量要求），疑为ABC，建议核实'),
    ('抽样调查的一般步骤包括（）。', None,
     '答案存疑：步骤一般为确定问题→方案设计→实施→数据处理→撰写报告，“搜集统计资料”表述存疑，建议核实'),
    ('先履行抗辩权成立的条件包括（）。', None,
     '答案存疑：先履行抗辩权条件通常不含“后给付义务人有不能给付危险”（更接近不安抗辩权），建议核实'),
    ('关于税收基本特征的说法，正确的是（）。', None,
     '答案存疑：该题解析与备选项相互矛盾（三项均被指错），源站答案可能有误，建议核实'),
    ('在编制财务会计报告之前，为了保证报告的数字真实可靠，应（）。', None,
     '答案存疑：编报前要求为账证/账账/账实相符，“账表相符”表述存疑，建议核实'),
]

re_a = re.compile(r'([{, ])a:(\[[^\]]*\]|\d+)')
total_changed = 0
for qsnip, newa, flag in ENTRIES:
    matched = [i for i, ln in enumerate(lines) if qsnip in ln]
    if not matched:
        print(f'!! NOT FOUND: {qsnip[:30]}')
        continue
    for li in matched:
        ln = lines[li]
        if ',flag:' in ln:
            continue
        # correct answer if requested
        if newa is not None:
            ln = re_a.sub(lambda m: m.group(1) + 'a:' + newa, ln, count=1)
        # insert flag before the final object-closing '}'
        last_brace = ln.rfind('}')
        if last_brace == -1:
            print(f'!! no }} on line {li+1}')
            continue
        ln = ln[:last_brace] + ",flag:'" + esc(flag) + "'" + ln[last_brace:]
        lines[li] = ln
        total_changed += 1
    print(f'OK ({len(matched)} line(s)): {qsnip[:28]} -> a={newa}')

content = '\n'.join(lines)
open(PATH, 'w', encoding='utf-8').write(content)
print(f'\nTotal lines modified: {total_changed}')
