import re

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

ip_start = content.find('const IP_QBANK = [')
ip_end = content.find('];', ip_start)
ip_segment = content[ip_start:ip_end]
existing_qs = re.findall(r"q:'([^']*)'", ip_segment)
existing_set = set()
for q in existing_qs:
    existing_set.add(q.strip())
print(f'Existing IP_QBANK questions: {len(existing_set)}')

with open('ip_extra.js', 'r', encoding='utf-8') as f:
    extra = f.read()

# Try double quotes
extra_dq = re.findall(r'q:"([^"]*)"', extra)
print(f'ip_extra.js double-quote questions: {len(extra_dq)}')

# Try single quotes
extra_sq = re.findall(r"q:'([^']*)'", extra)
print(f'ip_extra.js single-quote questions: {len(extra_sq)}')

all_extra = extra_dq + extra_sq
print(f'Total extra questions extracted: {len(all_extra)}')

missing = []
for q in all_extra:
    q_clean = q.replace("\\'", "'").strip()
    if q_clean not in existing_set:
        missing.append(q_clean[:80])

print(f'\nMissing: {len(missing)}')
for m in missing:
    print(f'  - {m}')
