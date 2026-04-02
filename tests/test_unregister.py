"""
Tests for POST /activities/{activity_name}/unregister endpoint.

Tests cover successful unregistration, error cases, and state consistency.
"""

import pytest


class TestUnregisterSuccess:
    """Test cases for successful unregistration operations."""

    def test_unregister_existing_participant(self, client, fresh_activities):
        """Test successfully unregistering an existing participant."""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Initial participant

        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Unregistered" in data["message"]

    def test_participant_removed_from_activity_list(self, client, fresh_activities):
        """Test that unregistered participant is removed from the activities list."""
        # Arrange
        activity_name = "Programming Class"
        email = "emma@mergington.edu"  # Initial participant

        # Act
        unregister_response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        list_response = client.get("/activities")

        # Assert
        assert unregister_response.status_code == 200
        assert list_response.status_code == 200
        activities = list_response.json()
        assert email not in activities[activity_name]["participants"]

    def test_unregister_one_of_multiple_participants(self, client, fresh_activities):
        """Test unregistering one participant when multiple are registered."""
        # Arrange
        activity_name = "Basketball Team"
        remove_email = "alex@mergington.edu"
        keep_email = "james@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": remove_email}
        )
        list_response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities = list_response.json()
        assert remove_email not in activities[activity_name]["participants"]
        assert keep_email in activities[activity_name]["participants"]


class TestUnregisterErrors:
    """Test cases for unregister error handling."""

    def test_unregister_non_registered_participant(self, client, fresh_activities):
        """Test that unregistering a participant not signed up fails."""
        # Arrange
        activity_name = "Tennis Club"
        email = "nonparticipant@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "not registered" in data["detail"].lower()

    def test_unregister_from_nonexistent_activity(self, client, fresh_activities):
        """Test that unregistering from a non-existent activity fails."""
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_unregister_with_special_characters_in_activity_name(self, client, fresh_activities):
        """Test unregister with URL-encoded activity names."""
        # Arrange
        activity_name = "Art Studio"
        email = "maya@mergington.edu"  # Initial participant

        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        list_response = client.get("/activities")
        activities = list_response.json()
        assert email not in activities[activity_name]["participants"]

    def test_unregister_twice_same_participant(self, client, fresh_activities):
        """Test that unregistering the same participant twice fails on second attempt."""
        # Arrange
        activity_name = "Debate Team"
        email = "isabella@mergington.edu"

        # First unregister should succeed
        client.post(f"/activities/{activity_name}/unregister", params={"email": email})

        # Act - try to unregister again
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"].lower()


class TestUnregisterEdgeCases:
    """Test cases for edge cases and boundary conditions."""

    def test_unregister_multiple_from_same_activity(self, client, fresh_activities):
        """Test unregistering multiple participants from the same activity."""
        # Arrange
        activity_name = "Science Club"
        emails_to_remove = ["william@mergington.edu", "charlotte@mergington.edu"]

        # Act
        responses = [
            client.post(f"/activities/{activity_name}/unregister", params={"email": email})
            for email in emails_to_remove
        ]
        
        list_response = client.get("/activities")

        # Assert
        all_successful = all(r.status_code == 200 for r in responses)
        assert all_successful
        
        activities = list_response.json()
        for email in emails_to_remove:
            assert email not in activities[activity_name]["participants"]

    def test_empty_participants_list_after_unregister_all(self, client, fresh_activities):
        """Test that participants list is empty after unregistering all."""
        # Arrange
        activity_name = "Tennis Club"
        # Tennis Club has two initial participants
        emails = ["jessica@mergington.edu", "ryan@mergington.edu"]

        # Act
        for email in emails:
            client.post(f"/activities/{activity_name}/unregister", params={"email": email})
        
        list_response = client.get("/activities")

        # Assert
        assert list_response.status_code == 200
        activities = list_response.json()
        assert activities[activity_name]["participants"] == []

    def test_unregister_and_resign_up(self, client, fresh_activities):
        """Test that a participant can unregister and then sign up again."""
        # Arrange
        activity_name = "Gym Class"
        email = "john@mergington.edu"

        # Act
        # First unregister
        unregister_response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Then sign up again
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        list_response = client.get("/activities")

        # Assert
        assert unregister_response.status_code == 200
        assert signup_response.status_code == 200
        activities = list_response.json()
        assert email in activities[activity_name]["participants"]
