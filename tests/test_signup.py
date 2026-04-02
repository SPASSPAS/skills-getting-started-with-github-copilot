"""
Tests for POST /activities/{activity_name}/signup endpoint.

Tests cover successful signups, duplicate signup prevention, and error cases.
"""

import pytest


class TestSignupSuccess:
    """Test cases for successful signup operations."""

    def test_signup_new_participant(self, client, fresh_activities):
        """Test successfully signing up a new participant."""
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]

    def test_participant_appears_in_activity_list(self, client, fresh_activities):
        """Test that newly signed up participant appears in the activities list."""
        # Arrange
        activity_name = "Programming Class"
        email = "newprogrammer@mergington.edu"

        # Act
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        list_response = client.get("/activities")

        # Assert
        assert signup_response.status_code == 200
        assert list_response.status_code == 200
        activities = list_response.json()
        assert email in activities[activity_name]["participants"]

    def test_multiple_signups_accumulate(self, client, fresh_activities):
        """Test that multiple signups to the same activity accumulate."""
        # Arrange
        activity_name = "Tennis Club"
        emails = ["player1@mergington.edu", "player2@mergington.edu", "player3@mergington.edu"]

        # Act
        for email in emails:
            client.post(f"/activities/{activity_name}/signup", params={"email": email})
        
        list_response = client.get("/activities")

        # Assert
        assert list_response.status_code == 200
        activities = list_response.json()
        participants = activities[activity_name]["participants"]
        for email in emails:
            assert email in participants


class TestSignupErrors:
    """Test cases for signup error handling."""

    def test_duplicate_signup_rejected(self, client, fresh_activities):
        """Test that signing up the same participant twice is rejected."""
        # Arrange
        activity_name = "Drama Club"
        email = "duplicatestudent@mergington.edu"
        
        # First signup should succeed
        client.post(f"/activities/{activity_name}/signup", params={"email": email})

        # Act
        duplicate_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert duplicate_response.status_code == 400
        data = duplicate_response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity(self, client, fresh_activities):
        """Test that signing up for a non-existent activity fails."""
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_signup_with_special_characters_in_activity_name(self, client, fresh_activities):
        """Test signup with URL-encoded activity names."""
        # Arrange
        activity_name = "Art Studio"
        email = "artist@mergington.edu"

        # Act - Client should handle URL encoding automatically
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        list_response = client.get("/activities")
        activities = list_response.json()
        assert email in activities[activity_name]["participants"]

    def test_signup_empty_email(self, client, fresh_activities):
        """Test that signup with empty email is handled."""
        # Arrange
        activity_name = "Science Club"
        email = ""

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        # Backend doesn't validate email format, but empty should be handled
        # This tests robustness
        assert response.status_code in [200, 400, 422]


class TestSignupEdgeCases:
    """Test cases for edge cases and boundary conditions."""

    def test_signup_already_registered_participant(self, client, fresh_activities):
        """Test that an initially registered participant cannot sign up again."""
        # Arrange
        activity_name = "Chess Club"
        # michael@mergington.edu is already registered for Chess Club
        email = "michael@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_to_different_activities(self, client, fresh_activities):
        """Test that a participant can sign up to multiple different activities."""
        # Arrange
        email = "multiactivity@mergington.edu"
        activities_to_join = ["Chess Club", "Programming Class", "Debate Team"]

        # Act
        responses = [
            client.post(f"/activities/{activity}/signup", params={"email": email})
            for activity in activities_to_join
        ]
        
        list_response = client.get("/activities")

        # Assert
        all_successful = all(r.status_code == 200 for r in responses)
        assert all_successful
        
        returned_activities = list_response.json()
        for activity in activities_to_join:
            assert email in returned_activities[activity]["participants"]
