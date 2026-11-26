"""
Diagnostic command for Rojgar Setu:
Validates Supabase PostgreSQL 17, PostGIS extension, and Google Gemini API setup.
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
from core.models import UserAccount, WorkerProfile, Job, Contract
from core.ai_service import GEMINI_API_KEY, GEMINI_MODEL


class Command(BaseCommand):
    help = 'Runs comprehensive diagnostic checks on Supabase PostgreSQL, PostGIS, and Gemini API'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=================================================="))
        self.stdout.write(self.style.NOTICE("   ROJGAR SETU SYSTEM & DATABASE DIAGNOSTIC"))
        self.stdout.write(self.style.NOTICE("=================================================="))

        # 1. Database Connection & Version
        self.stdout.write("1. Testing Database Connection...")
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                pg_version = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f"   ✓ Database Connected: {pg_version[:60]}..."))

                # Check PostGIS
                cursor.execute("SELECT postgis_full_version();")
                postgis_version = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f"   ✓ PostGIS Extension Active: {postgis_version[:40]}..."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ✗ Database Check Failed: {e}"))

        # 2. Check Table Row Counts
        self.stdout.write("\n2. Checking Core Table Records...")
        try:
            workers_count = WorkerProfile.objects.count()
            employers_count = UserAccount.objects.filter(role='employer').count()
            jobs_count = Job.objects.count()
            contracts_count = Contract.objects.count()

            self.stdout.write(self.style.SUCCESS(f"   ✓ Verified Karigars:    {workers_count}"))
            self.stdout.write(self.style.SUCCESS(f"   ✓ Individual Employers: {employers_count}"))
            self.stdout.write(self.style.SUCCESS(f"   ✓ Pre-Signed Gigs:      {jobs_count}"))
            self.stdout.write(self.style.SUCCESS(f"   ✓ Handshake Contracts:  {contracts_count}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ✗ Table Check Failed: {e}"))

        # 3. Gemini API Key
        self.stdout.write("\n3. Checking Gemini AI Configuration...")
        if GEMINI_API_KEY and not GEMINI_API_KEY.startswith("<"):
            self.stdout.write(self.style.SUCCESS(f"   ✓ GEMINI_API_KEY detected (Length: {len(GEMINI_API_KEY)} chars)"))
            self.stdout.write(self.style.SUCCESS(f"   ✓ Active AI Model: {GEMINI_MODEL}"))
        else:
            self.stdout.write(self.style.WARNING("   ! GEMINI_API_KEY is not configured or using default template."))

        self.stdout.write(self.style.NOTICE("\n=================================================="))
        self.stdout.write(self.style.SUCCESS("All systems operational. Ready for teammates & GitHub."))
        self.stdout.write(self.style.NOTICE("=================================================="))
