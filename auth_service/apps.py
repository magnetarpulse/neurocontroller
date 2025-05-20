import random
import string
import logging
from django.apps import AppConfig
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

def generate_random_string(length=12):
    """Generate a secure random string."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

class AuthServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auth_service'

    def ready(self):
        """Ensures the superuser is created when the app is ready."""
        from django.db.utils import OperationalError, ProgrammingError  # Catch database errors
        User = get_user_model()

        try:
            from auth_service.models import Users  # Import inside the method to prevent premature loading
        except ImportError:
            logger.error("Error importing Users model. Ensure auth_service.models.Users exists.")
            return

        username = 'admin'
        password = generate_random_string()

        try:
            if not User.objects.exists():  # Prevents premature database access
                user, created = User.objects.get_or_create(username=username)
                if created:
                    user.set_password(password)
                    user.is_superuser = True
                    user.is_staff = True
                    user.save()
                    print(f'Creating superuser {username} with password: {password}')

                else:
                    print(f'Superuser {username} already exists')

                # Create or get the corresponding Users table entry
                Users.objects.get_or_create(
                    username=username,
                    defaults={"password": user.password, "user_id": user}
                )
                print(f'Created user table entry for {username}:{password}')

        except (OperationalError, ProgrammingError) as e:
            print(f'Database error: {e}')
