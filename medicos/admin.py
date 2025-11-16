from django.contrib import admin
from .models import Paciente, EjeCriterio, CriterioClinico, CriterioSocial, RangoTiempo, HistorialPuntaje

# Register your models here.
# admin.site.register(Paciente)

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'actualizado_en')
    fields = (
        'id', 'nombre', 'rut', 'fecha_nacimiento', 'telefono', 'correo', 'sexo', 'comentario',
        'direccion', 'estado', 'fecha_cambio_estado', 'creado_en', 'actualizado_en', 'eliminado_en',
        'creado_por', 'actualizado_por'
    )

@admin.register(EjeCriterio)
class EjeCriterioAdmin(admin.ModelAdmin):
    readonly_fields = ('id','creado_en', 'actualizado_en')

@admin.register(CriterioClinico)
class CriterioClinicoAdmin(admin.ModelAdmin):
    readonly_fields = ('id','creado_en', 'actualizado_en')

@admin.register(CriterioSocial)
class CriterioSocialAdmin(admin.ModelAdmin):
    readonly_fields = ('id','creado_en', 'actualizado_en')

@admin.register(RangoTiempo)
class RangoTiempoAdmin(admin.ModelAdmin):
    readonly_fields = ('id','creado_en', 'actualizado_en')

@admin.register(HistorialPuntaje)
class HistorialPuntajeAdmin(admin.ModelAdmin):
    pass
