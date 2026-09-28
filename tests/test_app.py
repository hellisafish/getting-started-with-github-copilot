from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


INITIAL_ACTIVITIES = deepcopy(activities)
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    activities.clear()
    activities.update(deepcopy(INITIAL_ACTIVITIES))
    yield
    activities.clear()
    activities.update(deepcopy(INITIAL_ACTIVITIES))


def test_root_redirects_to_static_index():
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_seeded_activities():
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert expected_activity in response.json()
    assert response.json()[expected_activity] == activities[expected_activity]


def test_signup_registers_new_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"
    activity_path = quote(activity_name, safe="")

    # Act
    response = client.post(
        f"/activities/{activity_path}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant():
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]
    activity_path = quote(activity_name, safe="")
    original_count = activities[activity_name]["participants"].count(email)

    # Act
    response = client.post(
        f"/activities/{activity_path}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert activities[activity_name]["participants"].count(email) == original_count


def test_signup_rejects_unknown_activity():
    # Arrange
    activity_name = "Robotics Club"
    activity_path = quote(activity_name, safe="")

    # Act
    response = client.post(
        f"/activities/{activity_path}/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_existing_participant():
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]
    activity_path = quote(activity_name, safe="")
    email_path = quote(email, safe="")

    # Act
    response = client.delete(
        f"/activities/{activity_path}/participants/{email_path}"
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert email not in activities[activity_name]["participants"]


def test_unregister_rejects_unknown_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "not.registered@mergington.edu"
    activity_path = quote(activity_name, safe="")
    email_path = quote(email, safe="")

    # Act
    response = client.delete(
        f"/activities/{activity_path}/participants/{email_path}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_rejects_unknown_activity():
    # Arrange
    activity_name = "Robotics Club"
    email = "student@mergington.edu"
    activity_path = quote(activity_name, safe="")
    email_path = quote(email, safe="")

    # Act
    response = client.delete(
        f"/activities/{activity_path}/participants/{email_path}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
