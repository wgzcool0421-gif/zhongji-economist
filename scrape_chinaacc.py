#!/usr/bin/env python3
"""
Batch scrape chinaacc.com weekly exercises for 经济基础 questions.
Uses proper HTML structure parsing.
"""
import urllib.request
import re
import json
import time
import os
import html as html_module

# ===== Chapter keyword mapping =====
CHAPTER_KEYWORDS = {
    1: ['社会主义', '公有制', '所有制', '按劳分配', '市场经济体制', '资源配置', '全民所有制', '个体经济', '私营经济', '混合所有制', '财产性收入', '股份合作制'],
    2: ['需求价格弹性', '需求交叉弹性', '供给价格弹性', '需求收入弹性', '均衡价格', '最高限价', '保护价格', '需求曲线', '供给曲线', '点弹性', '弧弹性'],
    3: ['生产函数', '总产量', '平均产量', '边际产量', '规模报酬', '成本函数', '机会成本', '显成本', '隐成本', '短期成本', '长期成本', '边际成本', '固定成本', '可变成本', '企业形成', '科斯', '交易成本', '预算线', '消费者均衡', '无差异曲线'],
    4: ['市场结构', '完全竞争', '完全垄断', '垄断竞争', '寡头垄断', '价格歧视', '进入障碍', '自然垄断', '古诺模型'],
    5: ['生产要素', '引致需求', '边际产品价值', '边际收益产品', '边际要素成本', '劳动的供给', '工资', '替代效应', '收入效应', '后弯', '地租', '准租金', '经济租金'],
    6: ['帕累托', '市场失灵', '外部性', '公共物品', '信息不对称', '垄断', '科斯定理', '非竞争性', '非排他性', '逆向选择', '道德风险', '公共选择'],
    7: ['国民收入核算', 'GDP', '国内生产总值', '消费函数', '储蓄函数', '投资乘数', '政府购买乘数', '边际消费倾向', '凯恩斯', '弗里德曼', '持久收入', '生命周期', '总需求', '总供给', '两部门', '三部门', '四部门'],
    8: ['经济增长', '经济周期', '经济发展', '古典型周期', '增长型周期', '景气循环', '经济波动', '同步指标', '领先指标', '滞后指标', '全要素生产率', '索洛', '技术进步'],
    9: ['价格总水平', '通货膨胀', '失业', '菲利普斯', '奥肯定律', '就业', '自然失业率', '摩擦性失业', '结构性失业', '周期性失业', '利率效应', '财富效应', '出口效应'],
    10: ['国际贸易', '比较优势', '绝对优势', '赫克歇尔', '规模经济', '关税', '非关税壁垒', '倾销', '反倾销', '国际资本流动'],
    11: ['公共财政', '公共物品的需求', '财政支出', '购买性支出', '转移性支出', '瓦格纳', '皮科克', '梯度渐进', '经济发展阶段', '非均衡增长', '财政支出规模', '财政支出增长率', '弹性系数', '边际倾向', '负荷定价', '成本效益分析', '最低费用选择', '公共定价', '赠与收入'],
    12: ['财政收入', '税收', '拉弗曲线', '税负转嫁', '前转', '后转', '消转', '税收基本特征', '宏观税负', '国债', '政府债务', '地方债务', '专项债', '增值税', '消费税', '所得税', '契税', '个人所得税'],
    13: ['政府预算', '分税制', '预算分类', '多年预算', '预算编制', '预算执行', '预算管理体制', '财政转移支付', '国库集中收付', '政府采购', '预算会计', '预算收入', '预算支出', '预算结余'],
    14: ['财政政策', '货币政策', '宏观调控', '紧缩性', '扩张性', '自动稳定器', '相机抉择', '汲水政策', '补偿政策', '存款准备金', '再贴现', '公开市场操作', '货币乘数', '基础货币', '狭义货币', '广义货币'],
    15: ['中央银行', '商业银行', '金融监管', '巴塞尔', '资本充足率', '存款保险', '最后贷款人', '金融市场', '货币市场', '资本市场', '金融风险', '社会融资规模', '利率市场化', '汇率制度', '金融业务'],
    16: ['统计', '统计学', '数据', '分类变量', '顺序变量', '数值型变量', '定性变量', '定量变量', '观测数据', '实验数据'],
    17: ['统计调查', '普查', '抽样调查', '重点调查', '典型调查', '统计报表', '概率抽样', '非概率抽样', '简单随机抽样', '分层抽样', '整群抽样', '等距抽样', '多阶段抽样', '方便抽样', '判断抽样', '配额抽样', '抽样框', '抽样误差', '非抽样误差', '无回答误差', '计量误差', '数据科学', '数据挖掘'],
    18: ['集中趋势', '均值', '中位数', '众数', '离散程度', '方差', '标准差', '离散系数', '极差', '四分位差', '偏态系数', '偏度', '标准分数', 'pearson', '相关系数', '相关分析'],
    19: ['回归分析', '一元线性回归', '最小二乘', '决定系数', '回归模型'],
    20: ['时间序列', '时期序列', '时点序列', '平均发展水平', '增长量', '逐期增长量', '累计增长量', '发展速度', '增长速度', '平均发展速度', '平均增长速度'],
    21: ['巴塞尔协议', '存款保险制度', '金融监管体制', '分业监管', '混业监管', '宏观审慎', '微观审慎', '系统性风险', '逆周期资本', '留存超额资本'],
    22: ['对外金融', '外汇', '汇率', '国际收支', '经常账户', '资本账户', '国际储备', '人民币国际化', '跨境贸易', '浮动汇率', '固定汇率'],
    23: ['统计指数', '加权指数', '拉氏指数', '帕氏指数', '居民消费价格指数', 'CPI', '生产者价格指数', 'PPI', '指数体系'],
    24: ['会计', '会计核算', '会计要素', '会计假设', '会计主体', '持续经营', '会计分期', '货币计量', '会计信息质量', '可靠性', '相关性', '可比性', '实质重于形式', '谨慎性'],
    25: ['资产', '负债', '所有者权益', '收入', '费用', '利润', '会计等式', '财务报表', '资产负债表', '利润表', '现金流量表', '会计报表', '财产清查', '账务处理程序', '收付实现制', '权责发生制'],
    26: ['偿债能力', '流动比率', '速动比率', '资产负债率', '运营能力', '盈利能力', '财务比率', '杜邦分析', '效率比率', '结构比率'],
    27: ['政府会计', '非营利组织会计', '预算会计', '财务会计', '经营支出', '事业收入', '财政拨款'],
    28: ['法律', '经济法', '调整对象', '法律关系', '法律体系', '民法', '商法'],
    29: ['物权', '所有权', '用益物权', '担保物权', '占有', '善意取得', '共有', '相邻关系', '宅基地', '建设用地使用权', '绝对消灭'],
    30: ['合同', '合同法', '要约', '承诺', '合同订立', '合同履行', '违约责任', '合同解除', '合同终止', '无效合同', '可撤销合同', '抗辩权', '代位权', '撤销权', '提存', '免除', '混同', '抵销', '定金', '保证', '抵押', '质押', '留置', '诺成合同', '实践合同', '有名合同', '无名合同', '不可抗力', '预期违约'],
    31: ['公司', '公司法', '有限责任公司', '股份有限公司', '董事会', '股东会', '监事会', '注册资本', '公司治理'],
    32: ['知识产权', '专利', '商标', '著作权', '版权', '专利法', '商标法', '反不正当竞争', '商业秘密'],
    33: ['产品质量', '消费者权益', '反垄断', '反垄断法', '经营者集中', '滥用市场支配地位', '垄断协议', '竞争法'],
    34: ['劳动合同', '劳动法', '劳动关系', '集体合同', '工作时间', '劳动争议', '劳动仲裁', '工伤保险', '失业保险'],
    35: ['社会保险', '养老保险', '医疗保险', '生育保险', '社会保险法'],
    36: ['公司法', '股份有限公司', '有限责任公司', '董事', '股东', '一人公司', '公司设立', '公司分立', '公司合并'],
    37: ['反垄断', '反垄断法', '经营者集中', '滥用市场支配地位', '垄断协议', '横向垄断', '纵向垄断', '相关市场界定'],
}

