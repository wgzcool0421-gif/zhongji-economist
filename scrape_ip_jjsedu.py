#!/usr/bin/env python3
"""
Scrape IP (知识产权) questions from jjsedu.org chapter exercises.
Tries multiple URL ranges across different years.
"""
import urllib.request
import re
import time
import json
import sys

# Chapter keyword mapping for assignment
CHAPTER_KEYWORDS = {
    1: ['知识产权制度概述', '知识产权基础', '知识产权概述', '知识产权的性质', '知识产权客体'],
    2: ['知识产权管理', '知识产权服务', '知识产权运用', '代理', '管理体制', '公共服务'],
    3: ['专利申请', '专利授权', '专利确权', '专利权无效', '无效宣告'],
    4: ['专利保护', '专利侵权', '全面覆盖'],
    5: ['专利运用', '专利许可', '专利转让', '专利质押', '开放许可', '专利布局', '专利导航'],
    6: ['商标注册', '商标申请', '商标审查', '商标核准', '商标异议', '马德里'],
    7: ['商标使用', '商标续展', '商标变更', '商标注销', '商标许可'],
    8: ['商标保护', '注册商标专用权', '驰名商标', '商标侵权', '地理标志'],
    9: ['著作权', '版权', '邻接权', '著作人身权', '著作财产权', '合理使用'],
    10: ['商业秘密', '集成电路', '植物新品种', '布图设计', '地理标志产品'],
    11: ['其他类型', '集成电路布图', '植物新品种权'],
    12: ['知识产权国际保护', '国际公约', '国际条约', '巴黎公约', 'TRIPS', 'WIPO', 'PCT', '伯尔尼'],
    13: ['海外知识产权', '海外保护', '海外纠纷', '337调查', '涉外', '海外布局'],
}

def assign_chapter(title, question_text):
    """Assign chapter number based on page title and question text."""
    text = (title + ' ' + question_text).lower()
    
    # Score each chapter
    scores = {}
    for ch, keywords in CHAPTER_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw.lower() in text:
                score += 1
        if score > 0:
            scores[ch] = score
    
    if scores:
        return max(scores, key=scores.get)
    return 1  # Default to chapter 1

def clean_html(html):
    """Remove scripts, styles, and HTML tags from content."""
    # Remove scripts
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    # Remove styles
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    # Remove HTML comments
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    # Replace common block elements with newlines
    html = re.sub(r'<br\s*/?>', '\n', html)
    html = re.sub(r'</?p[^>]*>', '\n', html)
    html = re.sub(r'</?div[^>]*>', '\n', html)
    html = re.sub(r'</?li[^>]*>', '\n', html)
    # Remove all remaining HTML tags
    html = re.sub(r'<[^>]+>', '', html)
    # Decode entities
    html = html.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'")
    # Collapse whitespace
    html = re.sub(r'\n\s*\n+', '\n\n', html)
    html = re.sub(r'[ \t]+', ' ', html)
    return html.strip()

