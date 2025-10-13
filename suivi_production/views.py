# --- Imports Django ---
import json
import csv
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.db.models import Sum, F, Max, Q
from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone




# --- Imports Locaux ---
from .models import (
    Operateur, OrdreFabrication, Operation, Pointage, 
    MatierePremiere, MatiereRequise, Anomalie, DailyReport
)
from .forms import (
    CustomUserCreationForm,
    OrdreFabricationForm,
    OperationFormSet,
    MatiereRequiseFormSet,
)

from .services.reporting import (
    compute_kpis_for_date,
    build_7day_series,
    build_alertes,
)
from .filters.of import OrdreFabricationFilter

# Import optionnel pour les codes-barres (utilisé dans fiche_of_view)
try:
    import barcode
    from barcode.writer import SVGWriter
except Exception:
    barcode = None
    SVGWriter = None

# =============================================================================
# VUES PRINCIPALES DE L'APPLICATION
# =============================================================================
def home_view(request):
    """Page d'accueil: redirige vers dashboard si authentifié et profil présent."""
    if request.user.is_authenticated and not hasattr(request.user, 'profile'):
        return render(request, 'suivi_production/home.html')
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'suivi_production/home.html')


def custom_login_view(request):
    """Page de connexion avec formulaire d'inscription injecté."""
    view = LoginView.as_view(
        template_name='registration/login.html',
        extra_context={'inscription_form': CustomUserCreationForm()},
    )
    return view(request)


