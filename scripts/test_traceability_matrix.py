#!/usr/bin/env python3
"""
Unit tests for traceability-matrix.py
"""

import unittest
from unittest.mock import Mock, patch
import json
from datetime import datetime

# Import the classes we want to test
import sys
import os
sys.path.append(os.path.dirname(__file__))

import importlib.util
spec = importlib.util.spec_from_file_location("traceability_matrix", os.path.join(os.path.dirname(__file__), "traceability-matrix.py"))
traceability_matrix = importlib.util.module_from_spec(spec)
spec.loader.exec_module(traceability_matrix)

TraceabilityItem = traceability_matrix.TraceabilityItem
TraceabilityParser = traceability_matrix.TraceabilityParser
TraceabilityMatrix = traceability_matrix.TraceabilityMatrix


class TestTraceabilityParser(unittest.TestCase):
    
    def setUp(self):
        self.parser = TraceabilityParser()
    
    def test_extract_item_type_requirement(self):
        labels = ['requirement', 'design-input']
        result = self.parser.extract_item_type(labels)
        self.assertEqual(result, 'requirement')
    
    def test_extract_item_type_design(self):
        labels = ['design', 'specification']
        result = self.parser.extract_item_type(labels)
        self.assertEqual(result, 'design')
    
    def test_extract_item_type_verification(self):
        labels = ['verification', 'test']
        result = self.parser.extract_item_type(labels)
        self.assertEqual(result, 'verification')
    
    def test_extract_item_type_risk(self):
        labels = ['risk', 'iso-14971']
        result = self.parser.extract_item_type(labels)
        self.assertEqual(result, 'risk')
    
    def test_extract_item_type_other(self):
        labels = ['documentation', 'misc']
        result = self.parser.extract_item_type(labels)
        self.assertEqual(result, 'other')
    
    def test_extract_references_issue_format(self):
        text = "This requirement relates to issue #123 and also addresses #456"
        result = self.parser.extract_references(text)
        self.assertIn('#123', result)
        self.assertIn('#456', result)
    
    def test_extract_references_closes_format(self):
        text = "This PR closes #789 and fixes #101"
        result = self.parser.extract_references(text)
        self.assertIn('#789', result)
        self.assertIn('#101', result)
    
    def test_extract_references_requirement_format(self):
        text = "Related to requirement: #42"
        result = self.parser.extract_references(text)
        self.assertIn('#42', result)
    
    def test_parse_issues(self):
        mock_issues = [
            {
                'number': 1,
                'title': 'User requirement for authentication',
                'body': 'As a user, I want to log in securely. Related to #2',
                'labels': [{'name': 'requirement'}, {'name': 'design-input'}],
                'state': 'open',
                'created_at': '2023-01-01T00:00:00Z',
                'updated_at': '2023-01-01T00:00:00Z',
                'user': {'login': 'testuser'},
                'assignee': None,
                'html_url': 'https://github.com/test/repo/issues/1'
            }
        ]
        
        result = self.parser.parse_issues(mock_issues)
        
        self.assertEqual(len(result), 1)
        item = result[0]
        self.assertEqual(item.id, '#1')
        self.assertEqual(item.type, 'requirement')
        self.assertEqual(item.title, 'User requirement for authentication')
        self.assertIn('#2', item.linked_items)


