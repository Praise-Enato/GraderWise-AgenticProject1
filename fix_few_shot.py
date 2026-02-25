import os
import re

file_path = "backend/src/few_shot_examples.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

from backend.src.business_rubric_templates import BYUMS_RUBRIC
correct_criteria = [item.criteria for item in BYUMS_RUBRIC]

# Let's find all the assessment blocks. In the file they look like:
# {"criteria": "...", "awarded": X, "max": Y},

lines = content.split('\n')
new_lines = []
criteria_index = 0

for line in lines:
    if '{"criteria": "' in line:
        if criteria_index >= len(correct_criteria):
            criteria_index = 0 # reset for the next example block
        
        # Replace the criteria string
        new_line = re.sub(r'{"criteria": ".*?",', f'{{"criteria": "{correct_criteria[criteria_index]}",', line)
        new_lines.append(new_line)
        criteria_index += 1
    elif '"assessments": [' in line:
        criteria_index = 0
        new_lines.append(line)
    else:
        new_lines.append(line)

new_content = '\n'.join(new_lines)
with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)
    
print("Successfully updated few_shot_examples.py criteria strings to perfectly match BYUMS_RUBRIC")
