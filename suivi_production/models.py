from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum, F
from django.utils.translation import gettext_lazy as _

# =============================================================================
# MODÈLES DE CONFIGURATION (Entités de base)
# =============================================================================

class Operateur(models.Model):
    """Représente un employé de l'atelier."""
    code = models.CharField(max_length=10, unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    cout_horaire = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    
    # --- DÉBUT DE LA MODIFICATION ---
    postes_qualifies = models.ManyToManyField(
        'PosteDeTravail',
        blank=True, # Un opérateur peut n'être assigné à aucun poste (ex: en formation)
        related_name='operateurs'
    )

    def __str__(self):
        return f"{self.code} - {self.prenom} {self.nom}"

class MatierePremiere(models.Model):
    """Représente un article en stock."""
    reference = models.CharField(max_length=100, unique=True)
    designation = models.CharField(max_length=255)
    quantite_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    unite_mesure = models.CharField(max_length=20, default='unité')
    seuil_alerte = models.DecimalField(max_digits=10, decimal_places=2, default=10.0)

    def __str__(self):
        return f"{self.reference} - {self.designation}"

class Machine(models.Model):
    """Représente une machine de l'atelier."""
    STATUT_CHOICES = (('DISPONIBLE', 'Disponible'), ('EN_PANNE', 'En Panne'), ('MAINTENANCE', 'En Maintenance'))
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='DISPONIBLE')

    def __str__(self):
        return self.nom

class PosteDeTravail(models.Model):
    """Représente un type de poste ou de famille d'opération dans l'atelier."""
    nom = models.CharField(max_length=100, unique=True, help_text="Ex: Cutting, Bending, Quality Inspection")
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nom

# =============================================================================
# MODÈLES DE PROCESSUS (Le cœur de la GPAO)
# =============================================================================

class OrdreFabrication(models.Model):
    """Représente un ordre de travail pour produire une certaine quantité d'un produit."""
    STATUT_CHOICES = [('PLANIFIE', _('Planifié')), ('PRODUCTION', _('En Production')), ('TERMINE', _('Terminé')),  ('ARCHIVE', _('Archivé'))]
    numero_of = models.CharField(max_length=50, unique=True)
    titre = models.CharField(max_length=255)
    quantite_a_produire = models.IntegerField(default=1)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='PLANIFIE')
    date_creation = models.DateField(auto_now_add=True)
    date_premiere_finalisation = models.DateField(null=True, blank=True, editable=False)
    date_debut_prevu = models.DateField(null=True, blank=True)
    date_fin_prevue = models.DateField(null=True, blank=True)
    plan_pdf = models.FileField(upload_to='plans/', blank=True, null=True)

    def __str__(self):
        return f"{self.numero_of} - {self.titre}"

    def update_statut(self):
        if not self.operations.exists(): self.statut = 'PLANIFIE'
        else:
            statuts_ops = list(self.operations.values_list('statut', flat=True))
            if 'EN_COURS' in statuts_ops: self.statut = 'PRODUCTION'
            elif 'A_FAIRE' in statuts_ops: self.statut = 'PRODUCTION'
            elif all(s == 'TERMINEE' for s in statuts_ops):
                if self.statut != 'TERMINE': 
                    if not self.date_premiere_finalisation:
                        self.date_premiere_finalisation = timezone.now().date()
                self.statut = 'TERMINE'
        self.save()

    @property
    def derniere_operation_terminee(self):
        return self.operations.filter(statut='TERMINEE').order_by('-numero_phase').first()

    @property
    def quantite_produite_actuelle(self):
        last_op = self.derniere_operation_terminee
        return last_op.quantite_sortie_bonne if last_op else 0

    @property
    def quantite_rebut_totale(self):
        return self.operations.aggregate(total=Sum('pointages__quantite_rebut'))['total'] or 0

    @property
    def progression_production(self):
        if self.quantite_a_produire <= 0: return 0
        progression = (self.quantite_produite_actuelle / self.quantite_a_produire) * 100
        return min(progression, 100)

