from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from suivi_production.models import OrdreFabrication

class Command(BaseCommand):
    help = "Archive les Ordres de Fabrication terminés depuis plus de 30 jours."

    def handle(self, *args, **options):
        # Définir la date limite : il y a 30 jours
        limite_archivage = timezone.now() - timedelta(days=1)
        
        # Sélectionner les OFs qui sont 'TERMINE' et dont la dernière modification est antérieure à la date limite
        # On utilise 'date_modification' car c'est la date la plus fiable pour savoir quand l'OF a été "touché" pour la dernière fois.
        ofs_a_archiver = OrdreFabrication.objects.filter(
            statut='TERMINE',
            date_creation__lt=limite_archivage # <-- CORRIGÉ
        )
        
        nombre_ofs = ofs_a_archiver.count()
        
        if nombre_ofs > 0:
            # Mettre à jour le statut de tous ces OFs en 'ARCHIVE' en une seule requête
            ofs_a_archiver.update(statut='ARCHIVE')
            self.stdout.write(self.style.SUCCESS(f'{nombre_ofs} OF(s) ont été archivé(s) avec succès.'))
        else:
            self.stdout.write(self.style.NOTICE('Aucun OF à archiver.'))