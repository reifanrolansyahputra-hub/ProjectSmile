from django.contrib import admin

from .models import PembayaranSPP, RekeningBank, TagihanSPP


@admin.register(RekeningBank)
class RekeningBankAdmin(admin.ModelAdmin):
    list_display = ('nama_bank', 'nomor_rekening', 'atas_nama', 'aktif')
    list_editable = ('aktif',)
    search_fields = ('nama_bank', 'nomor_rekening', 'atas_nama')


class PembayaranSPPInline(admin.TabularInline):
    model = PembayaranSPP
    extra = 0
    autocomplete_fields = ('dicatat_oleh',)
    readonly_fields = ('created_at',)


@admin.register(TagihanSPP)
class TagihanSPPAdmin(admin.ModelAdmin):
    list_display = ('siswa', 'bulan', 'tahun', 'nominal_tagihan', 'total_dibayar', 'sisa', 'status')
    list_filter = ('tahun', 'bulan', 'siswa__kelas')
    search_fields = ('siswa__user__first_name', 'siswa__user__username')
    autocomplete_fields = ('siswa', 'dibuat_oleh')
    inlines = [PembayaranSPPInline]

    @admin.display(description='Terbayar')
    def total_dibayar(self, obj):
        return f"Rp{obj.total_dibayar:,}".replace(',', '.')

    @admin.display(description='Sisa')
    def sisa(self, obj):
        return f"Rp{obj.sisa:,}".replace(',', '.')

    @admin.display(description='Status')
    def status(self, obj):
        return obj.status


@admin.register(PembayaranSPP)
class PembayaranSPPAdmin(admin.ModelAdmin):
    list_display = ('tagihan', 'jumlah', 'tanggal_bayar', 'dicatat_oleh')
    list_filter = ('tanggal_bayar',)
    search_fields = ('tagihan__siswa__user__first_name',)
    autocomplete_fields = ('tagihan', 'dicatat_oleh')
    date_hierarchy = 'tanggal_bayar'
