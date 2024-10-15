import os

with open('thwiki-sentseg-small.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

tmp  = ''.join(lines)
new_lines = tmp.split('\n\n\n\n\n\n\n')
print(len(new_lines))

# print(f"first article -----> {new_lines[0]}")
# print(f"second article -----> {new_lines[1]}")
# print(f"third article -----> {new_lines[2]}")
# print(f"third article -----> {new_lines[3]}")
# print(f"third article -----> {new_lines[-1]}")

if not os.path.exists(os.path.join(os.getcwd(), 'knowledge_cleaned')):
    os.mkdir('knowledge_cleaned')

for i, line in enumerate(new_lines):
    if line == '':
        continue
    with open(f'knowledge_cleaned/article{str(i+1).zfill(3)}.txt', 'a', encoding='utf-8') as f:
        f.write(line)