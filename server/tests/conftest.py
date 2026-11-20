import pytest
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from core.models import UserRole

@pytest.fixture
def demo_users(db):
    users = {}
    for username, role in [('test-admin', 'admin'), ('test-clinician', 'clinician'), ('test-researcher', 'researcher')]:
        user = User.objects.create_user(username=username, password='UnitTestStrongPass!')
        UserRole.objects.create(user=user, role=role)
        users[role] = {'user': user, 'token': Token.objects.create(user=user)}
    return users

@pytest.fixture
def seeded_demo(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        from django.core.management import call_command
        call_command('seed_demo', verbosity=0)
    return True
