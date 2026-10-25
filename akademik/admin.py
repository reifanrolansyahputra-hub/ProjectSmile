from django.contrib import admin

from .models import Absensi, Kelas, NilaiTugas, OrangTua, Siswa, Tugas


@admin.register(Kelas)
class KelasAdmin(admin.ModelAdmin):
    list_display = ('nama', 'tingkat', 'wali_kelas', 'jumlah_siswa', 'nominal_spp')
    list_filter = ('tingkat',)
    search_fields = ('nama',)
    autocomplete_fields = ('wali_kelas',)
    ordering = ('tingkat', 'nama')


@admin.register(Siswa)
class SiswaAdmin(admin.ModelAdmin):
    list_display = ('nama_lengkap', 'nisn', 'kelas', 'jenis_kelamin', 'aktif')
    list_filter = ('kelas', 'aktif', 'jenis_kelamin')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'nisn')
    autocomplete_fields = ('user', 'kelas')
    list_editable = ('kelas', 'aktif')

    @admin.display(description='Nama')
    def nama_lengkap(self, obj):
        return obj.nama_lengkap


@admin.register(OrangTua)
class OrangTuaAdmin(admin.ModelAdmin):
    list_display = ('user', 'daftar_anak', 'no_hp')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'anak__user__first_name')
    autocomplete_fields = ('user', 'anak')

    @admin.display(description='Anak')
    def daftar_anak(self, obj):
        return ', '.join(a.nama_lengkap for a in obj.anak.all()) or '-'


@admin.register(Absensi)
class AbsensiAdmin(admin.ModelAdmin):
    list_display = ('siswa', 'tanggal', 'status', 'dicatat_oleh')
    list_filter = ('status', 'siswa__kelas', 'tanggal')
    search_fields = ('siswa__user__first_name', 'siswa__user__username')
    autocomplete_fields = ('siswa', 'dicatat_oleh')
    date_hierarchy = 'tanggal'


class NilaiTugasInline(admin.TabularInline):
    model = NilaiTugas
    extra = 0
    autocomplete_fields = ('siswa',)


@admin.register(Tugas)
class TugasAdmin(admin.ModelAdmin):
    list_display = ('judul', 'kelas', 'mapel', 'jenis', 'guru', 'tanggal', 'jumlah_dinilai')
    list_filter = ('kelas', 'mapel', 'jenis')
    search_fields = ('judul',)
    autocomplete_fields = ('kelas', 'guru')
    date_hierarchy = 'tanggal'
    inlines = [NilaiTugasInline]


@admin.register(NilaiTugas)
class NilaiTugasAdmin(admin.ModelAdmin):
    list_display = ('siswa', 'tugas', 'nilai', 'updated_at')
    list_filter = ('tugas__kelas', 'tugas__mapel')
    search_fields = ('siswa__user__first_name', 'tugas__judul')
    autocomplete_fields = ('siswa', 'tugas')
