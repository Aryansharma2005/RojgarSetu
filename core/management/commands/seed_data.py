"""
Backward-compatible proxy command for seed_data.
Redirects to seed_p2p_data.
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Seeds realistic Indian P2P gig economy data into Supabase PostgreSQL'

    def handle(self, *args, **options):
        call_command('seed_p2p_data')
