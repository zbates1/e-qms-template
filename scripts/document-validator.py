#!/usr/bin/env python3
"""
Document Validator for eQMS GitHub-native Quality Management System

This script validates document naming conventions, template completeness,
regulatory mapping, and document relationships according to FDA 21 CFR 820
and ISO 13485 compliance requirements.

Usage:
    python scripts/document-validator.py [--check] [--paths PATH1,PATH2]
    
Options:
    --check     Run all validation checks (default)
    --paths     Comma-separated list of paths to validate (default: docs,QMS,DHF,RMF)
"""

import os
import sys
import re
import yaml
import argparse
from pathlib import Path
from typing import List, Dict, Set, Tuple


class DocumentValidator:
    """Validates eQMS documents for compliance requirements."""
    
    def __init__(self, paths: List[str] = None):
        self.paths = paths or ['docs', 'QMS', 'DHF', 'RMF']
        self.errors = []
        self.warnings = []
        
        # Valid regulatory mappings
        self.valid_regulations = [
            'FDA 21 CFR 820.30',
            'FDA 21 CFR 820.40', 
            'FDA 21 CFR 820.181',
            'FDA 21 CFR 820.184',
            'FDA 21 CFR 11.200',
            'ISO 13485:2016',
            'ISO 14971'
        ]
        
        # Required metadata fields for document templates
        self.required_fields = {
            'title': str,
            'version': str,
            'author': str,
            'date': str,
            'regulatory_mapping': list
        }
    
    def validate_naming_conventions(self) -> bool:
        """Validate file and directory naming conventions."""
        print("Validating naming conventions...")
        
        # QMS file naming: SOP-XXX_Name.md (allow en-dash or hyphen in both positions)
        if os.path.exists('QMS'):
            for root, dirs, files in os.walk('QMS'):
                for file in files:
                    if file.endswith('.md'):
                        if not re.match(r'^SOP[\u2011\u2012\u2013\u2014-]\d{3}_[A-Za-z0-9_\u2011\u2012\u2013\u2014-]+\.md$', file):
                            self.errors.append(f'QMS file naming violation: {os.path.join(root, file)}')
        
        # DHF directory numbering: 01_Name format (allow various hyphens)
        if os.path.exists('DHF'):
            dhf_dirs = [d for d in os.listdir('DHF') if os.path.isdir(os.path.join('DHF', d))]
            for dir_name in dhf_dirs:
                if not re.match(r'^\d{2}_[A-Za-z0-9_\u2011\u2012\u2013\u2014-]+$', dir_name):
                    self.errors.append(f'DHF directory naming violation: DHF/{dir_name}')
        
        return len(self.errors) == 0
    
    def validate_template_completeness(self) -> bool:
        """Validate that documents have required metadata."""
        print("Validating template completeness...")
        initial_error_count = len(self.errors)
        
        # Check all markdown files in specified paths for required metadata
        for path in self.paths:
            if not os.path.exists(path):
                continue
                
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.endswith('.md'):
                        file_path = os.path.join(root, file)
                        # Skip sample files and README files
                        if 'sample' in file_path.lower() or 'readme' in file_path.lower():
                            continue
                            
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                
                            if content.startswith('---'):
                                end_marker = content.find('---', 3)
                                if end_marker != -1:
                                    frontmatter = content[3:end_marker]
                                    try:
                                        metadata = yaml.safe_load(frontmatter)
                                        if metadata:
                                            for field, field_type in self.required_fields.items():
                                                if field not in metadata:
                                                    self.errors.append(f'{file_path}: Missing required field "{field}"')
                                                elif not isinstance(metadata[field], field_type):
                                                    self.errors.append(f'{file_path}: Field "{field}" has wrong type')
                                    except yaml.YAMLError as e:
                                        self.errors.append(f'{file_path}: Invalid YAML in frontmatter: {e}')
                                else:
                                    self.errors.append(f'{file_path}: Incomplete YAML frontmatter')
                            else:
                                self.errors.append(f'{file_path}: Missing YAML frontmatter')
                                
                        except Exception as e:
                            self.errors.append(f'{file_path}: Error reading file: {e}')
        
        return len(self.errors) == initial_error_count
    
    def validate_regulatory_mapping(self) -> bool:
        """Validate that regulatory mappings use valid standards."""
        print("Validating regulatory mapping...")
        initial_error_count = len(self.errors)
        
        for path in self.paths:
            if not os.path.exists(path):
                continue
                
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.endswith('.md'):
                        file_path = os.path.join(root, file)
                        # Skip sample files and README files
                        if 'sample' in file_path.lower() or 'readme' in file_path.lower():
                            continue
                            
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
                                                if mapping not in self.valid_regulations:
                                                    self.errors.append(f'{file_path}: Invalid regulatory mapping "{mapping}"')
                                    except yaml.YAMLError:
                                        pass  # Already handled in template validation
                        except Exception:
                            pass  # Already handled in template validation
        
        return len(self.errors) == initial_error_count
    
    def check_document_relationships(self) -> bool:
        """Check document relationships and identify potential orphans."""
        print("Checking document relationships...")
        
        # Find all markdown documents
        all_docs = []
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.md') and not file.startswith('README'):
                    all_docs.append(os.path.join(root, file))
        
        # Find all referenced documents
        referenced_docs = set()
        for doc_path in all_docs:
            try:
                with open(doc_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Find markdown links and references
                    links = re.findall(r'\[.*?\]\((.*?\.md)\)', content)
                    for link in links:
                        # Resolve relative paths
                        if not link.startswith('/'):
                            link = os.path.normpath(os.path.join(os.path.dirname(doc_path), link))
                        referenced_docs.add(link)
            except Exception:
                continue
        
        # Report potential orphans (warnings, not errors)
        for doc in all_docs:
            if doc not in referenced_docs and any(path in doc for path in self.paths):
                self.warnings.append(f'Potentially orphaned document: {doc}')
        
        return True  # This check never fails, only warns
    
    def run_all_validations(self) -> bool:
        """Run all validation checks."""
        print("🔍 Running eQMS document validation...\n")
        
        validations = [
            self.validate_naming_conventions,
            self.validate_template_completeness,
            self.validate_regulatory_mapping,
            self.check_document_relationships
        ]
        
        success = True
        for validation in validations:
            try:
                if not validation():
                    success = False
            except Exception as e:
                self.errors.append(f"Validation error: {str(e)}")
                success = False
            print()
        
        return success
    
    def print_results(self):
        """Print validation results."""
        if self.errors:
            print("❌ Validation errors found:")
            for error in self.errors:
                print(f"  - {error}")
            print()
        
        if self.warnings:
            print("⚠️  Validation warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")
            print()
        
        if not self.errors and not self.warnings:
            print("✅ All validations passed successfully!")
        elif not self.errors:
            print("✅ All validations passed with warnings noted above")
        else:
            print("❌ Validation failed - please fix errors above")
        
        print(f"\n📊 Results: {len(self.errors)} errors, {len(self.warnings)} warnings")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Validate eQMS documents for FDA 21 CFR 820 and ISO 13485 compliance'
    )
    parser.add_argument(
        '--check', 
        action='store_true', 
        default=True,
        help='Run all validation checks (default)'
    )
    parser.add_argument(
        '--paths',
        type=str,
        default='docs,QMS,DHF,RMF',
        help='Comma-separated list of paths to validate'
    )
    
    args = parser.parse_args()
    paths = [p.strip() for p in args.paths.split(',')]
    
    validator = DocumentValidator(paths)
    success = validator.run_all_validations()
    validator.print_results()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())