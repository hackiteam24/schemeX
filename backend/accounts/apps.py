from django.apps import AppConfig
from django.db.models.signals import post_migrate


def create_default_admin(sender, **kwargs):
    from accounts.models import User
    try:
        user = User.objects.filter(username="admin").first()
        if not user:
            # Create a superuser with role=admin and password=admin123
            user = User.objects.create_superuser(
                username="admin",
                email="admin@schemex.ai",
                password="admin123"
            )
            user.role = User.Role.ADMIN
            user.save()
            print("Successfully created default admin user (username: admin, password: admin123)")
        else:
            # Ensure password, role and permissions are correct
            user.set_password("admin123")
            user.role = User.Role.ADMIN
            user.is_superuser = True
            user.is_staff = True
            user.save()
            print("Successfully synced/updated default admin user credentials to admin/admin123")
    except Exception:
        # Ignore errors during initial migrations or if database is not ready
        pass


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        post_migrate.connect(create_default_admin, sender=self)
