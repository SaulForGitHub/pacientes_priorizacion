from django.db import models
import uuid
from django.contrib.auth import get_user_model

# Create your models here.

User = get_user_model()  # Usa el modelo de usuarios configurado en AUTH_USER_MODEL

PACIENTE_ESTADO_CHOICES = [
    ("EN_ESPERA", "En Espera"),
    ("OPERADO", "Operado"),
]

TIPOS_EJE = [
    ("CLINICO", "Clínico"),
    ("SOCIAL", "Social"),
]

PACIENTE_SEXO_CHOICES = [
    ("M", "Mujer"),
    ("H", "Hombre"),
]

class Paciente(models.Model):
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        help_text="Identificador"
    )
    from django.core.validators import RegexValidator
    nombre = models.CharField(
        max_length=255,
        help_text="Nombre",
        validators=[RegexValidator(regex='^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$', message='Solo se permiten letras y espacios en el nombre.')]
    )
    rut = models.CharField(
        max_length=20,
        null=False,
        blank=False,
        help_text="Documento de identidad (RUT/DNI)"
    )
    fecha_nacimiento = models.DateField(
        null=False,
        blank=False,
        help_text="Fecha de nacimiento"
    )
    telefono = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Número de contacto telefónico"
    )
    correo = models.EmailField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Correo electrónico de contacto"
    )
    sexo = models.CharField(
        max_length=1,
        choices=PACIENTE_SEXO_CHOICES,
        null=False,
        blank=False,
        help_text="Sexo del paciente: H para hombre, M para mujer"
    )
    comentario = models.TextField(
        null=True,
        blank=True,
        help_text="Comentario libre sobre el paciente"
    )
    direccion = models.TextField(
        null=True,
        blank=True,
        help_text="Dirección de residencia"
    )
    estado = models.CharField(
        max_length=20,
        choices=PACIENTE_ESTADO_CHOICES,
        null=False,
        blank=True,
        help_text="Estado del paciente: EN_ESPERA o OPERADO",
        default="EN_ESPERA"
    )
    fecha_cambio_estado = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Fecha en que el paciente cambió de estado"
    )
    creado_en = models.DateTimeField(
        help_text="Fecha de creación del registro"
    )
    actualizado_en = models.DateTimeField(
        auto_now=True,
        help_text="Fecha de última actualización del registro"
    )
    eliminado_en = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Fecha soft delete"
    )
    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pacientes_creados",
        help_text="Usuario que creó el registro"
    )
    actualizado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pacientes_actualizados",
        help_text="Usuario que modificó el registro"
    )

    class Meta:
        db_table = "pacientes"
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"

    def __str__(self):
        return f"(Nombre: {self.nombre}) (Rut:{self.rut}) (Estado: {self.estado}) (eliminado_en: {self.eliminado_en})"

class EjeCriterio(models.Model):

    id = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=20, choices=TIPOS_EJE, help_text="Tipo de eje: CLINICO o SOCIAL")
    descripcion = models.TextField(help_text="Nombre del eje, solo enunciado general")
    orden = models.IntegerField(null=True, blank=True, help_text="Orden en que debe desplegarse el eje en la interfaz")
    creado_en = models.DateTimeField(auto_now_add=True, help_text="Fecha de creación del eje de criterios")
    actualizado_en = models.DateTimeField(auto_now=True, help_text="Fecha de última actualización del eje")
    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ejes_creados",
        help_text="Usuario que creó el eje"
    )
    actualizado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ejes_actualizados",
        help_text="Usuario que modificó el eje"
    )

    class Meta:
        db_table = "ejes_criterios"
        verbose_name = "Eje de criterio"
        verbose_name_plural = "Ejes de criterios"

    def __str__(self):
        return f"{self.tipo} - {self.descripcion}"

