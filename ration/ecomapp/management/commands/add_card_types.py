from django.core.management.base import BaseCommand
from ecomapp.models import CardType


class Command(BaseCommand):
    help = 'Add default card types with colors'

    def handle(self, *args, **options):
        card_types = [
            {'code': 'APL', 'name': 'Above Poverty Line', 'color': 'white'},
            {'code': 'BPL', 'name': 'Below Poverty Line', 'color': 'pink'},
            {'code': 'AAY', 'name': 'Antyodaya Anna Yojana', 'color': 'yellow'},
            {'code': 'PHH', 'name': 'Priority House Hold', 'color': 'cream'},
        ]

        for card_data in card_types:
            card_type, created = CardType.objects.get_or_create(
                code=card_data['code'],
                defaults={
                    'name': card_data['name'],
                    'color': card_data['color']
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created card type: {card_type}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Card type already exists: {card_type}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Card types setup completed!')
        )