"""Early validation; the rootless, resource-limited container is the execution boundary."""
import ast
import io
import re
import tokenize

IMPORTS = {'bpy', 'math', 'random', 'mathutils'}
HELPERS = {'make_material', 'mesh_object', 'tube', 'ellipsoid', 'join_meshes', 'hair_lock'}
BLOCKED = {'open', 'exec', 'eval', 'compile', '__import__', 'globals', 'locals', 'vars',
           'getattr', 'setattr', 'delattr', 'breakpoint', 'input', 'help', 'dir', 'type',
           'object', 'memoryview', 'classmethod', 'staticmethod', 'property'}
BLOCKED_ATTRS = {'wm', 'script', 'app', 'preferences', 'libraries', 'texts', 'handlers',
                 'driver_add', 'driver_namespace', 'as_pointer', 'bl_rna', 'rna_type',
                 'load', 'write', 'save', 'open', 'user_resource', 'resource_path'}


class CodePolicyError(ValueError):
    def __init__(self, operation, line, partial_code=''):
        self.operation = operation
        self.line = line
        self.partial_code = partial_code
        super().__init__('Niedozwolona operacja: %s (wiersz %s). AI musi tworzyc tekstury funkcja make_material, bez odczytu plikow.' % (operation, line))


class StreamPolicyGuard:
    """Reject forbidden attributes on complete code lines before wasting a full response.

    Tokenization ignores strings/comments. This is only early feedback: the full
    AST policy and the isolated container remain mandatory before execution.
    """
    def __init__(self):
        self.text = ''

    def feed(self, fragment):
        self.text += fragment
        if '\n' not in fragment:
            return
        complete = self.text[:self.text.rfind('\n') + 1]
        previous = None
        try:
            for token in tokenize.generate_tokens(io.StringIO(complete).readline):
                if token.type in (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE,
                                  tokenize.INDENT, tokenize.DEDENT, tokenize.ENCODING):
                    continue
                if (previous is not None and previous.type == tokenize.OP and previous.string == '.'
                        and token.type == tokenize.NAME
                        and (token.string.startswith('_') or token.string in BLOCKED_ATTRS)):
                    raise CodePolicyError(token.string, token.start[0], self.text)
                previous = token
        except (tokenize.TokenError, IndentationError):
            # The rest of the program has not arrived yet. Never execute a prefix.
            pass


def repair_instruction(error):
    instruction = ('Return a COMPLETE corrected Python script for the ORIGINAL requested object. '
                   'Use the provided geometry helpers and make_material for every material. '
                   'Do not return a patch or an explanation. ')
    if isinstance(error, CodePolicyError):
        return instruction + (
            'The previous response was rejected for forbidden attribute .%s on line %s. '
            'NO INPUT ASSET FILES EXIST. Do not load textures or models from any path. '
            'Remove external-file/image-loading logic entirely. Never call bpy.data.images.load, '
            'load, open, save, read_factory_settings or any file/network API. '
            'Create packed textures with these EXISTING helpers instead:\n'
            'bark_material = make_material("oak_bark", (0.27, 0.14, 0.06), "bark")\n'
            'leaf_material = make_material("oak_leaves", (0.12, 0.36, 0.05), "leaf")\n'
            'Pass those materials to tube, mesh_object or ellipsoid. '
            'For other objects choose the appropriate supported material pattern. '
            'Keep all recognizable geometry requested by the user.' % (error.operation, error.line))
    return instruction + 'Fix this error while respecting all original limits: ' + str(error)[-2500:]

def extract_code(text):
    blocks = re.findall(r'```(?:python|py)?\s*\n(.*?)```', text, re.S | re.I)
    return (max(blocks, key=len) if blocks else text).strip()

def prepare_code(code):
    # Inspect the entire original program first, including discarded definitions.
    # A helper replacement never makes forbidden file/network operations acceptable.
    validate_code(code, allow_helper_definitions=True)
    tree = ast.parse(code)
    # Geometry definitions may have different return types. Never replace them
    # and keep their callers: that caused the Object unpacking failure in v5.
    if any(isinstance(node, ast.FunctionDef) and node.name in HELPERS - {'make_material'} for node in ast.walk(tree)):
        raise ValueError('Zapisany skrypt ma niezgodne funkcje geometrii. Utworz nowy model w trybie planu sceny.')
    replaced = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name == 'make_material' and not node.decorator_list]
    if replaced:
        tree.body = [node for node in tree.body if node not in replaced]
        code = ast.unparse(tree)
    validate_code(code)
    for node in ast.walk(ast.parse(code)):
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name) and node.value.func.id in HELPERS
                and any(isinstance(target, (ast.Tuple, ast.List)) for target in node.targets)):
            raise ValueError('Zapisany skrypt oczekuje innych wynikow funkcji geometrii. Utworz nowy model w trybie planu sceny.')
    return code, [node.name for node in replaced]


def validate_code(code, *, allow_helper_definitions=False):
    if not isinstance(code, str) or not code.strip() or len(code.encode()) > 60000:
        raise ValueError('AI musi zwrocic kompletny skrypt Python do 60 KB.')
    tree = ast.parse(code)
    if sum(1 for _ in ast.walk(tree)) > 12000:
        raise ValueError('Skrypt przekracza limit zlozonosci.')
    for node in ast.walk(tree):
        binding = (node.id if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)) else
                   node.arg if isinstance(node, ast.arg) else
                   node.name if isinstance(node, ast.ExceptHandler) else
                   (node.asname or node.name) if isinstance(node, ast.alias) else
                   node.name if isinstance(node, ast.FunctionDef) and not allow_helper_definitions else None)
        if binding in HELPERS:
            raise ValueError('Nie nadpisuj gotowej funkcji %s. Wywolaj funkcje dostarczona przez Froge.' % binding)
        if isinstance(node, ast.Import):
            if any(n.name not in IMPORTS for n in node.names):
                raise ValueError('Dozwolone importy: bpy, math, random, mathutils.')
        elif isinstance(node, ast.ImportFrom):
            if node.level or node.module not in IMPORTS or any(n.name.startswith('_') or n.name == '*' for n in node.names):
                raise ValueError('Niedozwolony import.')
        elif isinstance(node, ast.Name) and (node.id in BLOCKED or node.id.startswith('_')):
            raise ValueError('Niedozwolona nazwa: ' + node.id)
        elif isinstance(node, ast.Attribute) and (node.attr.startswith('_') or node.attr in BLOCKED_ATTRS):
            raise CodePolicyError(node.attr, node.lineno)
        elif isinstance(node, (ast.ClassDef, ast.Global, ast.Nonlocal, ast.AsyncFunctionDef)):
            raise ValueError('Uzyj zwyklych funkcji i operacji modelowania.')
    return code
