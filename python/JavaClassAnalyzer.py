import os
import re
from collections import defaultdict

# Regex patterns to capture class and interface structure
CLASS_PATTERN = re.compile(r'\bclass\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+))?')
INTERFACE_PATTERN = re.compile(r'\binterface\s+(\w+)(?:\s+extends\s+([\w,\s]+))?')

# Storage
class_relations = defaultdict(list)
all_classes = set()
parents = {}

def parse_java_file(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

        # Find classes
        for match in CLASS_PATTERN.finditer(content):
            child = match.group(1)
            parent = match.group(2)
            interfaces = match.group(3)

            all_classes.add(child)
            if parent:
                parents[child] = parent
                class_relations[parent].append(child)
            if interfaces:
                for interface in interfaces.split(','):
                    iface = interface.strip()
                    class_relations[iface].append(child)
                    parents[child] = iface  # Only store one parent for hierarchy

        # Find interfaces
        for match in INTERFACE_PATTERN.finditer(content):
            interface = match.group(1)
            extended = match.group(2)
            all_classes.add(interface)
            if extended:
                for parent_iface in extended.split(','):
                    class_relations[parent_iface.strip()].append(interface)
                    parents[interface] = parent_iface.strip()


def traverse_directory(root_dir):
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.java'):
                parse_java_file(os.path.join(root, file))


def print_hierarchy(class_name, level=0):
    print("    " * level + f"- {class_name}")
    for child in class_relations.get(class_name, []):
        print_hierarchy(child, level + 1)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Analyze Java Class Dependencies")
    parser.add_argument("path", help="Root directory of Java source files")
    args = parser.parse_args()

    traverse_directory(args.path)

    # Print top-level classes/interfaces (those with no parent)
    root_nodes = [cls for cls in all_classes if cls not in parents]
    print("\n📁 Java Class Hierarchy:\n")
    for root in sorted(root_nodes):
        print_hierarchy(root)
