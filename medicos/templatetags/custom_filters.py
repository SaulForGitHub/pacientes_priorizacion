from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


# Filtro para formatear RUT chileno: 12.345.678-9
@register.filter
def rut_format(value):
    """Formatea un RUT chileno: 12345678-9 -> 12.345.678-9"""
    if not value:
        return ''
    rut = str(value).replace('.', '').replace('-', '')
    if len(rut) < 2:
        return value
    cuerpo = rut[:-1]
    dv = rut[-1]
    cuerpo = cuerpo[::-1]
    partes = [cuerpo[i:i+3] for i in range(0, len(cuerpo), 3)]
    cuerpo_formateado = '.'.join(partes)[::-1]
    return f"{cuerpo_formateado}-{dv}"