def parse_questions(text, page_title):
    """Parse questions from cleaned page text."""
    questions = []
    
    # Remove header/footer noise
    # Find the main content area - look for patterns that mark the start
    start_patterns = [
        r'参考解析',
        r'参考答案',
    ]
    
    # Split by question numbers: N、 or N. or N．or N[.]
    # For 2026 format: "N 问题()" or "N.问题()"
    # For 2022 format: "N[.单选题]问题()" or "N[.多选题]问题()"
    
    # First try the 2026 format (no [.类型] markers)
    # Split by question number followed by content
    question_blocks = re.split(r'(?:^|\n)\s*(\d+)\s*[、．.]?\s*(?:单选题|多选题)?\s*\n?', text)
    
    # Process blocks
    i = 1  # Skip first empty element
    while i < len(question_blocks):
        try:
            q_num = question_blocks[i].strip()
            if not q_num or not q_num.isdigit():
                i += 1
                continue
            
            # Check if next block exists
            if i + 1 >= len(question_blocks):
                break
                
            block = question_blocks[i + 1].strip()
            
            # Determine type
            q_type = 'single'
            if '多选题' in block[:20] or '多选题' in text[max(0, text.find(block)-30):text.find(block)]:
                q_type = 'multi'
            if '单选题' in block[:20]:
                q_type = 'single'
            
            # Extract question text (everything before A.)
            # Find where options start
            opt_match = re.search(r'\n\s*A[.、．]\s*', block)
            if not opt_match:
                i += 2
                continue
            
            q_text = block[:opt_match.start()].strip()
            # Clean question text
            q_text = re.sub(r'^(?:单选题|多选题)\s*', '', q_text).strip()
            
            if not q_text or len(q_text) < 5:
                i += 2
                continue
            
            # Extract options
            options_text = block[opt_match.start():]
            # Find where options end (before 参考答案)
            answer_match = re.search(r'参考答案[：:]', options_text)
            if not answer_match:
                i += 2
                continue
            
            opt_section = options_text[:answer_match.start()]
            
            # Parse individual options
            option_lines = re.findall(r'[A-E][.、．]\s*(.+?)(?=\n[A-E][.、．]|\n参考答案|\Z)', opt_section, re.DOTALL)
            options = [o.strip().rstrip(',') for o in option_lines]
            
            if not options or len(options) < 2:
                i += 2
                continue
            
            # Extract answer
            after_answer = options_text[answer_match.end():]
            answer_line = after_answer.split('\n')[0].strip()
            
            # Parse answer - could be single letter or multiple letters separated by comma
            answer_letters = re.findall(r'[A-E]', answer_line)
            if not answer_letters:
                i += 2
                continue
            
            # Convert to indices
            answer_indices = [ord(c) - ord('A') for c in answer_letters if ord(c) - ord('A') < len(options)]
            if not answer_indices:
                i += 2
                continue
            
            # Extract explanation
            exp_match = re.search(r'参考解析[：:]?\s*\n?(.+?)(?=\n\s*\d+\s*[、．.]|\Z)', after_answer, re.DOTALL)
            explanation = ''
            if exp_match:
                explanation = exp_match.group(1).strip()
                # Clean up explanation
                explanation = re.sub(r'\s+', ' ', explanation)[:500]  # Limit length
            
            if not explanation:
                # Try without 参考解析 prefix
                rest = after_answer.split('\n', 1)
                if len(rest) > 1:
                    explanation = rest[1].strip()[:500]
            
            # Assign chapter
            chapter = assign_chapter(page_title, q_text)
            
            # Escape single quotes for JS
            q_text = q_text.replace("'", "\\'")
            options_escaped = [o.replace("'", "\\'") for o in options]
            explanation = explanation.replace("'", "\\'").replace('\n', ' ')
            
            # Build question object
            q_obj = f"  {{ch:{chapter},type:'{q_type}',q:'{q_text}',o:{json.dumps(options_escaped, ensure_ascii=False)},a:{json.dumps(answer_indices if q_type == 'multi' else answer_indices[0])},x:'{explanation}'}},"
            
            questions.append(q_obj)
            
        except Exception as e:
            print(f"  Error parsing question {q_num}: {e}", file=sys.stderr)
        
        i += 2
    
    return questions

def fetch_page(url):
    """Fetch a page and return cleaned text + title."""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='replace')
        
        # Extract title
        title_match = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
        title = title_match.group(1) if title_match else ''
        
        # Clean HTML
        text = clean_html(html)
        return text, title
    except Exception as e:
        print(f"  Fetch error: {e}", file=sys.stderr)
        return None, None

def main():
    # URL ranges to try
    # 2026 content: 79939-79970
    # 2025 content: 79436-79445, 79036-79040
    # 2022 content: 73577, 71311
    url_ranges = [
        # (start, end, label)
        (79935, 79975, "2026-main"),
        (79430, 79450, "2025-chapter"),
        (79030, 79050, "2025-extra"),
        (73570, 73600, "2022-main"),
        (71300, 71330, "2022-old"),
        (72000, 72020, "2022-extra"),
    ]
    
    all_questions = []
    fetched = 0
    empty = 0
    
    for start, end, label in url_ranges:
        print(f"\n=== Trying {label} range: {start}-{end} ===", file=sys.stderr)
        for n in range(start, end + 1):
            url = f"http://jjsedu.org/zhongji/moniti/chanquan/{n}"
            
            text, title = fetch_page(url)
            if text is None:
                continue
            
            questions = parse_questions(text, title)
            
            if questions:
                print(f"  [{n}] {title[:50]}: {len(questions)} questions", file=sys.stderr)
                all_questions.extend(questions)
                fetched += 1
            else:
                empty += 1
            
            time.sleep(0.5)  # Be polite
    
    # Write output
    output = "// Auto-generated IP questions from jjsedu.org\n"
    output += "// Total: " + str(len(all_questions)) + " questions\n"
    output += "// Fetched from " + str(fetched) + " pages\n\n"
    output += "const IP_QBANK_NEW = [\n"
    output += "\n".join(all_questions)
    output += "\n];\n"
    
    with open('ip_jjsedu_new.js', 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"\n=== DONE ===", file=sys.stderr)
    print(f"Total questions: {len(all_questions)}", file=sys.stderr)
    print(f"Fetched from {fetched} pages", file=sys.stderr)
    print(f"Empty/error: {empty} pages", file=sys.stderr)

if __name__ == '__main__':
    main()
