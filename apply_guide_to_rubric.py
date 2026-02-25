import os
import re

# Read course guide
with open("backend/training_data/course_guide.md", "r") as f:
    guide_text = f.read()

# Chunk by headers
chunks = {}
current_header = None
current_body = []
for line in guide_text.splitlines():
    if line.startswith("## "):
        if current_header:
            chunks[current_header] = "\n".join(current_body).strip()
        current_header = line[3:].strip()
        current_body = []
    elif current_header:
        current_body.append(line)
if current_header:
    chunks[current_header] = "\n".join(current_body).strip()

from backend.src.business_rubric_templates import BYUMS_RUBRIC

# Update business_rubric_templates.py
template_path = "backend/src/business_rubric_templates.py"
with open(template_path, "r", encoding="utf-8") as f:
    content = f.read()

# For each criteria, find its matching chunk and append it explicitly!
# We will inject `comprehensive_guide="""..."""` into the RubricItem definition.
# Wait, let's first prepare the new text for BYUMS_RUBRIC.
# But it's easier to just modify the output.

new_rubric_str = "BYUMS_RUBRIC = [\n"

for i, item in enumerate(BYUMS_RUBRIC):
    # Try to find a matching header chunk
    matching_chunk = ""
    # Header format typically: "Category - Criteria" or similar.
    for header, body in chunks.items():
        if header.lower() == item.criteria.lower():
            matching_chunk = body
            break
        # Sometimes header is like "Problem/Pain Point - Clearly Defined the Problem/Pain Being Addressed"
        # and item criteria is "Problem/Pain Point - Clearly defined the problem"
        elif item.criteria.split(" - ")[-1].lower() in header.lower() or header.lower() in item.criteria.lower():
            matching_chunk = body
            break
            
    escaped_body = matching_chunk.replace('"""', '\\"\\"\\"') if matching_chunk else ""
    
    new_rubric_str += f"""    RubricItem(
        criteria="{item.criteria}",
        max_points={item.max_points},
        description="{item.description}",
        developing_points={item.developing_points},
        developing_description="{item.developing_description}",
        zero_points={item.zero_points},
        zero_description="{item.zero_description}",
        course_guide=\"""{escaped_body}\"""
    ),
"""
new_rubric_str += "]"

pattern = r"BYUMS_RUBRIC\s*=\s*\[.*?^\]"
new_content = re.sub(pattern, new_rubric_str, content, flags=re.DOTALL | re.MULTILINE)

with open(template_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Updated BYUMS_RUBRIC with course_guide chunks.")
