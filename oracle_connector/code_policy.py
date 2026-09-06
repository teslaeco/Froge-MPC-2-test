"""Early validation; the rootless, resource-limited container is the execution boundary."""
import ast
import re

IMPORTS = {'bpy', 'math', 'random', 'mathutils'}
BLOCKED = {'open', 'exec', 'eval', 'compile', '__import__', 'globals', 'locals', 'vars',
           'getattr', 'setattr', 'delattr', 'breakpoint', 'input', 'help', 'dir', 'type',
           'object', 'memoryview', 'classmethod', 'staticmethod', 'property'}
BLOCKED_ATTRS = {'wm', 'script', 'app', 'preferences', 'libraries', 'texts', 'handlers',
                 'driver_add', 'driver_namespace', 'as_pointer', 'bl_rna', 'rna_type',
                 'load', 'write', 'save', 'open', 'user_resource', 'resource_path'}

def extract_code(text):
    blocks = re.findall(r'```(?:python|py)?\s*\n(.*?)```', text, re.S | re.I)
    return (max(blocks, key=len) if blocks else text).strip()

def validate_code(code):
    if not isinstance(code, str) or not code.strip() or len(code.encode()) > 60000:
        raise ValueError('AI musi zwrocic kompletny skrypt Python do 60 KB.')
    tree = ast.parse(code)
    if sum(1 for _ in ast.walk(tree)) > 12000:
        raise ValueError('Skrypt przekracza limit zlozonosci.')
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(n.name not in IMPORTS for n in node.names):
                raise ValueError('Dozwolone importy: bpy, math, random, mathutils.')
        elif isinstance(node, ast.ImportFrom):
            if node.level or node.module not in IMPORTS or any(n.name.startswith('_') or n.name == '*' for n in node.names):
                raise ValueError('Niedozwolony import.')
        elif isinstance(node, ast.Name) and (node.id in BLOCKED or node.id.startswith('_')):
            raise ValueError('Niedozwolona nazwa: ' + node.id)
        elif isinstance(node, ast.Attribute) and (node.attr.startswith('_') or node.attr in BLOCKED_ATTRS):
            raise ValueError('Niedozwolona operacja: ' + node.attr)
        elif isinstance(node, (ast.ClassDef, ast.Global, ast.Nonlocal, ast.AsyncFunctionDef)):
            raise ValueError('Uzyj zwyklych funkcji i operacji modelowania.')
    return code
