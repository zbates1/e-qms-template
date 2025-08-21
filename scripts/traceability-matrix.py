#!/usr/bin/env python3
"""
Traceability Matrix Generator for GitHub-based eQMS
Parses GitHub Issues and PRs to generate regulatory traceability reports.
"""

import argparse
import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

import requests
import pandas as pd
from jinja2 import Template


@dataclass
class TraceabilityItem:
    """Represents a traceable item (requirement, design, test, risk)"""
    id: str
    type: str  # requirement, design, verification, validation, risk
    title: str
    description: str
    labels: List[str]
    status: str
    created_date: str
    updated_date: str
    author: str
    assignee: Optional[str]
    url: str
    linked_items: List[str]  # IDs of linked items


class GitHubAPI:
    """GitHub API client for fetching issues and PRs"""
    
    def __init__(self, token: str, repo: str):
        self.token = token
        self.repo = repo
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = f'https://api.github.com/repos/{repo}'
        
    def get_issues(self, state: str = 'all') -> List[Dict[str, Any]]:
        """Fetch all issues from the repository"""
        issues = []
        page = 1
        
        while True:
            url = f'{self.base_url}/issues'
            params = {
                'state': state,
                'per_page': 100,
                'page': page,
                'sort': 'created',
                'direction': 'asc'
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            page_issues = response.json()
            if not page_issues:
                break
                
            # Filter out pull requests (they appear as issues in the API)
            actual_issues = [issue for issue in page_issues if 'pull_request' not in issue]
            issues.extend(actual_issues)
            
            page += 1
            
        return issues
    
    def get_pull_requests(self, state: str = 'all') -> List[Dict[str, Any]]:
        """Fetch all pull requests from the repository"""
        prs = []
        page = 1
        
        while True:
            url = f'{self.base_url}/pulls'
            params = {
                'state': state,
                'per_page': 100,
                'page': page,
                'sort': 'created',
                'direction': 'asc'
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            page_prs = response.json()
            if not page_prs:
                break
                
            prs.extend(page_prs)
            page += 1
            
        return prs


class TraceabilityParser:
    """Parses GitHub data to extract traceability relationships"""
    
    def __init__(self):
        # Patterns for extracting references from text
        self.issue_ref_pattern = re.compile(r'#(\d+)|(?:issues?|requirements?|reqs?)[:\s]+#?(\d+)', re.IGNORECASE)
        self.pr_ref_pattern = re.compile(r'(?:pr|pull request)[:\s]+#?(\d+)', re.IGNORECASE)
        self.closes_pattern = re.compile(r'(?:closes?|fixes?|resolves?)[:\s]+#?(\d+)', re.IGNORECASE)
        
    def extract_item_type(self, labels: List[str]) -> str:
        """Determine item type from labels"""
        label_names = [label.lower() for label in labels]
        
        if any(label in label_names for label in ['requirement', 'design-input', 'user-need']):
            return 'requirement'
        elif any(label in label_names for label in ['design', 'specification', 'design-output']):
            return 'design'
        elif any(label in label_names for label in ['verification', 'test', 'testing']):
            return 'verification'
        elif any(label in label_names for label in ['validation', 'clinical', 'user-validation']):
            return 'validation'
        elif any(label in label_names for label in ['risk', 'iso-14971', 'hazard']):
            return 'risk'
        else:
            return 'other'
    
    def extract_references(self, text: str) -> List[str]:
        """Extract issue/PR references from text"""
        if not text:
            return []
            
        references = []
        
        # Find issue references
        for match in self.issue_ref_pattern.finditer(text):
            ref_id = match.group(1) or match.group(2)
            if ref_id:
                references.append(f'#{ref_id}')
        
        # Find closes/fixes references
        for match in self.closes_pattern.finditer(text):
            ref_id = match.group(1)
            if ref_id:
                references.append(f'#{ref_id}')
                
        return list(set(references))  # Remove duplicates
    
    def parse_issues(self, issues: List[Dict[str, Any]]) -> List[TraceabilityItem]:
        """Parse GitHub issues into traceability items"""
        items = []
        
        for issue in issues:
            labels = [label['name'] for label in issue.get('labels', [])]
            item_type = self.extract_item_type(labels)
            
            # Extract references from body and comments
            body_refs = self.extract_references(issue.get('body', ''))
            
            item = TraceabilityItem(
                id=f"#{issue['number']}",
                type=item_type,
                title=issue['title'],
                description=issue.get('body', '')[:500] + '...' if len(issue.get('body', '')) > 500 else issue.get('body', ''),
                labels=labels,
                status=issue['state'],
                created_date=issue['created_at'],
                updated_date=issue['updated_at'],
                author=issue['user']['login'],
                assignee=issue['assignee']['login'] if issue.get('assignee') else None,
                url=issue['html_url'],
                linked_items=body_refs
            )
            items.append(item)
            
        return items
    
    def parse_pull_requests(self, prs: List[Dict[str, Any]]) -> List[TraceabilityItem]:
        """Parse GitHub pull requests into traceability items"""
        items = []
        
        for pr in prs:
            # Extract references from title and body
            title_refs = self.extract_references(pr['title'])
            body_refs = self.extract_references(pr.get('body', ''))
            all_refs = list(set(title_refs + body_refs))
            
            item = TraceabilityItem(
                id=f"PR#{pr['number']}",
                type='design',
                title=pr['title'],
                description=pr.get('body', '')[:500] + '...' if len(pr.get('body', '')) > 500 else pr.get('body', ''),
                labels=[],  # PRs don't have labels in the same way
                status=pr['state'],
                created_date=pr['created_at'],
                updated_date=pr['updated_at'],
                author=pr['user']['login'],
                assignee=pr['assignee']['login'] if pr.get('assignee') else None,
                url=pr['html_url'],
                linked_items=all_refs
            )
            items.append(item)
            
        return items


class TraceabilityMatrix:
    """Generates traceability matrix and reports"""
    
    def __init__(self, items: List[TraceabilityItem]):
        self.items = items
        self.items_by_id = {item.id: item for item in items}
        
    def build_matrix(self) -> Dict[str, Any]:
        """Build the traceability matrix structure"""
        matrix = {
            'metadata': {
                'generated_date': datetime.now().isoformat(),
                'total_items': len(self.items),
                'items_by_type': {}
            },
            'items': [asdict(item) for item in self.items],
            'relationships': [],
            'coverage_analysis': {}
        }
        
        # Count items by type
        for item in self.items:
            item_type = item.type
            matrix['metadata']['items_by_type'][item_type] = matrix['metadata']['items_by_type'].get(item_type, 0) + 1
        
        # Build relationships
        for item in self.items:
            for linked_id in item.linked_items:
                if linked_id in self.items_by_id:
                    relationship = {
                        'from_id': item.id,
                        'from_type': item.type,
                        'to_id': linked_id,
                        'to_type': self.items_by_id[linked_id].type,
                        'relationship_type': 'references'
                    }
                    matrix['relationships'].append(relationship)
        
        # Analyze coverage
        matrix['coverage_analysis'] = self._analyze_coverage()
        
        return matrix
    
    def _analyze_coverage(self) -> Dict[str, Any]:
        """Analyze traceability coverage and gaps"""
        analysis = {
            'requirements_with_design': 0,
            'requirements_with_verification': 0,
            'requirements_with_validation': 0,
            'designs_with_verification': 0,
            'risks_with_mitigation': 0,
            'orphaned_items': [],
            'coverage_percentage': 0.0
        }
        
        requirements = [item for item in self.items if item.type == 'requirement']
        designs = [item for item in self.items if item.type == 'design']
        verifications = [item for item in self.items if item.type == 'verification']
        validations = [item for item in self.items if item.type == 'validation']
        risks = [item for item in self.items if item.type == 'risk']
        
        # Check requirement coverage
        for req in requirements:
            has_design = any(req.id in item.linked_items for item in designs)
            has_verification = any(req.id in item.linked_items for item in verifications)
            has_validation = any(req.id in item.linked_items for item in validations)
            
            if has_design:
                analysis['requirements_with_design'] += 1
            if has_verification:
                analysis['requirements_with_verification'] += 1
            if has_validation:
                analysis['requirements_with_validation'] += 1
                
            if not (has_design or has_verification or has_validation):
                analysis['orphaned_items'].append(req.id)
        
        # Calculate overall coverage percentage
        if requirements:
            covered_requirements = analysis['requirements_with_design']
            analysis['coverage_percentage'] = (covered_requirements / len(requirements)) * 100
        
        return analysis
    
    def export_to_excel(self, output_path: str):
        """Export traceability matrix to Excel format"""
        matrix = self.build_matrix()
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Items sheet
            items_df = pd.DataFrame(matrix['items'])
            items_df.to_excel(writer, sheet_name='Items', index=False)
            
            # Relationships sheet
            relationships_df = pd.DataFrame(matrix['relationships'])
            relationships_df.to_excel(writer, sheet_name='Relationships', index=False)
            
            # Coverage analysis sheet
            coverage_data = []
            for key, value in matrix['coverage_analysis'].items():
                if key != 'orphaned_items':
                    coverage_data.append({'Metric': key, 'Value': value})
            
            coverage_df = pd.DataFrame(coverage_data)
            coverage_df.to_excel(writer, sheet_name='Coverage Analysis', index=False)
    
    def export_to_pdf(self, output_path: str):
        """Export traceability matrix to PDF format"""
        matrix = self.build_matrix()
        
        # HTML template for PDF generation
        template_str = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Traceability Matrix Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { text-align: center; margin-bottom: 30px; }
                .section { margin-bottom: 30px; }
                .coverage-table, .items-table { width: 100%; border-collapse: collapse; }
                .coverage-table th, .coverage-table td, .items-table th, .items-table td {
                    border: 1px solid #ddd; padding: 8px; text-align: left;
                }
                .coverage-table th, .items-table th { background-color: #f2f2f2; }
                .orphaned { color: red; font-weight: bold; }
                .covered { color: green; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Traceability Matrix Report</h1>
                <p>Generated: {{ metadata.generated_date }}</p>
                <p>Total Items: {{ metadata.total_items }}</p>
            </div>
            
            <div class="section">
                <h2>Coverage Analysis</h2>
                <table class="coverage-table">
                    <tr><th>Metric</th><th>Value</th></tr>
                    {% for key, value in coverage_analysis.items() %}
                        {% if key != 'orphaned_items' %}
                        <tr><td>{{ key.replace('_', ' ').title() }}</td><td>{{ value }}</td></tr>
                        {% endif %}
                    {% endfor %}
                </table>
                
                {% if coverage_analysis.orphaned_items %}
                <h3 class="orphaned">Orphaned Items (No Traceability)</h3>
                <ul>
                    {% for item_id in coverage_analysis.orphaned_items %}
                    <li class="orphaned">{{ item_id }}</li>
                    {% endfor %}
                </ul>
                {% endif %}
            </div>
            
            <div class="section">
                <h2>Items Summary</h2>
                <table class="items-table">
                    <tr><th>ID</th><th>Type</th><th>Title</th><th>Status</th><th>Linked Items</th></tr>
                    {% for item in items %}
                    <tr>
                        <td>{{ item.id }}</td>
                        <td>{{ item.type }}</td>
                        <td>{{ item.title[:50] }}{% if item.title|length > 50 %}...{% endif %}</td>
                        <td>{{ item.status }}</td>
                        <td>{{ item.linked_items|join(', ') }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
        </body>
        </html>
        """
        
        template = Template(template_str)
        html_content = template.render(**matrix)
        
        # Write HTML to file first
        html_path = output_path.replace('.pdf', '.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        try:
            import weasyprint
            weasyprint.HTML(string=html_content).write_pdf(output_path)
            # Clean up HTML file
            os.remove(html_path)
        except ImportError:
            logging.warning("WeasyPrint not available. HTML file saved instead of PDF.")
            logging.info(f"HTML report saved to: {html_path}")


def main():
    parser = argparse.ArgumentParser(description='Generate traceability matrix from GitHub repository')
    parser.add_argument('--repo', required=True, help='GitHub repository (owner/repo)')
    parser.add_argument('--token', required=True, help='GitHub API token')
    parser.add_argument('--output-dir', required=True, help='Output directory for reports')
    parser.add_argument('--format', choices=['pdf', 'excel', 'both'], default='both', help='Export format')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        # Initialize GitHub API client
        github_api = GitHubAPI(args.token, args.repo)
        
        # Fetch data
        logging.info("Fetching issues from GitHub...")
        issues = github_api.get_issues()
        logging.info(f"Found {len(issues)} issues")
        
        logging.info("Fetching pull requests from GitHub...")
        prs = github_api.get_pull_requests()
        logging.info(f"Found {len(prs)} pull requests")
        
        # Parse data
        parser = TraceabilityParser()
        issue_items = parser.parse_issues(issues)
        pr_items = parser.parse_pull_requests(prs)
        
        all_items = issue_items + pr_items
        logging.info(f"Parsed {len(all_items)} total traceability items")
        
        # Generate matrix
        matrix = TraceabilityMatrix(all_items)
        matrix_data = matrix.build_matrix()
        
        # Save JSON data
        json_path = os.path.join(args.output_dir, 'traceability-matrix.json')
        with open(json_path, 'w') as f:
            json.dump(matrix_data, f, indent=2)
        logging.info(f"Traceability matrix saved to: {json_path}")
        
        # Export in requested formats
        if args.format in ['excel', 'both']:
            excel_path = os.path.join(args.output_dir, 'traceability-matrix.xlsx')
            matrix.export_to_excel(excel_path)
            logging.info(f"Excel report saved to: {excel_path}")
        
        if args.format in ['pdf', 'both']:
            pdf_path = os.path.join(args.output_dir, 'traceability-matrix.pdf')
            matrix.export_to_pdf(pdf_path)
            logging.info(f"PDF report saved to: {pdf_path}")
        
        # Print coverage summary
        coverage = matrix_data['coverage_analysis']
        logging.info(f"Coverage Summary:")
        logging.info(f"  Requirements with design: {coverage['requirements_with_design']}")
        logging.info(f"  Requirements with verification: {coverage['requirements_with_verification']}")
        logging.info(f"  Overall coverage: {coverage['coverage_percentage']:.1f}%")
        
        if coverage['orphaned_items']:
            logging.warning(f"Found {len(coverage['orphaned_items'])} orphaned items without traceability")
        
    except Exception as e:
        logging.error(f"Error generating traceability matrix: {str(e)}")
        raise


if __name__ == '__main__':
    main()