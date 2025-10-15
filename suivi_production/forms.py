from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (
    Profile, OrdreFabrication, Operation, 
    MatiereRequise
)

# =============================================================================
# FORMULAIRE D'INSCRIPTION UTILISATEUR
# =============================================================================

class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=Profile.ROLE_CHOICES, 
        required=True, 
        label="Je suis un",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')

    def save(self, commit=True):
        # Étape 1 : On laisse le formulaire de base créer l'utilisateur.
        # super().save() va appeler user.save(), ce qui déclenchera le signal.
        user = super().save(commit=commit)
        
        # Étape 2 : Maintenant que le profil existe, on met à jour son rôle.
        user.profile.role = self.cleaned_data.get('role')
        if commit:
            user.profile.save() # On sauvegarde le profil mis à jour
            
        return user

# =============================================================================
# FORMULAIRES POUR LA GESTION DES OFs ET OPÉRATIONS
# =============================================================================

class OrdreFabricationForm(forms.ModelForm):
    class Meta:
        model = OrdreFabrication
        # --- CORRECTION ICI : 'quantite_a_produire' est ajouté à la liste ---
        fields = [
            'numero_of', 
            'titre', 
            'quantite_a_produire', 
            'statut', 
            'date_debut_prevu', 
            'date_fin_prevue'
        ]
        widgets = {
            'numero_of': forms.TextInput(attrs={'class': 'form-control'}),
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'quantite_a_produire': forms.NumberInput(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'date_debut_prevu': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_fin_prevue': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class OperationForm(forms.ModelForm):
    class Meta:
        model = Operation
        fields = [
            'numero_phase', 
            'poste', 
            'titre', 
            'type_operation', 
            'machine_assignee', 
            'temps_prevu_minutes',
            'instructions',
            'matieres_requises_json', # Ajout du champ
        ]
        widgets = {
            'numero_phase': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'poste': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'titre': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Description brève'}),
            'type_operation': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'machine_assignee': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'temps_prevu_minutes': forms.NumberInput(attrs={'class': 'form-control form-control-sm'}),
            'instructions': forms.HiddenInput(),
            'matieres_requises_json': forms.HiddenInput(), # Ajout du widget
        }
        # Rendre le champ 'titre' optionnel
        labels = {
            'titre': 'Description',
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['titre'].required = False

# Formset pour gérer plusieurs Opérations à l'intérieur d'un OrdreFabrication
OperationFormSet = forms.inlineformset_factory(
    OrdreFabrication, 
    Operation, 
    form=OperationForm, 
    extra=1, # Affiche une ligne vide pour un nouvel ajout
    can_delete=True
)

# =============================================================================
# FORMULAIRE POUR LA GESTION DES MATIÈRES PREMIÈRES
# =============================================================================

# Formset pour gérer plusieurs MatiereRequise à l'intérieur d'une Opération
MatiereRequiseFormSet = forms.inlineformset_factory(
    Operation,
    MatiereRequise,
    fields=('matiere', 'quantite_necessaire'),
    extra=1,
    can_delete=True,
    widgets={
        'matiere': forms.Select(attrs={'class': 'form-select'}),
        'quantite_necessaire': forms.NumberInput(attrs={'class': 'form-control'}),
    }
)