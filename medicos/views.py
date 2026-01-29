
from django import template
from django.contrib.auth.decorators import login_required
from datetime import date
import unicodedata
from django import template
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.db import IntegrityError
from django.db.models import Q
from django.utils import timezone
from .forms import CreatePatientForm, UpdatePatientForm
from django.views.decorators.http import require_GET
from .models import (
    CriterioClinico, CriterioSocial, RangoTiempo, Paciente, HistorialPuntaje
)

register = template.Library()

@login_required
def criterios_list(request):
    criterios_clinicos = CriterioClinico.objects.select_related('eje').order_by('eje__orden', 'eje__descripcion', 'orden', 'descripcion')
    criterios_sociales = CriterioSocial.objects.select_related('eje').order_by('eje__orden', 'eje__descripcion', 'orden', 'descripcion')
    return render(request, 'criterios_list.html', {
        'criterios_clinicos': criterios_clinicos,
        'criterios_sociales': criterios_sociales
    })

@login_required
def rangos_tiempo_list(request):
    rangos = RangoTiempo.objects.all().order_by('dias_min', 'dias_max')
    return render(request, 'rangos_tiempo_list.html', {'rangos': rangos})

@login_required
def waiting_patients_list(request):
    """
    Displays a list of patients currently in waiting status.
    
    Args:
        request (HttpRequest): The HTTP request object.
        
    Returns:
        HttpResponse: Renders 'waiting_patients.html' template with a list of patients
                     that have status "EN_ESPERA" and are not soft-deleted,
                     ordered by creation date and name.
    """
    # Recalcular ranking y actualizar historial de puntajes antes de mostrar la lista
    pacientes = Paciente.objects.filter(estado='EN_ESPERA', eliminado_en__isnull=True)
    rangos_tiempo = RangoTiempo.objects.all().order_by('dias_min')
    pacientes_con_puntaje = []
    for paciente in pacientes:
        try:
            puntaje_inicial = 0
            puntaje_total_anterior = 0
            ultimo_puntaje = HistorialPuntaje.objects.filter(paciente=paciente).order_by('-puntaje_total').first()
            if ultimo_puntaje:
                puntaje_inicial = ultimo_puntaje.puntaje_inicial
                puntaje_total_anterior = ultimo_puntaje.puntaje_total
            dias_en_lista = (date.today() - paciente.creado_en.date()).days
            puntaje_total_mostrar = 0
            # Para cada rango de tiempo que el paciente haya superado, crear historial si no existe
            for rango in rangos_tiempo:
                if dias_en_lista >= rango.dias_min:
                    existe_historial = HistorialPuntaje.objects.filter(paciente=paciente, rango_tiempo=rango).exists()
                    if not existe_historial:
                        puntaje_rango = rango.puntaje
                        puntaje_total = puntaje_inicial + puntaje_rango
                        HistorialPuntaje.objects.create(
                            paciente=paciente,
                            fecha_cambio=date.today(),
                            puntaje_inicial=puntaje_inicial,
                            puntaje_tiempo=puntaje_rango,
                            puntaje_total=puntaje_total,
                            motivo_cambio='PERMANENCIA',
                            rango_tiempo=rango
                        )
                        puntaje_inicial = puntaje_total  # Acumula para el siguiente rango
            # Obtener el puntaje total más reciente para mostrar y ordenar
            ultimo_puntaje = HistorialPuntaje.objects.filter(paciente=paciente).order_by('-puntaje_total').first()
            puntaje_total_mostrar = ultimo_puntaje.puntaje_total if ultimo_puntaje else 0
            pacientes_con_puntaje.append({
                'paciente': paciente,
                'puntaje_total': puntaje_total_mostrar
            })
        except Exception:
            pacientes_con_puntaje.append({
                'paciente': paciente,
                'puntaje_total': 0
            })
    # Ordenar por puntaje total descendente
    pacientes_con_puntaje.sort(key=lambda x: x['puntaje_total'], reverse=True)

    return render(request, 'waiting_patients.html', {
        'patients': [p['paciente'] for p in pacientes_con_puntaje],
        'puntajes': {p['paciente'].id: p['puntaje_total'] for p in pacientes_con_puntaje}
    })

@login_required
def operated_patients_list(request):
    """
    Displays a list of patients who have been operated on.
    Args:
        request (HttpRequest): The HTTP request object.        
    Returns:
        HttpResponse: Renders 'operated_patients.html' template with a list of patients
        that have status "OPERADO" and are not soft-deleted,
        ordered by creation date and name.
    """
    operated_patients = Paciente.objects.filter(estado="OPERADO", eliminado_en__isnull=True).order_by('creado_en', 'nombre')
    return render(request, 'operated_patients.html', {
        'patients': operated_patients
    })

