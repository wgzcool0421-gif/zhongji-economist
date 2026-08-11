#!/usr/bin/env python3
"""
Scrape ALL IP (知识产权) questions from chinaacc.com weekly exercises.
Parses ~52 weekly exercise pages, ~7 questions each = ~364 questions.
"""
import urllib.request
import re
import time
import json
import sys
import ssl

# Chapter keyword mapping
CHAPTER_KEYWORDS = {
    1: ['知识产权制度概述', '知识产权基础', '知识产权概述', '知识产权的性质', '知识产权客体', '狭义的知识产权', '知识产权三大'],
    2: ['知识产权管理', '知识产权服务', '知识产权运用', '代理', '管理体制', '公共服务', '知识产权管理体系', '企业知识产权管理',
        '专利代理', '商标代理', '贯标'],
    3: ['专利申请', '专利授权', '专利确权', '专利权无效', '无效宣告', '专利保护客体', '专利审查', '专利申请文件',
        '新颖性', '创造性', '实用性', '外观设计的授权', '专利复审', '优先权'],
    4: ['专利保护', '专利侵权', '全面覆盖', '等同侵权', '专利纠纷', '专利侵权判定', '专利侵权责任',
        '专利权属纠纷', '专利合同纠纷', '诉前禁令'],
    5: ['专利运用', '专利许可', '专利转让', '专利质押', '开放许可', '专利布局', '专利导航', '专利检索',
        '专利许可类型', '专利许可贸易', '专利转让合同', '专利实施许可'],
    6: ['商标注册', '商标申请', '商标审查', '商标核准', '商标异议', '马德里', '商标评审', '商标行政复议',
        '商标法基本原则', '商标的类型', '立体商标', '颜色组合', '声音商标'],
    7: ['商标使用', '商标续展', '商标变更', '商标注销', '商标许可', '商标使用许可', '商标转让',
        '商标品牌', '商标印制', '集体商标', '证明商标'],
    8: ['商标保护', '注册商标专用权', '驰名商标', '商标侵权', '地理标志', '商标专用权', '侵犯注册商标',
        '商标相同近似', '商标一般违法', '地理标志产品', '地理标志专用标志'],
    9: ['著作权', '版权', '邻接权', '著作人身权', '著作财产权', '合理使用', '法定许可', '著作权法',
        '著作权集体管理', '著作权转让', '著作权登记', '表演者权', '出租权', '信息网络传播',
        '著作权侵权', '技术措施'],
    10: ['商业秘密', '集成电路', '植物新品种', '布图设计', '地理标志产品', '集成电路布图', '植物新品种权',
         '商业秘密构成', '侵犯商业秘密', '反向工程', '商业秘密管理'],
    11: ['集成电路布图', '植物新品种权', '其他类型', '民间文学', '商号', '商号权'],
    12: ['知识产权国际保护', '国际公约', '国际条约', '巴黎公约', 'TRIPS', 'WIPO', 'PCT', '伯尔尼',
         '国民待遇原则', '最低保护标准', '自动保护原则', '独立保护原则'],
    13: ['海外知识产权', '海外保护', '海外纠纷', '337调查', '涉外', '海外布局', '对外贸易'],
}

def assign_chapter(title, question_text, explanation):
    """Assign chapter number based on page title, question text, and explanation."""
    text = (title + ' ' + question_text + ' ' + explanation).lower()
    scores = {}
    for ch, keywords in CHAPTER_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text)
        if score > 0:
            scores[ch] = score
    if scores:
        return max(scores, key=scores.get)
    return 1

def clean_html(html):
    """Clean HTML to extract readable text."""
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    html = re.sub(r'<br\s*/?>', '\n', html)
    html = re.sub(r'</?p[^>]*>', '\n', html)
    html = re.sub(r'</?div[^>]*>', '\n', html)
    html = re.sub(r'</?li[^>]*>', '\n', html)
    html = re.sub(r'<[^>]+>', '', html)
    html = html.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
    # Full-width parentheses to normal
    html = html.replace('（', '(').replace('）', ')').replace('　', ' ')
    html = re.sub(r'\n\s*\n+', '\n\n', html)
    html = re.sub(r'[ \t]+', ' ', html)
    return html.strip()

