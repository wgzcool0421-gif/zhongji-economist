#!/usr/bin/env python3
"""Merge IP questions from ip_extra.js and new_ip_questions.js into index.html IP_QBANK."""

import re, json

def extract_questions(filepath):
    """Extract question objects from a JS file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    # Find all {ch:...} blocks
    questions = []
    # Simple regex to match question objects
    pattern = r'\{[^{}]*?ch:\d+[^{}]*?\}'
    matches = re.finditer(pattern, content)
    for m in matches:
        q_text = m.group(0)
        questions.append(q_text)
    return questions

def normalize_q(q_text):
    """Normalize question text for dedup comparison."""
    # Convert to single quotes (standardize format)
    q_text = q_text.replace('\\"', '"').replace('"', "'")
    # Extract just the q: field value for dedup
    m = re.search(r"q:'([^']*)'", q_text)
    if m:
        return m.group(1).strip()
    return q_text.strip()

def format_q(q_text):
    """Format a question object to match index.html style."""
    # Replace double quotes with single quotes
    q_text = q_text.replace('"', "'")
    # Fix escaped single quotes in arrays
    # Ensure it ends with a comma
    q_text = q_text.strip()
    if q_text.endswith('}'):
        q_text += ','
    elif q_text.endswith('},'):
        pass
    return q_text

def main():
    # 1. Read existing index.html questions
    with open('index.html', 'r', encoding='utf-8') as f:
        index_content = f.read()

    # Extract existing IP_QBANK content
    ip_start = index_content.find('const IP_QBANK = [')
    if ip_start == -1:
        print("ERROR: IP_QBANK not found")
        return
    
    # Find the closing ]; for IP_QBANK
    ip_content_start = ip_start + len('const IP_QBANK = [')
    # Find ]; after IP_QBANK start
    depth = 1
    ip_end = -1
    for i in range(ip_content_start, len(index_content)):
        c = index_content[i]
        if c == '[':
            depth += 1
        elif c == ']':
            depth -= 1
            if depth == 0:
                ip_end = i
                break
    
    if ip_end == -1:
        print("ERROR: IP_QBANK closing ] not found")
        return
    
    ip_body = index_content[ip_content_start:ip_end]
    
    # Extract existing question texts for dedup
    existing_qs = re.findall(r"q:'([^']*)'", ip_body)
    existing_set = set()
    for q in existing_qs:
        existing_set.add(q.strip())

    print(f"Existing IP_QBANK questions: {len(existing_set)}")

    # 2. Extract questions from ip_extra.js
    extra_qs = extract_questions('ip_extra.js')
    print(f"Questions in ip_extra.js: {len(extra_qs)}")
    
    # 3. Extract questions from new_ip_questions.js
    new_qs = extract_questions('new_ip_questions.js')
    print(f"Questions in new_ip_questions.js: {len(new_qs)}")
    
    # 4. Deduplicate and collect new questions
    all_new = []
    dup_count = 0
    
    for q_set, name in [(extra_qs, 'ip_extra.js'), (new_qs, 'new_ip_questions.js')]:
        for q in q_set:
            norm = normalize_q(q)
            if norm and norm not in existing_set:
                existing_set.add(norm)
                formatted = format_q(q)
                all_new.append(formatted)
            else:
                dup_count += 1
    
    print(f"New unique questions to add: {len(all_new)}")
    print(f"Duplicates skipped: {dup_count}")
    
    if not all_new:
        print("No new questions to add - all are duplicates!")
        return

    # 5. Insert into index.html at IP_QBANK closing ]
    # We need to insert BEFORE the ];
    insert_text = '\n' + '\n'.join(all_new)
    
    new_content = index_content[:ip_end] + insert_text + index_content[ip_end:]
    
    # Write
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    # Verify
    with open('index.html', 'r', encoding='utf-8') as f:
        verify = f.read()
    v_qs = re.findall(r"q:'", verify[verify.find('const IP_QBANK = ['):verify.find('];', verify.find('const IP_QBANK = ['))])
    print(f"\n=== RESULT ===")
    print(f"IP_QBANK questions after merge: {len(v_qs)}")
    print(f"Total added: {len(all_new)}")
    print(f"Done!")

if __name__ == '__main__':
    main()