@login_required
def deleted_patients_list(request):
    """
    Displays a list of patients who have been soft-deleted.
    Args:
        request (HttpRequest): The HTTP request object.
    Returns:
        HttpResponse: Renders 'deleted_patients.html' template with a list of patients
                     that have been soft-deleted, ordered by deletion date and name.
    """
    deleted_patients = Paciente.objects.filter(eliminado_en__isnull=False).order_by('eliminado_en', 'nombre')
    return render(request, 'deleted_patients.html', {
        'patients': deleted_patients
    })

def normalize_text(text):
    """
    Normalizes text by removing accents and converting to lowercase.
    Args:
        text (str): The input text to be normalized.
        Returns:
        str: The normalized text.
    """
    if not text:
        return ''
    text = unicodedata.normalize('NFKD', text)
    text = ''.join([c for c in text if not unicodedata.combining(c)])
    return text.lower()

@require_GET
def rut_exists(request):
    rut = request.GET.get('rut', '').strip()
    paciente = Paciente.objects.filter(rut__iexact=rut).first()
    if paciente:
        return JsonResponse({'exists': True, 'id': str(paciente.id)})
    else:
        return JsonResponse({'exists': False})

@login_required
def ranking_patients(request):
    from .models import Paciente, HistorialPuntaje, RangoTiempo

    # obtener todos los pacientes en con estado EN_ESPERA y no desestimados
    pacientes = Paciente.objects.filter(estado='EN_ESPERA', eliminado_en__isnull=True)

    # obtener todos los rangos de tiempo ordenados por dias_min ascendente
    rangos_tiempo = RangoTiempo.objects.all().order_by('dias_min')

    pacientes_no_actualizados = []
    errores = []

    for paciente in pacientes:
        try:
            puntaje_inicial = 0
            puntaje_total_anterior = 0
            ultimo_puntaje = HistorialPuntaje.objects.filter(paciente=paciente).order_by('-fecha_cambio').first()
            if ultimo_puntaje:
                puntaje_inicial = ultimo_puntaje.puntaje_inicial
                puntaje_total_anterior = ultimo_puntaje.puntaje_total

            dias_en_lista = (date.today() - paciente.creado_en.date()).days

            puntaje_rango = 0
            puntaje_total = 0
            rango_identificado = False
            rango_seleccionado = None
            for rango in rangos_tiempo:
                if dias_en_lista >= rango.dias_min and dias_en_lista <= rango.dias_max:
                    rango_identificado = True
                    puntaje_rango = rango.puntaje
                    puntaje_total = puntaje_inicial + puntaje_rango
                    rango_seleccionado = rango
                    break

            if rango_identificado and rango_seleccionado:
                # Verificar si ya existe un historial para este paciente y rango
                existe_historial = HistorialPuntaje.objects.filter(
                    paciente=paciente,
                    rango_tiempo=rango_seleccionado
                ).exists()
                if not existe_historial:
                    nuevo_historial = HistorialPuntaje(
                        paciente=paciente,
                        fecha_cambio=date.today(),
                        puntaje_inicial=puntaje_total_anterior,
                        puntaje_tiempo=puntaje_rango,
                        puntaje_total=puntaje_total,
                        motivo_cambio='PERMANENCIA',
                        rango_tiempo=rango_seleccionado
                    )
                    nuevo_historial.save()
            else:
                pacientes_no_actualizados.append(f"{paciente.nombre} - {paciente.rut}")
        except Exception as e:
            errores.append(f"{paciente.nombre} - {paciente.rut}: {str(e)}")

    mensaje = 'Puntajes actualizados correctamente.'
    if pacientes_no_actualizados:
        mensaje = f'Puntajes actualizados. Pacientes no actualizados: {", ".join(pacientes_no_actualizados)}'
    if errores:
        mensaje += f' Errores: {"; ".join(errores)}'

    return render(request, 'waiting_patients.html', {
        'message': mensaje
    })

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@login_required
def rangos_tiempo_list(request):
    rangos = RangoTiempo.objects.all().order_by('dias_min', 'dias_max')
    return render(request, 'rangos_tiempo_list.html', {'rangos': rangos})
from django.shortcuts import render, redirect # to render templates and redirect users
from django.http import HttpResponse # to return simple HTTP responses
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm # built-in form for user registration
from django.contrib.auth.models import User # built-in user model
from django.contrib.auth import login, logout, authenticate # create a session for the user
from django.db import IntegrityError # handle database errors
from .forms import CreatePatientForm, UpdatePatientForm
from .models import Paciente, HistorialPuntaje
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import date
import unicodedata

