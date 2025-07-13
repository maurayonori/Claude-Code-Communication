#!/usr/bin/env python3
"""
TradeFlow Cleanup Script - Phase 1: Unused Imports
Safe removal of unused imports with backup and verification
"""

import ast
import re
import shutil
from pathlib import Path
from typing import List, Tuple

class UnusedImportCleaner:
    def __init__(self, root_dir: str, backup_dir: str = None):
        self.root_dir = Path(root_dir)
        self.backup_dir = Path(backup_dir) if backup_dir else Path("backup_src")
        self.cleaned_files = []
        self.backup_created = False
        
    def create_backup(self):
        """Create backup of source directory"""
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        
        shutil.copytree(self.root_dir, self.backup_dir)
        self.backup_created = True
        print(f"Backup created at: {self.backup_dir}")
    
    def find_unused_imports(self, file_path: Path) -> List[Tuple[int, str]]:
        """Find unused imports in a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            unused_imports = []
            
            for i, line in enumerate(lines):
                # Skip if not an import line
                if not (line.strip().startswith('import ') or line.strip().startswith('from ')):
                    continue
                
                # Extract import names
                import_names = self._extract_import_names(line)
                
                # Check if any are unused
                for import_name in import_names:
                    if self._is_import_unused(import_name, content, line):
                        unused_imports.append((i, line.strip()))
                        break  # Don't double-count the same line
            
            return unused_imports
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return []
    
    def _extract_import_names(self, line: str) -> List[str]:
        """Extract import names from import line"""
        import_names = []
        
        # Handle 'import module' format
        if line.strip().startswith('import '):
            import_part = line.strip()[7:]  # Remove 'import '
            for item in import_part.split(','):
                item = item.strip()
                if ' as ' in item:
                    import_names.append(item.split(' as ')[1].strip())
                else:
                    import_names.append(item.split('.')[0])
        
        # Handle 'from module import item' format  
        elif line.strip().startswith('from '):
            if ' import ' in line:
                import_part = line.split(' import ')[1]
                for item in import_part.split(','):
                    item = item.strip()
                    if ' as ' in item:
                        import_names.append(item.split(' as ')[1].strip())
                    else:
                        import_names.append(item)
        
        return import_names
    
    def _is_import_unused(self, import_name: str, content: str, import_line: str) -> bool:
        """Check if import is unused in the content"""
        # Skip certain imports that are commonly used implicitly
        skip_imports = {
            'List', 'Dict', 'Tuple', 'Optional', 'Union', 'Any', 'Type',
            '__future__', '*'
        }
        
        if import_name in skip_imports:
            return False
        
        # Count occurrences
        pattern = r'\b' + re.escape(import_name) + r'\b'
        matches = re.findall(pattern, content)
        
        # If only found in the import line itself, it's unused
        # Allow for 1-2 matches to account for the import line
        return len(matches) <= 1
    
    def clean_file(self, file_path: Path) -> bool:
        """Clean unused imports from a file"""
        unused_imports = self.find_unused_imports(file_path)
        
        if not unused_imports:
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Remove unused import lines (reverse order to maintain line numbers)
            for line_num, import_line in reversed(unused_imports):
                print(f"  Removing: {import_line}")
                del lines[line_num]
            
            # Write cleaned content back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            self.cleaned_files.append(str(file_path))
            return True
            
        except Exception as e:
            print(f"Error cleaning {file_path}: {e}")
            return False
    
    def clean_directory(self, max_files: int = 20) -> dict:
        """Clean unused imports from multiple files"""
        if not self.backup_created:
            self.create_backup()
        
        python_files = list(self.root_dir.rglob("*.py"))
        results = {
            'processed': 0,
            'cleaned': 0,
            'errors': 0,
            'files_cleaned': []
        }
        
        # Prioritize files with most unused imports
        file_priorities = []
        for file_path in python_files:
            unused_count = len(self.find_unused_imports(file_path))
            if unused_count > 0:
                file_priorities.append((unused_count, file_path))
        
        file_priorities.sort(reverse=True)
        
        print(f"Found {len(file_priorities)} files with unused imports")
        print(f"Processing top {min(max_files, len(file_priorities))} files...")
        
        for i, (unused_count, file_path) in enumerate(file_priorities[:max_files]):
            results['processed'] += 1
            rel_path = file_path.relative_to(self.root_dir)
            
            print(f"\n{i+1}. Cleaning {rel_path} ({unused_count} unused imports)")
            
            try:
                if self.clean_file(file_path):
                    results['cleaned'] += 1
                    results['files_cleaned'].append(str(rel_path))
            except Exception as e:
                print(f"ERROR: {e}")
                results['errors'] += 1
        
        return results
    
    def restore_backup(self):
        """Restore from backup"""
        if not self.backup_created or not self.backup_dir.exists():
            print("No backup available to restore")
            return False
        
        if self.root_dir.exists():
            shutil.rmtree(self.root_dir)
        
        shutil.copytree(self.backup_dir, self.root_dir)
        print(f"Restored from backup: {self.backup_dir}")
        return True

def main():
    print("TradeFlow Unused Import Cleaner")
    print("=" * 50)
    
    # Initialize cleaner
    cleaner = UnusedImportCleaner("/Users/yono/Build/TradeFlow/src")
    
    print("\nPhase 1: Creating backup...")
    cleaner.create_backup()
    
    print("\nPhase 2: Analyzing and cleaning files...")
    results = cleaner.clean_directory(max_files=15)  # Start with top 15 files
    
    print("\n" + "=" * 50)
    print("CLEANUP SUMMARY:")
    print(f"Files processed: {results['processed']}")
    print(f"Files cleaned: {results['cleaned']}")
    print(f"Errors: {results['errors']}")
    
    if results['files_cleaned']:
        print(f"\nCleaned files:")
        for file_path in results['files_cleaned']:
            print(f"  • {file_path}")
    
    print(f"\nBackup location: {cleaner.backup_dir}")
    print("\nNext steps:")
    print("1. Run test suite to verify no breakage")
    print("2. If tests pass, commit changes")
    print("3. If tests fail, run: python cleanup_script.py --restore")
    
    # Offer to restore if there are errors
    if results['errors'] > 0:
        response = input(f"\n{results['errors']} errors occurred. Restore backup? (y/N): ")
        if response.lower() == 'y':
            cleaner.restore_backup()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--restore':
        cleaner = UnusedImportCleaner("/Users/yono/Build/TradeFlow/src")
        cleaner.backup_dir = Path("backup_src")
        cleaner.backup_created = True
        cleaner.restore_backup()
    else:
        main()