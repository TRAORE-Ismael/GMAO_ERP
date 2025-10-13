import datetime
from django.test import TestCase
from django.utils import timezone
from ..models import OrdreFabrication, Operation, PosteDeTravail
from ..services.reporting import compute_kpis_for_date, build_7day_series, queryset_rebuts_par_of


class ReportingServicesTests(TestCase):
    def setUp(self):
        self.poste = PosteDeTravail.objects.create(nom='TestPoste')
        # OF1 terminé aujourd'hui, prod 10, rebut 2
        self.of1 = OrdreFabrication.objects.create(numero_of='OF1', titre='OF 1', quantite_a_produire=20, statut='TERMINE', date_premiere_finalisation=timezone.now().date())
        op1 = Operation.objects.create(ordre_fabrication=self.of1, numero_phase=1, poste=self.poste, titre='Op1', temps_prevu_minutes=10)
        # Simuler sorties via propriétés: on ne crée pas de pointages ici; on patcherait idéalement ou créerait des pointages
        # Pour ce test minimal, on définit des attributs dynamiques si possibles, mais les propriétés lisent les agrégats
        # Donc ce test se concentrera sur la présence/absence et la série de 7 jours sans entrer dans le détail des quantités.

    def test_kpis_today_runs(self):
        today = timezone.now().date()
        daily = compute_kpis_for_date(today)
        # Vérifie que l'objet a les attributs attendus
        self.assertTrue(hasattr(daily, 'operations_en_cours'))
        self.assertTrue(hasattr(daily, 'operateurs_actifs'))
        self.assertTrue(hasattr(daily, 'qty_fabriquee_today'))
        self.assertTrue(hasattr(daily, 'taux_rebut_today'))

    def test_7day_series_labels_length(self):
        today = timezone.now().date()
        labels, prod, reb, taux = build_7day_series(today)
        self.assertEqual(len(labels), 7)
        self.assertEqual(len(prod), 7)
        self.assertEqual(len(reb), 7)
        self.assertEqual(len(taux), 7)

    def test_queryset_rebuts_filters(self):
        # Sans rebuts, le QS doit être vide
        qs = queryset_rebuts_par_of(numero='OF1')
        self.assertEqual(qs.count(), 0)
