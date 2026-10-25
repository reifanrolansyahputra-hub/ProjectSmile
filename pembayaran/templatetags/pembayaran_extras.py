from django import template

register = template.Library()


@register.filter
def rupiah(value):
    """Format angka jadi Rupiah dengan titik ribuan. Contoh: 300000 -> Rp300.000"""
    try:
        angka = int(value)
    except (TypeError, ValueError):
        return value
    return "Rp{:,}".format(angka).replace(',', '.')
