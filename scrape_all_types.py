#!/usr/bin/env python3
"""
Scrape ALL question types (single, multi, case) from jjsedu.org
for both Economics (37 chapters) and IP (available chapters).
"""

import urllib.request
import re
import time
import json
import html as htmlmod

# Confirmed ECON chapter IDs
ECON_CHAPTER_IDS = {
    1:76250, 2:76251, 3:76252, 4:76259, 5:76260, 6:76261,
    7:76269, 8:76270, 9:76271, 10:76277, 11:76278, 12:76279,
    13:76286, 14:76287, 15:76312, 16:76313, 17:76319, 18:76320,
    19:76321, 20:76329, 21:76330, 22:76331, 23:76339, 24:76340,
    25:76341, 26:76357, 27:76358, 28:76359, 29:76366, 30:76367,
    31:76368, 32:76384, 33:76385, 34:76386, 35:76401, 36:76402,
    37:76403
}

# Known IP chapter IDs (from previous scanning)
IP_CHAPTER_IDS = {
    1:78382, 2:78383, 8:78448, 9:79961
}

def fetch_page(url, timeout=10):
    """Fetch a page and return decoded text."""
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    req.add_header('Accept', 'text/html,application/xhtml+xml')
    req.add_header('Accept-Language', 'zh-CN,zh;q=0.9')
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        data = resp.read()
        try:
            return data.decode('gbk')
        except:
            return data.decode('utf-8', errors='ignore')
    except:
        return None

