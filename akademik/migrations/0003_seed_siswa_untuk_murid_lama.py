from django.db import migrations


def buat_siswa_untuk_murid_lama(apps, schema_editor):
    Profile = apps.get_model('accounts', 'Profile')
    Siswa = apps.get_model('akademik', 'Siswa')
    Kelas = apps.get_model('akademik', 'Kelas')

    kelas_default = Kelas.objects.filter(nama='1A').first()

    for profile in Profile.objects.filter(role='murid'):
        Siswa.objects.get_or_create(user=profile.user, defaults={'kelas': kelas_default})


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('akademik', '0002_seed_kelas'),
        ('accounts', '0004_profile_untuk_superuser'),
    ]

    operations = [
        migrations.RunPython(buat_siswa_untuk_murid_lama, noop_reverse),
    ]