class TestTraceabilityMatrix(unittest.TestCase):
    
    def setUp(self):
        # Create sample traceability items
        self.items = [
            TraceabilityItem(
                id='#1',
                type='requirement',
                title='User authentication requirement',
                description='Users must be able to authenticate',
                labels=['requirement', 'security'],
                status='open',
                created_date='2023-01-01T00:00:00Z',
                updated_date='2023-01-01T00:00:00Z',
                author='testuser',
                assignee=None,
                url='https://github.com/test/repo/issues/1',
                linked_items=[]
            ),
            TraceabilityItem(
                id='PR#2',
                type='design',
                title='Implement authentication system',
                description='Implementation of user authentication. Closes #1',
                labels=[],
                status='merged',
                created_date='2023-01-02T00:00:00Z',
                updated_date='2023-01-02T00:00:00Z',
                author='developer',
                assignee=None,
                url='https://github.com/test/repo/pull/2',
                linked_items=['#1']
            ),
            TraceabilityItem(
                id='#3',
                type='verification',
                title='Test authentication functionality',
                description='Verify that authentication works. Tests for #1',
                labels=['verification', 'test'],
                status='closed',
                created_date='2023-01-03T00:00:00Z',
                updated_date='2023-01-03T00:00:00Z',
                author='tester',
                assignee=None,
                url='https://github.com/test/repo/issues/3',
                linked_items=['#1']
            )
        ]
        
        self.matrix = TraceabilityMatrix(self.items)
    
    def test_build_matrix_structure(self):
        result = self.matrix.build_matrix()
        
        # Check basic structure
        self.assertIn('metadata', result)
        self.assertIn('items', result)
        self.assertIn('relationships', result)
        self.assertIn('coverage_analysis', result)
        
        # Check metadata
        self.assertEqual(result['metadata']['total_items'], 3)
        self.assertIn('items_by_type', result['metadata'])
        
        # Check items
        self.assertEqual(len(result['items']), 3)
        
        # Check relationships
        self.assertTrue(len(result['relationships']) >= 2)  # PR#2 -> #1, #3 -> #1
    
    def test_coverage_analysis(self):
        matrix_data = self.matrix.build_matrix()
        coverage = matrix_data['coverage_analysis']
        
        # Should have requirements with design (PR#2 references #1)
        self.assertEqual(coverage['requirements_with_design'], 1)
        
        # Should have requirements with verification (#3 references #1)
        self.assertEqual(coverage['requirements_with_verification'], 1)
        
        # Coverage percentage should be 100% (1 requirement, 1 has design)
        self.assertEqual(coverage['coverage_percentage'], 100.0)
    
    def test_items_by_id_mapping(self):
        # Test that items are properly mapped by ID
        self.assertIn('#1', self.matrix.items_by_id)
        self.assertIn('PR#2', self.matrix.items_by_id)
        self.assertIn('#3', self.matrix.items_by_id)
        
        item1 = self.matrix.items_by_id['#1']
        self.assertEqual(item1.type, 'requirement')
        self.assertEqual(item1.title, 'User authentication requirement')


class TestIntegration(unittest.TestCase):
    """Integration tests that test the complete workflow"""
    
    @patch('requests.get')
    def test_full_workflow_simulation(self, mock_get):
        """Test a complete workflow with mocked GitHub API responses"""
        
        # Mock GitHub API responses
        mock_issues_response = Mock()
        mock_issues_response.json.return_value = [
            {
                'number': 1,
                'title': 'Authentication requirement',
                'body': 'Users need secure login functionality',
                'labels': [{'name': 'requirement'}],
                'state': 'open',
                'created_at': '2023-01-01T00:00:00Z',
                'updated_at': '2023-01-01T00:00:00Z',
                'user': {'login': 'product_manager'},
                'assignee': None,
                'html_url': 'https://github.com/test/repo/issues/1'
            }
        ]
        mock_issues_response.raise_for_status.return_value = None
        
        mock_prs_response = Mock()
        mock_prs_response.json.return_value = [
            {
                'number': 10,
                'title': 'Implement OAuth authentication - closes #1',
                'body': 'Implementation of OAuth2 authentication system. Closes #1',
                'state': 'merged',
                'created_at': '2023-01-02T00:00:00Z',
                'updated_at': '2023-01-02T00:00:00Z',
                'user': {'login': 'developer'},
                'assignee': None,
                'html_url': 'https://github.com/test/repo/pull/10'
            }
        ]
        mock_prs_response.raise_for_status.return_value = None
        
        # Set up mock to return empty list on second call (pagination end)
        mock_get.side_effect = [
            mock_issues_response,  # First issues call
            Mock(json=lambda: [], raise_for_status=lambda: None),  # Second issues call (empty)
            mock_prs_response,     # First PRs call
            Mock(json=lambda: [], raise_for_status=lambda: None)   # Second PRs call (empty)
        ]
        
        # Test the workflow
        GitHubAPI = traceability_matrix.GitHubAPI
        
        api = GitHubAPI('fake-token', 'test/repo')
        issues = api.get_issues()
        prs = api.get_pull_requests()
        
        parser = TraceabilityParser()
        issue_items = parser.parse_issues(issues)
        pr_items = parser.parse_pull_requests(prs)
        
        all_items = issue_items + pr_items
        matrix = TraceabilityMatrix(all_items)
        matrix_data = matrix.build_matrix()
        
        # Verify results
        self.assertEqual(len(all_items), 2)
        self.assertEqual(matrix_data['metadata']['total_items'], 2)
        self.assertTrue(len(matrix_data['relationships']) > 0)
        
        # Check that the PR references the issue
        relationships = matrix_data['relationships']
        pr_to_issue_rel = next((r for r in relationships if r['from_id'] == 'PR#10' and r['to_id'] == '#1'), None)
        self.assertIsNotNone(pr_to_issue_rel)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)