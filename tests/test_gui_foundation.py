from pathlib import Path

from fastapi.testclient import TestClient

from watch.webapp import create_app


def test_operator_shell_uses_shared_operations_suite_foundation(tmp_path: Path) -> None:
    response = TestClient(create_app(tmp_path)).get("/")

    assert response.status_code == 200
    assert 'class="app-shell"' in response.text
    assert 'class="sidebar" aria-label="WATCH application navigation"' in response.text
    assert "Web Operations Control Hub" in response.text
    assert 'class="content-shell"' in response.text
    assert 'class="topbar"' in response.text
    assert "Local operator" in response.text
    assert 'class="page-header"' in response.text
    assert "WATCH operations" in response.text


def test_operator_shell_keeps_responsive_and_accessible_foundation(tmp_path: Path) -> None:
    response = TestClient(create_app(tmp_path)).get("/targets")

    assert response.status_code == 200
    assert '@media (max-width: 720px)' in response.text
    assert '@media (max-width: 430px)' in response.text
    assert 'class="skip-link" href="#main-content"' in response.text
    assert 'id="main-content" tabindex="-1"' in response.text
    assert 'nav aria-label="Primary"' in response.text
    assert ':focus-visible' in response.text
