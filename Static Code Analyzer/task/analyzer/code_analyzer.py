import ast
import os.path
import sys
import re


class Analyzer:
    messages = {'S001': 'Too long',
                'S002': 'Indentation is not a multiple of four',
                'S003': 'Unnecessary semicolon after a statement',
                'S004': 'Less than two spaces before inline comments',
                'S005': 'TODO found',
                'S006': 'More than two blank lines preceding a code line',
                'S007': 'Too many spaces after construction_name (def or class)',
                'S008': 'Class name class_name should be written in CamelCase',
                'S009': 'Function name function_name should be written in snake_case',
                'S010': 'Argument name arg_name should be written in snake case',
                'S011': 'Variable var_name should be written in snake_case',
                'S012': 'The default argument value is mutable'}

    comment_order = None
    empty_line_count = 0

    def __init__(self, file):
        self.file = file

    def printer(self, n, code):
        print(f'Line {n}: {code} {self.messages[code]}')

    def ast_processor(self, ast_errors):
        class FuncErrorFinder(ast.NodeVisitor):
            def __init__(self, ast_errors):
                self.ast_errors = ast_errors

            def visit_FunctionDef(self, node):
                args = [a.arg for a in node.args.args]
                for arg in args:
                    if not re.match(r'\A[a-z0-9_]+\Z', arg):
                        self.ast_errors['s010'].append(node.lineno)
                for node1 in ast.walk(node):
                    if isinstance(node1, ast.Name) and isinstance(node1.ctx, ast.Store):
                        if not re.match(r'\A[a-z0-9_]+\Z', node1.id):
                            self.ast_errors['s011'].append(node1.lineno)
                def_args = [def_arg for def_arg in node.args.defaults]
                for def_arg in def_args:
                    if isinstance(def_arg, ast.List) or isinstance(def_arg, ast.Dict):
                        self.ast_errors['s012'].append(def_arg.lineno)
        FuncErrorFinder(ast_errors).visit(self.tree)

    def comment_locator(self, line):
        new_line_list = list(line)
        for index, char in enumerate(line[1:], start=1):
            if char in ["'", '"'] and line[index - 1] == '\\':
                new_line_list[index] = '_'
        for num, char in enumerate(new_line_list):
            if char == '#':
                odd_chars = [c for c in new_line_list[:num] if c == '"' or c == "'"]
                if not odd_chars:
                    return num
                elif len(odd_chars) >= 2 and odd_chars[0] == odd_chars[-1]:
                    return num
        return None

    def s001(self, n, line):
        if len(line) > 79:
            self.printer(n, 'S001')

    def s002(self, n, line):
        for count, char in enumerate(line):
            if char != ' ':
                if count % 4:
                    self.printer(n, 'S002')
                break

    def s003(self, n, line):
        if self.comment_order is None and line[-1] == ';':
            self.printer(n, 'S003')
        elif self.comment_order == 0:
            return
        elif line[:self.comment_order].rstrip(' ').endswith(';'):
            self.printer(n, 'S003')

    def s004(self, n, line):
        if self.comment_order and len(line[self.comment_order:]) > 1:
            if line[self.comment_order - 2: self.comment_order] != '  ':
                self.printer(n, 'S004')

    def s005(self, n, line):
        if self.comment_order is None:
            return
        elif 'TODO' in line[self.comment_order:].upper():
            self.printer(n, 'S005')

    def s006(self, n, line):
        if self.empty_line_count > 2:
            self.printer(n, 'S006')
        self.empty_line_count = 0

    def s007(self, n, line):
        if re.match(' *class {2}', line) or re.match(' *def {2}', line):
            self.printer(n, 'S007')

    def s008(self, n, line):
        m = re.match(r' *class +', line)
        if m:
            if not re.match(r'[A-Z][a-zA-Z0-9]* *[(:]', line[m.end():]):
                self.printer(n, 'S008')

    def s009(self, n, line):
        m = re.match(r' *def +', line)
        if m:
            if not re.match(r'[a-z_]{1,2}[a-z0-9_]*[(]', line[m.end():]):
                self.printer(n, 'S009')

    def s010(self, n, line):
        if n in self.ast_errors['s010']:
            self.printer(n, 'S010')

    def s011(self, n, line):
        if n in self.ast_errors['s011']:
            self.printer(n, 'S011')

    def s012(self, n, line):
        if n in self.ast_errors['s012']:
            self.printer(n, 'S012')

    def analyze(self):
        self.ast_processor(self.ast_errors)
        for n, line in enumerate(self.file, start=1):
            line_mod = line.strip('\n\r')
            if line_mod == '':
                self.empty_line_count += 1
                continue
            else:
                self.comment_order = self.comment_locator(line_mod)
                self.s001(n, line_mod)
                self.s002(n, line_mod)
                self.s003(n, line_mod)
                self.s004(n, line_mod)
                self.s005(n, line_mod)
                self.s006(n, line_mod)
                self.s007(n, line_mod)
                self.s008(n, line_mod)
                self.s009(n, line_mod)
                self.s010(n, line_mod)
                self.s011(n, line_mod)
                self.s012(n, line_mod)


class Analyzer2(Analyzer):
    def __init__(self, file, r_path):
        super().__init__(file)
        self.r_path = r_path
        self.ast_errors = {'s010': [], 's011': [], 's012': []}
        self.tree = ast.parse(open(r_path).read())

    def printer(self, n, code):
        print(f'{self.r_path}: ', end='')
        super().printer(n, code)


# my_path = input()
file_path_list = []
# my_path2 = r'..\test\myTest.py'
my_path2 = sys.argv[1]
if os.path.isfile(my_path2):
    file_path_list.append(my_path2)
else:
    for dirpath, dirnames, files in os.walk(os.path.join('.', my_path2)):
        for file_name in files:
            if file_name.endswith('.py'):
                file_path_list.append(os.path.join(dirpath, file_name))
for file_path in file_path_list:
    with open(file_path, 'r') as my_file:
        my_analyzer = Analyzer2(my_file, file_path)
        my_analyzer.analyze()
