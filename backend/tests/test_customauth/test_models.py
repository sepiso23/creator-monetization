"""
Tests for authentication models.
"""
import pytest
from django.contrib.auth import get_user_model
from apps.customauth.models import APIClient
from apps.creators.models import CreatorProfile
from tests.factories import UserFactory, APIClientFactory, CreatorProfileFactory

User = get_user_model()


@pytest.mark.django_db
class TestCustomUserModel:
    """Test CustomUser model."""

    def test_create_user(self):
        """Test creating a regular user."""
        user = UserFactory(user_type="creator")
        assert user.email
        assert user.username
        assert user.is_active is True
        assert user.is_staff is False
        assert user.user_type == "creator"

    def test_create_user_with_password(self):
        """Test creating user with password."""
        user = UserFactory(password="SecurePass123")
        assert user.check_password("SecurePass123")

    def test_user_str_representation(self):
        """Test user string representation."""
        user = UserFactory(email="test@example.com")
        assert str(user) == "test@example.com"

    def test_get_full_name(self):
        """Test getting user full name."""
        user = UserFactory(first_name="John", last_name="Doe")
        assert user.get_full_name() == "John Doe"

    def test_get_full_name_with_missing_parts(self):
        """Test full name with missing first or last name."""
        user = UserFactory(first_name="John", last_name="")
        assert user.get_full_name() == "John"

    def test_get_short_name(self):
        """Test getting user short name."""
        user = UserFactory(first_name="John", last_name="Doe")
        assert user.get_short_name() == "John"

    def test_is_creator_method(self):
        """Test is_creator method."""
        creator = UserFactory(user_type="creator")
        assert creator.is_creator() is True

        staff = UserFactory(user_type="staff")
        assert staff.is_creator() is False

    def test_is_admin_user_method(self):
        """Test is_admin_user method."""
        creator = UserFactory(user_type="creator")
        assert creator.is_admin_user() is False

        staff = UserFactory(user_type="staff")
        assert staff.is_admin_user() is True

        admin = UserFactory(user_type="admin")
        assert admin.is_admin_user() is True

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="adminpass123"
        )
        assert user.is_superuser is True
        assert user.is_staff is True
        assert user.is_active is True

    def test_create_superuser_without_password(self):
        """Test creating superuser without password."""
        user = User.objects.create_superuser(
            email="admin@example.com",
            username="admin"
        )
        assert user.is_superuser is True

    def test_email_uniqueness(self):
        """Test email field uniqueness."""
        UserFactory(email="unique@example.com")
        with pytest.raises(Exception):  # IntegrityError
            UserFactory(email="unique@example.com")

    def test_username_uniqueness(self):
        """Test username field uniqueness."""
        UserFactory(username="uniqueusername")
        with pytest.raises(Exception):  # IntegrityError
            UserFactory(username="uniqueusername")

    def test_user_ordering(self):
        """Test users are ordered by date_joined descending."""
        user1 = UserFactory()
        user2 = UserFactory()
        users = User.objects.all()
        assert list(users) == [user2, user1]


@pytest.mark.django_db
class TestAPIClientModel:
    """Test APIClient model."""

    def test_create_api_client(self):
        """Test creating an API client."""
        client = APIClientFactory()
        assert client.name
        assert client.client_type == "web"
        assert client.is_active is True
        assert client.rate_limit == 1000

    def test_api_key_generation(self):
        """Test API key is generated automatically."""
        client = APIClientFactory()
        assert client.api_key
        assert client.api_key.startswith("sk_")

    def test_api_key_uniqueness(self):
        """Test API keys are unique."""
        client1 = APIClientFactory()
        client2 = APIClientFactory()
        assert client1.api_key != client2.api_key

    def test_regenerate_api_key(self):
        """Test regenerating API key."""
        client = APIClientFactory()
        old_key = client.api_key
        client.regenerate_api_key()
        assert client.api_key != old_key
        assert client.api_key.startswith("sk_")

    def test_client_str_representation(self):
        """Test client string representation."""
        client = APIClientFactory(name="Test App")
        assert str(client) == "Test App"

    def test_client_type_choices(self):
        """Test client type field choices."""
        for client_type in ["web", "mobile", "internal", "partner"]:
            client = APIClientFactory(client_type=client_type)
            assert client.client_type == client_type

    def test_api_client_ordering(self):
        """Test API clients are ordered by created_at descending."""
        client1 = APIClientFactory()
        client2 = APIClientFactory()
        clients = APIClient.objects.all()
        assert list(clients) == [client2, client1]

    def test_client_deactivation(self):
        """Test deactivating a client."""
        client = APIClientFactory(is_active=True)
        client.is_active = False
        client.save()
        assert client.is_active is False


@pytest.mark.django_db
class TestCreatorProfileModel:
    """Test CreatorProfile model."""

    def test_create_creator_profile(self):
        """Test creating a creator profile."""
        profile = CreatorProfileFactory()
        assert profile.user
        assert profile.status == "active"
        assert profile.followers_count >= 0
        assert profile.rating >= 0

    def test_creator_profile_str_representation(self):
        """Test creator profile string representation."""
        user = UserFactory(first_name="John", last_name="Doe")
        profile = CreatorProfileFactory(user=user)
        assert "John Doe" in str(profile)

    def test_is_verified_property(self):
        """Test is_verified property."""
        profile = CreatorProfileFactory(verified=True)
        assert profile.is_verified is True

        profile.verified = False
        assert profile.is_verified is False

    def test_is_suspended_property(self):
        """Test is_suspended property."""
        profile = CreatorProfileFactory(status="suspended")
        assert profile.is_suspended is True

        profile.status = "active"
        assert profile.is_suspended is False

    def test_is_banned_property(self):
        """Test is_banned property."""
        profile = CreatorProfileFactory(status="banned")
        assert profile.is_banned is True

        profile.status = "active"
        assert profile.is_banned is False

    def test_status_choices(self):
        """Test status field choices."""
        for status in ["active", "inactive", "suspended", "banned"]:
            profile = CreatorProfileFactory(status=status)
            assert profile.status == status

    def test_creator_profile_one_to_one(self):
        """Test one-to-one relationship between user and profile."""
        user = UserFactory()
        CreatorProfileFactory(user=user)
        
        # Creating another profile for same user should fail
        with pytest.raises(Exception):
            CreatorProfileFactory(user=user)

    def test_creator_profile_deletion_cascades(self):
        """Test that profile is deleted when user is deleted."""
        user = UserFactory()
        profile = CreatorProfileFactory(user=user)
        profile_id = profile.id
        
        user.delete()
        
        with pytest.raises(CreatorProfile.DoesNotExist):
            CreatorProfile.objects.get(id=profile_id)

    def test_creator_profile_ordering(self):
        """Test creator profiles are ordered by followers count."""
        profile1 = CreatorProfileFactory(followers_count=100)
        profile2 = CreatorProfileFactory(followers_count=500)
        profile3 = CreatorProfileFactory(followers_count=200)
        
        profiles = CreatorProfile.objects.all()
        assert list(profiles) == [profile2, profile3, profile1]
