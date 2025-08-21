#!/usr/bin/env python3
"""
Integration test for compliance-check workflow
Tests the complete workflow structure and basic file operations
"""

import os
import yaml
import subprocess
from pathlib import Path


def test_workflow_structure():
    """Test that the workflow file has correct structure."""
    workflow_path = Path(__file__).parent.parent / 'workflows' / 'compliance-check.yml'
    
    if not workflow_path.exists():
        raise AssertionError(f"Workflow file not found: {workflow_path}")
        
    with open(workflow_path, 'r') as f:
        workflow_content = yaml.safe_load(f)
        
    # Check required fields  
    assert 'name' in workflow_content, "Workflow missing name"
    assert ('on' in workflow_content or True in workflow_content), "Workflow missing triggers"
    assert 'jobs' in workflow_content, "Workflow missing jobs"
    
    # Check triggers (note: 'on' is a Python keyword so YAML may parse it as True)
    triggers = workflow_content.get('on') or workflow_content.get(True)
    if not triggers:
        raise AssertionError("Workflow missing 'on' triggers section")
    assert 'pull_request' in triggers, "Missing pull_request trigger"
    assert 'pull_request_review' in triggers, "Missing pull_request_review trigger"
    
    # Check job structure
    jobs = workflow_content['jobs']
    assert 'compliance-validation' in jobs, "Missing compliance-validation job"
    
    job = jobs['compliance-validation']
    assert 'runs-on' in job, "Job missing runs-on"
    assert 'steps' in job, "Job missing steps"
    
    # Check for key steps
    steps = job['steps']
    step_names = [step.get('name', step.get('uses', '')) for step in steps]
    
    required_steps = [
        'Checkout repository',
        'Setup Python', 
        'Install dependencies',
        'Run compliance validation'
    ]
    
    for required_step in required_steps:
        if not any(required_step in step_name for step_name in step_names):
            raise AssertionError(f"Missing required step: {required_step}")
            
    print("✅ Workflow structure validation passed")


def test_script_files_exist():
    """Test that required script files exist."""
    script_dir = Path(__file__).parent
    
    required_files = [
        'compliance-validator.py',
        'test_compliance_validator.py'
    ]
    
    for file_name in required_files:
        file_path = script_dir / file_name
        if not file_path.exists():
            raise AssertionError(f"Required script file missing: {file_name}")
            
    print("✅ Script files existence check passed")


def test_script_permissions():
    """Test that script files have proper permissions."""
    script_dir = Path(__file__).parent
    
    compliance_script = script_dir / 'compliance-validator.py'
    
    # Check if file is readable
    if not os.access(compliance_script, os.R_OK):
        raise AssertionError("Compliance validator script not readable")
        
    print("✅ Script permissions check passed")


def test_script_syntax():
    """Test that Python scripts have valid syntax."""
    script_dir = Path(__file__).parent
    
    python_files = [
        'compliance-validator.py',
        'test_compliance_validator.py'
    ]
    
    for py_file in python_files:
        file_path = script_dir / py_file
        
        # Use py_compile to check syntax
        try:
            result = subprocess.run(
                ['python3', '-m', 'py_compile', str(file_path)],
                capture_output=True,
                text=True,
                cwd=script_dir
            )
            
            if result.returncode != 0:
                raise AssertionError(f"Syntax error in {py_file}: {result.stderr}")
                
        except FileNotFoundError:
            # Python3 not available - skip syntax check
            print(f"⚠️ Skipping syntax check for {py_file} (python3 not available)")
            continue
            
    print("✅ Script syntax validation passed")


def test_workflow_environment_setup():
    """Test that workflow sets up environment correctly."""
    workflow_path = Path(__file__).parent.parent / 'workflows' / 'compliance-check.yml'
    
    with open(workflow_path, 'r') as f:
        content = f.read()
        
    # Check for required environment variables
    required_env_vars = [
        'GITHUB_TOKEN',
        'PR_NUMBER',
        'REPOSITORY'
    ]
    
    for env_var in required_env_vars:
        if env_var not in content:
            raise AssertionError(f"Workflow missing environment variable: {env_var}")
            
    # Check for Python setup
    if 'setup-python@v4' not in content:
        raise AssertionError("Workflow missing Python setup action")
        
    # Check for dependency installation
    if 'pip install' not in content:
        raise AssertionError("Workflow missing dependency installation")
        
    print("✅ Workflow environment setup validation passed")


def test_compliance_script_structure():
    """Test basic structure of compliance validator script."""
    script_path = Path(__file__).parent / 'compliance-validator.py'
    
    with open(script_path, 'r') as f:
        content = f.read()
        
    # Check for key class and methods
    required_elements = [
        'class ComplianceValidator',
        'def validate_document_presence',
        'def validate_approval_status', 
        'def validate_document_relationships',
        'def validate_template_compliance',
        'def run_validation'
    ]
    
    for element in required_elements:
        if element not in content:
            raise AssertionError(f"Missing required element in compliance script: {element}")
            
    # Check for proper error handling
    if 'self.errors' not in content:
        raise AssertionError("Compliance script missing error tracking")
        
    print("✅ Compliance script structure validation passed")


def run_all_tests():
    """Run all integration tests."""
    tests = [
        test_workflow_structure,
        test_script_files_exist,
        test_script_permissions,
        test_script_syntax,
        test_workflow_environment_setup,
        test_compliance_script_structure
    ]
    
    passed = 0
    failed = 0
    
    print("🧪 Running compliance-check integration tests...\n")
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
            
    print(f"\n📊 Integration test results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All integration tests passed!")
        return True
    else:
        print(f"\n💥 {failed} integration test(s) failed!")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)