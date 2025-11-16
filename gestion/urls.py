"""
URL configuration for gestion project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from medicos import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('patients/waiting/', views.waiting_patients_list, name='waiting_patients_list'),
    path('patients/operated/', views.operated_patients_list, name='operated_patients_list'),
    path('patients/deleted/', views.deleted_patients_list, name='deleted_patients_list'),
    path('patients/create', views.create_patient, name='create_patients'),
    path('rut-exists/', views.rut_exists, name='rut_exists'),
    path('patients/detail/<uuid:patient_id>/', views.detail_patient, name='patient_detail'),
    path('patients/delete/<uuid:patient_id>/', views.delete_patient, name='delete_patient'),
    path('about/', views.about, name='about'),
    path('logout/', views.singout, name='logout'),
    path('signin/', views.signin, name='signin'),
    path('patients/search/', views.search_patient, name='search_patient'),
    path('rangos-tiempo/', views.rangos_tiempo_list, name='rangos_tiempo_list'),
    path('criterios/', views.criterios_list, name='criterios_list'),
]
