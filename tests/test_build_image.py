import os
from unittest.mock import mock_open, patch

from click.testing import CliRunner

from birdfeeder.build_image import get_available_images, get_org_from_dockerfile, main


def test_get_available_images():
    dockerfiles = ["Dockerfile.foo", "Dockerfile.bar"]
    unrelated_files = ["xxx.yyy", ".gitignore"]
    with patch("os.listdir", return_value=dockerfiles + unrelated_files):
        images = get_available_images()
        assert images == ["foo", "bar"]


def test_get_org_from_dockerfile():
    test_org = "coinalpha"
    mock_data = mock_open(read_data=f'LABEL org="{test_org}"\n')

    # test existing label
    with patch("builtins.open", mock_data):
        org = get_org_from_dockerfile("Dockerfile.test")
        assert org == test_org

    # test fallback
    with patch("builtins.open", mock_open()):
        org = get_org_from_dockerfile("Dockerfile.test")
        assert org == test_org


def test_main_no_dockerfiles():
    runner = CliRunner()
    result = runner.invoke(main, ["nonexistent"])
    assert result.exit_code == 1


@patch("birdfeeder.build_image.push_image")
@patch("birdfeeder.build_image.build_image")
def test_main(mock_build_image, mock_push_image):
    runner = CliRunner()
    os.chdir(os.path.join(os.path.dirname(__file__), "dockerfiles"))
    result = runner.invoke(main, ["test", "--tag", "mytag", "--push"])
    assert result.exit_code == 0
    mock_build_image.assert_called_with("testorg", "Dockerfile.test", "test", "mytag")
    mock_push_image.assert_called_with("testorg", "test", "mytag")