# ******************************* OPERACIONES BÁSICAS *******************************


def home(request):
    """
    Renders the home page of the medical application.
    """
    from django.utils import timezone
    from datetime import timedelta
    pacientes_espera_qs = Paciente.objects.filter(estado='EN_ESPERA', eliminado_en__isnull=True)
    pacientes_espera_count = pacientes_espera_qs.count()
    # Calcular tiempo promedio en espera (en días)
    if pacientes_espera_count > 0:
        total_dias = 0
        today = timezone.now().date()
        for paciente in pacientes_espera_qs:
            dias_espera = (today - paciente.creado_en.date()).days
            total_dias += dias_espera
        promedio_espera = round(total_dias / pacientes_espera_count)
    else:
        promedio_espera = 0
    # Pacientes operados en el último mes
    from datetime import timedelta
    today = timezone.now().date()
    hace_un_mes = today - timedelta(days=30)
    operados_mes_count = Paciente.objects.filter(
        estado="OPERADO",
        fecha_cambio_estado__isnull=False,
        fecha_cambio_estado__date__gte=hace_un_mes,
        fecha_cambio_estado__date__lte=today
    ).count()
    # Promedio de puntaje de pacientes en espera
    from medicos.models import HistorialPuntaje
    puntajes = []
    for paciente in pacientes_espera_qs:
        historial = paciente.historial_puntajes.order_by('-fecha_cambio').first()
        if historial and historial.puntaje_total is not None:
            puntajes.append(historial.puntaje_total)
    if puntajes:
        promedio_puntaje = round(sum(puntajes) / len(puntajes), 1)
    else:
        promedio_puntaje = 0
    return render(request, 'home.html', {
        'pacientes_espera_count': pacientes_espera_count,
        'promedio_espera': promedio_espera,
        'operados_mes_count': operados_mes_count,
        'promedio_puntaje': promedio_puntaje
    })

@login_required
def about(request):
    """
    Renders the about page with project information.
    """
    return render(request, 'about.html')

@login_required
def signup(request):
    """
    Handles user registration for the medical application.
    
    Args:
        request (HttpRequest): The HTTP request object.
        
    Returns:
        HttpResponse: 
            - GET: Renders signup form
            - POST: Creates new user and redirects to patients page on success,
                   or renders form with error message on failure
    
    Raises:
        IntegrityError: When username already exists in database
    """
    # POST request, process form data
    if request.method == 'POST':
        if request.POST['password1'] == request.POST['password2']:
            try:
                user = User.objects.create_user(
                    username=request.POST['username'],
                    password=request.POST['password1']
                )
                user.save()
                # if successful, redirect to home or login page
                # return HttpResponse('User created successfully')
                login(request, user)  # log the user in
                return redirect('waiting_patients_list')
            except IntegrityError:
                return render(request, 'signup.html', {
                    'form': UserCreationForm,
                    'message': 'Username already exists'
                })
        else:
            return render(request, 'signup.html', {
                'form': UserCreationForm,
                'message': 'Passwords do not match'
            })
    else:
        # GET request, return the signup form
        return render(request, 'signup.html', {
            'form': UserCreationForm
        })

@login_required
def singout(request):
    """
    Logs out the current user from the medical application.
    Args:
        request (HttpRequest): The HTTP request object.
    Returns:
        HttpResponse: Renders the 'logout.html' template after logging out the user.
    """
    logout(request)
    return render(request, 'logout.html')


def signin(request):
    """
    Handles user authentication and login.
    
    Args:
        request (HttpRequest): The HTTP request object.
        
    Returns:
        HttpResponse:
            - GET: Renders login form
            - POST: Authenticates user and redirects to waiting patients list on success,
                   or renders form with error message on failure
    """
    if request.method == 'GET':
        return render(request, 'signin.html', {
            'form': AuthenticationForm
        })
    else:
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user is None:
            return render(request, 'signin.html', {
                'form': AuthenticationForm,
                'message': 'Nombre de usuario o contraseña incorrecta'
            })
        else:
            login(request, user) # save session 
            return redirect('home')        

# ******************************* OPERACIONES BÁSICAS *******************************


# ******************************* INICIO LISTADOS *******************************