class CriterioClinico(models.Model):
    id = models.AutoField(primary_key=True)
    eje = models.ForeignKey(
        "EjeCriterio", on_delete=models.CASCADE,
        related_name="criterios_clinicos",
        help_text="FK hacia ejes_criterios.id"
    )
    descripcion = models.TextField(help_text="Descripción del criterio clínico (ej: 'Lipoma')")
    max_dias = models.IntegerField(null=True, blank=True,
                                   help_text="Tiempo máximo aplicable al criterio en días")
    puntaje = models.IntegerField(null=True, blank=True,
                                  help_text="Puntaje asignado al cumplir el criterio")
    orden = models.IntegerField(null=True, blank=True,
                                help_text="Orden dentro del eje en que se debe mostrar el criterio")

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="criterios_clinicos_creados"
    )
    actualizado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="criterios_clinicos_actualizados"
    )

    class Meta:
        db_table = "criterios_clinicos"
        verbose_name = "Criterio clínico"
        verbose_name_plural = "Criterios clínicos"

    def __str__(self):
        return self.descripcion

class CriterioSocial(models.Model):
    id = models.AutoField(primary_key=True)
    eje = models.ForeignKey(
        "EjeCriterio", on_delete=models.CASCADE,
        related_name="criterios_sociales",
        help_text="FK hacia ejes_criterios.id"
    )
    descripcion = models.TextField(help_text="Descripción del criterio social (ej: 'Jefe de hogar incapacitado')")
    puntaje = models.IntegerField(null=True, blank=True)
    orden = models.IntegerField(null=True, blank=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="criterios_sociales_creados"
    )
    actualizado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="criterios_sociales_actualizados"
    )

    class Meta:
        db_table = "criterios_sociales"
        verbose_name = "Criterio social"
        verbose_name_plural = "Criterios sociales"

    def __str__(self):
        return self.descripcion

class RangoTiempo(models.Model):
    id = models.AutoField(primary_key=True)
    descripcion = models.TextField(null=True, blank=True,
                                   help_text="Descripción del rango (ej: '3-4 meses en lista')")
    dias_min = models.IntegerField(null=True, blank=True,
                                   help_text="Cantidad mínima de días en lista para aplicar el rango")
    dias_max = models.IntegerField(null=True, blank=True,
                                   help_text="Cantidad máxima de días en lista para aplicar el rango")
    puntaje = models.IntegerField(null=True, blank=True,
                                  help_text="Puntaje otorgado por permanencia en este rango")

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="rangos_creados"
    )
    actualizado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="rangos_actualizados"
    )

    class Meta:
        db_table = "rangos_tiempo"
        verbose_name = "Rango de tiempo"
        verbose_name_plural = "Rangos de tiempo"

    def __str__(self):
        return self.descripcion or f"Rango {self.id}"

class HistorialPuntaje(models.Model):
    MOTIVOS = [
        ("INGRESO", "Ingreso"),
        ("PERMANENCIA", "Permanencia"),
        ("AJUSTE_CRITERIOS", "Ajuste de criterios"),
        ("CAMBIO_ESTADO", "Cambio de estado"),
        ("MANUAL", "Manual"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False,
                          help_text="Identificador único del registro de historial de puntajes")
    paciente = models.ForeignKey(
        "Paciente", on_delete=models.CASCADE,
        related_name="historial_puntajes",
        help_text="FK hacia pacientes.id"
    )
    fecha_cambio = models.DateTimeField(help_text="Fecha en que se registró el cambio de puntaje")
    puntaje_inicial = models.IntegerField(null=True, blank=True,
                                          help_text="Puntaje por criterios clínicos/sociales en ese momento")
    puntaje_tiempo = models.IntegerField(null=True, blank=True,
                                         help_text="Puntaje por tiempo de permanencia")
    puntaje_total = models.IntegerField(null=True, blank=True,
                                        help_text="Suma de puntaje_inicial + puntaje_tiempo")
    motivo_cambio = models.CharField(max_length=50, choices=MOTIVOS, null=True, blank=True,
                                     help_text="Motivo del cambio")
    rango_tiempo = models.ForeignKey(
        "RangoTiempo", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="historial_puntajes",
        help_text="FK hacia rangos_tiempo.id"
    )

    class Meta:
        db_table = "historial_puntajes"
        verbose_name = "Historial de puntaje"
        verbose_name_plural = "Historial de puntajes"

    def __str__(self):
        return f"{self.paciente.nombre} - {self.motivo_cambio or 'Sin motivo'}"
