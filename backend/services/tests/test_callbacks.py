import pytest

from services.callbacks import validate_callback_url


def test_private_callback_allowed_only_explicitly():
    assert validate_callback_url("http://127.0.0.1:9090", allow_private=True)


def test_private_callback_rejected_in_production_mode():
    with pytest.raises(ValueError):
        validate_callback_url("http://127.0.0.1:9090", allow_private=False)


def test_metadata_endpoint_is_never_allowed():
    with pytest.raises(ValueError):
        validate_callback_url("http://169.254.169.254/latest/meta-data/", allow_private=True)


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "http://user:pass@127.0.0.1/",
        "http://169.254.169.254/latest/meta-data/",
        "not-a-url",
    ],
)
def test_unsafe_callback_urls_are_rejected(url):
    with pytest.raises(ValueError):
        validate_callback_url(url, allow_private=False)
