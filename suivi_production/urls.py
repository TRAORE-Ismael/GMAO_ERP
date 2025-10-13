from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import (
        liste_archives_view, 
        api_dashboard_data,
        of_list_view
)
from .views import (
    # ... vos autres imports
    rapport_production_par_of_view,    # <-- Assurez-vous que c'est bien importé
    rapport_production_par_operation_view # <-- Assurez-vous que c'est bien importé
)


urlpatterns = [
    # URLs principales
    path('', views.home_view, name='home'),
    path('dashboard/redirect/', views.dashboard_redirect_view, name='dashboard'),
    path('archives/', liste_archives_view, name='liste_archives'),

    # URLs d'authentification
    path('inscription/', views.inscription_view, name='inscription'),
    path('connexion/', views.custom_login_view, name='connexion'),
    path('deconnexion/', auth_views.LogoutView.as_view(), name='deconnexion'),
    path('en-attente-assignation/', views.dashboard_redirect_view, name='attente_assignation'),
    
    # URLs pour le rôle "Poste de Travail"
    path('saisie-atelier/', views.saisie_atelier_view, name='saisie_atelier'),

    # URLs pour le rôle "Manager"
    path('dashboard/manager/', views.dashboard_manager_view, name='dashboard_manager'),
    path('suivi-atelier/', views.suivi_of_list_view, name='suivi_atelier'),
    path('suivi-atelier/of/<int:pk>/', views.suivi_detail_of_view, name='suivi_detail_of'),
    path('suivi-atelier/of/<int:pk>/export/csv/', views.export_suivi_csv, name='export_suivi_csv'),
    
    # URLs de gestion des OFs
    path('gestion/of/', views.of_list_view, name='of_list'),
    path('gestion/of/creer/', views.of_create_view, name='of_create'),
    path('gestion/of/<int:pk>/modifier/', views.of_update_view, name='of_update'),
    path('of/<int:pk>/fiche/', views.fiche_of_view, name='fiche_of'),

    # URLs pour les APIs AJAX
    path('api/demarrer_tache/', views.api_demarrer_tache, name='api_demarrer_tache'),
    path('api/terminer_tache/', views.api_terminer_tache, name='api_terminer_tache'),
        # NOUVELLES URLs POUR LES RAPPORTS
    path('rapports/production-du-jour/', rapport_production_par_of_view, name='rapport_production_par_of'),
    path('rapports/production-par-operation/<int:pk>/', views.rapport_production_par_operation_view, name='rapport_production_par_operation'),
    path('rapports/rebuts/', views.rapport_rebuts_par_of_view, name='rapport_rebuts'),
    path('rapports/rebuts/export/pdf/', views.export_rebuts_par_of_pdf, name='export_rebuts_par_of_pdf'),
    path('rapports/rebuts/export/xlsx/', views.export_rebuts_par_of_xlsx, name='export_rebuts_par_of_xlsx'),
    path('gestion/operation/<int:pk>/modifier/', views.operation_update_view, name='operation_update'),
    path('gestion/of/<int:pk>/supprimer/', views.of_delete_view, name='of_delete'),
    path('gestion/operation/<int:pk>/fiche/', views.fiche_operation_view, name='fiche_operation'),
    path('rapports/rebuts/of/<int:pk>/', views.rapport_rebuts_par_operation_view, name='rapport_rebuts_par_operation'),
    path('api/anomalie/<int:pk>/', views.api_get_anomalie_detail, name='api_get_anomalie_detail'),
    path('api/anomalie/<int:pk>/resolve/', views.api_resolve_anomalie, name='api_resolve_anomalie'),
    path('rapport-production/<int:of_id>/<str:date_str>/', views.rapport_production_of_jour, name='rapport_production_of_jour'),
    path('api/dashboard-data/', api_dashboard_data, name='api_dashboard_data'),
    path('historique/', views.historique_view, name='historique'),
]

