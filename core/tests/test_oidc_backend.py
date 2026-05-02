from django.test import TestCase

from sso_auth.backends import MyOIDCBackend
from sso_auth.models import MacFastUser


class MyOIDCBackendTests(TestCase):
    def setUp(self) -> None:
        self.backend = MyOIDCBackend()

    def test_create_user_does_not_grant_admin_permissions(self) -> None:
        user = self.backend.create_user(
            {
                'email': 'student@mcmaster.ca',
                'preferred_username': 'student',
            }
        )

        assert user.is_staff is False
        assert user.is_superuser is False

    def test_update_user_preserves_existing_admin_permissions(self) -> None:
        user = MacFastUser.objects.create_user(
            username='instructor',
            email='instructor@mcmaster.ca',
            is_staff=True,
            is_superuser=True,
        )

        updated_user = self.backend.update_user(user, {'name': 'instructor-renamed'})

        assert updated_user.username == 'instructor-renamed'
        assert updated_user.is_staff is True
        assert updated_user.is_superuser is True
