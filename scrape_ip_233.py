#!/usr/bin/env python3
"""
Scrape ALL IP (知识产权) questions from 233.com (233网校) chapter exercises.
Parses ~36 pages, ~5-6 questions each = ~180-200 questions.
"""
import urllib.request
import re
import time
import json
import sys
import ssl
import html as html_lib

# Chapter keyword mapping
CHAPTER_KEYWORDS = {
    1: ['知识产权制度概述', '知识产权基础', '知识产权概述', '知识产权的性质', '知识产权客体',
        '知识产权的作用', '知识产权密集型', '工业产权', '知识产权法律体系'],
    2: ['知识产权管理', '知识产权服务', '知识产权运用', '代理', '管理体制', '公共服务',
        '企业知识产权管理', '专利代理', '商标代理', '贯标', '知识产权公共服务', '知识产权认证'],
    3: ['专利申请', '专利授权', '专利确权', '专利权无效', '无效宣告', '专利保护客体',
        '专利审查', '专利申请文件', '新颖性', '创造性', '实用性',
        '外观设计的授权', '专利复审', '优先权', '权利要求', '专利授权的基本要求',
        '专利申请文件的撰写', '专利代理监管'],
    4: ['专利保护', '专利侵权', '全面覆盖', '等同侵权', '专利纠纷', '专利侵权判定',
        '专利权保护范围', '专利纠纷的类型', '专利纠纷的多元', '专利仲裁', '诉前禁令',
        '专利权属纠纷', '专利合同纠纷'],
    5: ['专利运用', '专利许可', '专利转让', '专利质押', '开放许可', '专利布局',
        '专利导航', '专利检索', '专利许可贸易', '专利运用概述', '专利信息利用'],
    6: ['商标注册', '商标申请', '商标审查', '商标核准', '商标异议', '马德里',
        '商标评审', '商标行政复议', '商标概述', '商标的注册', '商标无效宣告',
        '商标法基本原则', '商标的类型', '立体商标', '颜色组合', '声音商标', '商标的国际注册'],
    7: ['商标使用', '商标续展', '商标变更', '商标注销', '商标许可', '商标使用许可',
        '商标转让', '商标品牌', '商标印制', '集体商标', '证明商标',
        '注册商标的更正', '注册商标使用的特殊', '商标权[^法]', '商标品牌战略'],
    8: ['商标保护', '注册商标专用权', '驰名商标', '商标侵权', '地理标志',
        '商标专用权', '侵犯注册商标', '商标相同近似', '商标一般违法',
        '侵犯注册商标专用权行为', '地理标志产品', '地理标志专用标志', '作为集体商标'],
    9: ['著作权', '版权', '邻接权', '著作人身权', '著作财产权', '合理使用',
        '法定许可', '著作权法', '著作权集体管理', '著作权转让', '著作权登记',
        '表演者权', '出租权', '信息网络传播', '著作权侵权', '技术措施',
        '著作权制度概述', '著作权许可', '侵犯著作权'],
    10: ['商业秘密', '集成电路', '植物新品种', '布图设计', '地理标志产品',
         '集成电路布图', '植物新品种权', '商业秘密构成', '侵犯商业秘密',
         '反向工程', '商业秘密管理', '地理标志国际保护'],
    11: ['集成电路布图', '植物新品种权', '其他类型', '民间文学', '商号', '商号权'],
    12: ['知识产权国际保护', '国际公约', '国际条约', '巴黎公约', 'TRIPS', 'WIPO',
         'PCT', '伯尔尼', '国民待遇原则', '最低保护标准', '自动保护原则',
         '独立保护原则', '国际申请', '海牙协定'],
    13: ['海外知识产权', '海外保护', '海外纠纷', '337调查', '涉外', '海外布局', '对外贸易'],
}