def parse_page(text, page_title):
    """Parse all questions from a page's cleaned text."""
    questions = []
    
    # First, normalize the text - merge split type markers
    # "1、多\n选题" -> "1、多选题"
    # "1、单\n选题" -> "1、单选题"
    text = re.sub(r'(\d+)、\s*(多|单)\s*\n\s*选题', r'\1、\2选题', text)
    
    # Find first question marker
    first_q = re.search(r'\n\s*1、', text)
    if not first_q:
        return questions
    text = text[first_q.start():]
    
    # Split by question number pattern: N、 (followed by 单选题/多选题 or directly content)
    # Use a more careful approach: split at newline followed by digit+、
    blocks = re.split(r'\n\s*(?=\d+、)', text)
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        
        # Extract question number and type
        header_match = re.match(r'(\d+)、\s*(单选题|多选题)?\s*', block)
        if not header_match:
            continue
        
        q_num = header_match.group(1)
        q_type_str = header_match.group(2)
        q_type = 'multi' if q_type_str == '多选题' else 'single'
        
        # Remove the header from block
        body = block[header_match.end():].strip()
        
        if not body or len(body) < 5:
            continue
        
        # Extract question text (everything before first option A、)
        opt_a_match = re.search(r'\n\s*A[、，,]', body)
        if not opt_a_match:
            continue
        
        q_text = body[:opt_a_match.start()].strip()
        q_text = q_text.replace('\n', ' ').strip()
        
        if not q_text or len(q_text) < 3:
            continue
        
        # Extract option section (from A to 【答案】)
        option_text = body[opt_a_match.start():]
        
        # Find answer marker
        answer_match = re.search(r'【答案】', option_text)
        if not answer_match:
            continue
        
        opt_section = option_text[:answer_match.start()]
        
        # Parse individual options: A、text B、text ...
        option_lines = re.findall(
            r'\n\s*([A-E])[、，,]\s*(.+?)(?=\n\s*[A-E][、，,]|\n\s*【答案】|\n\s*$|\Z)',
            opt_section, re.DOTALL
        )
        
        if not option_lines or len(option_lines) < 2:
            continue
        
        options = []
        for letter, text_val in option_lines:
            text_val = text_val.strip().rstrip(';；')
            text_val = re.sub(r'\s+', ' ', text_val)
            options.append(text_val)
        
        if len(options) < 2:
            continue
        
        # Extract answer
        after_answer = option_text[answer_match.end():]
        answer_section = after_answer.split('【解析】')[0] if '【解析】' in after_answer else after_answer.split('\n', 1)[0]
        answer_section = answer_section.strip()
        
        # Parse answer letters
        answer_letters = re.findall(r'[A-E]', answer_section)
        if not answer_letters:
            continue
        
        answer_indices = [ord(c) - ord('A') for c in answer_letters if ord(c) - ord('A') < len(options)]
        if not answer_indices:
            continue
        
        # Extract explanation
        explanation = ''
        exp_match = re.search(r'【解析】\s*(.+?)(?=\n\s*\d+、|\Z)', after_answer, re.DOTALL)
        if exp_match:
            explanation = exp_match.group(1).strip()
            explanation = re.sub(r'\s+', ' ', explanation)[:800]
        
        # Assign chapter
        chapter = assign_chapter(page_title, q_text, explanation)
        
        # Escape for JS
        q_text_esc = q_text.replace("'", "\\'")
        options_esc = [o.replace("'", "\\'") for o in options]
        explanation_esc = explanation.replace("'", "\\'").replace('\n', ' ')
        
        # Build answer value
        if q_type == 'multi' and len(answer_indices) > 1:
            a_val = json.dumps(answer_indices)
        elif len(answer_indices) > 1:
            q_type = 'multi'
            a_val = json.dumps(answer_indices)
        else:
            a_val = str(answer_indices[0])
        
        q_obj = f"  {{ch:{chapter},type:'{q_type}',q:'{q_text_esc}',o:{json.dumps(options_esc, ensure_ascii=False)},a:{a_val},x:'{explanation_esc}'}},"
        
        questions.append(q_obj)
    
    return questions

