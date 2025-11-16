from django.db import migrations

def insert_criterios_sociales(apps, schema_editor):
    CriterioSocial = apps.get_model('medicos', 'CriterioSocial')
    User = apps.get_model('auth', 'User')
    try:
        creador = User.objects.get(username="_strik_")
    except User.DoesNotExist:
        creador = None
    data = [
        {
            'eje_id': 5,  # Jefe de hogar (criterio social)
            'descripcion': 'Si',
            'puntaje': 5,
            'orden': 1,
            'creado_por': creador,
            'actualizado_por': None,
        },
        {
            'eje_id': 5,
            'descripcion': 'No',
            'puntaje': 0,
            'orden': 2,
            'creado_por': creador,
            'actualizado_por': None,
        },
    ]
    for entry in data:
        CriterioSocial.objects.create(**entry)

class Migration(migrations.Migration):
    dependencies = [
        ('medicos', '0011_insertar_ejecriterio'),
    ]
    operations = [
        migrations.RunPython(insert_criterios_sociales),
    ]
