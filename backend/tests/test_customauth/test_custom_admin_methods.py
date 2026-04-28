"""This module tests custom admin methods for the 
custom authentication system."""

import pytest
from apps.customauth.models import CustomUser

@pytest.mark.django_db
def test_create_user():
    """Test the create_user method of CustomUserManager."""
    user = CustomUser.objects.create_user(
        email="test@example.com",
        password="testpassword"
    )
    assert user.email == "test@example.com"
    assert user.check_password("testpassword")
    assert not user.is_staff
    assert not user.is_superuser

@pytest.mark.django_db
def test_create_superuser():
    """Test the create_superuser method of CustomUserManager."""
    superuser = CustomUser.objects.create_superuser(
        email="superuser@example.com",
        password="superuserpassword"
    )
    assert superuser.email == "superuser@example.com"
    assert superuser.check_password("superuserpassword")
    assert superuser.is_staff
    assert superuser.is_superuser


@pytest.mark.django_db
def test_create_superuser_without_staff():
    """Test that creating a superuser without is_staff=True raises an error."""
    with pytest.raises(ValueError) as excinfo:
        CustomUser.objects.create_superuser(
            email="superuser@example.com",
            password="superuserpassword",
            is_staff=False
        )


@pytest.mark.django_db
def test_overide_save_method():
    """Test that the save method correctly generates a slug."""
    user = CustomUser.objects.create_user(
        email="test@example.com",
        password="testpassword",
        username="Test User"
    )
    assert user.slug == "test-user"


@pytest.mark.django_db
def test_overide_save_method_is_case_insensitive():
    """Test that the save method correctly generates a slug
    regardless of case."""
    user = CustomUser.objects.create_user(
        email="test@example.com",
        password="testpassword",
        username="TEST USER"
    )
    assert user.slug == "test-user"

@pytest.mark.django_db
def test_overide_save_method_with_special_characters():
    """Test that the save method correctly generates a slug
    when the username contains special characters."""
    user = CustomUser.objects.create_user(
        email="test@example.com",
        password="testpassword",
        username="Test User!"
    )
    assert user.slug == "test-user"

@pytest.mark.django_db
def test_overide_save_method_with_duplicate_username():
    """Test that the save method correctly generates a unique slug
    when there are duplicate usernames."""
    user1 = CustomUser.objects.create_user(
        email="test1@example.com",
        password="testpassword",
        username="Test User"
    )
    user2 = CustomUser.objects.create_user(
        email="test2@example.com",
        password="testpassword",
        username="Test User"
    )
    assert user1.slug == "test-user"
    # Assert second users slug has a unique 4 digit suffix
    assert user2.slug[-4:].isdigit()
    assert user2.slug.startswith("test-user")