def assign_chapter(question_text):
    scores = {}
    for ch, keywords in CHAPTER_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in question_text)
        if score > 0:
            scores[ch] = score
    return max(scores, key=scores.get) if scores else 0

def clean_html(html):
    """Convert HTML to plain text preserving line structure"""
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    html = re.sub(r'<br\s*/?>', '\n', html)
    html = re.sub(r'</p>', '\n', html)
    html = re.sub(r'</div>', '\n', html)
    text = re.sub(r'<[^>]+>', '', html)
    text = html_module.unescape(text)
    text = text.replace('&#32;', ' ').replace('&nbsp;', ' ').replace('\u3000', '')
    return text

def parse_exercise_page(html, url):
    """Parse a single exercise page using HTML structure"""
    # First clean to plain text
    text = clean_html(html)
    # Remove excessive blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    questions = []
    
    # Pattern to match each question block
    # Each block starts with: optional number + 单选题/多选题
    # Then question text
    # Then options (A、... B、... etc)
    # Then 【答案】\nLETTER
    # Then 【解析】\nexplanation
    
    # Strategy: split by question header pattern, then parse each block
    # Header: N、单选题 or N、多选题 (or just 单选题/多选题 for first Q)
    
    # Split text at each question header
    pattern = r'(\d+)[、．.]\s*(单选题|多选题)\s*\n'
    blocks = re.split(pattern, text)
    
    # After split: blocks[0] is before first Q, then [num, type, content, num, type, content, ...]
    q_texts = []
    for i in range(1, len(blocks), 3):
        if i + 2 < len(blocks):
            num = blocks[i]
            qtype = blocks[i+1]
            content = blocks[i+2]
            q_texts.append((num, qtype, content))
    
    # Parse each question block
    for num, qtype, content in q_texts:
        content = content.strip()
        
        # Extract question text (before first option)
        # Options start with A、 or A．
        opt_start = re.search(r'[A-E][、．.]', content)
        if not opt_start:
            continue
        
        q_text = content[:opt_start.start()].strip()
        q_text = re.sub(r'\s+', '', q_text)
        if not q_text:
            continue
        
        rest = content[opt_start.start():]
        
        # Find 【答案】 marker
        ans_marker = rest.find('【答案】')
        if ans_marker < 0:
            continue
        
        # Options are between start and 【答案】
        opts_section = rest[:ans_marker].strip()
        ans_section = rest[ans_marker:]
        
        # Parse options
        opt_pattern = r'([A-E])[、．.]\s*(.+?)(?=\s*[A-E][、．.]|\s*【答案】)'
        raw_opts = re.findall(opt_pattern, opts_section)
        options = []
        for letter, text_opt in raw_opts:
            opt_text = text_opt.strip().replace('\n', '')
            options.append(opt_text)
        
        if not options:
            continue
        
        # Parse answer and explanation from ans_section
        ans_match = re.search(r'【答案】\s*\n?\s*([A-E]+)', ans_section)
        if not ans_match:
            continue
        
        ans_letters = ans_match.group(1).strip()
        exp_match = re.search(r'【解析】\s*\n?\s*(.+?)$', ans_section, re.DOTALL)
        explanation = ''
        if exp_match:
            explanation = exp_match.group(1).strip().replace('\n', '')
            explanation = re.sub(r'\s+', '', explanation)
        
        # Convert letters to indices
        answer_indices = [ord(c) - ord('A') for c in ans_letters if c in 'ABCDE']
        if not answer_indices:
            continue
        
        if len(answer_indices) == 1:
            answer = answer_indices[0]
            final_type = 'single'
        else:
            answer = answer_indices
            final_type = 'multi'
        
        # Assign chapter
        ch = assign_chapter(q_text)
        
        # Escape single quotes
        q_text_esc = q_text.replace("'", "\\'")
        explanation_esc = explanation.replace("'", "\\'")
        
        questions.append({
            'ch': ch,
            'type': final_type,
            'q': q_text_esc,
            'o': options,
            'a': answer,
            'x': explanation_esc,
        })
    
    return questions


