from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from django.utils import timezone
from typing import Dict, List, Tuple

from django.db.models import Sum, F, QuerySet
from django.utils import timezone

from ..models import OrdreFabrication, Pointage, Anomalie, MatierePremiere


@dataclass
class DailyKpis:
    operations_en_cours: int
    operateurs_actifs: int
    qty_fabriquee_today: int
    taux_rebut_today: float
    today_iso: str


def get_ofs_finalises_le(jour: date) -> QuerySet:
    return OrdreFabrication.objects.exclude(statut='ARCHIVE').filter(
        date_premiere_finalisation=jour
    )


def compute_operational_counters(jour: date) -> Tuple[int, int]:
    base = Pointage.objects.exclude(operation__ordre_fabrication__statut='ARCHIVE')
    ops_en_cours = base.filter(heure_fin__isnull=True).count()
    operateurs_actifs = base.filter(heure_debut__date=jour).values('operateur').distinct().count()
    return ops_en_cours, operateurs_actifs


def compute_taux_rebut_ofs(ofs: QuerySet) -> Tuple[int, int, float]:
    total_prod = 0
    total_rebut = 0
    for of in ofs:
        total_prod += of.quantite_produite_actuelle
        total_rebut += of.quantite_rebut_totale
    total_decl = total_prod + total_rebut
    taux = (total_rebut / total_decl * 100) if total_decl > 0 else 0.0
    return total_prod, total_rebut, taux


def compute_kpis_for_date(jour: date) -> DailyKpis:
    ofs_today = get_ofs_finalises_le(jour)
    qty_fabriquee_today = sum(of.quantite_produite_actuelle for of in ofs_today)
    total_prod, total_rebut, taux = compute_taux_rebut_ofs(ofs_today)
    ops_en_cours, operateurs_actifs = compute_operational_counters(jour)
    return DailyKpis(
        operations_en_cours=ops_en_cours,
        operateurs_actifs=operateurs_actifs,
        qty_fabriquee_today=qty_fabriquee_today,
        taux_rebut_today=taux,
        today_iso=jour.isoformat(),
    )


def build_7day_series(jour: date):
    dates_chart = [(jour - timedelta(days=i)) for i in range(6, -1, -1)]
    start_date = jour - timedelta(days=6)
    ofs_periode = OrdreFabrication.objects.exclude(statut='ARCHIVE').filter(
        date_premiere_finalisation__gte=start_date,
        date_premiere_finalisation__lte=jour,
    )
    daily_totals = {d: {'prod': 0, 'rebut': 0} for d in dates_chart}
    for of in ofs_periode:
        d = of.date_premiere_finalisation
        if d in daily_totals:
            daily_totals[d]['prod'] += of.quantite_produite_actuelle
            daily_totals[d]['rebut'] += of.quantite_rebut_totale
    labels = [d.strftime('%d/%m') for d in dates_chart]
    production_data = []
    rebut_data = []
    taux_rebut_data = []
    for d in dates_chart:
        prod = daily_totals[d]['prod']
        reb = daily_totals[d]['rebut']
        production_data.append(prod)
        rebut_data.append(reb)
        total = prod + reb
        taux = (reb / total * 100) if total > 0 else 0.0
        taux_rebut_data.append(round(taux, 2))
    return labels, production_data, rebut_data, taux_rebut_data


def build_alertes(jour: date):
    base_pointages = Pointage.objects.exclude(operation__ordre_fabrication__statut='ARCHIVE')
    alertes = {
        'stock_bas': MatierePremiere.objects.filter(quantite_stock__lte=F('seuil_alerte')),
        'retards': [
            {'pointage': p, 'depassement_minutes': round(p.duree_minutes - p.operation.temps_prevu_minutes)}
            for p in base_pointages.filter(heure_fin__isnull=True).select_related('operation', 'operateur')
            if p.duree_minutes > p.operation.temps_prevu_minutes
        ],
        'anomalies_ouvertes': Anomalie.objects.filter(statut='OUVERTE')
            .exclude(operation__ordre_fabrication__statut='ARCHIVE')
            .select_related('operation__ordre_fabrication')
    }
    return alertes


def queryset_rebuts_par_of(numero: str = "", date_str: str = ""):
    """Construit le QuerySet des OF avec rebuts > 0, filtres par numéro et date de première finalisation.

    - numero: filtre contient sur numero_of
    - date_str: 'YYYY-MM-DD' pour filtrer date_premiere_finalisation
    Retourne un QuerySet annoté avec total_rebut et prêt pour tri.
    """
    qs = OrdreFabrication.objects.exclude(statut='ARCHIVE') \
        .annotate(total_rebut=Sum('operations__pointages__quantite_rebut')) \
        .filter(total_rebut__gt=0)
    if numero:
        qs = qs.filter(numero_of__icontains=numero.strip())
    if date_str:
        try:
            filter_date = timezone.datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
            qs = qs.filter(date_premiere_finalisation=filter_date)
        except Exception:
            pass
    return qs.order_by('-date_premiere_finalisation', '-total_rebut', '-date_creation')