def inscription_view(request):
    """Création de compte utilisateur via CustomUserCreationForm."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Compte créé avec succès. Vous pouvez maintenant vous connecter.")
            return redirect('connexion')
        return render(request, 'registration/login.html', {'inscription_form': form})
    return redirect('connexion')


def dashboard_redirect_view(request):
    """Redirige vers le bon tableau selon le rôle ou affiche l'attente d'assignation."""
    if not request.user.is_authenticated:
        return redirect('connexion')
    if not hasattr(request.user, 'profile') or not getattr(request.user.profile, 'role', None):
        return render(request, 'suivi_production/en_attente_assignation.html')
    role = request.user.profile.role
    if role == 'MANAGER':
        return redirect('dashboard_manager')
    if role == 'POSTE':
        return redirect('saisie_atelier')
    return redirect('home')


@login_required
def saisie_atelier_view(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'POSTE':
        raise PermissionDenied
    return render(request, 'suivi_production/saisie_atelier.html')


@login_required
def dashboard_manager_view(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'MANAGER':
        raise PermissionDenied
    today = timezone.now().date()
    # KPIs via service
    daily = compute_kpis_for_date(today)
    kpis = {
        'operations_en_cours': daily.operations_en_cours,
        'operateurs_actifs': daily.operateurs_actifs,
        'qty_fabriquee_today': daily.qty_fabriquee_today,
        'taux_rebut_today': daily.taux_rebut_today,
        'today_iso': daily.today_iso,
    }
    # Chart via service
    chart_labels, production_data, rebut_data, taux_rebut_data = build_7day_series(today)
    # Alertes via service
    alertes = build_alertes(today)
    context = {
        'kpi': kpis,
        'chart': {
            'labels': chart_labels,
            'production_data': production_data,
            'rebut_data': rebut_data,
            'taux_rebut_data': taux_rebut_data,
        },
        'alertes': alertes,
    }
    return render(request, 'suivi_production/dashboard_manager.html', context)

# =============================================================================
# VUES DE SUIVI, GESTION ET RAPPORTS
# =============================================================================

@login_required
def suivi_of_list_view(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'MANAGER': raise PermissionDenied
    base = OrdreFabrication.objects.exclude(statut='ARCHIVE').order_by('date_creation')
    f = OrdreFabricationFilter(request.GET, queryset=base)
    context = {
        'ofs': f.qs,
        'filter': f,
        'filtre_numero': request.GET.get('numero', '').strip(),  # compat template existant
    }
    return render(request, 'suivi_production/suivi_of_list.html', context)

@login_required
def suivi_detail_of_view(request, pk):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'MANAGER': raise PermissionDenied
    try:
        of = OrdreFabrication.objects.get(pk=pk)
        pointages_list = Pointage.objects.filter(operation__ordre_fabrication=of).select_related('operation', 'operateur', 'operation__machine_assignee')
        if request.GET.get('date_filtre'): pointages_list = pointages_list.filter(heure_debut__date=request.GET.get('date_filtre'))
        if request.GET.get('operateur_filtre'): pointages_list = pointages_list.filter(operateur_id=request.GET.get('operateur_filtre'))
        if request.GET.get('statut_filtre') == 'en_cours': pointages_list = pointages_list.filter(heure_fin__isnull=True)
        elif request.GET.get('statut_filtre') == 'termine': pointages_list = pointages_list.filter(heure_fin__isnull=False)
        context = {'of': of, 'pointages': pointages_list.order_by('operation__numero_phase', 'heure_debut'), 'operateurs': Operateur.objects.all(), 'valeurs_filtres': request.GET}
        return render(request, 'suivi_production/suivi_detail_of.html', context)
    except OrdreFabrication.DoesNotExist: raise Http404("Ordre de Fabrication non trouvé")

@login_required
def rapport_production_view(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'MANAGER': raise PermissionDenied
    today = timezone.now().date()
    pointages_finaux_du_jour = []
    pointages_termines_today = Pointage.objects.filter(heure_fin__date=today).select_related('operation__ordre_fabrication')
    for p in pointages_termines_today:
        derniere_phase_numero = p.operation.ordre_fabrication.operations.aggregate(max_phase=Max('numero_phase'))['max_phase']
        if p.operation.numero_phase == derniere_phase_numero:
            pointages_finaux_du_jour.append(p)
    context = {'pointages': pointages_finaux_du_jour, 'date': today}
    return render(request, 'suivi_production/rapports/rapport_production.html', context)

@login_required
def rapport_rebuts_par_of_view(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'MANAGER':
        raise PermissionDenied

    numero = request.GET.get('numero', '').strip()
    date_str = request.GET.get('date', '').strip()
    from .services.reporting import queryset_rebuts_par_of
    ofs_avec_rebut = queryset_rebuts_par_of(numero=numero, date_str=date_str)
    return render(request, 'suivi_production/rapports/rapport_rebuts_par_of.html', {
        'ordres_fabrication': ofs_avec_rebut,
        'filtre_numero': numero,
        'filtre_date': date_str,
        'filter': OrdreFabricationFilter(request.GET, queryset=OrdreFabrication.objects.none()),
    })


 


@login_required
def export_rebuts_par_of_pdf(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'MANAGER':
        raise PermissionDenied
    from .exports.rebuts import export_rebuts_pdf
    numero = request.GET.get('numero', '').strip()
    date_str = request.GET.get('date', '').strip()
    return export_rebuts_pdf(numero=numero, date_str=date_str)


@login_required
def export_rebuts_par_of_xlsx(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'MANAGER':
        raise PermissionDenied
    from .exports.rebuts import export_rebuts_xlsx
    numero = request.GET.get('numero', '').strip()
    date_str = request.GET.get('date', '').strip()
    return export_rebuts_xlsx(numero=numero, date_str=date_str)

@login_required
def rapport_rebuts_par_operation_view(request, pk):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'MANAGER': raise PermissionDenied
    of = OrdreFabrication.objects.get(pk=pk)
    operations_avec_rebut = of.operations.filter(pointages__quantite_rebut__gt=0).distinct().annotate(total_rebut_op=Sum('pointages__quantite_rebut'), total_fab_op=Sum('pointages__quantite_fabriquee')).select_related('ordre_fabrication')
    return render(request, 'suivi_production/rapports/rapport_rebuts_par_operation.html', {'of': of, 'operations': operations_avec_rebut})

def synchroniser_gamme(ordre_fabrication):
    operations = ordre_fabrication.operations.order_by('numero_phase')
    for i, op in enumerate(operations):
        quantite_entree_calculee = 0
        if i == 0:
            quantite_entree_calculee = ordre_fabrication.quantite_a_produire
        else:
            op_precedente = operations[i-1]
            if op_precedente.statut == 'TERMINEE':
                quantite_entree_calculee = op_precedente.quantite_sortie_bonne
        if op.statut == 'A_FAIRE':
            op.quantite_entree = quantite_entree_calculee
        op.save()

@login_required
def of_list_view(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'MANAGER': raise PermissionDenied
    
    query = request.GET.get('q', '')
    
    # On exclut les OFs archivés
    base_queryset = OrdreFabrication.objects.exclude(statut='ARCHIVE')
    
    if query:
        # On recherche sur les champs qui existent : numero_of et titre
        search_results = base_queryset.filter(
            Q(numero_of__icontains=query) |
            Q(titre__icontains=query)
        )
    else:
        search_results = base_queryset.all()
        
    ofs = search_results.order_by('-date_creation')
    
    return render(request, 'suivi_production/gestion/of_list.html', {'ofs': ofs})

@login_required
def of_create_view(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'MANAGER': raise PermissionDenied
    if request.method == 'POST':
        form = OrdreFabricationForm(request.POST)
        formset = OperationFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            of = form.save(); formset.instance = of; formset.save()
            synchroniser_gamme(of)
            messages.success(request, f"L'OF '{of.numero_of}' a été créé.")
            return redirect('of_list')
    else: form = OrdreFabricationForm(); formset = OperationFormSet()
    return render(request, 'suivi_production/gestion/of_form.html', {'form': form, 'formset': formset})

@login_required
def of_update_view(request, pk):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'MANAGER': raise PermissionDenied
    of = OrdreFabrication.objects.get(pk=pk)
    if request.method == 'POST':
        form = OrdreFabricationForm(request.POST, instance=of)
        formset = OperationFormSet(request.POST, instance=of)
        if form.is_valid() and formset.is_valid():
            form.save(); formset.save()
            synchroniser_gamme(of)
            of.update_statut()
            messages.success(request, f"L'OF '{of.numero_of}' a été mis à jour.")
            return redirect('of_list')
    else: form = OrdreFabricationForm(instance=of); formset = OperationFormSet(instance=of)
    return render(request, 'suivi_production/gestion/of_form.html', {'form': form, 'formset': formset, 'of': of})

@login_required
def of_delete_view(request, pk):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'MANAGER': raise PermissionDenied
    if request.method == 'POST':
        try:
            of = OrdreFabrication.objects.get(pk=pk); numero_of = of.numero_of; of.delete()
            messages.success(request, f"L'OF '{numero_of}' a été supprimé.")
        except OrdreFabrication.DoesNotExist:
            messages.error(request, "L'OF que vous essayez de supprimer n'existe pas.")
    return redirect('of_list')

@login_required
def operation_update_view(request, pk):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'MANAGER': raise PermissionDenied
    operation = Operation.objects.get(pk=pk)
    if request.method == 'POST':
        formset = MatiereRequiseFormSet(request.POST, instance=operation)
        if formset.is_valid():
            formset.save()
            messages.success(request, f"Les matières pour '{operation.titre}' ont été mises à jour.")
            return redirect('of_update', pk=operation.ordre_fabrication.pk)
    else: formset = MatiereRequiseFormSet(instance=operation)
    return render(request, 'suivi_production/gestion/operation_form.html', {'formset': formset, 'operation': operation})

# =============================================================================
# VUES "API" (pour AJAX) ET EXPORTS
# =============================================================================

@login_required
def api_demarrer_tache(request):
    """API pour démarrer un pointage. Interdit le redémarrage sur une opération terminée."""
    if request.method != 'POST': 
        return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # --- PHASE 2 : DÉMARRAGE EFFECTIF ---
        if data.get('action') == 'valider_demarrage':
            operation = Operation.objects.get(id=data.get('operation_id'))
            operateur = Operateur.objects.get(id=data.get('operateur_id'))
            quantite_prise = int(data.get('quantite_prise', 0))

            # ==================== DÉBUT DE LA CORRECTION PRINCIPALE (Phase 2) ====================
            # On vérifie une dernière fois le statut de l'opération AVANT de créer le pointage
            if operation.statut == 'TERMINEE':
                return JsonResponse({
                    'status': 'error', 
                    'message': f"Action impossible : L'opération '{operation.titre}' est déjà terminée et verrouillée."
                }, status=400)
            # ===================== FIN DE LA CORRECTION PRINCIPALE (Phase 2) =====================

            Pointage.objects.create(
                operation=operation, 
                operateur=operateur, 
                heure_debut=timezone.now(), 
                quantite_prise_en_charge=quantite_prise
            )
            
            # Mise à jour du statut de l'opération et de l'OF
            operation.statut = 'EN_COURS'
            operation.save()
            
            of = operation.ordre_fabrication
            if of.statut == 'PLANIFIE':
                of.statut = 'PRODUCTION'
                of.save()

            return JsonResponse({'status': 'success', 'message': 'Démarrage de la tâche enregistré.'})

        # --- PHASE 1 : PRÉPARATION DE LA MODAL ---
        operateur = Operateur.objects.get(code__iexact=data.get('code_operateur'))
        parts = data.get('code_of_operation').split('/')
        operation = Operation.objects.select_related('ordre_fabrication', 'poste').get(ordre_fabrication__numero_of=parts[0], numero_phase=int(parts[1]))
        of = operation.ordre_fabrication

        # --- VÉRIFICATION DE COMPÉTENCE ---
        # On s'assure que l'opérateur est bien qualifié pour le poste requis par l'opération.
        if operation.poste not in operateur.postes_qualifies.all():
            return JsonResponse({
                'status': 'error',
                'message': f"Compétence manquante : L'opérateur {operateur.nom} n'est pas qualifié pour le poste '{operation.poste.nom}'."
            }, status=403) # 403 Forbidden est plus sémantique ici

        # ==================== DÉBUT DE LA CORRECTION PRINCIPALE (Phase 1) ====================
        # On interdit explicitement de démarrer une opération terminée.
        if operation.statut == 'TERMINEE':
            return JsonResponse({
                'status': 'error', 
                'message': f"Opération verrouillée : L'opération '{operation.titre}' est déjà terminée. Contactez un manager pour une retouche."
            }, status=400)
            
        # On autorise le démarrage uniquement si c'est 'A_FAIRE' ou 'EN_COURS'
        if operation.statut not in ['A_FAIRE', 'EN_COURS']:
            return JsonResponse({
                'status': 'error', 
                'message': f"Cette opération est déjà '{operation.get_statut_display()}'."
            }, status=400)
        # ===================== FIN DE LA CORRECTION PRINCIPALE (Phase 1) =====================
            
        pieces_prises_par_autres = Pointage.objects.filter(operation=operation, heure_fin__isnull=True).aggregate(total=Sum('quantite_prise_en_charge'))['total'] or 0
        quantite_disponible = operation.quantite_entree - pieces_prises_par_autres

        if quantite_disponible <= 0 and operation.statut != 'EN_COURS':
            return JsonResponse({'status': 'error', 'message': "Aucune pièce disponible pour cette opération."}, status=400)

        return JsonResponse({
            'status': 'confirmation_demarrage',
            'operation_id': operation.id,
            'operateur_id': operateur.id,
            'operation_titre': operation.titre,
            'quantite_disponible': quantite_disponible,
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f"Erreur : {str(e)}"}, status=500)

@login_required
def api_terminer_tache(request):
    """API pour trouver un pointage à terminer (phase 1) ou pour le valider (phase 2)."""
    if request.method != 'POST': 
        return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # --- PHASE 2 : L'utilisateur a soumis le formulaire de la modal ---
        if data.get('action') == 'valider_fin':
            pointage = Pointage.objects.get(id=data.get('pointage_id'))
            qty_fabriquee = int(data.get('quantite_fabriquee', 0))
            qty_rebut = int(data.get('quantite_rebut', 0))
                        # --- AJOUT DE LA VÉRIFICATION ---
            if pointage.operation.statut == 'TERMINEE':
                return JsonResponse({
                    'status': 'error', 
                    'message': "Action impossible : L'opération a été terminée et verrouillée par un autre utilisateur."
                }, status=400)
            # --- FIN DE L'AJOUT ---

            # Contrôle de cohérence
            if (qty_fabriquee + qty_rebut) != pointage.quantite_prise_en_charge:
                return JsonResponse({
                    'status': 'error', 
                    'message': f"La somme ({qty_fabriquee + qty_rebut}) doit être égale à la quantité prise en charge ({pointage.quantite_prise_en_charge})."
                }, status=400)
            
            # Sauvegarde du pointage
            pointage.heure_fin = timezone.now()
            pointage.quantite_fabriquee = qty_fabriquee
            pointage.quantite_rebut = qty_rebut
            pointage.save()

            # Création de l'anomalie si elle a été signalée
            probleme_signale = data.get('probleme_signale', False)
            if probleme_signale:
                Anomalie.objects.create(
                    operation=pointage.operation,
                    operateur=pointage.operateur,
                    description=data.get('probleme_description', 'Non spécifié')
                )

            operation = pointage.operation
            of = operation.ordre_fabrication
            
            # Vérification si l'opération globale est terminée
            total_declare_pour_op = operation.quantite_sortie_bonne + operation.quantite_sortie_rebut
            if total_declare_pour_op >= operation.quantite_entree:
                operation.statut = 'TERMINEE'
                operation.save()
                
                # Décrémentation du stock (uniquement si c'est la première phase)
                premiere_phase = of.operations.order_by('numero_phase').first()
                if premiere_phase and operation == premiere_phase:
                    matieres_a_decrementer = operation.matiererequise_set.all()
                    for item in matieres_a_decrementer:
                        quantite_a_retirer = item.quantite_necessaire * operation.quantite_entree
                        MatierePremiere.objects.filter(pk=item.matiere.pk).update(quantite_stock=F('quantite_stock') - quantite_a_retirer)
                
                # Déblocage de l'opération suivante
                op_suivante = of.operations.filter(numero_phase__gt=operation.numero_phase).order_by('numero_phase').first()
                if op_suivante:
                    op_suivante.quantite_entree = operation.quantite_sortie_bonne
                    op_suivante.statut = 'A_FAIRE'
                    op_suivante.save()
            
            # On met à jour le statut global de l'OF à la fin
            of.update_statut()
            
            return JsonResponse({'status': 'success', 'message': f"FIN de travail enregistrée pour '{operation.titre}'."})

        # --- PHASE 1 : L'utilisateur a cliqué sur le bouton "Terminer Tâche" ---
        operateur = Operateur.objects.get(code__iexact=data.get('code_operateur'))
        parts = data.get('code_of_operation').split('/')
        operation = Operation.objects.select_related('ordre_fabrication').get(ordre_fabrication__numero_of=parts[0], numero_phase=int(parts[1]))
        
        pointage_en_cours = Pointage.objects.filter(operateur=operateur, operation=operation, heure_fin__isnull=True).first()

        if not pointage_en_cours:
            return JsonResponse({'status': 'error', 'message': "Aucune tâche en cours trouvée pour cette combinaison."}, status=404)
        
        return JsonResponse({
            'status': 'confirmation_requise',
            'pointage_id': pointage_en_cours.id,
            'operation_titre': operation.titre,
            'quantite_a_declarer': pointage_en_cours.quantite_prise_en_charge,
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f"Erreur inattendue: {str(e)}"}, status=500)

@login_required
def fiche_of_view(request, pk):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'MANAGER': raise PermissionDenied
    try:
        of = OrdreFabrication.objects.get(pk=pk)
        operations_with_barcodes = [{'operation': op, 'barcode_svg': barcode.get('code128', f"{of.numero_of}/{op.numero_phase}", writer=SVGWriter()).render().decode('utf-8'), 'temps_prevu_heures': op.temps_prevu_minutes / 60} for op in of.operations.all()]
        return render(request, 'suivi_production/fiche_of.html', {'of': of, 'operations_with_barcodes': operations_with_barcodes})
    except OrdreFabrication.DoesNotExist:
        raise Http404("Ordre de Fabrication non trouvé")

@login_required
def fiche_operation_view(request, pk):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'MANAGER': raise PermissionDenied
    try:
        operation = Operation.objects.select_related('ordre_fabrication', 'machine_assignee').get(pk=pk)
        matieres_requises = MatiereRequise.objects.filter(operation=operation).select_related('matiere')
        context = {'operation': operation, 'of': operation.ordre_fabrication, 'matieres_requises': matieres_requises}
        return render(request, 'suivi_production/gestion/fiche_operation.html', context)
    except Operation.DoesNotExist:
        raise Http404("Opération non trouvée")

@login_required
def export_suivi_csv(request, pk):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'MANAGER': raise PermissionDenied
    try:
        of = OrdreFabrication.objects.get(pk=pk)
        response = HttpResponse(content_type='text/csv', headers={'Content-Disposition': f'attachment; filename="export_suivi_{of.numero_of}_{timezone.now().strftime("%Y-%m-%d")}.csv"'})
        response.write(u'\ufeff'.encode('utf8'))
        writer = csv.writer(response, delimiter=';')
        writer.writerow(['OF', 'Titre OF', 'Phase', 'Opération', 'Machine', 'Opérateur', 'Date Début', 'Heure Début', 'Date Fin', 'Heure Fin', 'Durée (min)', 'Qté Fabriquée', 'Qté Rebut', 'Coût M.O. (€)'])
        pointages_list = Pointage.objects.filter(operation__ordre_fabrication=of).select_related('operation', 'operateur', 'operation__machine_assignee')
        if request.GET.get('date_filtre'): pointages_list = pointages_list.filter(heure_debut__date=request.GET.get('date_filtre'))
        if request.GET.get('operateur_filtre'): pointages_list = pointages_list.filter(operateur_id=request.GET.get('operateur_filtre'))
        if request.GET.get('statut_filtre') == 'en_cours': pointages_list = pointages_list.filter(heure_fin__isnull=True)
        elif request.GET.get('statut_filtre') == 'termine': pointages_list = pointages_list.filter(heure_fin__isnull=False)
        for p in pointages_list.order_by('operation__numero_phase', 'heure_debut'):
            writer.writerow([
                p.operation.ordre_fabrication.numero_of, p.operation.ordre_fabrication.titre, p.operation.numero_phase,
                p.operation.titre, p.operation.machine_assignee.nom if p.operation.machine_assignee else '', p.operateur.code,
                p.heure_debut.strftime('%d/%m/%Y'), p.heure_debut.strftime('%H:%M'),
                p.heure_fin.strftime('%d/%m/%Y') if p.heure_fin else '', p.heure_fin.strftime('%H:%M') if p.heure_fin else '',
                f"{p.duree_minutes:.2f}".replace('.', ','), p.quantite_fabriquee, p.quantite_rebut,
                f"{p.cout_mo:.2f}".replace('.', ',')
            ])
        return response
    except OrdreFabrication.DoesNotExist:
        raise Http404("Ordre de Fabrication non trouvé")

@login_required
def export_suivi_global_csv(request):
    """NOUVELLE VUE : Exporte TOUS les pointages, en appliquant les filtres globaux."""
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'MANAGER': raise PermissionDenied
    response = HttpResponse(content_type='text/csv', headers={'Content-Disposition': f'attachment; filename="export_suivi_global_{timezone.now().strftime("%Y-%m-%d")}.csv"'})
    response.write(u'\ufeff'.encode('utf8'))
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['OF', 'Titre OF', 'Phase', 'Opération', 'Machine', 'Opérateur', 'Date Début', 'Heure Début', 'Date Fin', 'Heure Fin', 'Durée (min)', 'Qté Fabriquée', 'Qté Rebut', 'Coût M.O. (€)'])
    
    pointages_list = Pointage.objects.select_related('operation__ordre_fabrication', 'operateur', 'operation__machine_assignee')
    if request.GET.get('date_filtre'): pointages_list = pointages_list.filter(heure_debut__date=request.GET.get('date_filtre'))
    
    for p in pointages_list:
        writer.writerow([
            p.operation.ordre_fabrication.numero_of, p.operation.ordre_fabrication.titre, p.operation.numero_phase,
            p.operation.titre, p.operation.machine_assignee.nom if p.operation.machine_assignee else '', p.operateur.code,
            p.heure_debut.strftime('%d/%m/%Y'), p.heure_debut.strftime('%H:%M'),
            p.heure_fin.strftime('%d/%m/%Y') if p.heure_fin else '', p.heure_fin.strftime('%H:%M') if p.heure_fin else '',
            f"{p.duree_minutes:.2f}".replace('.', ','), p.quantite_fabriquee, p.quantite_rebut,
            f"{p.cout_mo:.2f}".replace('.', ',')
        ])
    return response

@login_required
def api_get_anomalie_detail(request, pk):
    """API pour récupérer les détails d'une anomalie spécifique."""
    try:
        anomalie = Anomalie.objects.select_related('operation', 'operateur').get(pk=pk)
        details = {
            'operation': f"{anomalie.operation.titre} (OF {anomalie.operation.ordre_fabrication.numero_of})",
            'operateur': anomalie.operateur.nom if anomalie.operateur else 'N/A',
            'date': anomalie.date_signalement.strftime('%d/%m/%Y à %H:%M'),
            'description': anomalie.description,
        }
        return JsonResponse({'status': 'success', 'details': details})
    except Anomalie.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Anomalie non trouvée'}, status=404)

