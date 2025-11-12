"""
Tests for prompts API endpoints
"""

import pytest


@pytest.mark.unit
def test_get_available_variables(client):
    """Test getting available template variables"""
    response = client.get("/api/prompts/variables/available")
    assert response.status_code == 200

    data = response.json()
    assert "variables" in data

    variables = data["variables"]
    assert "{date}" in variables
    assert "{time}" in variables
    assert "{restaurant_name}" in variables
    assert "{restaurant_phone}" in variables
    assert "{restaurant_address}" in variables


@pytest.mark.unit
def test_preview_prompt(client, sample_prompt_content):
    """Test prompt preview with variable substitution"""
    response = client.post(
        "/api/prompts/preview",
        json={"content": sample_prompt_content}
    )
    assert response.status_code == 200

    data = response.json()
    assert "preview" in data

    # Verify variables were replaced
    preview = data["preview"]
    assert "{date}" not in preview  # Should be replaced
    assert "{time}" not in preview  # Should be replaced
    assert "{restaurant_name}" not in preview  # Should be replaced


@pytest.mark.integration
def test_get_all_prompts(client):
    """Test getting all prompts"""
    response = client.get("/api/prompts/")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    # Should have at least the default system prompt
    if len(data) > 0:
        prompt = data[0]
        assert "id" in prompt
        assert "name" in prompt
        assert "content" in prompt
        assert "version" in prompt
        assert "is_active" in prompt
