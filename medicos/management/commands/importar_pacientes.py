import csv
from django.core.management.base import BaseCommand
from medicos.models import Paciente
from django.contrib.auth import get_user_model
from datetime import datetime

User = get_user_model()

class Command(BaseCommand):
    help = 'Importa pacientes desde un archivo CSV (separado por comas)'

    def add_arguments(self, parser):
        parser.add_argument('archivo', type=str, help='Ruta al archivo CSV')

    def handle(self, *args, **kwargs):
        archivo = kwargs['archivo']
        from medicos.models import HistorialPuntaje, RangoTiempo
        with open(archivo, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                creado_por = User.objects.filter(username=row.get('creado_por')).first() if row.get('creado_por') else None
                actualizado_por = User.objects.filter(username=row.get('actualizado_por')).first() if row.get('actualizado_por') else None

                # Convertir fechas
                fecha_nacimiento = None
                if row.get('fecha_nacimiento'):
                    try:
                        fecha_nacimiento = datetime.strptime(row['fecha_nacimiento'], '%Y-%m-%d').date()
                    except Exception:
                        fecha_nacimiento = None
                creado_en = None
                if row.get('creado_en'):
                    try:
                        creado_en = datetime.strptime(row['creado_en'], '%Y-%m-%d').date()
                    except Exception:
                        creado_en = None

                paciente, created = Paciente.objects.get_or_create(
                    rut=row['rut'],
                    defaults={
                        'nombre': row.get('nombre'),
                        'fecha_nacimiento': fecha_nacimiento,
                        'telefono': row.get('telefono'),
                        'correo': row.get('correo'),
                        'sexo': row.get('sexo'),
                        'comentario': row.get('comentario'),
                        'direccion': row.get('direccion'),
                        'estado': row.get('estado', 'EN_ESPERA'),
                        'creado_en': creado_en,
                        'creado_por': creado_por,
                        'actualizado_por': actualizado_por
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Paciente creado: {paciente}'))
                    # Crear el primer registro de HistorialPuntaje si las columnas existen
                    fecha_cambio = row.get('fecha_cambio')
                    motivo_cambio = row.get('motivo_cambio')
                    puntaje_inicial = row.get('puntaje_inicial')
                    puntaje_tiempo = row.get('puntaje_tiempo')
                    puntaje_total = row.get('puntaje_total')
                    rango_tiempo_id = row.get('rango_tiempo')
                    # Solo crear si hay fecha_cambio y motivo_cambio
                    if fecha_cambio and motivo_cambio:
                        try:
                            fecha_cambio_dt = datetime.strptime(fecha_cambio, '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            fecha_cambio_dt = datetime.strptime(fecha_cambio, '%Y-%m-%d')
                        rango_tiempo = None
                        if rango_tiempo_id:
                            try:
                                rango_tiempo = RangoTiempo.objects.filter(id=int(rango_tiempo_id)).first()
                            except Exception:
                                rango_tiempo = None
                        HistorialPuntaje.objects.create(
                            paciente=paciente,
                            fecha_cambio=fecha_cambio_dt,
                            puntaje_inicial=int(puntaje_inicial) if puntaje_inicial else None,
                            puntaje_tiempo=int(puntaje_tiempo) if puntaje_tiempo else None,
                            puntaje_total=int(puntaje_total) if puntaje_total else None,
                            motivo_cambio=motivo_cambio,
                            rango_tiempo=rango_tiempo
                        )
                        self.stdout.write(self.style.SUCCESS(f'HistorialPuntaje creado para paciente: {paciente}'))
                else:
                    self.stdout.write(self.style.WARNING(f'Paciente ya existe: {paciente}'))
