#!/usr/bin/env python3
"""
Compliance Validator for eQMS GitHub Repository
Validates document relationships and compliance requirements before merge.
"""

import os
import sys
import json
import yaml
import requests
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional


class ComplianceValidator:
    def __init__(self):
        self.github_token = os.environ.get('GITHUB_TOKEN')
        self.pr_number = os.environ.get('PR_NUMBER')
        self.repository = os.environ.get('REPOSITORY')
        self.errors = []
        self.warnings = []
        
        if not all([self.github_token, self.pr_number, self.repository]):
            raise ValueError("Required environment variables not set")
            
        self.headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
    def validate_document_presence(self, changed_files: List[str]) -> bool:
        """Verify all required documents are present for regulatory compliance."""
        errors_found = False
        
        # Required document structure based on architecture.md
        required_docs = {
            'docs/design-controls/requirements/': 'Design input requirements',
            'docs/design-controls/specifications/': 'Design output specifications', 
            'docs/design-controls/verification/': 'Design verification protocols',
            'docs/design-controls/validation/': 'Design validation protocols',
            'docs/design-controls/risk-management/': 'Risk management files',
            'docs/quality-system/document-control/': 'Document control procedures',
            'docs/device-master-record/': 'Device master record files'
        }
        
        # Check if any design control files are being modified
        design_files = [f for f in changed_files if f.startswith('docs/design-controls/')]
        if design_files:
            # If design files are modified, ensure related compliance docs exist
            for req_path, description in required_docs.items():
                if not any(f.startswith(req_path) for f in self._get_all_repo_files()):
                    self.errors.append(f"Missing required {description} in {req_path}")
                    errors_found = True
                    
        return not errors_found
        
    def validate_approval_status(self) -> bool:
        """Check if PR has required approvals per CODEOWNERS."""
        errors_found = False
        
        # Get PR reviews
        reviews_url = f"https://api.github.com/repos/{self.repository}/pulls/{self.pr_number}/reviews"
        response = requests.get(reviews_url, headers=self.headers)
        
        if response.status_code != 200:
            self.errors.append(f"Failed to fetch PR reviews: {response.status_code}")
            return False
            
        reviews = response.json()
        approved_reviews = [r for r in reviews if r['state'] == 'APPROVED']
        
        # Get required reviewers from CODEOWNERS
        required_reviewers = self._get_required_reviewers()
        
        if not required_reviewers:
            self.warnings.append("No CODEOWNERS file found or no reviewers required")
            return True
            
        # Check if all required reviewers have approved
        approved_users = {r['user']['login'] for r in approved_reviews}
        
        for required_reviewer in required_reviewers:
            # Strip @ prefix if present
            reviewer = required_reviewer.lstrip('@')
            if reviewer not in approved_users:
                self.errors.append(f"Missing approval from required reviewer: {reviewer}")
                errors_found = True
                
        return not errors_found
        
    def validate_document_relationships(self, changed_files: List[str]) -> bool:
        """Validate that document relationships are properly maintained."""
        errors_found = False
        
        # Check for orphaned documents
        design_control_files = [f for f in changed_files if f.startswith('docs/design-controls/')]
        
        for file_path in design_control_files:
            # Check if requirements have corresponding specifications
            if 'requirements/' in file_path:
                req_name = Path(file_path).stem
                spec_path = f"docs/design-controls/specifications/{req_name}"
                if not self._file_exists_in_repo(spec_path + '.md'):
                    self.warnings.append(f"Requirement {req_name} missing corresponding specification")
                    
            # Check if specifications have verification protocols
            elif 'specifications/' in file_path:
                spec_name = Path(file_path).stem
                verif_path = f"docs/design-controls/verification/{spec_name}"
                if not self._file_exists_in_repo(verif_path + '.md'):
                    self.warnings.append(f"Specification {spec_name} missing verification protocol")
                    
        # Check for proper risk management linkage
        risk_files = [f for f in changed_files if 'risk-management/' in f]
        if risk_files:
            # Ensure risks are linked to mitigation designs
            for risk_file in risk_files:
                risk_name = Path(risk_file).stem
                if not self._check_risk_mitigation_linkage(risk_name):
                    self.warnings.append(f"Risk {risk_name} may be missing mitigation documentation")
                    
        return not errors_found
        
    def validate_template_compliance(self, changed_files: List[str]) -> bool:
        """Ensure documents follow required templates."""
        errors_found = False
        
        for file_path in changed_files:
            if file_path.endswith('.md'):
                file_content = self._get_file_content(file_path)
                if file_content is None:
                    continue
                    
                # Check for required metadata in design control documents
                if 'docs/design-controls/' in file_path:
                    if not self._has_required_metadata(file_content):
                        self.errors.append(f"Document {file_path} missing required metadata headers")
                        errors_found = True
                        
                # Check for specific template compliance
                if 'requirements/' in file_path:
                    if not self._validate_requirement_template(file_content):
                        self.errors.append(f"Requirement document {file_path} doesn't follow template")
                        errors_found = True
                        
        return not errors_found
        
    def _get_changed_files(self) -> List[str]:
        """Get list of files changed in the PR."""
        files_url = f"https://api.github.com/repos/{self.repository}/pulls/{self.pr_number}/files"
        response = requests.get(files_url, headers=self.headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch PR files: {response.status_code}")
            
        files_data = response.json()
        return [f['filename'] for f in files_data]
        
    def _get_all_repo_files(self) -> List[str]:
        """Get all files in the repository."""
        # This is a simplified implementation - in reality you'd need to handle pagination
        tree_url = f"https://api.github.com/repos/{self.repository}/git/trees/main?recursive=1"
        response = requests.get(tree_url, headers=self.headers)
        
        if response.status_code != 200:
            return []
            
        tree_data = response.json()
        return [item['path'] for item in tree_data.get('tree', []) if item['type'] == 'blob']
        
    def _get_required_reviewers(self) -> List[str]:
        """Extract required reviewers from CODEOWNERS file."""
        try:
            codeowners_content = self._get_file_content('.github/CODEOWNERS')
            if not codeowners_content:
                return []
                
            reviewers = []
            for line in codeowners_content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split()
                    if len(parts) > 1:
                        # Extract reviewers (everything after the path pattern)
                        reviewers.extend(parts[1:])
                        
            return reviewers
        except:
            return []
            
    def _file_exists_in_repo(self, file_path: str) -> bool:
        """Check if a file exists in the repository."""
        file_url = f"https://api.github.com/repos/{self.repository}/contents/{file_path}"
        response = requests.get(file_url, headers=self.headers)
        return response.status_code == 200
        
    def _get_file_content(self, file_path: str) -> Optional[str]:
        """Get content of a file from the repository."""
        file_url = f"https://api.github.com/repos/{self.repository}/contents/{file_path}"
        response = requests.get(file_url, headers=self.headers)
        
        if response.status_code != 200:
            return None
            
        file_data = response.json()
        if file_data.get('encoding') == 'base64':
            import base64
            return base64.b64decode(file_data['content']).decode('utf-8')
            
        return file_data.get('content', '')
        
    def _has_required_metadata(self, content: str) -> bool:
        """Check if document has required metadata headers."""
        required_fields = ['title', 'version', 'author', 'date']
        
        # Check for YAML frontmatter
        if content.startswith('---'):
            try:
                end_index = content.find('---', 3)
                if end_index > 0:
                    frontmatter = content[3:end_index]
                    metadata = yaml.safe_load(frontmatter)
                    return all(field in metadata for field in required_fields)
            except:
                pass
                
        # Check for markdown headers
        lines = content.split('\n')[:10]  # Check first 10 lines
        found_fields = set()
        for line in lines:
            for field in required_fields:
                if line.lower().startswith(f'**{field}'):
                    found_fields.add(field)
                    
        return len(found_fields) >= len(required_fields) // 2  # At least half required
        
    def _validate_requirement_template(self, content: str) -> bool:
        """Validate requirement document follows proper template."""
        required_sections = ['user need', 'intended use', 'acceptance criteria']
        content_lower = content.lower()
        
        found_sections = sum(1 for section in required_sections 
                           if section in content_lower)
        
        return found_sections >= 2  # At least 2 of 3 required sections
        
    def _check_risk_mitigation_linkage(self, risk_name: str) -> bool:
        """Check if risk has corresponding mitigation documentation."""
        # This is a simplified check - in practice you'd check for actual links
        mitigation_paths = [
            f"docs/design-controls/specifications/{risk_name}_mitigation.md",
            f"docs/design-controls/verification/{risk_name}_test.md"
        ]
        
        return any(self._file_exists_in_repo(path) for path in mitigation_paths)
        
    def run_validation(self) -> bool:
        """Run all compliance validations."""
        print("🔍 Starting compliance validation...")
        
        try:
            changed_files = self._get_changed_files()
            print(f"📄 Checking {len(changed_files)} changed files")
            
            # Run all validations
            validations = [
                ("Document Presence", self.validate_document_presence(changed_files)),
                ("Approval Status", self.validate_approval_status()),
                ("Document Relationships", self.validate_document_relationships(changed_files)),
                ("Template Compliance", self.validate_template_compliance(changed_files))
            ]
            
            all_passed = True
            for name, passed in validations:
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"{status} {name}")
                if not passed:
                    all_passed = False
                    
            # Write errors to file for GitHub Actions
            if self.errors or self.warnings:
                with open('compliance-errors.txt', 'w') as f:
                    if self.errors:
                        f.write("### ❌ Errors (Must Fix):\n")
                        for error in self.errors:
                            f.write(f"- {error}\n")
                        f.write("\n")
                        
                    if self.warnings:
                        f.write("### ⚠️ Warnings (Recommended):\n")
                        for warning in self.warnings:
                            f.write(f"- {warning}\n")
                            
            if all_passed:
                print("✅ All compliance checks passed!")
            else:
                print("❌ Compliance validation failed!")
                
            return all_passed
            
        except Exception as e:
            print(f"❌ Compliance validation error: {str(e)}")
            with open('compliance-errors.txt', 'w') as f:
                f.write(f"### ❌ Validation Error:\n- {str(e)}\n")
            return False


if __name__ == "__main__":
    validator = ComplianceValidator()
    success = validator.run_validation()
    sys.exit(0 if success else 1)