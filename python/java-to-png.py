import os
import re
from graphviz import Digraph

class JavaClass:
    def __init__(self, name):
        self.name = name
        self.fields = []
        self.methods = []
        self.superclass = None
        self.uses = set()

def parse_java_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()

    classes = []
    class_pattern = re.compile(r'\bclass\s+(\w+)(?:\s+extends\s+(\w+))?')
    field_pattern = re.compile(r'(public|private|protected)\s+([\w<>]+)\s+(\w+);')
    method_pattern = re.compile(r'(public|private|protected)\s+[\w<>]+\s+(\w+)\s*\([^)]*\)\s*[{;]')
    usage_pattern = re.compile(r'new\s+(\w+)\s*\(')

    for class_match in class_pattern.finditer(content):
        cls_name = class_match.group(1)
        superclass = class_match.group(2)
        cls = JavaClass(cls_name)
        cls.superclass = superclass

        class_body_start = class_match.end()
        brace_depth = 1
        body = content[class_body_start:]
        i = 0
        while i < len(body) and brace_depth > 0:
            if body[i] == '{':
                brace_depth += 1
            elif body[i] == '}':
                brace_depth -= 1
            i += 1

        class_body = body[:i]
        for f in field_pattern.findall(class_body):
            cls.fields.append((f[0], f[1], f[2]))
        for m in method_pattern.findall(class_body):
            cls.methods.append((m[0], m[1]))
        for u in usage_pattern.findall(class_body):
            cls.uses.add(u)

        classes.append(cls)
    return classes

def walk_and_parse_project(root):
    all_classes = {}
    for subdir, _, files in os.walk(root):
        for file in files:
            if file.endswith('.java'):
                path = os.path.join(subdir, file)
                for cls in parse_java_file(path):
                    all_classes[cls.name] = cls
    return all_classes

def generate_graph(classes: dict, output_file="java_class_diagram"):
    dot = Digraph(comment="Java Class Diagram", format="png")
    dot.attr("node", shape="record", fontsize="10")

    for cls in classes.values():
        label = f"{{{cls.name}|"
        label += "\\l".join([f"- {ftype} {fname}" for _, ftype, fname in cls.fields]) + "\\l|"
        label += "\\l".join([f"+ {mname}()" for _, mname in cls.methods]) + "\\l}"
        dot.node(cls.name, label=label)

    for cls in classes.values():
        if cls.superclass and cls.superclass in classes:
            dot.edge(cls.superclass, cls.name, arrowhead="empty", label="extends")
        for used in cls.uses:
            if used in classes and used != cls.name:
                dot.edge(cls.name, used, style="dashed", label="uses")

    dot.render(output_file, view=True)
    print(f"✅ Diagram saved to: {output_file}.png")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python java_to_graphviz.py /path/to/java/project")
        sys.exit(1)

    project_path = sys.argv[1]
    parsed_classes = walk_and_parse_project(project_path)
    generate_graph(parsed_classes)