@login_required
def waiting_patients_list(request):
    """
    Displays a list of patients currently in waiting status.
    
    Args:
        request (HttpRequest): The HTTP request object.
        
    Returns:
        HttpResponse: Renders 'waiting_patients.html' template with a list of patients
                     that have status "EN_ESPERA" and are not soft-deleted,
                     ordered by creation date and name.
    """
    # Recalcular ranking y actualizar historial de puntajes antes de mostrar la lista
    from .models import RangoTiempo
    pacientes = Paciente.objects.filter(estado='EN_ESPERA', eliminado_en__isnull=True)
    rangos_tiempo = RangoTiempo.objects.all().order_by('dias_min')
    pacientes_con_puntaje = []
    for paciente in pacientes:
        try:
            puntaje_inicial = 0
            puntaje_total_anterior = 0
            ultimo_puntaje = HistorialPuntaje.objects.filter(paciente=paciente).order_by('-puntaje_total').first()
            if ultimo_puntaje:
                puntaje_inicial = ultimo_puntaje.puntaje_inicial
                puntaje_total_anterior = ultimo_puntaje.puntaje_total
            dias_en_lista = (date.today() - paciente.creado_en.date()).days
            puntaje_total_mostrar = 0
            # Para cada rango de tiempo que el paciente haya superado, crear historial si no existe
            for rango in rangos_tiempo:
                if dias_en_lista >= rango.dias_min:
                    existe_historial = HistorialPuntaje.objects.filter(paciente=paciente, rango_tiempo=rango).exists()
                    if not existe_historial:
                        puntaje_rango = rango.puntaje
                        puntaje_total = puntaje_inicial + puntaje_rango
                        HistorialPuntaje.objects.create(
                            paciente=paciente,
                            fecha_cambio=date.today(),
                            puntaje_inicial=puntaje_inicial,
                            puntaje_tiempo=puntaje_rango,
                            puntaje_total=puntaje_total,
                            motivo_cambio='PERMANENCIA',
                            rango_tiempo=rango
                        )
                        puntaje_inicial = puntaje_total  # Acumula para el siguiente rango
            # Obtener el puntaje total más reciente para mostrar y ordenar
            ultimo_puntaje = HistorialPuntaje.objects.filter(paciente=paciente).order_by('-puntaje_total').first()
            puntaje_total_mostrar = ultimo_puntaje.puntaje_total if ultimo_puntaje else 0
            pacientes_con_puntaje.append({
                'paciente': paciente,
                'puntaje_total': puntaje_total_mostrar
            })
        except Exception:
            pacientes_con_puntaje.append({
                'paciente': paciente,
                'puntaje_total': 0
            })
    # Ordenar por puntaje total descendente
    pacientes_con_puntaje.sort(key=lambda x: x['puntaje_total'], reverse=True)

    return render(request, 'waiting_patients.html', {
        'patients': [p['paciente'] for p in pacientes_con_puntaje],
        'puntajes': {p['paciente'].id: p['puntaje_total'] for p in pacientes_con_puntaje}
    })


@login_required
def operated_patients_list(request):
    """
    Displays a list of patients who have been operated on.
    Args:
        request (HttpRequest): The HTTP request object.
        
    Returns:
        HttpResponse: Renders 'operated_patients.html' template with a list of patients
                     that have status "OPERADO" and are not soft-deleted,
                     ordered by creation date and name.
    """
    operated_patients = Paciente.objects.filter(estado="OPERADO", eliminado_en__isnull=True).order_by('creado_en', 'nombre')
    return render(request, 'operated_patients.html', {
        'patients': operated_patients
    })


@login_required
def deleted_patients_list(request):
    """
    Displays a list of patients who have been soft-deleted.
    Args:
        request (HttpRequest): The HTTP request object.
    Returns:
        HttpResponse: Renders 'deleted_patients.html' template with a list of patients
                     that have been soft-deleted, ordered by deletion date and name.
    """
    deleted_patients = Paciente.objects.filter(eliminado_en__isnull=False).order_by('eliminado_en', 'nombre')
    return render(request, 'deleted_patients.html', {
        'patients': deleted_patients
    })

# ****************************** FIN LISTADOS *******************************


# ******************************* CRUD PACIENTES *******************************