def fetch_page(url):
    """Fetch a chinaacc.com page and return cleaned text + title."""
    try:
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        })
        with urllib.request.urlopen(req, timeout=20, context=ssl_ctx) as resp:
            raw = resp.read()
            html = raw.decode('utf-8', errors='replace')
        
        # Extract title
        title_match = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
        title = title_match.group(1) if title_match else ''
        
        text = clean_html(html)
        return text, title
    except Exception as e:
        print(f"  Fetch error [{url}]: {e}", file=sys.stderr)
        return None, None

def main():
    # All exercise URLs found from the summary page
    urls = [
        # Week 1-6 (ca prefix)
        'https://www.chinaacc.com/zhongjijingjishi/shiti/ca20211109142803.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/ca20211115142113.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/ca20211115170027.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/ca20211115171218.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/ca20211115172701.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/ca20211115173713.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/ca20211115175343.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/ca20211115180337.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/ca20211122154028.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/ca20211130164739.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/ca20211206205505.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/ca20211213201922.shtml',
        # ho prefix exercises
        'https://www.chinaacc.com/zhongjijingjishi/shiti/ho20211220135756.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/ho20211227140329.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/ho20220104140020.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/ho20220110141141.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/ho20220117162635.shtml',
        # ca prefix continued
        'https://www.chinaacc.com/zhongjijingjishi/shiti/ca20220125163811.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/ca20220207182449.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/ca20220214174859.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/ca20220221172456.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/ca20220228200819.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/ca20220308203706.shtml',
        # li prefix exercises (weeks 18-51)
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20220314104159.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20220321095308.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20220328105200.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20220406100512.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20220411105054.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20220418104954.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20220425125638.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/wk20220502094949.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20220509102317.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20220516140454.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20220523095437.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20220531110722.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20220606113559.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20220613101000.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20220620101917.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20220627103254.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20220704112050.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20220711105425.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20220718112223.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20220725102441.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20220801120222.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20220808110541.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20220815094921.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20220822102603.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20220829102350.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20220905102601.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/wk20220912102111.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20220919102045.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20220926102506.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/wk20221003220942.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20221010110614.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20221017143013.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20221024102402.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20221031101353.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/li20221107142327.shtml',
        # Daily exercises from 2023
        'https://www.chinaacc.com/zhongjijingjishi/shiti/mr20230929075243.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/mr20230930085103.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/mr20231001072440.shtml',
        'https://www.chinaacc.com/zhongjijingjishi/shiti/mr20231002084341.shtml',
    ]
    
    all_questions = []
    success_count = 0
    
    for idx, url in enumerate(urls):
        print(f"[{idx+1}/{len(urls)}] {url.split('/')[-1]}", file=sys.stderr, end=' ')
        text, title = fetch_page(url)
        
        if text is None:
            print("FAIL", file=sys.stderr)
            continue
        
        questions = parse_page(text, title)
        print(f"-> {len(questions)} questions", file=sys.stderr)
        all_questions.extend(questions)
        success_count += 1
        
        time.sleep(0.3)  # Be polite
    
    # Write output
    output = "// Auto-generated IP questions from chinaacc.com\n"
    output += f"// Total: {len(all_questions)} questions\n"
    output += f"// From {success_count} pages\n\n"
    output += "const IP_CHINAACC_NEW = [\n"
    output += "\n".join(all_questions)
    output += "\n];\n"
    
    with open('ip_chinaacc_new.js', 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"\n=== DONE ===", file=sys.stderr)
    print(f"Total questions: {len(all_questions)}", file=sys.stderr)
    print(f"From {success_count}/{len(urls)} pages", file=sys.stderr)

if __name__ == '__main__':
    main()