def clean_text(text):
    """Clean HTML entities and whitespace."""
    text = htmlmod.unescape(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_questions_from_page(html_text, chapter_num, source='econ'):
    """Extract all question types from a page."""
    results = {'single': [], 'multi': [], 'case': []}
    
    if not html_text:
        return results
    
    # Find the content div
    content_match = re.search(r'<div class="contents"[^>]*>(.*?)</div>\s*(?:<div|<ul|<script|$)', 
                               html_text, re.DOTALL)
    if not content_match:
        content_match = re.search(r'<div class="contents"[^>]*>(.*)', html_text, re.DOTALL)
    
    if not content_match:
        return results
    
    content = content_match.group(1)
    
    # Split by question type markers
    # ECON format: 【2022年真题】 etc, 参考答案, 参考解析
    # IP format: [.单选题], [.多选题], [.案例分析题], [答案], [解析]
    
    if source == 'ip':
        # IP moniti format
        sections = re.split(r'\[\.\s*(单选题|多选题|案例分析题)\s*\]', content)
        for i in range(1, len(sections), 2):
            qtype = sections[i].strip()
            qcontent = sections[i+1] if i+1 < len(sections) else ''
            
            if qtype == '单选题':
                results['single'].extend(parse_ip_single(qcontent, chapter_num))
            elif qtype == '多选题':
                results['multi'].extend(parse_ip_multi(qcontent, chapter_num))
            elif qtype == '案例分析题':
                results['case'].extend(parse_ip_case(qcontent, chapter_num))
    else:
        # ECON format - try to identify multi/case by question content
        # Parse all questions with 参考答案 format
        all_questions = parse_econ_questions(content, chapter_num)
        
        # Heuristic: questions with "多选" in answer are multi-choice
        # Questions with shared background material are case studies
        for q in all_questions:
            answer = q.get('answer_text', '')
            if len(answer) > 1 and re.match(r'^[A-E]{2,}$', answer):
                q['type'] = 'multi'
                q['a'] = [ord(c) - ord('A') for c in answer]
                results['multi'].append(q)
            else:
                q['type'] = 'single'
                results['single'].append(q)
    
    return results

def parse_econ_questions(content, chapter_num):
    """Parse ECON format questions."""
    questions = []
    
    # Split by question numbers
    # Format: N.【year】question() A.xxx B.xxx C.xxx D.xxx 参考答案：X 参考解析：text
    blocks = re.split(r'(?=\d+[\.\．、]\s*(?:【|下列|关于|根据|某|在|以下))', content)
    
    for block in blocks:
        block = block.strip()
        if not block or len(block) < 20:
            continue
        
        # Extract question text
        q_match = re.match(r'(\d+)[\.\．、]\s*(?:【\d+年[真题]*】\s*)?(.*?)(?=\s*[A-E][\.\．、])', block, re.DOTALL)
        if not q_match:
            continue
        
        q_text = clean_text(q_match.group(2))
        if not q_text or len(q_text) < 5:
            continue
        
        # Extract options
        opts = re.findall(r'([A-E])[\.\．、]\s*(.*?)(?=\s*[A-E][\.\．、]|\s*参考答案|\s*$)', block, re.DOTALL)
        options = [clean_text(opt[1]) for opt in opts if clean_text(opt[1])]
        
        if len(options) < 2:
            continue
        
        # Extract answer
        ans_match = re.search(r'参考答案[：:]\s*([A-E]+)', block)
        if not ans_match:
            continue
        answer_text = ans_match.group(1)
        
        # Extract explanation
        exp_match = re.search(r'参考解析[：:]\s*(.*?)(?=\d+[\.\．、]|\Z)', block, re.DOTALL)
        explanation = clean_text(exp_match.group(1))[:300] if exp_match else ''
        
        q = {
            'type': 'single',
            'ch': chapter_num,
            'q': q_text,
            'o': options,
            'answer_text': answer_text,
            'x': explanation
        }
        
        if len(answer_text) == 1:
            q['a'] = ord(answer_text) - ord('A')
        
        questions.append(q)
    
    return questions

def parse_ip_single(content, chapter_num):
    """Parse IP single choice questions."""
    questions = []
    # Format: N question() A.xxx B.xxx C.xxx D.xxx [答案]X [解析]text
    blocks = re.split(r'(?=\d+[\.\．、]\s*(?:下列|关于|根据|某|在|以下|以下哪))', content)
    
    for block in blocks:
        block = block.strip()
        if len(block) < 20:
            continue
        
        q_match = re.match(r'(\d+)[\.\．、]\s*(.*?)(?=\s*[A-E][\.\．、])', block, re.DOTALL)
        if not q_match:
            continue
        
        q_text = clean_text(q_match.group(2))
        if not q_text or len(q_text) < 5:
            continue
        
        opts = re.findall(r'([A-E])[\.\．、]\s*(.*?)(?=\s*[A-E][\.\．、]|\s*\[答案\]|\s*$)', block, re.DOTALL)
        options = [clean_text(opt[1]) for opt in opts if clean_text(opt[1])]
        
        if len(options) < 2:
            continue
        
        ans_match = re.search(r'\[答案\]\s*([A-E]+)', block)
        if not ans_match:
            continue
        answer_text = ans_match.group(1)
        
        exp_match = re.search(r'\[解析\]\s*(.*?)(?=\d+[\.\．、]|\Z)', block, re.DOTALL)
        explanation = clean_text(exp_match.group(1))[:300] if exp_match else ''
        
        if len(answer_text) == 1:
            questions.append({
                'type': 'single',
                'ch': chapter_num,
                'q': q_text,
                'o': options,
                'a': ord(answer_text) - ord('A'),
                'x': explanation
            })
    
    return questions

def parse_ip_multi(content, chapter_num):
    """Parse IP multi choice questions."""
    questions = []
    blocks = re.split(r'(?=\d+[\.\．、]\s*(?:下列|关于|根据|某|在|以下))', content)
    
    for block in blocks:
        block = block.strip()
        if len(block) < 20:
            continue
        
        q_match = re.match(r'(\d+)[\.\．、]\s*(.*?)(?=\s*[A-E][\.\．、])', block, re.DOTALL)
        if not q_match:
            continue
        
        q_text = clean_text(q_match.group(2))
        if not q_text or len(q_text) < 5:
            continue
        
        opts = re.findall(r'([A-E])[\.\．、]\s*(.*?)(?=\s*[A-E][\.\．、]|\s*\[答案\]|\s*$)', block, re.DOTALL)
        options = [clean_text(opt[1]) for opt in opts if clean_text(opt[1])]
        
        if len(options) < 2:
            continue
        
        ans_match = re.search(r'\[答案\]\s*([A-E]+)', block)
        if not ans_match:
            continue
        answer_text = ans_match.group(1)
        
        exp_match = re.search(r'\[解析\]\s*(.*?)(?=\d+[\.\．、]|\Z)', block, re.DOTALL)
        explanation = clean_text(exp_match.group(1))[:300] if exp_match else ''
        
        answers = [ord(c) - ord('A') for c in answer_text]
        questions.append({
            'type': 'multi',
            'ch': chapter_num,
            'q': q_text,
            'o': options,
            'a': answers,
            'x': explanation
        })
    
    return questions

def parse_ip_case(content, chapter_num):
    """Parse IP case study questions."""
    # Case studies are complex - parse as best effort
    questions = []
    # Try to find shared scenario + sub-questions
    # This is a simplified parser
    return questions

def format_js(q, counter):
    """Format a question as JS object."""
    qtype = q['type']
    ch = q['ch']
    
    # Escape strings
    def esc(s):
        return s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")
    
    q_str = esc(q['q'])
    opts_str = ", ".join([f"'{esc(o)}'" for o in q['o']])
    x_str = esc(q.get('x', ''))
    
    if qtype == 'single':
        return f"  {{id:{counter},type:'single',ch:{ch},q:'{q_str}',o:[{opts_str}],a:{q['a']},x:'{x_str}'}},"
    elif qtype == 'multi':
        a_str = ", ".join(str(a) for a in q['a'])
        return f"  {{id:{counter},type:'multi',ch:{ch},q:'{q_str}',o:[{opts_str}],a:[{a_str}],x:'{x_str}'}},"
    elif qtype == 'case':
        # Simplified - skip case for now
        return None
    return None

def main():
    all_econ = {'single': [], 'multi': [], 'case': []}
    all_ip = {'single': [], 'multi': [], 'case': []}
    
    print("=== Scraping ECON chapters ===")
    for ch_num, page_id in sorted(ECON_CHAPTER_IDS.items()):
        url = f"http://jjsedu.org/zhongji/moniti/jingjijiichu/{page_id}.html"
        html_text = fetch_page(url)
        if not html_text:
            print(f"  Ch{ch_num}: FAILED to fetch")
            time.sleep(0.3)
            continue
        
        result = extract_questions_from_page(html_text, ch_num, 'econ')
        for t in ['single', 'multi', 'case']:
            all_econ[t].extend(result[t])
        
        total = sum(len(result[t]) for t in result)
        print(f"  Ch{ch_num}: {total} questions (S:{len(result['single'])} M:{len(result['multi'])} C:{len(result['case'])})")
        time.sleep(0.2)
    
    print(f"\nECON total: {sum(len(all_econ[t]) for t in all_econ)} (S:{len(all_econ['single'])} M:{len(all_econ['multi'])} C:{len(all_econ['case'])})")
    
    print("\n=== Scraping IP chapters ===")
    for ch_num, page_id in sorted(IP_CHAPTER_IDS.items()):
        url = f"http://jjsedu.org/zhongji/moniti/chanquan/{page_id}.html"
        html_text = fetch_page(url)
        if not html_text:
            print(f"  Ch{ch_num}: FAILED to fetch")
            time.sleep(0.3)
            continue
        
        result = extract_questions_from_page(html_text, ch_num, 'ip')
        for t in ['single', 'multi', 'case']:
            all_ip[t].extend(result[t])
        
        total = sum(len(result[t]) for t in result)
        print(f"  Ch{ch_num}: {total} questions (S:{len(result['single'])} M:{len(result['multi'])} C:{len(result['case'])})")
        time.sleep(0.2)
    
    print(f"\nIP total: {sum(len(all_ip[t]) for t in all_ip)} (S:{len(all_ip['single'])} M:{len(all_ip['multi'])} C:{len(all_ip['case'])})")
    
    # Also try additional IP ID ranges
    print("\n=== Scanning additional IP IDs ===")
    ip_found = dict(IP_CHAPTER_IDS)
    cn_map = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,
              '十一':11,'十二':12,'十三':13}
    for pid in range(78384, 78500):
        if pid in ip_found:
            continue
        url = f"http://jjsedu.org/zhongji/moniti/chanquan/{pid}.html"
        html_text = fetch_page(url, timeout=5)
        if not html_text:
            time.sleep(0.08)
            continue
        m = re.search(r'<title>([^<]+)</title>', html_text)
        if not m:
            time.sleep(0.08)
            continue
        title = m.group(1).strip()
        chm = re.search(r'第([一二三四五六七八九十百\d]+)章', title)
        if chm:
            cs = chm.group(1)
            if cs.isdigit():
                ch = int(cs)
            else:
                ch = cn_map.get(cs)
            if ch and ch not in ip_found.values():
                ip_found[pid] = ch
                result = extract_questions_from_page(html_text, ch, 'ip')
                for t in ['single', 'multi', 'case']:
                    all_ip[t].extend(result[t])
                total = sum(len(result[t]) for t in result)
                print(f"  FOUND Ch{ch} (ID:{pid}): {total} questions")
        time.sleep(0.08)
    
    # Also scan 79950-80050 range
    for pid in range(79950, 80050):
        if pid in ip_found:
            continue
        url = f"http://jjsedu.org/zhongji/moniti/chanquan/{pid}.html"
        html_text = fetch_page(url, timeout=5)
        if not html_text:
            time.sleep(0.08)
            continue
        m = re.search(r'<title>([^<]+)</title>', html_text)
        if not m:
            time.sleep(0.08)
            continue
        title = m.group(1).strip()
        chm = re.search(r'第([一二三四五六七八九十百\d]+)章', title)
        if chm:
            cs = chm.group(1)
            if cs.isdigit():
                ch = int(cs)
            else:
                ch = cn_map.get(cs)
            if ch and ch not in ip_found.values():
                ip_found[pid] = ch
                result = extract_questions_from_page(html_text, ch, 'ip')
                for t in ['single', 'multi', 'case']:
                    all_ip[t].extend(result[t])
                total = sum(len(result[t]) for t in result)
                print(f"  FOUND Ch{ch} (ID:{pid}): {total} questions")
        time.sleep(0.08)
    
    print(f"\nIP final total: {sum(len(all_ip[t]) for t in all_ip)} (S:{len(all_ip['single'])} M:{len(all_ip['multi'])} C:{len(all_ip['case'])})")
    
    # Deduplicate
    def dedup(qs):
        seen = set()
        result = []
        for q in qs:
            key = q['q'][:40]
            if key not in seen:
                seen.add(key)
                result.append(q)
        return result
    
    all_econ['single'] = dedup(all_econ['single'])
    all_econ['multi'] = dedup(all_econ['multi'])
    all_ip['single'] = dedup(all_ip['single'])
    all_ip['multi'] = dedup(all_ip['multi'])
    
    econ_total = len(all_econ['single']) + len(all_econ['multi']) + len(all_econ['case'])
    ip_total = len(all_ip['single']) + len(all_ip['multi']) + len(all_ip['case'])
    print(f"\nAfter dedup:")
    print(f"  ECON: {econ_total} (S:{len(all_econ['single'])} M:{len(all_econ['multi'])} C:{len(all_econ['case'])})")
    print(f"  IP: {ip_total} (S:{len(all_ip['single'])} M:{len(all_ip['multi'])} C:{len(all_ip['case'])})")
    
    # Save as JSON for later processing
    with open('scraped_all_types.json', 'w', encoding='utf-8') as f:
        json.dump({'econ': all_econ, 'ip': all_ip}, f, ensure_ascii=False, indent=2)
    
    print("\nSaved to scraped_all_types.json")

if __name__ == '__main__':
    main()
