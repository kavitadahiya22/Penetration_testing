#!/usr/bin/env python3
"""
Expert Developer Fix Script
Systematic implementation of SET recommendations

Based on Expert SET Final Report - implementing:
1. Phase 1: API endpoint fixes (/runs → /agents/pentest/run)
2. Phase 2: Request schema fixes (wrap inputs in proper structure)
3. Phase 3: Config key fixes (api_base_url → api_base)
"""

import os
import re
import glob
from typing import List, Tuple

class TestSuiteFixer:
    def __init__(self, testsuite_path: str):
        self.testsuite_path = testsuite_path
        self.fixed_files = []
        self.errors = []
    
    def fix_all_test_files(self):
        """Apply all fixes systematically"""
        print("🔧 Expert Developer Fix Script")
        print("📋 Implementing SET recommendations...")
        
        # Get all test files
        test_files = glob.glob(os.path.join(self.testsuite_path, "e2e", "*.py"))
        
        for file_path in test_files:
            print(f"\n📄 Processing: {os.path.basename(file_path)}")
            try:
                self.fix_single_file(file_path)
                self.fixed_files.append(file_path)
                print(f"✅ Fixed: {os.path.basename(file_path)}")
            except Exception as e:
                self.errors.append((file_path, str(e)))
                print(f"❌ Error in {os.path.basename(file_path)}: {e}")
        
        self.print_summary()
    
    def fix_single_file(self, file_path: str):
        """Fix a single test file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Phase 1: Fix API endpoints
        content = self.fix_endpoints(content)
        
        # Phase 2: Fix request schema structure
        content = self.fix_request_schema(content)
        
        # Phase 3: Fix config keys
        content = self.fix_config_keys(content)
        
        # Only write if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
    
    def fix_endpoints(self, content: str) -> str:
        """Phase 1: Fix API endpoints"""
        # Fix POST endpoints
        content = re.sub(
            r'api_client\.post\("\s*/runs\s*"',
            'api_client.post("/agents/pentest/run"',
            content
        )
        
        # GET endpoints for /runs/{run_id} are correct - they should remain as /runs/{run_id}
        # Only the POST endpoint for creating runs should change
        
        return content
    
    def fix_config_keys(self, content: str) -> str:
        """Phase 3: Fix config keys"""
        # Fix api_base_url → api_base
        content = re.sub(
            r'test_config\["api_base_url"\]',
            'test_config["api_base"]',
            content
        )
        
        return content
    
    def fix_request_schema(self, content: str) -> str:
        """Phase 2: Fix request schema - wrap data in inputs field"""
        
        # Find run_input dictionary definitions
        # Look for patterns like: run_input = { ... }
        
        # This is a complex transformation, let's handle specific patterns
        
        # Pattern 1: Basic run_input structure
        pattern1 = r'run_input\s*=\s*\{([^}]*"targets"[^}]*)\}'
        
        def replace_run_input(match):
            content_inside = match.group(1).strip()
            
            # Skip if already has "inputs" structure
            if '"inputs"' in content_inside:
                return match.group(0)
            
            # Extract fields that should be wrapped in inputs
            input_fields = ['targets', 'depth', 'features', 'simulate', 'auto_plan', 'policy']
            
            lines = content_inside.split('\n')
            input_lines = []
            root_lines = []
            
            for line in lines:
                line = line.strip()
                if not line or line == ',':
                    continue
                    
                is_input_field = False
                for field in input_fields:
                    if f'"{field}"' in line:
                        is_input_field = True
                        break
                
                if is_input_field:
                    input_lines.append(line)
                else:
                    root_lines.append(line)
            
            # Build new structure
            result = "run_input = {\n"
            
            # Add root level fields first
            for line in root_lines:
                if line.endswith(','):
                    result += f"        {line}\n"
                else:
                    result += f"        {line},\n"
            
            # Add inputs wrapper
            if input_lines:
                result += '        "inputs": {\n'
                for i, line in enumerate(input_lines):
                    if i == len(input_lines) - 1 and line.endswith(','):
                        line = line[:-1]  # Remove trailing comma from last item
                    if not line.endswith(',') and i < len(input_lines) - 1:
                        line += ','
                    result += f"            {line}\n"
                result += '        }\n'
            
            result += "    }"
            return result
        
        content = re.sub(pattern1, replace_run_input, content, flags=re.DOTALL)
        
        return content
    
    def print_summary(self):
        """Print fix summary"""
        print("\n" + "="*60)
        print("🎯 EXPERT DEVELOPER FIX SUMMARY")
        print("="*60)
        print(f"✅ Files successfully fixed: {len(self.fixed_files)}")
        print(f"❌ Files with errors: {len(self.errors)}")
        
        if self.fixed_files:
            print("\n📝 Fixed files:")
            for file_path in self.fixed_files:
                print(f"  • {os.path.basename(file_path)}")
        
        if self.errors:
            print("\n⚠️  Errors:")
            for file_path, error in self.errors:
                print(f"  • {os.path.basename(file_path)}: {error}")
        
        print("\n🚀 Next steps:")
        print("  1. Run test suite to verify fixes")
        print("  2. Check for remaining schema issues")
        print("  3. Initialize OpenSearch indices if needed")
        print("="*60)

def main():
    testsuite_path = "/Users/sumitdahiya/PenTesting/PenetrationTesting/testsuite"
    fixer = TestSuiteFixer(testsuite_path)
    fixer.fix_all_test_files()

if __name__ == "__main__":
    main()
