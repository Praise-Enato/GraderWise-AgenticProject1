import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
from backend.src.business_rubric_templates import BYUMS_RUBRIC
from backend.src.few_shot_examples import EXAMPLE_LOW, EXAMPLE_MID, EXAMPLE_HIGH

def verify():
    rubric_criteria = [item.criteria for item in BYUMS_RUBRIC]
    
    print(f"BYUMS_RUBRIC has {len(rubric_criteria)} criteria.")
    print("Rubric Criteria sample:")
    for c in rubric_criteria[:3]:
        print(f" - {c}")
        
    print("\nChecking EXAMPLE_HIGH...")
    example_criteria = [a["criteria"] for a in EXAMPLE_HIGH["assessments"]]
    print(f"EXAMPLE_HIGH has {len(example_criteria)} criteria.")
    
    mismatches = 0
    for ec in example_criteria:
        if ec not in rubric_criteria:
            print(f"MISMATCH: '{ec}' not found in actual rubric.")
            mismatches += 1
            
    print(f"\nTotal Mismatches in Example: {mismatches}")

if __name__ == "__main__":
    verify()