# ===== URL lists from the summary pages =====
URLS_2022 = [
    "ca20211109113606", "ca20211115114345", "ca20211122142713", "ca20211130161717",
    "ca20211206202649", "ca20211213192529", "ho20211220092650", "ho20211227113645",
    "ho20220104113834", "ho20220110113618", "ho20220117152029", "ca20220124165826",
    "ca20220207180155", "ca20220214165850", "ca20220221164248", "ca20220228193020",
    "ca20220308201719", "li20220314100203", "li20220321093236", "li20220328102340",
    "li20220406094345", "li20220411102506", "li20220418102655", "li20220425120527",
    "wk20220502094706", "li20220509095604", "li20220516110219", "li20220523093943",
    "li20220531095321", "li20220606111128", "li20220613094644", "li20220620095446",
    "li20220627101443", "li20220704103332", "li20220711095430", "li20220718110146",
    "li20220725100708", "li20220801112454", "li20220808104125", "li20220815093120",
    "li20220822095340", "li20220829100011", "li20220905095341", "wk20220912095852",
    "li20220919100018", "li20220926093847", "wk20221003215114", "li20221010094742",
    "li20221017135842", "li20221020145912", "li20221031094750", "li20221107112336",
]

all_questions = []
scraped = 0
errors = 0

print(f"Starting batch scrape of {len(URLS_2022)} pages...")