@login_required
def create_patient(request):
    """
        Handles the creation of a new patient record.
        Args:
            request (HttpRequest): The HTTP request object.

            Returns:
                HttpResponse: 
                    - GET: Renders patient creation form with clinical and social criteria
                    - POST: Creates new patient record, calculates initial scores,
                            saves score history, and redirects to patients list on success,
                            or renders form with error messages on failure
    """
    from .models import CriterioClinico, CriterioSocial
    criterios_clinicos = CriterioClinico.objects.select_related('eje').order_by('eje__orden', 'eje__descripcion', 'orden', 'descripcion')
    criterios_sociales = CriterioSocial.objects.select_related('eje').order_by('eje__orden', 'eje__descripcion', 'orden', 'descripcion')

    if request.method == 'GET':
        anios = range(date.today().year, date.today().year - 120, -1)
        meses = range(1, 13)
        dias = range(1, 32)
        return render(request, 'create_patient.html', {
            'form': CreatePatientForm,
            'criterios_clinicos': criterios_clinicos,
            'criterios_sociales': criterios_sociales,
            'anios': anios,
            'meses': meses,
            'dias': dias
        })
    else:
        # Armar fecha de nacimiento desde los selects
        anio = request.POST.get('anio')
        mes = request.POST.get('mes')
        dia = request.POST.get('dia')
        fecha_nacimiento = None
        if anio and mes and dia:
            try:
                fecha_nacimiento = f"{anio.zfill(4)}-{mes.zfill(2)}-{dia.zfill(2)}"
                request.POST = request.POST.copy()
                request.POST['fecha_nacimiento'] = fecha_nacimiento
            except Exception:
                pass

        
        form = CreatePatientForm(request.POST)

        anios = range(date.today().year, date.today().year - 120, -1)
        meses = range(1, 13)
        dias = range(1, 32)

        # Validaciones personalizadas
        errores = []
        campos_obligatorios = ['nombre', 'rut',]
        for campo in campos_obligatorios:
            if not request.POST.get(campo):
                errores.append(f"El campo '{campo}' es obligatorio.")

        # Validar fecha de nacimiento
        anio = request.POST.get('anio')
        mes = request.POST.get('mes')
        dia = request.POST.get('dia')
        if not (anio and mes and dia):
            errores.append("Debe seleccionar una fecha de nacimiento completa.")
        else:
            try:
                fecha_nacimiento = f"{anio.zfill(4)}-{mes.zfill(2)}-{dia.zfill(2)}"
                request.POST = request.POST.copy()
                request.POST['fecha_nacimiento'] = fecha_nacimiento
            except Exception:
                errores.append("La fecha de nacimiento es inválida.")

        anio_creado = request.POST.get('anio_creado')
        mes_creado = request.POST.get('mes_creado')
        dia_creado = request.POST.get('dia_creado')
        if not (anio_creado and mes_creado and dia_creado):
            errores.append("Debe seleccionar una fecha de creación.")
        else:
            try:
                fecha_creacion = f"{anio_creado.zfill(4)}-{mes_creado.zfill(2)}-{dia_creado.zfill(2)}"
                request.POST = request.POST.copy()
                request.POST['fecha_creacion'] = fecha_creacion
            except Exception:
                errores.append("La fecha de creación es inválida.")

        # Validar selección de criterios por eje
        ejes_clinicos_ids = set(criterio.eje.id for criterio in criterios_clinicos)
        ejes_sociales_ids = set(criterio.eje.id for criterio in criterios_sociales)
        for eje_id in ejes_clinicos_ids:
            if not request.POST.get(f'criterio_clinico_{eje_id}'):
                errores.append(f"Debe seleccionar un criterio en el eje clínico {eje_id}.")
        for eje_id in ejes_sociales_ids:
            if not request.POST.get(f'criterio_social_{eje_id}'):
                errores.append(f"Debe seleccionar un criterio en el eje social {eje_id}.")

        # Validar el formulario Django
        if not form.is_valid():
            for field, field_errors in form.errors.items():
                for error in field_errors:
                    errores.append(f"{field}: {error}")

        if errores:
            return render(request, 'create_patient.html', {
                'form': form,
                'message': ' '.join(errores),
                'criterios_clinicos': criterios_clinicos,
                'criterios_sociales': criterios_sociales,
                'anios': anios,
                'meses': meses,
                'dias': dias
            })
        else:

            # Sumar puntajes seleccionados por el usuario para cada eje
            puntaje_por_tiempo = 0  # Inicialmente es 0 al crear el paciente
            total_puntaje_social = 0
            suma_total_criterios = 0
            total_puntaje_clinico = 0

            # Para cada eje clínico, busca el valor seleccionado (si existe) y suma
            ejes_clinicos_ids = set(criterio.eje.id for criterio in criterios_clinicos)
            for eje_id in ejes_clinicos_ids:
                puntaje = request.POST.get(f'criterio_clinico_{eje_id}')
                if puntaje:
                    try:
                        total_puntaje_clinico += int(puntaje)
                    except ValueError:
                        pass

            # Para cada eje social, busca el valor seleccionado (si existe) y suma
            ejes_sociales_ids = set(criterio.eje.id for criterio in criterios_sociales)
            for eje_id in ejes_sociales_ids:
                puntaje = request.POST.get(f'criterio_social_{eje_id}')
                if puntaje:
                    try:
                        total_puntaje_social += int(puntaje)
                    except ValueError:
                        pass

            # print(f"Total puntaje clínico seleccionado: {total_puntaje_clinico}")
            # print(f"Total puntaje social seleccionado: {total_puntaje_social}")
            suma_total_criterios = total_puntaje_clinico + total_puntaje_social
            
            try:
                primer_rango = RangoTiempo.objects.all().order_by('dias_min').first()
                paciente = form.save(commit=False)
                paciente.creado_por = request.user
                from django.utils import timezone
                paciente.creado_en = fecha_creacion
                paciente.save()

                # guardar historial de puntajes
                historial = HistorialPuntaje(
                    paciente=paciente, # objeto paciente directamente, sin id o uuid
                    fecha_cambio=date.today(),
                    puntaje_inicial=suma_total_criterios,
                    puntaje_tiempo=puntaje_por_tiempo,
                    puntaje_total=suma_total_criterios + puntaje_por_tiempo,
                    motivo_cambio="INGRESO",
                    rango_tiempo=primer_rango
                )
                historial.save()

                return redirect('waiting_patients_list')
            
            except ValueError:
                return render(request, 'create_patient.html', {
                    'form': form,
                    'message': form.errors, # muestra errores de validación
                    'criterios_clinicos': criterios_clinicos,
                    'criterios_sociales': criterios_sociales
                })

