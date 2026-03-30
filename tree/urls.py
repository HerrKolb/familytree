from django.urls import path
from . import views
from .csv_import import csv_import as csv_import_view

urlpatterns = [
    path('',                               views.dashboard,           name='dashboard'),
    path('stammbaum/',                     views.tree_view,            name='tree'),
    path('stammbaum/daten/',               views.tree_data,            name='tree_data'),
    path('personen/',                      views.person_list,          name='person_list'),
    path('personen/neu/',                  views.person_create,        name='person_create'),
    path('personen/<int:pk>/',             views.person_detail,        name='person_detail'),
    path('personen/<int:pk>/bearbeiten/',  views.person_edit,          name='person_edit'),
    path('personen/<int:pk>/loeschen/',    views.person_delete,        name='person_delete'),
    path('personen/<int:person_pk>/beziehung/',        views.relationship_create, name='relationship_create'),
    path('personen/<int:person_pk>/beziehungen/',      views.relationship_list,   name='relationship_list'),
    path('beziehung/<int:pk>/bearbeiten/',             views.relationship_edit,   name='relationship_edit'),
    path('beziehung/<int:pk>/loeschen/',               views.relationship_delete, name='relationship_delete'),
    path('einladen/',                      views.invite,               name='invite'),
    path('personen/csv-import/',           csv_import_view,            name='csv_import'),
    path('register/<uuid:token>/',         views.register,             name='register'),
    path('mein-profil/',                   views.my_profile,           name='my_profile'),
]
