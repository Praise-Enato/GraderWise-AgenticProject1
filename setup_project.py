import os

def create_directory_structure():
    directories = [
        "frontend",
        "backend/src",
        "backend/tests",
        "backend/data/rubrics",
        "backend/data/course_materials",
        "docs/specs"
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")

if __name__ == "__main__":
    create_directory_structure()