@login_required
def delete_patient(request, patient_id):
    """
    Deletes (soft delete) a patient record by setting the deletion timestamp.
    Args:
        request (HttpRequest): The HTTP request object.
        patient_id (UUID): The unique identifier of the patient to be deleted.
    Returns:
        HttpResponse: Redirects to the waiting patients list after deletion.
    """
    # hard delete...    
    # if request.method == 'POST':
        # paciente_encontrado = get_object_or_404(Paciente, pk=patient_id)
        # paciente_encontrado.delete()
        # return redirect('waiting_patients_list')

    # soft delete...
    if request.method == 'POST':
        paciente_encontrado = get_object_or_404(Paciente, pk=patient_id)
        paciente_encontrado.eliminado_en = timezone.now()
        paciente_encontrado.save()
        return redirect('waiting_patients_list')
    
@login_required
def detail_patient(request, patient_id):
    """
    Displays and updates details of a specific patient.
    Args:
        request (HttpRequest): The HTTP request object.
        patient_id (UUID): The unique identifier of the patient to be viewed.
    Returns:
        HttpResponse: Renders the patient detail page with the patient's information.
    """
    if request.method == 'GET':
        paciente_encontrado = get_object_or_404(Paciente, pk=patient_id)
        form = UpdatePatientForm(instance=paciente_encontrado)
        anios = range(date.today().year, date.today().year - 120, -1)
        meses = range(1, 13)
        dias = range(1, 32)
        historial_puntajes = HistorialPuntaje.objects.filter(paciente=paciente_encontrado).order_by('-puntaje_total')
        from_list = request.GET.get('from_list', None)
        return render(request, 'detail_patient.html', {
            'patient': paciente_encontrado,
            'form': form,
            'anios': anios,
            'meses': meses,
            'dias': dias,
            'historial_puntajes': historial_puntajes,
            'from_list': from_list
        })
    else:
        paciente_encontrado = get_object_or_404(Paciente, pk=patient_id)
        estado_anterior = paciente_encontrado.estado

        anios = range(date.today().year, date.today().year - 120, -1)
        meses = range(1, 13)
        dias = range(1, 32)
        historial_puntajes = HistorialPuntaje.objects.filter(paciente=paciente_encontrado).order_by('-puntaje_total')

        errores = []

        # Validar fecha de nacimiento
        anio = request.POST.get('anio')
        mes = request.POST.get('mes')
        dia = request.POST.get('dia')
        if not (anio and mes and dia):
            errores.append("Debe seleccionar una fecha de nacimiento completa.")
        else:
            try:
                fecha_nacimiento = f"{anio.zfill(4)}-{mes.zfill(2)}-{dia.zfill(2)}"
                request.POST = request.POST.copy()
                request.POST['fecha_nacimiento'] = fecha_nacimiento
            except Exception:
                errores.append("La fecha de nacimiento es inválida.")

        # Validar fecha de creación
        anio_creado = request.POST.get('anio_creado')
        mes_creado = request.POST.get('mes_creado')
        dia_creado = request.POST.get('dia_creado')
        if not (anio_creado and mes_creado and dia_creado and anio_creado.strip() and mes_creado.strip() and dia_creado.strip()):
            errores.append("Debe seleccionar una fecha de creación completa.")
        else:
            try:
                fecha_creado = f"{str(anio_creado).zfill(4)}-{str(mes_creado).zfill(2)}-{str(dia_creado).zfill(2)} 00:00"
                request.POST = request.POST.copy()
                request.POST['creado_en'] = fecha_creado
            except Exception:
                errores.append("La fecha de creación es inválida.")

        campos_obligatorios = ['nombre', 'rut', 'estado', 'creado_en']
        for campo in campos_obligatorios:
            valor = request.POST.get(campo)
            if not valor:
                errores.append(f"El campo '{campo}' es obligatorio.")
            if campo == 'estado' and valor not in ['EN_ESPERA', 'OPERADO']:
                errores.append("El estado seleccionado no es válido.")

        form = UpdatePatientForm(request.POST, instance=paciente_encontrado)
        if not form.is_valid():
            for field, field_errors in form.errors.items():
                for error in field_errors:
                    errores.append(f"{field}: {error}")

        if errores:
            return render(request, 'detail_patient.html', {
                'patient': paciente_encontrado,
                'form': form,
                'anios': anios,
                'meses': meses,
                'dias': dias,
                'historial_puntajes': historial_puntajes,
                'message': ' '.join(errores)
            })
        else:
            nuevo_estado = form.cleaned_data['estado']
            paciente_actualizado = form.save(commit=False)
            if estado_anterior != nuevo_estado:
                paciente_actualizado.fecha_cambio_estado = timezone.now()
            paciente_actualizado.actualizado_por = request.user
            paciente_actualizado.actualizado_en = timezone.now()
            paciente_actualizado.creado_en = form.cleaned_data['creado_en']
            paciente_actualizado.save()
            return redirect('waiting_patients_list')

