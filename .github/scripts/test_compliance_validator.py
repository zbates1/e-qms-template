#!/usr/bin/env python3
"""
Unit tests for ComplianceValidator
"""

import unittest
import os
import tempfile
import json
from unittest.mock import patch, MagicMock, mock_open
from compliance_validator import ComplianceValidator


class TestComplianceValidator(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment."""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_token',
            'PR_NUMBER': '123',
            'REPOSITORY': 'test/repo'
        })
        self.env_patcher.start()
        
        self.validator = ComplianceValidator()
        
    def tearDown(self):
        """Clean up after tests."""
        self.env_patcher.stop()
        
    def test_init_with_missing_env_vars(self):
        """Test initialization fails with missing environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                ComplianceValidator()
                
    @patch('compliance_validator.requests.get')
    def test_validate_document_presence_success(self, mock_get):
        """Test document presence validation passes when required docs exist."""
        # Mock API response for repository tree
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'tree': [
                {'path': 'docs/design-controls/requirements/req1.md', 'type': 'blob'},
                {'path': 'docs/design-controls/specifications/spec1.md', 'type': 'blob'},
                {'path': 'docs/design-controls/verification/test1.md', 'type': 'blob'},
                {'path': 'docs/design-controls/validation/val1.md', 'type': 'blob'},
                {'path': 'docs/design-controls/risk-management/risk1.md', 'type': 'blob'},
                {'path': 'docs/quality-system/document-control/doc_control.md', 'type': 'blob'},
                {'path': 'docs/device-master-record/dmr1.md', 'type': 'blob'}
            ]
        }
        
        changed_files = ['docs/design-controls/requirements/req1.md']
        result = self.validator.validate_document_presence(changed_files)
        
        self.assertTrue(result)
        self.assertEqual(len(self.validator.errors), 0)
        
    @patch('compliance_validator.requests.get')
    def test_validate_document_presence_missing_docs(self, mock_get):
        """Test document presence validation fails when required docs are missing."""
        # Mock API response with missing required directories
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'tree': [
                {'path': 'docs/design-controls/requirements/req1.md', 'type': 'blob'}
            ]
        }
        
        changed_files = ['docs/design-controls/requirements/req1.md']
        result = self.validator.validate_document_presence(changed_files)
        
        self.assertFalse(result)
        self.assertGreater(len(self.validator.errors), 0)
        
    @patch('compliance_validator.requests.get')
    def test_validate_approval_status_success(self, mock_get):
        """Test approval status validation passes with required approvals."""
        # Mock PR reviews API response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {
                'state': 'APPROVED',
                'user': {'login': 'reviewer1'}
            },
            {
                'state': 'APPROVED', 
                'user': {'login': 'reviewer2'}
            }
        ]
        
        # Mock CODEOWNERS content
        with patch.object(self.validator, '_get_required_reviewers', return_value=['reviewer1', 'reviewer2']):
            result = self.validator.validate_approval_status()
            
        self.assertTrue(result)
        self.assertEqual(len(self.validator.errors), 0)
        
    @patch('compliance_validator.requests.get')
    def test_validate_approval_status_missing_approval(self, mock_get):
        """Test approval status validation fails with missing approvals."""
        # Mock PR reviews API response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {
                'state': 'APPROVED',
                'user': {'login': 'reviewer1'}
            }
        ]
        
        # Mock CODEOWNERS content requiring two reviewers
        with patch.object(self.validator, '_get_required_reviewers', return_value=['reviewer1', 'reviewer2']):
            result = self.validator.validate_approval_status()
            
        self.assertFalse(result)
        self.assertGreater(len(self.validator.errors), 0)
        self.assertIn('reviewer2', str(self.validator.errors))
        
    def test_validate_document_relationships_warnings(self):
        """Test document relationships validation generates appropriate warnings."""
        changed_files = [
            'docs/design-controls/requirements/req1.md',
            'docs/design-controls/specifications/spec1.md'
        ]
        
        # Mock file existence checks
        with patch.object(self.validator, '_file_exists_in_repo', return_value=False):
            result = self.validator.validate_document_relationships(changed_files)
            
        # Should return True but generate warnings
        self.assertTrue(result)
        self.assertGreater(len(self.validator.warnings), 0)
        
    def test_has_required_metadata_yaml_frontmatter(self):
        """Test metadata validation with YAML frontmatter."""
        content = """---
title: Test Document
version: 1.0
author: Test Author
date: 2023-01-01
---

# Test Document Content"""
        
        result = self.validator._has_required_metadata(content)
        self.assertTrue(result)
        
    def test_has_required_metadata_markdown_headers(self):
        """Test metadata validation with markdown headers."""
        content = """**Title**: Test Document
**Version**: 1.0
**Author**: Test Author
**Date**: 2023-01-01

# Test Document Content"""
        
        result = self.validator._has_required_metadata(content)
        self.assertTrue(result)
        
    def test_has_required_metadata_missing(self):
        """Test metadata validation fails when metadata is missing."""
        content = """# Test Document

Just some content without metadata."""
        
        result = self.validator._has_required_metadata(content)
        self.assertFalse(result)
        
    def test_validate_requirement_template_success(self):
        """Test requirement template validation passes with proper sections."""
        content = """# User Need
This describes the user need.

# Intended Use
This describes the intended use.

# Acceptance Criteria
- Criteria 1
- Criteria 2"""
        
        result = self.validator._validate_requirement_template(content)
        self.assertTrue(result)
        
    def test_validate_requirement_template_missing_sections(self):
        """Test requirement template validation fails with missing sections."""
        content = """# User Need
This describes the user need only."""
        
        result = self.validator._validate_requirement_template(content)
        self.assertFalse(result)
        
    @patch('compliance_validator.requests.get')
    def test_get_changed_files(self, mock_get):
        """Test getting changed files from PR."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {'filename': 'docs/test1.md'},
            {'filename': 'docs/test2.md'}
        ]
        
        files = self.validator._get_changed_files()
        
        self.assertEqual(files, ['docs/test1.md', 'docs/test2.md'])
        
    @patch('compliance_validator.requests.get')
    def test_get_changed_files_api_error(self, mock_get):
        """Test getting changed files handles API errors."""
        mock_get.return_value.status_code = 404
        
        with self.assertRaises(Exception):
            self.validator._get_changed_files()
            
    def test_get_required_reviewers_codeowners(self):
        """Test parsing CODEOWNERS file for required reviewers."""
        codeowners_content = """# CODEOWNERS file
