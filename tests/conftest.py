"""
Pytest configuration and shared fixtures for FastAPI application tests.

Provides TestClient, app instance, and fresh activity state for each test.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """
    Provide a TestClient instance for the FastAPI application.
    
    Yields:
        TestClient: Configured test client for making requests.
    """
    return TestClient(app)


@pytest.fixture
def fresh_activities():
    """
    Reset activities to initial state before each test.
    
    This ensures tests don't pollute each other's state. The app module
    maintains a shared activities dict that persists between requests,
    so we reset it to known values before each test runs.
    
    Yields:
        dict: The activities dictionary as it exists for this test.
    """
    # Store original state
    original_activities = {
        activity: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy(),
        }
        for activity, details in activities.items()
    }
    
    yield activities
    
    # Restore original state after test
    for activity in activities:
        activities[activity]["participants"] = original_activities[activity]["participants"].copy()
