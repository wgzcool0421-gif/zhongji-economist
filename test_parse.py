import urllib.request, re, html as html_module

url = 'https://chinaacc.com/zhongjijingjishi/shiti/li20220606111128.shtml'
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})
with urllib.request.urlopen(req, timeout=15) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

print(f'HTML length: {len(html)}')

# Test parsing
html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
html = re.sub(r'<br\s*/?>', '\n', html)
html = re.sub(r'</p>', '\n', html)
html = re.sub(r'</div>', '\n', html)
text = re.sub(r'<[^>]+>', '', html)
text = html_module.unescape(text)
text = text.replace('&#32;', ' ').replace('&nbsp;', ' ')

# Find questions
pattern = r'(\d+)[、．.]\s*(单选题|多选题)\s*\n\s*(.+?)(?:\n\s*)+((?:[A-E][、．.].+?(?:\n|$))+)【答案】\s*\n?\s*([A-E]+)\s*\n?\s*【解析】\s*\n?\s*(.+?)(?=\n\s*\d+[、．.]\s*(?:单选题|多选题)|$)'
matches = re.findall(pattern, text, re.DOTALL)
print(f'Matches found: {len(matches)}')
for i, m in enumerate(matches[:3]):
    print(f'  Q{i+1}: type={m[1]}, answer={m[4]}, text={m[2][:40]}...')
