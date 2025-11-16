from django.db import migrations

def insert_ejecriterio(apps, schema_editor):

    # Busca el usuario por username (ajusta si el nombre es diferente)
    User = apps.get_model('auth', 'User')
    try:
        creador = User.objects.get(username="_strik_")
    except User.DoesNotExist:
        creador = None

    EjeCriterio = apps.get_model('medicos', 'EjeCriterio')
    data = [
        {
            'tipo': 'Clínico',
            'descripcion': 'Contenido saco',
            'orden': 1,
            'creado_por': creador,
            'actualizado_por': None,
            'creado_en': '2025-10-31',
            'actualizado_en': None,
        },
        {
            'tipo': 'Clínico',
            'descripcion': 'Relación anillo / saco',
            'orden': 2,
            'creado_por': creador,
            'actualizado_por': None,
            'creado_en': '2025-10-31',
            'actualizado_en': None,
        },
        {
            'tipo': 'Clínico',
            'descripcion': 'Hernia gigante (saco > 15cm o anillo > 8cm)',
            'orden': 3,
            'creado_por': creador,
            'actualizado_por': None,
            'creado_en': '2025-10-31',
            'actualizado_en': None,
        },
        {
            'tipo': 'Clínico',
            'descripcion': 'Patología crónica',
            'orden': 4,
            'creado_por': creador,
            'actualizado_por': None,
            'creado_en': '2025-10-31',
            'actualizado_en': None,
        },
        {
            'tipo': 'Social',
            'descripcion': 'Jefe de hogar (sostenedor económico de la familia) y estar incapacitado de trabajar por la condición en que se encuentra / Está al cuidado de niños o personas que no puedan valerse por sí mismas.',
            'orden': 5,
            'creado_por': creador,
            'actualizado_por': None,
            'creado_en': '2025-10-31',
            'actualizado_en': None,
        },
    ]
    for entry in data:
        EjeCriterio.objects.create(**entry)

class Migration(migrations.Migration):
    dependencies = [
        ('medicos', '0010_historialpuntaje_rango_tiempo'),
    ]
    operations = [
        migrations.RunPython(insert_ejecriterio),
    ]
