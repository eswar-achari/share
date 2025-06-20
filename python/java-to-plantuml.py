import os
import re
from collections import defaultdict

class JavaClass:
    def __init__(self, name):
        self.name = name
        self.fields = []
        self.methods = []
        self.superclass = None
        self.used_classes = set()

def parse_java_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()

    classes = []
    class_pattern = re.compile(r'\bclass\s+(\w+)(?:\s+extends\s+(\w+))?')
    field_pattern = re.compile(r'(private|protected|public)\s+([\w<>]+)\s+(\w+);')
    method_pattern = re.compile(r'(public|private|protected)\s+[\w<>]+\s+(\w+)\s*\([^)]*\)\s*[{;]')
    usage_pattern = re.compile(r'new\s+(\w+)\s*\(')

    for class_match in class_pattern.finditer(content):
        cls_name = class_match.group(1)
        superclass = class_match.group(2)
        java_class = JavaClass(cls_name)
        java_class.superclass = superclass

        class_block = content[class_match.end():]
        brace_count = 1
        i = 0
        while i < len(class_block) and brace_count > 0:
            if class_block[i] == '{':
                brace_count += 1
            elif class_block[i] == '}':
                brace_count -= 1
            i += 1
        class_content = class_block[:i]

        for field in field_pattern.findall(class_content):
            java_class.fields.append((field[0], field[1], field[2]))

        for method in method_pattern.findall(class_content):
            java_class.methods.append((method[0], method[1]))

        for usage in usage_pattern.findall(class_content):
            java_class.used_classes.add(usage)

        classes.append(java_class)
    return classes

def walk_project_and_parse(root_dir):
    all_classes = {}
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".java"):
                filepath = os.path.join(subdir, file)
                for cls in parse_java_file(filepath):
                    all_classes[cls.name] = cls
    return all_classes

def generate_plantuml(classes):
    lines = ["@startuml"]

    for cls in classes.values():
        lines.append(f"class {cls.name} {{")
        for access, ftype, fname in cls.fields:
            symbol = "+" if access == "public" else "-" if access == "private" else "#"
            lines.append(f"    {symbol} {ftype} {fname}")
        lines.append("    --")
        for access, mname in cls.methods:
            symbol = "+" if access == "public" else "-" if access == "private" else "#"
            lines.append(f"    {symbol} void {mname}()")
        lines.append("}")

    for cls in classes.values():
        if cls.superclass and cls.superclass in classes:
            lines.append(f"{cls.name} --|> {cls.superclass}")
        for used in cls.used_classes:
            if used in classes and used != cls.name:
                lines.append(f"{cls.name} --> {used} : uses")

    for cls in classes.values():
        json_lines = []
        for _, ftype, fname in cls.fields:
            sample_value = '"sample"' if 'String' in ftype else '0'
            json_lines.append(f'  "{fname}": {sample_value}')
        json_block = ",\n".join(json_lines)
        lines.append(f'object {cls.name}_JSON {{\n{json_block}\n}}')

    lines.append("@enduml")
    return "\n".join(lines)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python java_to_plantuml.py /path/to/java/project")
        sys.exit(1)

    project_dir = sys.argv[1]
    parsed_classes = walk_project_and_parse(project_dir)
    plantuml_output = generate_plantuml(parsed_classes)

    output_file = "output.puml"
    with open(output_file, "w") as f:
        f.write(plantuml_output)

    print(f"✅ PlantUML diagram generated: {output_file}")