def normalize_text(text):
    """
    Normalizes text by removing accents and converting to lowercase.
    Args:
        text (str): The input text to be normalized.
        Returns:
        str: The normalized text.
    """
    if not text:
        return ''
    text = unicodedata.normalize('NFKD', text)
    text = ''.join([c for c in text if not unicodedata.combining(c)])
    return text.lower()

@login_required
def search_patient(request):
    """
     Handles searching for patients based on various criteria.
    Args:
        request (HttpRequest): The HTTP request object.
        Returns:
        HttpResponse: Renders the search results page with matching patients
    """
    paciente = None
    historial_puntajes = []
    pacientes = []
    form = None
    searched = False
    anios = range(date.today().year, date.today().year - 120, -1)
    meses = range(1, 13)
    dias = range(1, 32)
    if request.method == 'GET' and request.GET.get('search_value'):
        search_field = request.GET.get('search_field')
        search_value = request.GET.get('search_value')
        estado_field = request.GET.get('estado_field')
        selected_id = request.GET.get('selected_id')
        searched = True
        filtro = Q(eliminado_en__isnull=True)
        if search_field == 'rut':
            filtro &= Q(rut__icontains=search_value)
        elif search_field == 'nombre':
            # Búsqueda flexible: primero filtra por icontains, luego normaliza en Python
            posibles = Paciente.objects.filter(filtro & Q(nombre__icontains=search_value))
            search_norm = normalize_text(search_value)
            pacientes = [p for p in posibles if search_norm in normalize_text(p.nombre)]
        elif search_field == 'email':
            filtro &= Q(correo__icontains=search_value)
        if search_field != 'nombre':
            if estado_field and estado_field != 'todos':
                filtro &= Q(estado=estado_field)
            pacientes = list(Paciente.objects.filter(filtro))
        else:
            if estado_field and estado_field != 'todos':
                pacientes = [p for p in pacientes if p.estado == estado_field]
        if len(pacientes) == 1 or selected_id:
            if selected_id:
                paciente = next((p for p in pacientes if str(p.id) == selected_id), None)
            else:
                paciente = pacientes[0]
            if paciente:
                from .forms import UpdatePatientForm
                form = UpdatePatientForm(instance=paciente)
                historial_puntajes = HistorialPuntaje.objects.filter(paciente=paciente).order_by('-fecha_cambio')
    elif request.method == 'POST' and paciente:
        # Armar fecha de nacimiento desde los selects
        anio = request.POST.get('anio')
        mes = request.POST.get('mes')
        dia = request.POST.get('dia')
        fecha_nacimiento = None
        if anio and mes and dia:
            try:
                fecha_nacimiento = f"{anio.zfill(4)}-{mes.zfill(2)}-{dia.zfill(2)}"
                request.POST = request.POST.copy()
                request.POST['fecha_nacimiento'] = fecha_nacimiento
            except Exception:
                pass
        from .forms import UpdatePatientForm
        # Guardar estado anterior para comparar

        estado_anterior = paciente.estado
        form = UpdatePatientForm(request.POST, instance=paciente)
        if form.is_valid():
            paciente_actualizado = form.save(commit=False)

            # Si el estado cambió, actualizar la fecha de cambio de estado
            if estado_anterior != paciente_actualizado.estado:
                paciente_actualizado.fecha_cambio_estado = timezone.now()
            paciente_actualizado.actualizado_por = request.user
            paciente_actualizado.actualizado_en = timezone.now()
            paciente_actualizado.save()
            historial_puntajes = HistorialPuntaje.objects.filter(paciente=paciente_actualizado).order_by('-fecha_cambio')
            pacientes = [paciente_actualizado]
            return render(request, 'search_patient.html', {
                'paciente': paciente_actualizado,
                'pacientes': pacientes,
                'form': form,
                'historial_puntajes': historial_puntajes,
                'searched': True,
                'anios': anios,
                'meses': meses,
                'dias': dias,
                'message': 'Paciente actualizado correctamente.'
            })
        else:
            historial_puntajes = HistorialPuntaje.objects.filter(paciente=paciente).order_by('-fecha_cambio')
            return render(request, 'search_patient.html', {
                'paciente': paciente,
                'pacientes': pacientes,
                'form': form,
                'historial_puntajes': historial_puntajes,
                'searched': True,
                'anios': anios,
                'meses': meses,
                'dias': dias,
                'message': 'Error al actualizar el paciente.'
            })
    return render(request, 'search_patient.html', {
        'paciente': paciente,
        'pacientes': pacientes,
        'form': form,
        'historial_puntajes': historial_puntajes,
        'searched': searched,
        'anios': anios,
        'meses': meses,
        'dias': dias
    })

