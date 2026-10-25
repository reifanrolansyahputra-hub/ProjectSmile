from django.db import migrations


def seed_kelas(apps, schema_editor):
    Kelas = apps.get_model('akademik', 'Kelas')
    for tingkat in range(1, 7):
        for huruf in ('A', 'B'):
            nama = f"{tingkat}{huruf}"
            Kelas.objects.get_or_create(
                nama=nama,
                defaults={'tingkat': tingkat, 'nominal_spp': 300000},
            )


def noop_reverse(apps, schema_editor):
    # Sengaja tidak menghapus data saat migrate di-reverse, supaya kelas yang
    # sudah dipakai (ada siswa/tugas/dsb di dalamnya) tidak hilang tiba-tiba.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('akademik', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_kelas, noop_reverse),
    ]
