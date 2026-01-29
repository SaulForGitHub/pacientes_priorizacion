
from django.forms import ModelForm
from .models import Paciente
from django import forms
import re

def clean_only_letters(value, message='Solo se permiten letras y espacios.'):
    if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$', value):
        raise forms.ValidationError(message)
    return value

def clean_email(value):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, value):
        raise forms.ValidationError('Ingrese un correo electrónico válido.')
    return value

def validar_rut(rut: str) -> bool:
    """
    Valida un RUT chileno usando el algoritmo Módulo 11.

    Parámetros:
        rut (str): RUT a validar. Puede incluir puntos, guiones o espacios.

    Retorna:
        bool: True si el RUT es válido, False en caso contrario.
    """

    # 1. Limpiar entrada (eliminar puntos, guiones, espacios)
    rut = rut.strip().replace(".", "").replace("-", "").replace(" ", "").upper()

    # 2. Validar formato básico (debe tener al menos 2 caracteres)
    if len(rut) < 2:
        return False

    # 3. Separar cuerpo y dígito verificador
    cuerpo, dv = rut[:-1], rut[-1]

    # 4. Validar que el cuerpo sea numérico
    if not cuerpo.isdigit():
        return False

    # 5. Calcular dígito verificador usando módulo 11
    reversed_digits = map(int, reversed(cuerpo))
    factors = [2, 3, 4, 5, 6, 7]
    total = 0
    factor_index = 0

    for d in reversed_digits:
        total += d * factors[factor_index]
        factor_index = (factor_index + 1) % len(factors)

    remainder = 11 - (total % 11)

    if remainder == 11:
        dv_calculado = "0"
    elif remainder == 10:
        dv_calculado = "K"
    else:
        dv_calculado = str(remainder)

    # 6. Comparar dígitos verificadores
    # return dv == dv_calculado

    if not dv == dv_calculado:
        raise forms.ValidationError('Ingrese un RUT válido.')
    return rut

def clean_phone(value):
    phone_regex = r'^\+?1?\d{9,15}$'
    numeros = [v.strip() for v in value.split(';') if v.strip()]
    for numero in numeros:
        if not re.match(phone_regex, numero):
            raise forms.ValidationError('Ingrese un número de teléfono válido. Puede separar varios números con ";".')
    return value

class CreatePatientForm(ModelForm):

    def clean_nombre(self):
        return clean_only_letters(self.cleaned_data['nombre'], 'Solo se permiten letras y espacios en el nombre.')

    def clean_correo(self):
        return clean_email(self.cleaned_data['correo'])
    
    def clean_rut(self):
        return validar_rut(self.cleaned_data['rut'])
    
    def clean_telefono(self):
        return clean_phone(self.cleaned_data['telefono'])

    class Meta:
        model = Paciente
        fields = [
            'nombre', 'rut', 'fecha_nacimiento', 'telefono', 'correo', 'direccion', 'sexo', 'comentario'
        ]
        error_messages = {
            'nombre': {'required': 'Este campo es obligatorio.'},
            'rut': {'required': 'Este campo es obligatorio.'},
            'fecha_nacimiento': {'required': 'Este campo es obligatorio.'},
            'sexo': {'required': 'Este campo es obligatorio.'},
            'comentario': {'required': 'Este campo es obligatorio.'},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Campos obligatorios
        required_fields = ['nombre', 'rut', 'fecha_nacimiento', 'sexo', 'comentario']
        for field in self.fields:
            self.fields[field].required = field in required_fields

    def clean_correo(self):
        correo = self.cleaned_data.get('correo', '')
        if correo:
            return clean_email(correo)
        return correo

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '')
        if telefono:
            return clean_phone(telefono)
        return telefono

    def clean_direccion(self):
        # No obligatorio, sin validación extra
        return self.cleaned_data.get('direccion', '')

class UpdatePatientForm(ModelForm):

    def clean_nombre(self):
        return clean_only_letters(self.cleaned_data['nombre'], 'Solo se permiten letras y espacios en el nombre.')
    
    def clean_correo(self):
        correo = self.cleaned_data.get('correo', '')
        if correo:
            return clean_email(correo)
        return correo
    
    def clean_rut(self):
        return validar_rut(self.cleaned_data['rut'])
    
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '')
        if telefono:
            return clean_phone(telefono)
        return telefono

    def clean_direccion(self):
        # No obligatorio, sin validación extra
        return self.cleaned_data.get('direccion', '')
    
    class Meta:
        model = Paciente
        fields = [
            'nombre', 'rut', 'fecha_nacimiento', 'telefono', 'correo', 'direccion', 'estado', 'creado_en', 'creado_por', 'actualizado_por', 'sexo', 'comentario'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limitar las opciones del campo estado solo a los choices válidos
        self.fields['estado'].empty_label = None
        self.fields['estado'].required = True
        self.fields['estado'].choices = [
            ('EN_ESPERA', 'En Espera'),
            ('OPERADO', 'Operado'),
        ]
        # Campos obligatorios (creado_en NO debe ser requerido, se setea manualmente en la vista)
        required_fields = ['nombre', 'rut', 'fecha_nacimiento', 'sexo', 'comentario', 'estado']
        for field in self.fields:
            if field in ['telefono', 'correo', 'direccion', 'creado_en']:
                self.fields[field].required = False
            else:
                self.fields[field].required = field in required_fields