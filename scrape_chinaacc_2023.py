#!/usr/bin/env python3
"""Scrape chinaacc.com 2023 weekly exercises"""
import sys
sys.path.insert(0, '.')
from scrape_chinaacc import parse_exercise_page, assign_chapter, clean_html
import urllib.request, re, json, time, os

# 2023 URLs from summary page (skip #1 as it's same as 2022)
URLS_2023 = [
    "li20221121101831", "li20221128103148", "li20221205102717", "li20221212095924",
    "li20221219092559", "zh20221226161022", "li20230103093552", "li20230108175216",
    "li20230116101428", "wa20230123112519", "li20230130101814", "li20230206102913",
    "li20230213091335", "li20230220095959", "li20230227083233", "li20230306100319",
    "li20230313094307", "li20230320092946", "li20230327091707", "li20230403100232",
    "li20230410134138", "li20230417095247", "li20230423090421", "li20230501093334",
    "li20230508092628", "li20230515134510", "li20230522134838", "li20230529134548",
    "li20230605172327", "zh20230612112004", "li20230619100102", "li20230626102259",
    "li20230703101623", "li20230710105619", "li20230717134942", "li20230724094429",
    "li20230731085311", "li20230807094130", "li20230814103014", "li20230821093217",
    "li20230828114636", "li20230904093013", "li20230911091409", "li20230918101146",
    "li20230925104653", "li20231009094840", "li20231016100528", "li20231023093238",
    "li20231030150116", "li20231106105343",
]

all_questions = []
scraped = 0
errors = 0

print(f"Starting 2023 batch scrape of {len(URLS_2023)} pages...")

for i, page_id in enumerate(URLS_2023):
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
        print(f"  [{i+1:2d}/{len(URLS_2023)}] {page_id}: {len(questions)} questions ({singles}S/{multis}M)")
    except Exception as e:
        errors += 1
        print(f"  [{i+1:2d}/{len(URLS_2023)}] {page_id}: ERROR - {e}")
    
    time.sleep(0.3)

print(f"\n2023 Scrape complete: {scraped} pages, {errors} errors, {len(all_questions)} questions")

# Deduplicate against existing ECON_QBANK
with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('const ECON_QBANK = [')
end = content.find('const IP_QBANK = [', start)
econ_section = content[start:end]

existing_qs = set()
for m in re.finditer(r"q:'([^']+)'", econ_section):
    existing_qs.add(m.group(1))

unique_questions = []
dupes = 0
for q in all_questions:
    # Unescape the stored text for comparison
    q_text = q['q'].replace("\\'", "'")
    if q_text not in existing_qs:
        unique_questions.append(q)
        existing_qs.add(q_text)
    else:
        dupes += 1

print(f"Unique new questions: {len(unique_questions)}, Duplicates: {dupes}")

# Generate JS
output_dir = 'output'
os.makedirs(output_dir, exist_ok=True)

lines = []
for q in unique_questions:
    ch = q['ch']
    q_type = q['type']
    q_text = q['q']
    options = q['o']
    answer = q['a']
    explanation = q['x']
    
    if isinstance(answer, list):
        lines.append(f"  {{ch:{ch},type:'multi',q:'{q_text}',o:{json.dumps(options, ensure_ascii=False)},a:{str(answer)},x:'{explanation}'}},")
    else:
        lines.append(f"  {{ch:{ch},q:'{q_text}',o:{json.dumps(options, ensure_ascii=False)},a:{answer},x:'{explanation}'}},")

js = f"// Auto-scraped from chinaacc.com 2023 weekly exercises\n// Total: {len(unique_questions)} unique new questions\n"
js += '\n'.join(lines) + '\n'

with open('chinaacc_econ_2023_new.js', 'w', encoding='utf-8') as f:
    f.write(js)

print(f"Written to chinaacc_econ_2023_new.js")

# Merge into index.html
with open('chinaacc_econ_2023_new.js', 'r', encoding='utf-8') as f:
    new_js = f.read()

content = content[:end]  # ECON_QBANK section end
# Find last ];
last_close = content.rfind('];')
insert_block = f'''
  // ===== 2023正保网校每周习题补充({len(unique_questions)}题) =====
{new_js.rstrip()}
'''
content = content[:last_close] + insert_block + content[last_close:]
# Append rest
content += content.split('];', 1)[1]  # No, need full content

# Read full content again for proper merge
with open('index.html', 'r', encoding='utf-8') as f:
    full_content = f.read()

ip_pos = full_content.find('const IP_QBANK = [')
econ_section = full_content[:ip_pos]
last_econ_close = econ_section.rfind('];')

new_full = full_content[:last_econ_close] + insert_block + full_content[last_econ_close:]

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(new_full)

# Verify
with open('index.html', 'r', encoding='utf-8') as f:
    vc = f.read()

es = vc.find('const ECON_QBANK = [')
ee = vc.find('const IP_QBANK = [', es)
is_ = ee
ie = vc.find('const PAST_PAPERS', is_)

ec = len(re.findall(r'^\s*\{ch:', vc[es:ee], re.MULTILINE))
ic = len(re.findall(r'^\s*\{ch:', vc[is_:ie], re.MULTILINE))
print(f"\nFinal: ECON={ec}, IP={ic}, Total={ec+ic}")

# Dupe check
qs = re.findall(r"q:'([^']+)'", vc[es:ee])
print(f"ECON unique: {len(qs)}/{len(set(qs))} {'OK' if len(qs)==len(set(qs)) else 'DUPES!'}")

# Update dist
import shutil
shutil.copy('index.html', 'dist/index.html')
print("dist/index.html updated")