class Operation(models.Model):
    """Représente une étape (phase) de la gamme de fabrication d'un OF."""
    STATUT_CHOICES = (('A_FAIRE', 'À Faire'), ('EN_COURS', 'En Cours'), ('TERMINEE', 'Terminée'))
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='A_FAIRE', verbose_name="Statut de l'Opération")
    quantite_entree = models.IntegerField(default=0)
    TYPE_CHOICES = (('PRODUCTION', 'Activité de Production'), ('CONSOMMATION', 'Consommation Matière (Input)'), ('QUALITE', 'Contrôle Qualité'), ('LOGISTIQUE', 'Approvisionnement (Supply)'))
    type_operation = models.CharField(max_length=20, choices=TYPE_CHOICES, default='PRODUCTION', verbose_name="Type d'élément")
    STATUT_CHOICES = (
        ('A_FAIRE', 'À Faire'),
        ('EN_COURS', 'En Cours'),
        ('TERMINEE', 'Terminée'),
        ('RETOUCHE', 'En Retouche'), # NOUVEAU STATUT
    )
    
    poste = models.ForeignKey(PosteDeTravail, on_delete=models.PROTECT, related_name='operations')
    titre = models.CharField(max_length=255, help_text="Description spécifique, ex: 'Coupe du tube principal'")
    instructions = models.JSONField(blank=True, null=True, help_text="Données structurées des instructions.")
    matieres_requises_json = models.JSONField(blank=True, null=True, help_text="Stockage temporaire des matières pour le formset.")

    ordre_fabrication = models.ForeignKey(OrdreFabrication, related_name='operations', on_delete=models.CASCADE)
    numero_phase = models.IntegerField()
    temps_prevu_minutes = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    machine_assignee = models.ForeignKey(Machine, on_delete=models.SET_NULL, null=True, blank=True, related_name='operations')
    matieres_requises = models.ManyToManyField(MatierePremiere, through='MatiereRequise', related_name='operations')
    

    class Meta:
        unique_together = ('ordre_fabrication', 'numero_phase')
        ordering = ['numero_phase']

    def __str__(self):
        return f"OF {self.ordre_fabrication.numero_of} / Phase {self.numero_phase} ({self.poste.nom}): {self.titre}"

    @property
    def quantite_sortie_bonne(self):
        return self.pointages.aggregate(total=Sum('quantite_fabriquee'))['total'] or 0
    @property
    def quantite_sortie_rebut(self):
        return self.pointages.aggregate(total=Sum('quantite_rebut'))['total'] or 0
    @property
    def taux_rebut(self):
        total_produit = self.quantite_sortie_bonne + self.quantite_sortie_rebut
        return (self.quantite_sortie_rebut / total_produit * 100) if total_produit > 0 else 0

class MatiereRequise(models.Model):
    """Table de liaison pour spécifier la quantité de matière nécessaire pour une opération."""
    operation = models.ForeignKey(Operation, on_delete=models.CASCADE)
    matiere = models.ForeignKey(MatierePremiere, on_delete=models.CASCADE)
    quantite_necessaire = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('operation', 'matiere')

class Pointage(models.Model):
    """Enregistre un intervalle de temps travaillé par un opérateur sur une opération."""
    operation = models.ForeignKey(Operation, related_name='pointages', on_delete=models.CASCADE)
    operateur = models.ForeignKey(Operateur, related_name='pointages', on_delete=models.PROTECT)
    heure_debut = models.DateTimeField()
    heure_fin = models.DateTimeField(null=True, blank=True)
    quantite_fabriquee = models.IntegerField(default=0)
    quantite_rebut = models.IntegerField(default=0)
    quantite_prise_en_charge = models.IntegerField(default=0)

    @property
    def duree_minutes(self):
        duration = (self.heure_fin or timezone.now()) - self.heure_debut
        return Decimal(duration.total_seconds() / 60)
    @property
    def cout_mo(self):
        return (self.duree_minutes / Decimal('60')) * self.operateur.cout_horaire

# =============================================================================
# MODÈLES UTILISATEURS (Profil)
# =============================================================================

class Profile(models.Model):
    """Modèle étendant le User de Django pour y ajouter un rôle."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ROLE_CHOICES = (('MANAGER', 'Manager'), ('POSTE', 'Poste de Travail'))
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='POSTE')

    def __str__(self):
        return f'{self.user.username} Profile ({self.get_role_display()})'

class Anomalie(models.Model):
    """Enregistre un problème signalé par un opérateur sur une opération."""
    STATUT_CHOICES = (
        ('OUVERTE', 'Ouverte'),
        ('RESOLUE', 'Résolue'),
    )
    operation = models.ForeignKey(Operation, on_delete=models.CASCADE, related_name='anomalies')
    operateur = models.ForeignKey(Operateur, on_delete=models.SET_NULL, null=True)
    description = models.TextField(help_text="Description du problème rencontré.")
    date_signalement = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='OUVERTE')
    resolu_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='anomalies_resolues')
    date_resolution = models.DateTimeField(null=True, blank=True)
    # Indique si l'anomalie a été masquée sur le dashboard sans être résolue (historique d'UI)
    masquee_dashboard = models.BooleanField(default=False)

    def __str__(self):
        return f"Anomalie sur {self.operation.titre} ({self.get_statut_display()})"
    
    

class DailyReport(models.Model):
    """
    Stocke une photographie des KPIs de production pour une journée donnée.
    Cette table est optimisée pour l'analyse historique sur de longues périodes.
    """
    date = models.DateField(unique=True, primary_key=True) # La date est la clé unique

    pieces_fabriquees = models.IntegerField(default=0)
    pieces_rebut = models.IntegerField(default=0)
    taux_rebut = models.FloatField(default=0.0)
    operateurs_actifs = models.IntegerField(default=0)
    
    # On pourrait ajouter d'autres indicateurs plus tard (ex: temps de production total)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Rapport du {self.date.strftime('%d/%m/%Y')}"    

# =============================================================================
# SIGNAUX (Logique automatisée)
# =============================================================================