for i, page_id in enumerate(URLS_2022):
    url = f"https://chinaacc.com/zhongjijingjishi/shiti/{page_id}.shtml"
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        
        questions = parse_exercise_page(html, url)
        all_questions.extend(questions)
        scraped += 1
        singles = sum(1 for q in questions if q['type'] == 'single')
        multis = sum(1 for q in questions if q['type'] == 'multi')
        print(f"  [{i+1:2d}/{len(URLS_2022)}] {page_id}: {len(questions)} questions ({singles}S/{multis}M)")
    except Exception as e:
        errors += 1
        print(f"  [{i+1:2d}/{len(URLS_2022)}] {page_id}: ERROR - {e}")
    
    time.sleep(0.3)

print(f"\nScrape complete: {scraped} pages scraped, {errors} errors")
print(f"Total questions collected: {len(all_questions)}")

# Count by chapter
from collections import Counter
ch_counts = Counter(q['ch'] for q in all_questions)
print(f"\nQuestions by chapter:")
for ch in sorted(ch_counts):
    label = f"Ch{ch}" if ch > 0 else "Unknown"
    print(f"  {label}: {ch_counts[ch]}")

# Count by type
single_count = sum(1 for q in all_questions if q['type'] == 'single')
multi_count = sum(1 for q in all_questions if q['type'] == 'multi')
print(f"\nQuestion types: {single_count} single, {multi_count} multi")

# Generate JS output
output_dir = 'output'
os.makedirs(output_dir, exist_ok=True)

lines = []
for q in all_questions:
    ch = q['ch']
    q_type = q['type']
    q_text = q['q']
    options = q['o']
    answer = q['a']
    explanation = q['x']
    
    if isinstance(answer, list):
        ans_str = str(answer)
        lines.append(f"  {{ch:{ch},type:'multi',q:'{q_text}',o:{json.dumps(options, ensure_ascii=False)},a:{ans_str},x:'{explanation}'}},")
    else:
        lines.append(f"  {{ch:{ch},q:'{q_text}',o:{json.dumps(options, ensure_ascii=False)},a:{answer},x:'{explanation}'}},")

js_content = f"// Auto-scraped from chinaacc.com weekly exercises (2022)\n"
js_content += f"// Total: {len(all_questions)} questions\n"
js_content += '\n'.join(lines) + '\n'

output_file = f'{output_dir}/chinaacc_econ_2022.js'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(js_content)

print(f"\nOutput written to {output_file}")
