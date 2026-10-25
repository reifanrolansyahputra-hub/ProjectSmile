from django.db import migrations


def buat_profile_admin(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Profile = apps.get_model('accounts', 'Profile')
    for user in User.objects.filter(is_superuser=True):
        Profile.objects.get_or_create(user=user, defaults={'role': 'admin'})


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_alter_profile_role'),
    ]

    operations = [
        migrations.RunPython(buat_profile_admin, noop_reverse),
    ]