def assign_chapter(page_title, question_text, explanation):
    text = (page_title + ' ' + question_text + ' ' + explanation)
    # Try to extract chapter from page title first
    for ch, keywords in CHAPTER_KEYWORDS.items():
        for kw in keywords:
            if kw in page_title:
                return ch
    
    # Fallback: keyword matching
    scores = {}
    for ch, keywords in CHAPTER_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[ch] = score
    if scores:
        return max(scores, key=scores.get)
    return 1

def clean_html(html_text):
    html_text = re.sub(r'<script[^>]*>.*?</script>', '', html_text, flags=re.DOTALL)
    html_text = re.sub(r'<style[^>]*>.*?</style>', '', html_text, flags=re.DOTALL)
    html_text = re.sub(r'<!--.*?-->', '', html_text, flags=re.DOTALL)
    html_text = re.sub(r'<br\s*/?>', '\n', html_text)
    html_text = re.sub(r'</?p[^>]*>', '\n', html_text)
    html_text = re.sub(r'</?div[^>]*>', '\n', html_text)
    html_text = re.sub(r'<[^>]+>', '', html_text)
    html_text = html_lib.unescape(html_text)
    html_text = re.sub(r'\n\s*\n+', '\n\n', html_text)
    html_text = re.sub(r'[ \t]+', ' ', html_text)
    return html_text.strip()

def parse_233_page(text, page_title):
    """Parse questions from 233.com format pages."""
    questions = []
    
    # Split by question number pattern: N、(question text)
    # 233 format: N、question\nA.option\nB.option\n...\n查看答案\n参考答案：X\n参考解析：...
    blocks = re.split(r'\n\s*(\d+)[、．.]\s*', text)
    
    i = 1
    while i < len(blocks):
        try:
            if i + 1 >= len(blocks):
                break
            q_num = blocks[i].strip()
            if not q_num or not q_num.isdigit():
                i += 1
                continue
            
            block = blocks[i + 1].strip()
            if not block or len(block) < 10:
                i += 2
                continue
            
            # Extract question text (everything before first option A.)
            opt_a_match = re.search(r'\n\s*A[.、]', block)
            if not opt_a_match:
                i += 2
                continue
            
            q_text = block[:opt_a_match.start()].strip()
            q_text = q_text.replace('\n', ' ').strip()
            
            if not q_text or len(q_text) < 5:
                i += 2
                continue
            
            # Extract options section
            option_text = block[opt_a_match.start():]
            
            # Find answer marker
            answer_match = re.search(r'查看答案|参考答案', option_text)
            if not answer_match:
                i += 2
                continue
            
            opt_section = option_text[:answer_match.start()]
            after_answer = option_text[answer_match.end():]
            
            # Parse options: A.xxx B.xxx C.xxx ...
            opt_pattern = re.findall(
                r'\n\s*([A-E])[.、．]\s*(.+?)(?=\n\s*[A-E][.、．]|\n\s*(?:查看答案|参考答案)|\Z)',
                opt_section, re.DOTALL
            )
            
            if not opt_pattern or len(opt_pattern) < 2:
                i += 2
                continue
            
            options = []
            for letter, opt_text in opt_pattern:
                opt_text = opt_text.strip().rstrip(';；')
                opt_text = re.sub(r'\s+', ' ', opt_text)
                # Clean reference markers like 【233网校独家解析】
                opt_text = re.sub(r'【[^】]*?】', '', opt_text).strip()
                options.append(opt_text)
            
            if len(options) < 2:
                i += 2
                continue
            
            # Determine question type
            q_type = 'multi' if len(options) >= 4 and '多选' in page_title.lower() else 'single'
            
            # Parse answer: "参考答案：A" or "参考答案：A,B,C"
            ans_line_match = re.search(r'参考答案[：:]\s*(.+?)(?=\n|$)', after_answer)
            if not ans_line_match:
                i += 2
                continue
            
            ans_line = ans_line_match.group(1).strip()
            # Handle answers like A,B,C or ABC or A B C
            answer_letters = re.findall(r'[A-E]', ans_line)
            
            if not answer_letters:
                i += 2
                continue
            
            answer_indices = [ord(c) - ord('A') for c in answer_letters if ord(c) - ord('A') < len(options)]
            if not answer_indices:
                i += 2
                continue
            
            # Determine type based on answer count
            if len(answer_indices) > 1:
                q_type = 'multi'
            
            # Extract explanation
            explanation = ''
            exp_match = re.search(r'参考解析[：:]\s*(.+?)(?=\n\s*\d+[、．.]|\Z)', after_answer, re.DOTALL)
            if exp_match:
                explanation = exp_match.group(1).strip()
                explanation = re.sub(r'\s+', ' ', explanation)[:500]
                # Clean reference markers
                explanation = re.sub(r'【[^】]*?】', '', explanation).strip()
            
            # Assign chapter
            chapter = assign_chapter(page_title, q_text, explanation)
            
            # Escape for JS
            q_text_esc = q_text.replace("'", "\\'").replace('\n', ' ')
            options_esc = [o.replace("'", "\\'").replace('\n', ' ') for o in options]
            explanation_esc = explanation.replace("'", "\\'").replace('\n', ' ')
            
            # Build answer value
            if q_type == 'multi':
                a_val = json.dumps(answer_indices)
            else:
                a_val = str(answer_indices[0])
            
            q_obj = f"  {{ch:{chapter},type:'{q_type}',q:'{q_text_esc}',o:{json.dumps(options_esc, ensure_ascii=False)},a:{a_val},x:'{explanation_esc}'}},"
            questions.append(q_obj)
            
        except Exception as e:
            print(f"  Error parsing Q{q_num}: {e}", file=sys.stderr)
        
        i += 2
    
    return questions

