"""
Integration tests for multi-step workflows and state consistency.

Tests verify end-to-end flows involving multiple API calls and
state transitions across the system.
"""

import pytest


class TestSignupUnregisterWorkflow:
    """Test complete workflows involving signup and unregister."""

    def test_signup_verify_unregister_verify(self, client, fresh_activities):
        """Test complete workflow: signup -> verify in list -> unregister -> verify removed."""
        # Arrange
        activity_name = "Chess Club"
        email = "workflow@mergington.edu"

        # Act & Assert - Step 1: Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200

        # Act & Assert - Step 2: Verify participant in list
        list_response = client.get("/activities")
        assert list_response.status_code == 200
        activities = list_response.json()
        assert email in activities[activity_name]["participants"]
        initial_count = len(activities[activity_name]["participants"])

        # Act & Assert - Step 3: Unregister
        unregister_response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200

        # Act & Assert - Step 4: Verify removed from list
        final_list_response = client.get("/activities")
        assert final_list_response.status_code == 200
        final_activities = final_list_response.json()
        assert email not in final_activities[activity_name]["participants"]
        assert len(final_activities[activity_name]["participants"]) == initial_count - 1

    def test_multiple_participants_different_activities(self, client, fresh_activities):
        """Test workflow with multiple participants in different activities."""
        # Arrange
        user1 = "user1@mergington.edu"
        user2 = "user2@mergington.edu"
        activity1 = "Programming Class"
        activity2 = "Drama Club"

        # Act
        # User1 signs up for activity1, user2 signs up for activity2
        client.post(f"/activities/{activity1}/signup", params={"email": user1})
        client.post(f"/activities/{activity2}/signup", params={"email": user2})

        # Both users cross-join
        client.post(f"/activities/{activity2}/signup", params={"email": user1})
        client.post(f"/activities/{activity1}/signup", params={"email": user2})

        list_response = client.get("/activities")

        # Assert
        activities = list_response.json()
        assert user1 in activities[activity1]["participants"]
        assert user2 in activities[activity1]["participants"]
        assert user1 in activities[activity2]["participants"]
        assert user2 in activities[activity2]["participants"]

    def test_participant_capacity_tracking(self, client, fresh_activities):
        """Test that available spots are correctly tracked as participants join/leave."""
        # Arrange
        activity_name = "Art Studio"
        new_email = "artist@mergington.edu"

        # Get initial availability
        initial_response = client.get("/activities")
        initial_activities = initial_response.json()
        initial_max = initial_activities[activity_name]["max_participants"]
        initial_count = len(initial_activities[activity_name]["participants"])
        initial_spots_left = initial_max - initial_count

        # Act - Sign up
        client.post(f"/activities/{activity_name}/signup", params={"email": new_email})
        after_signup_response = client.get("/activities")
        after_signup_activities = after_signup_response.json()
        after_signup_count = len(after_signup_activities[activity_name]["participants"])
        after_signup_spots_left = (
            after_signup_activities[activity_name]["max_participants"] - after_signup_count
        )

        # Assert signup reduced spots
        assert after_signup_count == initial_count + 1
        assert after_signup_spots_left == initial_spots_left - 1

        # Act - Unregister
        client.post(f"/activities/{activity_name}/unregister", params={"email": new_email})
        after_unregister_response = client.get("/activities")
        after_unregister_activities = after_unregister_response.json()
        after_unregister_count = len(after_unregister_activities[activity_name]["participants"])
        after_unregister_spots_left = (
            after_unregister_activities[activity_name]["max_participants"] - after_unregister_count
        )

        # Assert unregister restored spots
        assert after_unregister_count == initial_count
        assert after_unregister_spots_left == initial_spots_left


class TestStateConsistency:
    """Test that system state remains consistent across operations."""

    def test_all_activities_remain_accessible(self, client, fresh_activities):
        """Test that all activities remain in the system after various operations."""
        # Arrange
        expected_activities = {
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Tennis Club",
            "Drama Club",
            "Art Studio",
            "Debate Team",
            "Science Club",
        }

        # Act - Perform various operations
        client.post("/activities/Chess Club/signup", params={"email": "test1@mergington.edu"})
        client.post("/activities/Programming Class/unregister", params={"email": "emma@mergington.edu"})
        client.post("/activities/Drama Club/signup", params={"email": "test2@mergington.edu"})

        response = client.get("/activities")

        # Assert - All activities still present
        assert response.status_code == 200
        activities = response.json()
        actual_activities = set(activities.keys())
        assert actual_activities == expected_activities

    def test_other_activities_unaffected_by_operations(self, client, fresh_activities):
        """Test that operations on one activity don't affect others."""
        # Arrange
        activity1 = "Chess Club"
        activity2 = "Gym Class"
        email = "newstudent@mergington.edu"

        # Get initial state of activity2
        initial_response = client.get("/activities")
        initial_activity2 = initial_response.json()[activity2]["participants"].copy()

        # Act - Perform operations only on activity1
        client.post(f"/activities/{activity1}/signup", params={"email": email})
        client.post(f"/activities/{activity1}/signup", params={"email": "another@mergington.edu"})

        # Check activity2
        final_response = client.get("/activities")
        final_activity2 = final_response.json()[activity2]["participants"]

        # Assert activity2 unchanged
        assert final_activity2 == initial_activity2

    def test_participants_list_immutability_across_requests(self, client, fresh_activities):
        """Test that getting activities multiple times returns consistent data."""
        # Arrange - Make the same request multiple times without other operations

        # Act
        response1 = client.get("/activities")
        response2 = client.get("/activities")
        response3 = client.get("/activities")

        # Assert - All responses are identical
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200

        activities1 = response1.json()
        activities2 = response2.json()
        activities3 = response3.json()

        # Deep equality check
        for activity_name in activities1:
            participants1 = activities1[activity_name]["participants"]
            participants2 = activities2[activity_name]["participants"]
            participants3 = activities3[activity_name]["participants"]

            assert participants1 == participants2
            assert participants2 == participants3


class TestConcurrentLikeOperations:
    """Test behavior with rapid/sequential operations that simulate concurrency."""

    def test_rapid_signups_same_activity(self, client, fresh_activities):
        """Test handling of rapid signup requests to the same activity."""
        # Arrange
        activity_name = "Science Club"
        emails = [f"student{i}@mergington.edu" for i in range(5)]

        # Act - Sign up multiple students rapidly
        responses = [
            client.post(f"/activities/{activity_name}/signup", params={"email": email})
            for email in emails
        ]

        list_response = client.get("/activities")

        # Assert - All successful, all appear in list
        assert all(r.status_code == 200 for r in responses)
        activities = list_response.json()
        for email in emails:
            assert email in activities[activity_name]["participants"]

    def test_alternating_signup_unregister(self, client, fresh_activities):
        """Test alternating signup and unregister operations."""
        # Arrange
        activity_name = "Basketball Team"
        email1 = "player1@mergington.edu"
        email2 = "player2@mergington.edu"

        # Act - Alternating operations
        client.post(f"/activities/{activity_name}/signup", params={"email": email1})
        client.post(f"/activities/{activity_name}/signup", params={"email": email2})
        client.post(f"/activities/{activity_name}/unregister", params={"email": email1})
        client.post(f"/activities/{activity_name}/signup", params={"email": email1})
        client.post(f"/activities/{activity_name}/unregister", params={"email": email2})

        final_response = client.get("/activities")

        # Assert - Only email1 remains
        activities = final_response.json()
        assert email1 in activities[activity_name]["participants"]
        assert email2 not in activities[activity_name]["participants"]