@login_required
def api_resolve_anomalie(request, pk):
    """API pour marquer une anomalie comme résolue (persistance côté base)."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)
    try:
        anomalie = Anomalie.objects.get(pk=pk)
        anomalie.statut = 'RESOLUE'
        anomalie.resolu_par = request.user if request.user.is_authenticated else None
        anomalie.date_resolution = timezone.now()
        anomalie.save(update_fields=['statut', 'resolu_par', 'date_resolution'])
        return JsonResponse({'status': 'success'})
    except Anomalie.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Anomalie non trouvée'}, status=404)

@login_required
def rapport_production_of_jour(request, of_id, date_str):
    """
    Affiche le détail des opérations terminées pour un OF spécifique à une date donnée.
    """
    date_production = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
    
    try:
        ordre_fabrication = OrdreFabrication.objects.get(id=of_id)
    except OrdreFabrication.DoesNotExist:
        raise Http404("L'Ordre de Fabrication n'existe pas.")

    pointages_du_jour = Pointage.objects.filter(
        operation__ordre_fabrication=ordre_fabrication,
        heure_fin__date=date_production
    ).select_related(
        'operation', 
        'operateur'
    ).order_by('heure_fin')

    total_quantite = pointages_du_jour.aggregate(total=Sum('quantite_fabriquee'))['total'] or 0

    context = {
        'ordre_fabrication': ordre_fabrication,
        'date_production': date_production,
        'pointages': pointages_du_jour,
        'total_quantite': total_quantite,
    }
    return render(request, 'suivi_production/rapport_of_jour.html', context)

# Vue pour la Page 1 : Liste des OFs terminés aujourd'hui
@login_required
def rapport_production_par_of_view(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'MANAGER':
        raise PermissionDenied
        
    date_str = request.GET.get('date', '').strip()
    numero = request.GET.get('numero', '').strip()
    qs = OrdreFabrication.objects.exclude(statut='ARCHIVE')
    if date_str:
        try:
            filter_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            qs = qs.filter(date_premiere_finalisation=filter_date)
            date_rapport = filter_date
        except Exception:
            date_rapport = timezone.now().date()
    else:
        date_rapport = timezone.now().date()
        qs = qs.filter(date_premiere_finalisation=date_rapport)
    if numero:
        qs = qs.filter(numero_of__icontains=numero)
    ofs_termines_aujourdhui = qs.order_by('-date_premiere_finalisation', '-date_creation')

    context = {
        'date_rapport': date_rapport,
        'ofs_termines': ofs_termines_aujourdhui,
        'filtre_numero': numero,
        'filtre_date': date_str,
    }
    context['filter'] = OrdreFabricationFilter(request.GET, queryset=OrdreFabrication.objects.none())
    return render(request, 'suivi_production/rapports/rapport_production_par_of.html', context)


# Vue pour la Page 2 : Détail des opérations pour un OF
@login_required
def rapport_production_par_operation_view(request, pk):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'MANAGER':
        raise PermissionDenied
    
    try:
        of = OrdreFabrication.objects.get(pk=pk)
    except OrdreFabrication.DoesNotExist:
        raise Http404("Ordre de Fabrication non trouvé")

    # On récupère toutes les opérations de cet OF, car elles ont toutes contribué au résultat final
    operations_of = of.operations.all().order_by('numero_phase')

    context = {
        'of': of,
        'operations': operations_of
    }
    return render(request, 'suivi_production/rapports/rapport_production_par_operation.html', context)

@login_required
def liste_archives_view(request):
    query = request.GET.get('q', '')
    
    # On ne prend que les OFs archivés
    base_queryset = OrdreFabrication.objects.filter(statut='ARCHIVE')
    
    if query:
        # On recherche sur les champs qui existent : numero_of et titre
        archives = base_queryset.filter(
            Q(numero_of__icontains=query) |
            Q(titre__icontains=query)
        ).order_by('-date_creation') # <-- CORRIGÉ
    else:
        archives = base_queryset.all().order_by('-date_creation') # <-- CORRIGÉ
    return render(request, 'suivi_production/gestion/liste_archives.html', {'archives': archives})


@login_required
def api_dashboard_data(request):
    """
    Vue API qui renvoie toutes les données dynamiques du tableau de bord au format JSON.
    """
    today = timezone.now().date()

    # Utilisation des services centralisés pour garantir la cohérence Front/Back
    daily = compute_kpis_for_date(today)
    labels, production_data, rebut_data, taux_rebut_data = build_7day_series(today)
    alertes_srv = build_alertes(today)

    # Mise en forme JSON attendue par le front
    kpis = {
        'operations_en_cours': daily.operations_en_cours,
        'operateurs_actifs': daily.operateurs_actifs,
        'qty_fabriquee_today': daily.qty_fabriquee_today,
        'taux_rebut_today': daily.taux_rebut_today,  # formatage (2 décimales) côté front
    }

    chart_data = {
        'labels': labels,
        'production_data': production_data,
        'rebut_data': rebut_data,
        'taux_rebut_data': taux_rebut_data,
    }

    # Sérialisation des alertes avec la même structure que précédemment
    anomalies_ouvertes = []
    for a in alertes_srv.get('anomalies_ouvertes', []):
        try:
            poste_nom = getattr(getattr(a.operation, 'poste', None), 'nom', None)
        except Exception:
            poste_nom = None
        anomalies_ouvertes.append({
            'id': a.id,
            'operation__poste__nom': poste_nom,
            'operation__ordre_fabrication__numero_of': a.operation.ordre_fabrication.numero_of if a.operation and a.operation.ordre_fabrication else None,
        })

    stock_bas = [
        {
            'designation': m.designation,
            'reference': m.reference,
            'quantite_stock': m.quantite_stock,
            'seuil_alerte': m.seuil_alerte,
            'unite_mesure': m.unite_mesure,
        }
        for m in alertes_srv.get('stock_bas', [])
    ]

    retards = []
    for item in alertes_srv.get('retards', []):
        p = item.get('pointage')
        depass = item.get('depassement_minutes')
        if not p:
            continue
        retards.append({
            'operation_titre': p.operation.titre if p.operation else None,
            'of_numero': p.operation.ordre_fabrication.numero_of if p.operation and p.operation.ordre_fabrication else None,
            'of_pk': p.operation.ordre_fabrication.pk if p.operation and p.operation.ordre_fabrication else None,
            'operateur_code': p.operateur.code if p.operateur else None,
            'depassement_minutes': depass,
        })

    alertes = {
        'anomalies_ouvertes': anomalies_ouvertes,
        'stock_bas': stock_bas,
        'retards': retards,
    }

    return JsonResponse({'kpis': kpis, 'chart': chart_data, 'alertes': alertes})

@login_required
def historique_view(request):
    # Par défaut, on affiche les 30 derniers jours
    jours_a_afficher = int(request.GET.get('jours', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=jours_a_afficher - 1)

    # On récupère les rapports sauvegardés
    rapports = DailyReport.objects.filter(date__gte=start_date, date__lte=end_date).order_by('date')
    
    # On prépare les données pour le graphique
    chart_labels = [r.date.strftime('%d/%m') for r in rapports]
    production_data = [r.pieces_fabriquees for r in rapports]
    rebut_data = [r.pieces_rebut for r in rapports]
    taux_rebut_data = [r.taux_rebut for r in rapports]
    
    context = {
        'rapports': rapports,
        'jours_a_afficher': jours_a_afficher,
        'chart': {
            'labels': chart_labels,
            'production_data': production_data,
            'rebut_data': rebut_data,
            'taux_rebut_data': taux_rebut_data,
        }
    }
    return render(request, 'suivi_production/historique.html', context)