def fetch_page(url):
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
            html_text = resp.read().decode('utf-8', errors='replace')
        
        # Extract title
        title_match = re.search(r'<title>(.*?)</title>', html_text, re.DOTALL)
        title = title_match.group(1) if title_match else ''
        
        text = clean_html(html_text)
        return text, title
    except Exception as e:
        print(f"  Fetch error [{url}]: {e}", file=sys.stderr)
        return None, None

def main():
    # All collected 233.com IP 试题精选 URLs
    urls = [
        # 202601
        ('https://www.233.com/zjjjs/cqmoniti/202601/20095908488777.html', '知识产权制度概述'),
        ('https://www.233.com/zjjjs/cqmoniti/202601/22095925408260.html', '知识产权的运用'),
        ('https://www.233.com/zjjjs/cqmoniti/202601/23095933410735.html', '知识产权的国际保护制度'),
        ('https://www.233.com/zjjjs/cqmoniti/202601/24095941325867.html', '知识产权的作用'),
        ('https://www.233.com/zjjjs/cqmoniti/202601/25095949288122.html', '我国知识产权管理体制'),
        ('https://www.233.com/zjjjs/cqmoniti/202601/26095959189238.html', '知识产权公共服务'),
        ('https://www.233.com/zjjjs/cqmoniti/202601/27100008324204.html', '专利代理监管'),
        ('https://www.233.com/zjjjs/cqmoniti/202601/28100016357266.html', '商标代理监管'),
        ('https://www.233.com/zjjjs/cqmoniti/202601/29100023724661.html', '专利申请文件的撰写要求'),
        ('https://www.233.com/zjjjs/cqmoniti/202601/30100036128809.html', '专利授权的基本要求'),
        ('https://www.233.com/zjjjs/cqmoniti/202601/31100046505229.html', '专利无效宣告请求'),
        # 202602
        ('https://www.233.com/zjjjs/cqmoniti/202602/01100054740378.html', '国际申请'),
        ('https://www.233.com/zjjjs/cqmoniti/202602/02114141641271.html', '专利权保护范围'),
        ('https://www.233.com/zjjjs/cqmoniti/202602/03114447270429.html', '专利纠纷的类型'),
        ('https://www.233.com/zjjjs/cqmoniti/202602/04114438730381.html', '专利纠纷的多元解决机制'),
        ('https://www.233.com/zjjjs/cqmoniti/202602/05114419281695.html', '专利运用概述'),
        ('https://www.233.com/zjjjs/cqmoniti/202602/06114410979147.html', '专利信息利用'),
        ('https://www.233.com/zjjjs/cqmoniti/202602/07114400868956.html', '专利许可与转让'),
        ('https://www.233.com/zjjjs/cqmoniti/202602/08114353303009.html', '商标概述'),
        ('https://www.233.com/zjjjs/cqmoniti/202602/09114345628173.html', '商标的注册'),
        ('https://www.233.com/zjjjs/cqmoniti/202602/10114337629819.html', '商标评审与注册商标的无效宣告'),
        ('https://www.233.com/zjjjs/cqmoniti/202602/11114329978245.html', '商标的国际注册'),
        ('https://www.233.com/zjjjs/cqmoniti/202602/12114321725429.html', '商标行政复议'),
        ('https://www.233.com/zjjjs/cqmoniti/202602/13114313264963.html', '商标权'),
        ('https://www.233.com/zjjjs/cqmoniti/202602/14114302778093.html', '侵犯注册商标专用权行为判定'),
        ('https://www.233.com/zjjjs/cqmoniti/202602/15114253853215.html', '驰名商标的保护'),
        ('https://www.233.com/zjjjs/cqmoniti/202602/16114245982351.html', '注册商标的更正、变更、续展与注销'),
        ('https://www.233.com/zjjjs/cqmoniti/202602/17114238701448.html', '注册商标的许可、转让与质押'),
        ('https://www.233.com/zjjjs/cqmoniti/202602/18114230890143.html', '注册商标使用的特殊情形'),
        ('https://www.233.com/zjjjs/cqmoniti/202602/19114221792303.html', '商标印制'),
        ('https://www.233.com/zjjjs/cqmoniti/202602/20114155155069.html', '商标品牌战略与策略'),
        ('https://www.233.com/zjjjs/cqmoniti/202602/21114108929746.html', '著作权制度概述'),
        # 202606
        ('https://www.233.com/zjjjs/cqmoniti/202606/15113334907282.html', '著作权转让与许可和融资'),
        ('https://www.233.com/zjjjs/cqmoniti/202606/16114029944480.html', '侵犯著作权的行为及其法律责任'),
        ('https://www.233.com/zjjjs/cqmoniti/202606/2411415867988.html', '作为集体商标或者证明商标注册的地理标志的保护'),
        ('https://www.233.com/zjjjs/cqmoniti/202606/25114207722677.html', '地理标志国际保护制度'),
    ]
    
    all_questions = []
    success_count = 0
    
    for idx, (url, topic) in enumerate(urls):
        print(f"[{idx+1}/{len(urls)}] {topic}", file=sys.stderr, end=' ')
        text, title = fetch_page(url)
        
        if text is None:
            print("FAIL", file=sys.stderr)
            continue
        
        # Find main content area (narrow to content containing questions)
        q_idx = text.find('查看答案')
        content_start = max(0, text.rfind('\n', 0, q_idx) - 500)
        if content_start < 100:
            content_start = 0
        text = text[content_start:]
        
        questions = parse_233_page(text, title or topic)
        print(f"-> {len(questions)} questions", file=sys.stderr)
        all_questions.extend(questions)
        success_count += 1
        
        time.sleep(0.3)
    
    # Write output
    output = "// Auto-generated IP questions from 233.com (233网校)\n"
    output += f"// Total: {len(all_questions)} questions\n"
    output += f"// From {success_count}/{len(urls)} pages\n\n"
    output += "const IP_233_NEW = [\n"
    output += "\n".join(all_questions)
    output += "\n];\n"
    
    with open('ip_233_new.js', 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"\n=== DONE ===", file=sys.stderr)
    print(f"Total questions: {len(all_questions)}", file=sys.stderr)
    print(f"From {success_count}/{len(urls)} pages", file=sys.stderr)

if __name__ == '__main__':
    main()
