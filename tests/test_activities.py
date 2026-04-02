"""
Tests for GET /activities endpoint.

Tests verify that the activities list is returned correctly with proper
structure and data integrity.
"""

import pytest


class TestGetActivities:
    """Test suite for retrieving activities list."""

    def test_returns_all_activities(self, client, fresh_activities):
        """Test that GET /activities returns all registered activities."""
        # Arrange
        expected_activity_count = 9
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Tennis Club",
            "Drama Club",
            "Art Studio",
            "Debate Team",
            "Science Club",
        ]

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == expected_activity_count
        assert all(name in activities for name in expected_activities)

    def test_activity_has_required_fields(self, client, fresh_activities):
        """Test that each activity has all required fields."""
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert response.status_code == 200
        for activity_name, activity_data in activities.items():
            for field in required_fields:
                assert field in activity_data, f"Activity '{activity_name}' missing field '{field}'"

    def test_participants_list_contains_initial_data(self, client, fresh_activities):
        """Test that participants list contains seeded participant data."""
        # Arrange
        expected_participants = {
            "Chess Club": ["michael@mergington.edu", "daniel@mergington.edu"],
            "Programming Class": ["emma@mergington.edu", "sophia@mergington.edu"],
            "Gym Class": ["john@mergington.edu", "olivia@mergington.edu"],
        }

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert response.status_code == 200
        for activity_name, expected_list in expected_participants.items():
            assert activities[activity_name]["participants"] == expected_list

    def test_max_participants_is_positive_integer(self, client, fresh_activities):
        """Test that max_participants is a positive integer for all activities."""
        # Arrange
        # No specific arrangement needed; we just check the response

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert response.status_code == 200
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data["max_participants"], int)
            assert activity_data["max_participants"] > 0

    def test_participants_is_list(self, client, fresh_activities):
        """Test that participants field is always a list."""
        # Arrange
        # No specific arrangement needed; we just check the response

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        assert response.status_code == 200
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data["participants"], list)
            # All items in participants list should be strings (emails)
            assert all(isinstance(p, str) for p in activity_data["participants"])
