"""Test caching implementation in GitHub Actions workflows."""

import yaml
from pathlib import Path


def test_main_workflow_has_caching():
    """Test that main.yml workflow has caching steps implemented."""
    workflow_path = Path(".github/workflows/main.yml")
    assert workflow_path.exists(), "main.yml workflow should exist"
    
    with open(workflow_path) as f:
        workflow = yaml.safe_load(f)
    
    # Check that we have jobs that should have caching
    assert "jobs" in workflow
    jobs = workflow["jobs"]
    
    # Test pre-commit job has both pip and pre-commit caching
    pre_commit_job = jobs.get("pre-commit", {})
    pre_commit_steps = pre_commit_job.get("steps", [])
    
    cache_steps = [step for step in pre_commit_steps if "cache" in step.get("name", "").lower()]
    assert len(cache_steps) >= 2, "pre-commit job should have at least 2 cache steps"
    
    # Verify cache actions use SHA pinning
    for step in cache_steps:
        if step.get("uses", "").startswith("actions/cache@"):
            uses = step["uses"]
            assert "@0400d5f644dc74513175e3cd8d07132dd4860809" in uses, \
                f"Cache action should use SHA pinning: {uses}"


def test_test_job_has_pip_caching():
    """Test that test job has pip caching."""
    workflow_path = Path(".github/workflows/main.yml")
    
    with open(workflow_path) as f:
        workflow = yaml.safe_load(f)
    
    test_job = workflow["jobs"].get("test", {})
    test_steps = test_job.get("steps", [])
    
    cache_steps = [step for step in test_steps if "cache" in step.get("name", "").lower()]
    assert len(cache_steps) >= 1, "test job should have at least 1 cache step"
    
    # Check that cache key includes python version
    pip_cache_step = next((step for step in cache_steps 
                          if "python dependencies" in step.get("name", "").lower()), None)
    assert pip_cache_step is not None, "Should have Python dependencies cache step"
    
    cache_key = pip_cache_step.get("with", {}).get("key", "")
    assert "matrix.python-version" in cache_key, \
        "Cache key should include Python version for matrix builds"


def test_build_job_has_caching():
    """Test that build job has caching."""
    workflow_path = Path(".github/workflows/main.yml")
    
    with open(workflow_path) as f:
        workflow = yaml.safe_load(f)
    
    build_job = workflow["jobs"].get("build", {})
    build_steps = build_job.get("steps", [])
    
    cache_steps = [step for step in build_steps if "cache" in step.get("name", "").lower()]
    assert len(cache_steps) >= 1, "build job should have at least 1 cache step"


def test_security_job_has_caching():
    """Test that security job has caching."""
    workflow_path = Path(".github/workflows/main.yml")
    
    with open(workflow_path) as f:
        workflow = yaml.safe_load(f)
    
    security_job = workflow["jobs"].get("security", {})
    security_steps = security_job.get("steps", [])
    
    cache_steps = [step for step in security_steps if "cache" in step.get("name", "").lower()]
    assert len(cache_steps) >= 1, "security job should have at least 1 cache step"


def test_workflow_failure_tracker_caching_comment():
    """Test that workflow-failure-tracker has appropriate caching comment."""
    workflow_path = Path(".github/workflows/workflow-failure-tracker.yml")
    assert workflow_path.exists(), "workflow-failure-tracker.yml should exist"
    
    with open(workflow_path) as f:
        content = f.read()
    
    # Check for bilingual comment explaining why no caching is needed
    assert "No caching needed" in content, \
        "Should have comment explaining why no caching is needed"
    assert "Kein Caching erforderlich" in content, \
        "Should have German comment explaining why no caching is needed"


def test_cache_keys_are_secure():
    """Test that cache keys include file hashes for security."""
    workflow_path = Path(".github/workflows/main.yml")
    
    with open(workflow_path) as f:
        workflow = yaml.safe_load(f)
    
    jobs = workflow["jobs"]
    
    for job_name, job in jobs.items():
        steps = job.get("steps", [])
        for step in steps:
            if step.get("uses", "").startswith("actions/cache@"):
                cache_key = step.get("with", {}).get("key", "")
                # Cache keys should include hashFiles for security
                assert "hashFiles" in cache_key, \
                    f"Cache key in {job_name} should include hashFiles: {cache_key}"


def test_bilingual_comments():
    """Test that caching steps have bilingual comments."""
    workflow_path = Path(".github/workflows/main.yml")
    
    with open(workflow_path) as f:
        content = f.read()
    
    # Check for English comments
    assert "Cache Python dependencies for faster builds" in content, \
        "Should have English comment about Python dependencies caching"
    assert "Cache pre-commit environments for faster hook execution" in content, \
        "Should have English comment about pre-commit caching"
    
    # Check for German comments
    assert "Cache für Python-Abhängigkeiten für schnellere Builds" in content, \
        "Should have German comment about Python dependencies caching"
    assert "Cache für Pre-commit-Umgebungen für schnellere Hook-Ausführung" in content, \
        "Should have German comment about pre-commit caching"