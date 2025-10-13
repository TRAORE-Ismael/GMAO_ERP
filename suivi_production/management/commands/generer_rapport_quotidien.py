from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count
from suivi_production.models import Pointage, DailyReport

class Command(BaseCommand):
    help = "Génère le rapport de production consolidé pour la journée précédente."

    def handle(self, *args, **options):
        # Par défaut, on génère le rapport pour la journée d'hier
        jour_a_traiter = timezone.now().date() - timedelta(days=1)
        
        self.stdout.write(f"Génération du rapport pour le {jour_a_traiter.strftime('%d/%m/%Y')}...")

        # On récupère tous les pointages terminés ce jour-là (sans se soucier des OFs)
        pointages_du_jour = Pointage.objects.filter(heure_fin__date=jour_a_traiter)

        # 1. Calcul des quantités
        agregats_production = pointages_du_jour.aggregate(
            total_fab=Sum('quantite_fabriquee'),
            total_rebut=Sum('quantite_rebut')
        )
        pieces_fab = agregats_production['total_fab'] or 0
        pieces_rebut = agregats_production['total_rebut'] or 0
        
        # 2. Calcul du taux de rebut
        total_declare = pieces_fab + pieces_rebut
        taux_rebut_jour = (pieces_rebut / total_declare * 100) if total_declare > 0 else 0
        
        # 3. Calcul des opérateurs actifs
        operateurs_actifs_jour = pointages_du_jour.values('operateur').distinct().count()

        # 4. Sauvegarde des données (Mise à jour si existe, sinon création)
        DailyReport.objects.update_or_create(
            date=jour_a_traiter,
            defaults={
                'pieces_fabriquees': pieces_fab,
                'pieces_rebut': pieces_rebut,
                'taux_rebut': taux_rebut_jour,
                'operateurs_actifs': operateurs_actifs_jour,
            }
        )
        
        self.stdout.write(self.style.SUCCESS("Rapport généré et sauvegardé avec succès !"))