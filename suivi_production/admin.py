from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Machine # Ajoutez Machine à la liste des imports
from .models import PosteDeTravail,Anomalie

# On importe tous les modèles nécessaires en une seule fois
from .models import (
    Profile, Operateur, OrdreFabrication, Operation, Pointage,
    MatierePremiere, MatiereRequise, DailyReport
)


# --- CONFIGURATION DE L'AFFICHAGE DES PROFILS DANS L'ADMIN USER ---

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profil'

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# --- CONFIGURATION DES INLINES POUR LES OFs ET OPERATIONS ---

# Cet inline sera utilisé dans la page OrdreFabricationAdmin
class OperationInline(admin.TabularInline):
    model = Operation
    extra = 1
    show_change_link = True # Permet de cliquer sur une opération pour la modifier en détail

# Cet inline sera utilisé dans la page OperationAdmin
class MatiereRequiseInline(admin.TabularInline):
    model = MatiereRequise
    extra = 1


# --- ENREGISTREMENT DES MODÈLES DE L'APPLICATION ---

@admin.register(OrdreFabrication)
class OrdreFabricationAdmin(admin.ModelAdmin):
    list_display = ('numero_of', 'titre', 'statut', 'lien_fiche')
    list_filter = ('statut',)
    search_fields = ('numero_of', 'titre')
    inlines = [OperationInline]

    def lien_fiche(self, obj):
        url = reverse('fiche_of', args=[obj.pk])
        return format_html(f'<a href="{url}" target="_blank">Voir la fiche</a>')
    
    lien_fiche.short_description = 'Fiche de Fabrication'

@admin.register(Operation)
class OperationAdmin(admin.ModelAdmin):
    list_display = ('titre', 'ordre_fabrication', 'numero_phase')
    list_filter = ('ordre_fabrication',)
    search_fields = ('titre', 'ordre_fabrication__numero_of')
    # On ajoute l'inline pour gérer les matières directement depuis la page de l'opération
    inlines = [MatiereRequiseInline]

@admin.register(MatierePremiere)
class MatierePremiereAdmin(admin.ModelAdmin):
    list_display = ('reference', 'designation', 'quantite_stock', 'unite_mesure')
    search_fields = ('reference', 'designation')

@admin.register(Operateur)
class OperateurAdmin(admin.ModelAdmin):
    list_display = ('code', 'prenom', 'nom', 'cout_horaire')
    search_fields = ('code', 'nom', 'prenom')
    filter_horizontal = ('postes_qualifies',)

@admin.register(Pointage)
class PointageAdmin(admin.ModelAdmin):
    list_display = ('operation', 'operateur', 'heure_debut', 'heure_fin', 'duree_minutes')
    list_filter = ('operateur', 'operation__ordre_fabrication')
    
@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ('nom', 'statut', 'description')
    list_filter = ('statut',)
    search_fields = ('nom',)
    
@admin.register(PosteDeTravail)
class PosteDeTravailAdmin(admin.ModelAdmin):
    list_display = ('nom', 'description')
    search_fields = ('nom',)

@admin.register(Anomalie)
class AnomalieAdmin(admin.ModelAdmin):
    list_display = ('operation', 'operateur', 'statut', 'date_signalement')
    list_filter = ('statut',)
    
@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    """
    Personnalisation de l'affichage du modèle DailyReport dans l'interface d'admin.
    """
    list_display = (
        'date', 
        'pieces_fabriquees', 
        'pieces_rebut', 
        'taux_rebut', 
        'operateurs_actifs'
    )
    list_filter = ('date',)
    ordering = ('-date',)