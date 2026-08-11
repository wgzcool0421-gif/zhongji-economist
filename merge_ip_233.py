import re

# Read the new questions
with open('ip_233_new.js', 'r', encoding='utf-8') as f:
    new_content = f.read()

# Read index.html
with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract existing IP question texts
ip_start = content.find('const IP_QBANK = [')
ip_search = content.find('];', ip_start)
while True:
    after = content[ip_search+2:ip_search+60].strip()
    if after.startswith('//') and 'BILIBILI' in after:
        break
    ip_search = content.find('];', ip_search+1)

ip_end = ip_search + 2
ip_segment = content[ip_start:ip_end]
existing_qs = set()
for m in re.finditer(r"q:'([^']*)'", ip_segment):
    existing_qs.add(m.group(1).strip().replace(' ', ''))

print(f'Existing IP_QBANK: {len(existing_qs)} questions')

# Parse new questions
new_lines = [line for line in new_content.split('\n') if line.strip().startswith('{ch:')]
print(f'New questions: {len(new_lines)}')

# Deduplicate
unique_new = []
dup_count = 0
for line in new_lines:
    q_match = re.search(r"q:'([^']*)'", line)
    if not q_match:
        continue
    q_text = q_match.group(1).replace("\\'", "'")
    q_norm = q_text.strip().replace(' ', '')
    
    is_dup = False
    for eq in existing_qs:
        eq_norm = eq.replace(' ', '')
        if len(q_norm) > 10 and q_norm[:10] == eq_norm[:10]:
            is_dup = True
            break
    if is_dup:
        dup_count += 1
    else:
        unique_new.append(line)
        # Add to existing set to prevent self-duplicates
        existing_qs.add(q_text.strip().replace(' ', ''))

print(f'Duplicates: {dup_count}')
print(f'Unique new: {len(unique_new)}')

if unique_new:
    insert_pos = ip_end - 2
    insert_block = '\n' + '\n'.join(unique_new) + '\n'
    content = content[:insert_pos] + insert_block + content[insert_pos:]
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f'Merged {len(unique_new)} new questions into IP_QBANK')
else:
    print('No new unique questions to merge')