# ******************************* CRUD PACIENTES *******************************

# ******************************* OPERACIONES SOBRE PACIENTES *******************************




@require_GET
def rut_exists(request):
    rut = request.GET.get('rut', '').strip()
    paciente = Paciente.objects.filter(rut__iexact=rut).first()
    if paciente:
        return JsonResponse({'exists': True, 'id': str(paciente.id)})
    else:
        return JsonResponse({'exists': False})

@login_required
def ranking_patients(request):
    from .models import Paciente, HistorialPuntaje, RangoTiempo

    # obtener todos los pacientes en con estado EN_ESPERA y no desestimados
    pacientes = Paciente.objects.filter(estado='EN_ESPERA', eliminado_en__isnull=True)

    # obtener todos los rangos de tiempo ordenados por dias_min ascendente
    rangos_tiempo = RangoTiempo.objects.all().order_by('dias_min')

    pacientes_no_actualizados = []
    errores = []

    for paciente in pacientes:
        try:
            puntaje_inicial = 0
            puntaje_total_anterior = 0
            ultimo_puntaje = HistorialPuntaje.objects.filter(paciente=paciente).order_by('-fecha_cambio').first()
            if ultimo_puntaje:
                puntaje_inicial = ultimo_puntaje.puntaje_inicial
                puntaje_total_anterior = ultimo_puntaje.puntaje_total

            dias_en_lista = (date.today() - paciente.creado_en.date()).days

            puntaje_rango = 0
            puntaje_total = 0
            rango_identificado = False
            rango_seleccionado = None
            for rango in rangos_tiempo:
                if dias_en_lista >= rango.dias_min and dias_en_lista <= rango.dias_max:
                    rango_identificado = True
                    puntaje_rango = rango.puntaje
                    puntaje_total = puntaje_inicial + puntaje_rango
                    rango_seleccionado = rango
                    break

            if rango_identificado and rango_seleccionado:
                # Verificar si ya existe un historial para este paciente y rango
                existe_historial = HistorialPuntaje.objects.filter(
                    paciente=paciente,
                    rango_tiempo=rango_seleccionado
                ).exists()
                if not existe_historial:
                    nuevo_historial = HistorialPuntaje(
                        paciente=paciente,
                        fecha_cambio=date.today(),
                        puntaje_inicial=puntaje_total_anterior,
                        puntaje_tiempo=puntaje_rango,
                        puntaje_total=puntaje_total,
                        motivo_cambio='PERMANENCIA',
                        rango_tiempo=rango_seleccionado
                    )
                    nuevo_historial.save()
            else:
                pacientes_no_actualizados.append(f"{paciente.nombre} - {paciente.rut}")
        except Exception as e:
            errores.append(f"{paciente.nombre} - {paciente.rut}: {str(e)}")

    mensaje = 'Puntajes actualizados correctamente.'
    if pacientes_no_actualizados:
        mensaje = f'Puntajes actualizados. Pacientes no actualizados: {", ".join(pacientes_no_actualizados)}'
    if errores:
        mensaje += f' Errores: {"; ".join(errores)}'

    return render(request, 'waiting_patients.html', {
        'message': mensaje
    })




    

    

# ******************************* OPERACIONES SOBRE PACIENTES *******************************
