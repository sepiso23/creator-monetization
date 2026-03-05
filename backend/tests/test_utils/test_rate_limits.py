import pytest
from utils.rate_limits import (
    check_login_attemps,
    increment_login_attemps,
    reset_login_attemps,
    check_payment_rate_limit
    )

@pytest.mark.django_db
def test_login_attempts_rate_limit():
    """
    Test rate limits for login
    """
    email = "test@example.com"
    # Test the rate limit for login attempts
    for _ in range(5):
        increment_login_attemps(email)
    assert check_login_attemps(email) == (False, "Account locked. Try again in 30 minutes.")
    reset_login_attemps(email)
    assert check_login_attemps(email) == (True, 0)


@pytest.mark.django_db
def test_payment_rate_limit():
    """
    Test rate limits for payments
    """
    wallet_id = "test_wallet"
    # Test the rate limit for payments
    for _ in range(5):
        assert check_payment_rate_limit(wallet_id) == (True, _ + 1)
    assert check_payment_rate_limit(wallet_id) == (False, "Rate limit exceeded. Try again later.")
