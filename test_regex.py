import re

sample = '''单选题

    按照美国经济学家科斯的观点，企业的本质或者显著特征是（　）。

    A、企业是推动技术进步的平台 

    B、企业是社会化大生产的产物 

    C、企业是承担社会责任的机制 

    D、企业是作为市场机制的替代物 

                【答案】
            D
                【解析】
            本题考查企业形成的理论。
    2、单选题

    边际产量递减规律发生作用的前提条件是（　）。

    A、投入的生产要素价格不变 

    B、各种生产要素投入比例不变 

    C、全要素生产率有所下降 

    D、技术水平和其他投入保持不变 

                【答案】
            D
                【解析】
            本题考查边际产量递减规律。'''

# Simpler pattern
pattern = r'(\d+)[、．.]\s*(单选题|多选题)\s*\n\s*(.+?)\n\s*((?:[A-E][、．.].+?\n)+)\s*【答案】\s*\n\s*([A-E]+)\s*\n\s*【解析】\s*\n\s*(.+?)(?=\n\s*\d+[、．.]\s*(?:单选题|多选题)|\Z)'
matches = re.findall(pattern, sample, re.DOTALL)
print(f'Matches: {len(matches)}')
for m in matches:
    print(f'  num={m[0]}, type={m[1]}, answer={m[4]}')
    print(f'  options: {repr(m[3][:80])}')
