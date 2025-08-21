#!/usr/bin/env python3
"""
Test script for document validation workflow.
Validates that the GitHub Actions workflow logic works correctly.
"""

import os
import sys
import tempfile
import shutil
import yaml
import re
from pathlib import Path

def test_naming_conventions():
    """Test file naming convention validation."""
    print("Testing naming conventions...")
    
    # Test QMS file naming (allow en-dash or hyphen)
    qms_files = []
    if os.path.exists('QMS'):
        for root, dirs, files in os.walk('QMS'):
            for file in files:
                if file.endswith('.md'):
                    qms_files.append(file)
    
    sop_pattern = re.compile(r'^SOP[\u2011\u2012\u2013\u2014-]\d{3}_[A-Za-z0-9_]+\.md$')
    for file in qms_files:
        if not sop_pattern.match(file):
            print(f"❌ QMS naming violation: {file}")
            return False
    
    # Test DHF directory naming
    if os.path.exists('DHF'):
        dhf_dirs = [d for d in os.listdir('DHF') if os.path.isdir(os.path.join('DHF', d))]
        dhf_pattern = re.compile(r'^\d{2}_[A-Za-z0-9_-]+$')
        for dir_name in dhf_dirs:
            if not dhf_pattern.match(dir_name):
                print(f"❌ DHF directory naming violation: {dir_name}")
                return False
    
    print("✅ Naming conventions check passed")
    return True

def test_template_completeness():
    """Test template completeness validation."""
    print("Testing template completeness...")
    
    required_fields = {
        'title': str,
        'version': str, 
        'author': str,
        'date': str,
        'regulatory_mapping': list
    }
    
    docs_files = []
    if os.path.exists('docs'):
        for root, dirs, files in os.walk('docs'):
            docs_files.extend([os.path.join(root, f) for f in files if f.endswith('.md')])
    
    for file_path in docs_files:
        # Skip sample files and README files
        if 'sample' in file_path.lower() or 'readme' in file_path.lower():
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if not content.startswith('---'):
                print(f"❌ Missing YAML frontmatter: {file_path}")
                return False
                
            end_marker = content.find('---', 3)
            if end_marker == -1:
                print(f"❌ Invalid YAML frontmatter: {file_path}")
                return False
                
            frontmatter = content[3:end_marker]
            try:
                metadata = yaml.safe_load(frontmatter)
                if metadata:
                    for field, field_type in required_fields.items():
                        if field not in metadata:
                            print(f"❌ Missing required field '{field}' in {file_path}")
                            return False
                        if not isinstance(metadata[field], field_type):
                            print(f"❌ Wrong type for field '{field}' in {file_path}")
                            return False
            except yaml.YAMLError as e:
                print(f"❌ Invalid YAML in {file_path}: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
            return False
    
    print("✅ Template completeness check passed")
    return True

def test_regulatory_mapping():
    """Test regulatory mapping validation."""
    print("Testing regulatory mapping...")
    
    valid_regulations = [
        'FDA 21 CFR 820.30',
        'FDA 21 CFR 820.40',
        'FDA 21 CFR 820.181', 
        'FDA 21 CFR 820.184',
        'FDA 21 CFR 11.200',
        'ISO 13485:2016',
        'ISO 14971'
    ]
    
    docs_files = []
    if os.path.exists('docs'):
        for root, dirs, files in os.walk('docs'):
            docs_files.extend([os.path.join(root, f) for f in files if f.endswith('.md')])
    
    for file_path in docs_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if content.startswith('---'):
                end_marker = content.find('---', 3)
                if end_marker != -1:
                    frontmatter = content[3:end_marker]
                    try:
                        metadata = yaml.safe_load(frontmatter)
                        if metadata and 'regulatory_mapping' in metadata:
                            for mapping in metadata['regulatory_mapping']:
                                if mapping not in valid_regulations:
                                    print(f"❌ Invalid regulatory mapping '{mapping}' in {file_path}")
                                    return False
                    except yaml.YAMLError:
                        pass  # Already handled in template validation
        except Exception:
            pass  # Already handled in template validation
    
    print("✅ Regulatory mapping check passed")
    return True

def test_document_relationships():
    """Test document relationship checking."""
    print("Testing document relationships...")
    
    all_docs = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.md') and not file.startswith('README'):
                all_docs.append(os.path.join(root, file))
    
    referenced_docs = set()
    for doc_path in all_docs:
        try:
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Find markdown links
                links = re.findall(r'\[.*?\]\((.*?\.md)\)', content)
                for link in links:
                    if not link.startswith('/'):
                        link = os.path.normpath(os.path.join(os.path.dirname(doc_path), link))
                    referenced_docs.add(link)
        except Exception:
            continue
    
    # Count orphaned documents in docs/
    orphaned_count = 0
    for doc in all_docs:
        if doc not in referenced_docs and 'docs/' in doc:
            orphaned_count += 1
    
    print(f"✅ Document relationships check completed ({orphaned_count} potential orphans found)")
    return True

def create_test_document():
    """Create a test document with proper metadata for testing."""
    test_content = """---
title: "Test Document"
version: "1.0"
author: "Test Author"
date: "2025-08-18"
regulatory_mapping:
  - "FDA 21 CFR 820.30"
  - "ISO 13485:2016"
---

# Test Document

This is a test document for validation testing.
"""
    
    os.makedirs('docs/test', exist_ok=True)
    with open('docs/test/test-document.md', 'w') as f:
        f.write(test_content)
    
    print("✅ Test document created")

def cleanup_test_files():
    """Clean up test files."""
    if os.path.exists('docs/test'):
        shutil.rmtree('docs/test')
    print("✅ Test files cleaned up")

def run_all_tests():
    """Run all validation tests."""
    print("🧪 Running document validation tests...\n")
    
    # Create test document
    create_test_document()
    
    try:
        tests = [
            test_naming_conventions,
            test_template_completeness,
            test_regulatory_mapping,
            test_document_relationships
        ]
        
        passed = 0
        for test in tests:
            if test():
                passed += 1
            print()
        
        print(f"📊 Test Results: {passed}/{len(tests)} tests passed")
        
        if passed == len(tests):
            print("🎉 All validation tests passed!")
            return True
        else:
            print("❌ Some validation tests failed")
            return False
            
    finally:
        # Clean up
        cleanup_test_files()

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)