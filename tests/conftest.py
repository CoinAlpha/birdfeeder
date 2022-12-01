import pytest

pytest_plugins = ["birdfeeder.pytest_fixtures"]


@pytest.fixture(scope="session")
def vcr_config():
    return {
        "filter_headers": ["Authorization", "X-Amz-Security-Token"],
    }
