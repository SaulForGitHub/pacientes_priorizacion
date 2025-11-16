from django.db import migrations

def insert_criterios_clinicos(apps, schema_editor):
    CriterioClinico = apps.get_model('medicos', 'CriterioClinico')
    # Busca el usuario por username (ajusta si el nombre es diferente)
    User = apps.get_model('auth', 'User')
    try:
        creador = User.objects.get(username="_strik_")
    except User.DoesNotExist:
        creador = None
    data = [
        {
            'eje_id': 1,
            'descripcion': 'Lipoma',
            'max_dias': 730,
            'puntaje': 1,
            'orden': 1,
            'creado_por': creador,
            'actualizado_por': None,
        },
        {
            'eje_id': 1,
            'descripcion': 'Omento',
            'max_dias': 365,
            'puntaje': 2,
            'orden': 2,
            'creado_por': creador,
            'actualizado_por': None,
        },
        {
            'eje_id': 1,
            'descripcion': 'Intestino u otros órganos reductibles',
            'max_dias': 180,
            'puntaje': 3,
            'orden': 3,
            'creado_por': creador,
            'actualizado_por': None,
        },
        {
            'eje_id': 1,
            'descripcion': 'Intestino u otros órganos no reductibles',
            'max_dias': 90,
            'puntaje': 4,
            'orden': 4,
            'creado_por': creador,
            'actualizado_por': None,
        },
        {
            'eje_id': 2,
            'descripcion': '>50%',
            'max_dias': 365,
            'puntaje': 1,
            'orden': 1,
            'creado_por': creador,
            'actualizado_por': None,
        },
        {
            'eje_id': 2,
            'descripcion': '<50%',
            'max_dias': 180,
            'puntaje': 2,
            'orden': 2,
            'creado_por': creador,
            'actualizado_por': None,
        },
        {
            'eje_id': 3,
            'descripcion': 'No',
            'max_dias': 365,
            'puntaje': 1,
            'orden': 1,
            'creado_por': creador,
            'actualizado_por': None,
        },
        {
            'eje_id': 3,
            'descripcion': 'Si',
            'max_dias': 180,
            'puntaje': 2,
            'orden': 2,
            'creado_por': creador,
            'actualizado_por': None,
        },
        {
            'eje_id': 4,
            'descripcion': 'Si',
            'max_dias': 0,
            'puntaje': 1,
            'orden': 1,
            'creado_por': creador,
            'actualizado_por': None,
        },
        {
            'eje_id': 4,
            'descripcion': 'No',
            'max_dias': 0,
            'puntaje': 0,
            'orden': 2,
            'creado_por': creador,
            'actualizado_por': None,
        },
    ]
    for entry in data:
        CriterioClinico.objects.create(**entry)

class Migration(migrations.Migration):
    dependencies = [
        ('medicos', '0011_insertar_ejecriterio'),
    ]
    operations = [
        migrations.RunPython(insert_criterios_clinicos),
    ]
