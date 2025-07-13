#!/usr/bin/env python3
"""
TradeFlow Dead Code Analysis Tool
Identifies unused imports, dead functions, and optimization opportunities
"""

import ast
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Set

class DeadCodeAnalyzer:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.all_files = list(self.root_dir.rglob("*.py"))
        self.function_definitions: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
        self.function_calls: Dict[str, List[str]] = defaultdict(list)
        self.imports_by_file: Dict[str, List[Tuple[str, str]]] = {}
        
    def analyze_all_files(self):
        """Analyze all Python files for dead code patterns"""
        print(f"Analyzing {len(self.all_files)} Python files...")
        
        for file_path in self.all_files:
            try:
                self._analyze_file(file_path)
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
    
    def _analyze_file(self, file_path: Path):
        """Analyze a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            rel_path = str(file_path.relative_to(self.root_dir))
            
            # Extract imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        imports.append((name, alias.name))
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if alias.name != '*':
                            name = alias.asname if alias.asname else alias.name
                            imports.append((name, alias.name))
            
            self.imports_by_file[rel_path] = imports
            
            # Extract function definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    self.function_definitions[node.name].append((rel_path, node.lineno))
                    
                    # Extract function calls within this function
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call):
                            if isinstance(child.func, ast.Name):
                                self.function_calls[child.func.id].append(rel_path)
                            elif isinstance(child.func, ast.Attribute):
                                self.function_calls[child.func.attr].append(rel_path)
            
        except Exception:
            pass
    
    def find_unused_imports(self) -> Dict[str, List[str]]:
        """Find potentially unused imports"""
        unused_imports = {}
        
        for file_path, imports in self.imports_by_file.items():
            try:
                with open(self.root_dir / file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_unused = []
                for import_name, full_name in imports:
                    # Skip common typing imports and special cases
                    if import_name in ['List', 'Dict', 'Tuple', 'Optional', 'Union', 'Any']:
                        continue
                    
                    # Simple regex check for usage
                    pattern = r'\b' + re.escape(import_name) + r'\b'
                    matches = len(re.findall(pattern, content))
                    
                    # If found only once (in the import line), potentially unused
                    if matches <= 1:
                        file_unused.append(f"{import_name} (from {full_name})")
                
                if file_unused:
                    unused_imports[file_path] = file_unused
                    
            except Exception:
                continue
        
        return unused_imports
    
    def find_dead_functions(self) -> List[Tuple[str, str, int]]:
        """Find functions that are defined but never called"""
        dead_functions = []
        
        for func_name, definitions in self.function_definitions.items():
            # Skip special methods and common patterns
            if (func_name.startswith('_') or 
                func_name in ['__init__', '__str__', '__repr__', 'main', 'run'] or
                func_name.startswith('test_')):
                continue
            
            # Check if function is called anywhere
            if func_name not in self.function_calls:
                for file_path, line_no in definitions:
                    dead_functions.append((func_name, file_path, line_no))
        
        return dead_functions
    
    def find_placeholder_functions(self) -> List[Tuple[str, int, str]]:
        """Find functions with only pass, TODO, or NotImplemented"""
        placeholders = []
        
        for file_path in self.all_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                rel_path = str(file_path.relative_to(self.root_dir))
                
                for i, line in enumerate(lines):
                    if 'def ' in line:
                        # Check next few lines for placeholder patterns
                        next_lines = lines[i+1:i+5]
                        content = ''.join(next_lines).strip()
                        
                        if (content == 'pass' or 
                            'TODO' in content or 
                            'FIXME' in content or 
                            'NotImplementedError' in content or
                            'raise NotImplemented' in content):
                            
                            func_match = re.search(r'def\s+(\w+)', line)
                            if func_match:
                                placeholders.append((rel_path, i+1, func_match.group(1)))
                
            except Exception:
                continue
        
        return placeholders
    
    def find_large_files_with_low_utilization(self) -> List[Tuple[str, int, int, float]]:
        """Find large files with potentially low function utilization"""
        large_files = []
        
        for file_path in self.all_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = len(f.readlines())
                
                if lines > 300:
                    rel_path = str(file_path.relative_to(self.root_dir))
                    
                    # Count functions in this file
                    func_count = sum(1 for defs in self.function_definitions.values() 
                                   for file, line in defs if file == rel_path)
                    
                    # Count called functions in this file
                    called_count = sum(1 for func_name, defs in self.function_definitions.items()
                                     for file, line in defs 
                                     if file == rel_path and func_name in self.function_calls)
                    
                    utilization = (called_count / func_count) if func_count > 0 else 0
                    large_files.append((rel_path, lines, func_count, utilization))
            
            except Exception:
                continue
        
        return sorted(large_files, key=lambda x: x[1], reverse=True)

def main():
    analyzer = DeadCodeAnalyzer("/Users/yono/Build/TradeFlow/src")
    analyzer.analyze_all_files()
    
    print("=" * 80)
    print("TRADEFLOW DEAD CODE ANALYSIS REPORT")
    print("=" * 80)
    
    # 1. Unused Imports
    print("\n1. UNUSED IMPORTS:")
    print("-" * 40)
    unused_imports = analyzer.find_unused_imports()
    total_unused_imports = 0
    for file_path, unused_list in unused_imports.items():
        if len(unused_list) > 2:  # Only show files with multiple unused imports
            print(f"\n{file_path}:")
            for unused in unused_list[:5]:  # Show top 5
                print(f"  • {unused}")
                total_unused_imports += 1
            if len(unused_list) > 5:
                print(f"  ... and {len(unused_list) - 5} more")
    
    print(f"\nTotal potentially unused imports: {total_unused_imports}")
    
    # 2. Dead Functions
    print("\n\n2. POTENTIALLY DEAD FUNCTIONS:")
    print("-" * 40)
    dead_functions = analyzer.find_dead_functions()
    for func_name, file_path, line_no in dead_functions[:15]:  # Show top 15
        print(f"• {func_name} in {file_path}:{line_no}")
    
    if len(dead_functions) > 15:
        print(f"... and {len(dead_functions) - 15} more")
    
    print(f"\nTotal potentially dead functions: {len(dead_functions)}")
    
    # 3. Placeholder Functions
    print("\n\n3. PLACEHOLDER/EMPTY FUNCTIONS:")
    print("-" * 40)
    placeholders = analyzer.find_placeholder_functions()
    for file_path, line_no, func_name in placeholders:
        print(f"• {func_name} in {file_path}:{line_no}")
    
    print(f"\nTotal placeholder functions: {len(placeholders)}")
    
    # 4. Large Files
    print("\n\n4. LARGE FILES WITH LOW UTILIZATION:")
    print("-" * 40)
    large_files = analyzer.find_large_files_with_low_utilization()
    for file_path, lines, func_count, utilization in large_files[:10]:
        print(f"• {file_path}: {lines} lines, {func_count} functions, {utilization:.1%} utilization")
    
    # 5. Summary
    print("\n\n5. CLEANUP OPPORTUNITIES SUMMARY:")
    print("-" * 40)
    print(f"• Unused imports: ~{total_unused_imports} lines could be removed")
    print(f"• Dead functions: ~{len(dead_functions) * 10} lines could be removed (est.)")
    print(f"• Placeholder functions: ~{len(placeholders) * 5} lines could be removed")
    print(f"• Large files needing review: {len([f for f in large_files if f[3] < 0.5])}")
    
    estimated_total = total_unused_imports + (len(dead_functions) * 10) + (len(placeholders) * 5)
    print(f"\nEstimated total lines that could be removed: ~{estimated_total}")
    print(f"Potential codebase reduction: ~{estimated_total/75718*100:.1f}%")

if __name__ == "__main__":
    main()