docs/design-controls/ @reviewer1 @reviewer2
docs/quality-system/ @reviewer3
*.md @reviewer4"""
        
        with patch.object(self.validator, '_get_file_content', return_value=codeowners_content):
            reviewers = self.validator._get_required_reviewers()
            
        self.assertIn('@reviewer1', reviewers)
        self.assertIn('@reviewer2', reviewers)
        self.assertIn('@reviewer3', reviewers)
        self.assertIn('@reviewer4', reviewers)
        
    def test_get_required_reviewers_no_file(self):
        """Test handling missing CODEOWNERS file."""
        with patch.object(self.validator, '_get_file_content', return_value=None):
            reviewers = self.validator._get_required_reviewers()
            
        self.assertEqual(reviewers, [])
        
    @patch('compliance_validator.requests.get')
    def test_file_exists_in_repo_true(self, mock_get):
        """Test file existence check returns True when file exists."""
        mock_get.return_value.status_code = 200
        
        result = self.validator._file_exists_in_repo('test/file.md')
        
        self.assertTrue(result)
        
    @patch('compliance_validator.requests.get')
    def test_file_exists_in_repo_false(self, mock_get):
        """Test file existence check returns False when file doesn't exist."""
        mock_get.return_value.status_code = 404
        
        result = self.validator._file_exists_in_repo('test/nonexistent.md')
        
        self.assertFalse(result)


class TestComplianceValidatorIntegration(unittest.TestCase):
    """Integration tests for the complete compliance validation workflow."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.env_patcher = patch.dict(os.environ, {
            'GITHUB_TOKEN': 'test_token',
            'PR_NUMBER': '123',
            'REPOSITORY': 'test/repo'
        })
        self.env_patcher.start()
        
    def tearDown(self):
        """Clean up after integration tests."""
        self.env_patcher.stop()
        
    @patch('compliance_validator.requests.get')
    @patch('builtins.open', new_callable=mock_open)
    def test_run_validation_success(self, mock_file, mock_get):
        """Test complete validation workflow succeeds."""
        validator = ComplianceValidator()
        
        # Mock all API calls to return success
        mock_responses = [
            # Changed files
            MagicMock(status_code=200, json=lambda: [{'filename': 'docs/test.md'}]),
            # Repository tree
            MagicMock(status_code=200, json=lambda: {'tree': [
                {'path': 'docs/design-controls/requirements/req1.md', 'type': 'blob'},
                {'path': 'docs/design-controls/specifications/spec1.md', 'type': 'blob'},
                {'path': 'docs/design-controls/verification/test1.md', 'type': 'blob'},
                {'path': 'docs/design-controls/validation/val1.md', 'type': 'blob'},
                {'path': 'docs/design-controls/risk-management/risk1.md', 'type': 'blob'},
                {'path': 'docs/quality-system/document-control/doc_control.md', 'type': 'blob'},
                {'path': 'docs/device-master-record/dmr1.md', 'type': 'blob'}
            ]}),
            # PR reviews
            MagicMock(status_code=200, json=lambda: [
                {'state': 'APPROVED', 'user': {'login': 'reviewer1'}}
            ]),
            # File content calls
            MagicMock(status_code=200, json=lambda: {
                'encoding': 'base64',
                'content': 'VGVzdCBjb250ZW50'  # base64 encoded "Test content"
            })
        ]
        mock_get.side_effect = mock_responses * 10  # Repeat for multiple calls
        
        # Mock CODEOWNERS parsing
        with patch.object(validator, '_get_required_reviewers', return_value=['reviewer1']):
            result = validator.run_validation()
            
        self.assertTrue(result)
        
    @patch('compliance_validator.requests.get')
    @patch('builtins.open', new_callable=mock_open)
    def test_run_validation_failure(self, mock_file, mock_get):
        """Test complete validation workflow fails appropriately."""
        validator = ComplianceValidator()
        
        # Mock API calls to simulate failures
        mock_responses = [
            # Changed files
            MagicMock(status_code=200, json=lambda: [{'filename': 'docs/design-controls/requirements/req1.md'}]),
            # Repository tree (missing required docs)
            MagicMock(status_code=200, json=lambda: {'tree': [
                {'path': 'docs/design-controls/requirements/req1.md', 'type': 'blob'}
            ]}),
            # PR reviews (no approvals)
            MagicMock(status_code=200, json=lambda: []),
        ]
        mock_get.side_effect = mock_responses * 10
        
        # Mock CODEOWNERS requiring reviewer
        with patch.object(validator, '_get_required_reviewers', return_value=['reviewer1']):
            result = validator.run_validation()
            
        self.assertFalse(result)
        # Verify error file was written
        mock_file.assert_called_with('compliance-errors.txt', 'w')


if __name__ == '__main__':
    unittest.main()