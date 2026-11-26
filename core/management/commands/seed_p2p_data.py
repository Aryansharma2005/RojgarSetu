"""
Management command to seed realistic Indian P2P gig economy data for Rojgar Setu.
Populates:
1. Vocational Categories (Bilingual)
2. Individual Homeowner Employers (Noida, Delhi, Gurugram GPS)
3. Verified Individual Karigars (with AI test scores & Aadhaar badges)
4. Pre-Signed Jobs with 1st-Party Digital Signatures
5. Active Chat Room & Handshake Pipeline
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import (
    UserAccount, WorkerProfile, Job, Application,
    ChatRoom, ChatMessage, Contract, Category
)
from core.ai_service import generate_dynamic_contract_terms, generate_worker_ai_bio


class Command(BaseCommand):
    help = 'Seeds initial realistic Indian P2P gig data into Supabase PostgreSQL'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Initializing Rojgar Setu P2P Seed Engine..."))

        # 1. Seed Categories
        categories_data = [
            {
                'name_en': 'Electrician',
                'name_hi': 'इलेक्ट्रीशियन',
                'slug': 'electrician',
                'icon': 'bolt',
                'typical_wage_daily': 700,
                'description': 'Wiring, switches, MCB repair, inverter setup, appliances.'
            },
            {
                'name_en': 'Plumber',
                'name_hi': 'प्लंबर',
                'slug': 'plumber',
                'icon': 'wrench',
                'typical_wage_daily': 650,
                'description': 'Pipes, taps, motor pumps, leakages, bathroom fittings.'
            },
            {
                'name_en': 'House Maid',
                'name_hi': 'घरेलू सहायिका (झाड़ू/पोछा/बर्तन)',
                'slug': 'house-maid',
                'icon': 'home',
                'typical_wage_daily': 500,
                'description': 'Daily cleaning, jhadu-pochha, utensils, dusting, laundry.'
            },
            {
                'name_en': 'Cook',
                'name_hi': 'रसोइया / बावर्ची',
                'slug': 'cook',
                'icon': 'utensils',
                'typical_wage_daily': 750,
                'description': 'Veg/non-veg cooking, breakfast, lunch, party meals, hygiene.'
            },
            {
                'name_en': 'Carpenter',
                'name_hi': 'बढ़ई',
                'slug': 'carpenter',
                'icon': 'hammer',
                'typical_wage_daily': 800,
                'description': 'Furniture repair, door locks, woodwork, modular fitting.'
            },
            {
                'name_en': 'Painter',
                'name_hi': 'पेंटर / रंगसाज',
                'slug': 'painter',
                'icon': 'paint-roller',
                'typical_wage_daily': 700,
                'description': 'Wall painting, waterproofing, touch-ups, putty.'
            },
            {
                'name_en': 'Gardener',
                'name_hi': 'माली',
                'slug': 'gardener',
                'icon': 'leaf',
                'typical_wage_daily': 550,
                'description': 'Lawn maintenance, trimming, potting, pest control.'
            },
            {
                'name_en': 'Driver',
                'name_hi': 'निजी चालक',
                'slug': 'driver',
                'icon': 'car',
                'typical_wage_daily': 850,
                'description': 'Personal car driving, local errands, outstation trips.'
            },
            {
                'name_en': 'Mechanic',
                'name_hi': 'मैकेनिक',
                'slug': 'mechanic',
                'icon': 'cog',
                'typical_wage_daily': 750,
                'description': 'Two/four-wheeler service, engine troubleshooting, puncture, brake repair, appliance fixing.'
            },
            {
                'name_en': 'Construction Worker',
                'name_hi': 'निर्माण श्रमिक / बेलदार',
                'slug': 'construction-worker',
                'icon': 'hard-hat',
                'typical_wage_daily': 600,
                'description': 'Masonry support, concrete mixing, loading/unloading, tile laying helper, demolition.'
            },
        ]

        for cat in categories_data:
            Category.objects.update_or_create(slug=cat['slug'], defaults=cat)
        self.stdout.write(self.style.SUCCESS(f"✓ Seeded {len(categories_data)} vocational trade categories."))

        # 2. Seed Individual Homeowner Employers
        employers_data = [
            {
                'name': 'Anita Sharma',
                'phone': '9811223344',
                'email': 'anita.sharma@example.com',
                'role': 'employer',
                'city': 'Noida',
                'locality': 'Sector 62, Stellar Park',
                'latitude': 28.6280,
                'longitude': 77.3649,
                'is_aadhaar_verified': True,
            },
            {
                'name': 'Vikram Malhotra',
                'phone': '9822334455',
                'email': 'vikram.malhotra@example.com',
                'role': 'employer',
                'city': 'Ghaziabad',
                'locality': 'Ahinsa Khand 2, Indirapuram',
                'latitude': 28.6415,
                'longitude': 77.3712,
                'is_aadhaar_verified': True,
            },
            {
                'name': 'Priya Sengupta',
                'phone': '9833445566',
                'email': 'priya.sengupta@example.com',
                'role': 'employer',
                'city': 'New Delhi',
                'locality': 'Block D, Lajpat Nagar II',
                'latitude': 28.5677,
                'longitude': 77.2433,
                'is_aadhaar_verified': True,
            },
            {
                'name': 'Rohit Khurana',
                'phone': '9844556677',
                'email': 'rohit.khurana@example.com',
                'role': 'employer',
                'city': 'Gurugram',
                'locality': 'DLF Phase 3, Sector 24',
                'latitude': 28.4912,
                'longitude': 77.0935,
                'is_aadhaar_verified': True,
            }
        ]

        employer_objs = []
        for emp_d in employers_data:
            user, created = UserAccount.objects.update_or_create(
                phone=emp_d['phone'],
                defaults={
                    'name': emp_d['name'],
                    'email': emp_d['email'],
                    'role': 'employer',
                    'city': emp_d['city'],
                    'locality': emp_d['locality'],
                    'latitude': emp_d['latitude'],
                    'longitude': emp_d['longitude'],
                    'is_aadhaar_verified': emp_d['is_aadhaar_verified'],
                }
            )
            user.set_password('password123')
            user.save()
            employer_objs.append(user)

        self.stdout.write(self.style.SUCCESS(f"✓ Seeded {len(employer_objs)} demo individual homeowners."))

        # 3. Seed Individual Karigars (Job Seekers)
        workers_data = [
            {
                'name': 'Manoj Kumar Prajapati',
                'phone': '9870001111',
                'email': 'manoj.prajapati@example.com',
                'city': 'Noida',
                'locality': 'Rasoolpur Nawada, Sector 62',
                'latitude': 28.6275,
                'longitude': 77.3655,
                'trades': ['Plumber', 'Electrician'],
                'primary_trade': 'Plumber',
                'experience': 6,
                'wage': 650.00,
                'score': 5,
                'total': 5,
                'aadhaar': True,
            },
            {
                'name': 'Sunita Devi',
                'phone': '9870002222',
                'email': 'sunita.devi@example.com',
                'city': 'Ghaziabad',
                'locality': 'Kanawani Village, Indirapuram',
                'latitude': 28.6420,
                'longitude': 77.3700,
                'trades': ['House Maid', 'Cook'],
                'primary_trade': 'House Maid',
                'experience': 5,
                'wage': 500.00,
                'score': 4,
                'total': 4,
                'aadhaar': True,
            },
            {
                'name': 'Ramesh Yadav',
                'phone': '9870003333',
                'email': 'ramesh.yadav@example.com',
                'city': 'New Delhi',
                'locality': 'Kotla Mubarakpur, Lajpat Nagar',
                'latitude': 28.5685,
                'longitude': 77.2420,
                'trades': ['Electrician', 'Carpenter'],
                'primary_trade': 'Electrician',
                'experience': 8,
                'wage': 800.00,
                'score': 5,
                'total': 5,
                'aadhaar': True,
            },
            {
                'name': 'Bablu Kumar',
                'phone': '9870004444',
                'email': 'bablu.painter@example.com',
                'city': 'Gurugram',
                'locality': 'Nathupur, DLF Phase 3',
                'latitude': 28.4925,
                'longitude': 77.0910,
                'trades': ['Painter', 'Gardener'],
                'primary_trade': 'Painter',
                'experience': 4,
                'wage': 700.00,
                'score': 4,
                'total': 5,
                'aadhaar': False,
            }
        ]

        worker_objs = []
        for wrk_d in workers_data:
            user, created = UserAccount.objects.update_or_create(
                phone=wrk_d['phone'],
                defaults={
                    'name': wrk_d['name'],
                    'email': wrk_d['email'],
                    'role': 'worker',
                    'city': wrk_d['city'],
                    'locality': wrk_d['locality'],
                    'latitude': wrk_d['latitude'],
                    'longitude': wrk_d['longitude'],
                    'is_aadhaar_verified': wrk_d['aadhaar'],
                }
            )
            user.set_password('password123')
            user.save()

            bio = generate_worker_ai_bio(
                name=user.name,
                trades=wrk_d['trades'],
                experience_years=wrk_d['experience'],
                score=wrk_d['score'],
                total_mcqs=wrk_d['total'],
                language='hi'
            )

            WorkerProfile.objects.update_or_create(
                user=user,
                defaults={
                    'karigar_id': f"RS-IND-{user.phone[-4:]}",
                    'trades': wrk_d['trades'],
                    'primary_trade': wrk_d['primary_trade'],
                    'experience_years': wrk_d['experience'],
                    'expected_wage': wrk_d['wage'],
                    'wage_type': 'daily',
                    'is_available': True,
                    'latitude': user.latitude,
                    'longitude': user.longitude,
                    'city': user.city,
                    'locality': user.locality,
                    'verification_badges': {
                        'aadhaar_verified': wrk_d['aadhaar'],
                        'mcq_passed': True,
                        'mcq_score': f"{wrk_d['score']}/{wrk_d['total']}",
                        'skill_badge': 'Skills Tested ★',
                        'score_pct': int((wrk_d['score'] / wrk_d['total']) * 100)
                    },
                    'ai_bio': bio,
                    'rating_avg': 4.90,
                    'total_reviews': 12,
                }
            )
            worker_objs.append(user)

        self.stdout.write(self.style.SUCCESS(f"✓ Seeded {len(worker_objs)} verified individual Karigars."))

        # 4. Seed Hyperlocal Jobs with 1st-Party Pre-Signed Dynamic Contracts
        jobs_data = [
            {
                'employer': employer_objs[0],  # Anita Sharma in Noida Sector 62
                'title': 'Urgent Plumber for Kitchen Pipe Leakage & Tap Fitting',
                'category': 'Plumber',
                'tasks': 'Inspect water leakage beneath kitchen sink, replace damaged rubber washer, and install new CPVC angle valve.',
                'duration': '2 Hours',
                'price': 650.00,
                'locality': 'Sector 62, Stellar Park, Noida',
                'city': 'Noida',
                'lat': 28.6280,
                'lng': 77.3649,
            },
            {
                'employer': employer_objs[1],  # Vikram Malhotra in Indirapuram
                'title': 'Full-Day Deep Cleaning Maid (Jhadu-Pochha-Bartan)',
                'category': 'House Maid',
                'tasks': 'Complete floor wet-mop with phenyl, kitchen utensils wash, balcony wash, and living room dusting.',
                'duration': '1 Day',
                'price': 500.00,
                'locality': 'Ahinsa Khand 2, Indirapuram',
                'city': 'Ghaziabad',
                'lat': 28.6415,
                'lng': 77.3712,
            },
            {
                'employer': employer_objs[2],  # Priya Sengupta in Lajpat Nagar
                'title': 'Electrician for Main MCB Tripping & Inverter Wiring',
                'category': 'Electrician',
                'tasks': 'Diagnose short circuit tripping the 32A DP switch in the bedroom circuit, isolate fault, rewire inverter output.',
                'duration': '3 Hours',
                'price': 800.00,
                'locality': 'Block D, Lajpat Nagar II, Delhi',
                'city': 'New Delhi',
                'lat': 28.5677,
                'lng': 77.2433,
            },
            {
                'employer': employer_objs[3],  # Rohit Khurana in Gurugram
                'title': 'Cook Required for Family Dinner & North Indian Meals',
                'category': 'Cook',
                'tasks': 'Prepare fresh chapati, dal makhani, paneer bhurji, and salad for 4 adults with strict kitchen hygiene.',
                'duration': '2.5 Hours',
                'price': 700.00,
                'locality': 'DLF Phase 3, Sector 24, Gurugram',
                'city': 'Gurugram',
                'lat': 28.4912,
                'lng': 77.0935,
            }
        ]

        created_jobs = []
        for j_d in jobs_data:
            emp = j_d['employer']
            terms = generate_dynamic_contract_terms(
                category=j_d['category'],
                price=j_d['price'],
                duration=j_d['duration'],
                tasks=j_d['tasks'],
                employer_name=emp.name
            )
            timestamp = int(timezone.now().timestamp())
            employer_sig = f"DIGITAL_SIGN_EMP_{emp.id}_{timestamp}"

            job, _ = Job.objects.update_or_create(
                employer=emp,
                title=j_d['title'],
                defaults={
                    'category': j_d['category'],
                    'responsibilities': j_d['tasks'],
                    'duration_text': j_d['duration'],
                    'offered_price': j_d['price'],
                    'wage_period': 'per_job',
                    'locality': j_d['locality'],
                    'city': j_d['city'],
                    'latitude': j_d['lat'],
                    'longitude': j_d['lng'],
                    'contract_terms': terms,
                    'employer_signature': employer_sig,
                    'employer_signed_at': timezone.now(),
                    'is_active': True,
                    'status': 'active'
                }
            )
            created_jobs.append(job)

        self.stdout.write(self.style.SUCCESS(f"✓ Seeded {len(created_jobs)} pre-signed hyperlocal jobs."))

        # 5. Seed Pre-Initiated Application & In-App Chat Room for Testing
        # Manoj Prajapati applies for Anita Sharma's Plumbing job (450m away in Noida Sec 62!)
        plumbing_job = created_jobs[0]
        manoj = worker_objs[0]

        app, _ = Application.objects.update_or_create(
            job=plumbing_job,
            worker=manoj,
            defaults={
                'fit_score': 100.0,
                'status': 'contract_forwarded',
                'notes': 'Experienced plumber nearby. 100% score in safety assessment.'
            }
        )

        chat_room, _ = ChatRoom.objects.update_or_create(
            application=app,
            defaults={
                'job': plumbing_job,
                'employer': plumbing_job.employer,
                'worker': manoj,
            }
        )

        ChatMessage.objects.get_or_create(
            chat_room=chat_room,
            sender=plumbing_job.employer,
            message="नमस्ते मनोज जी, मैंने आपकी प्रोफाइल और 100% AI टेस्ट स्कोर देखा। क्या आप आज शाम 4 बजे आ सकते हैं?",
            defaults={'is_system_notice': False}
        )
        ChatMessage.objects.get_or_create(
            chat_room=chat_room,
            sender=manoj,
            message="नमस्ते मैम! हाँ, मैं पास ही सेक्टर 62 में हूँ और 4 बजे तक अपने सभी टूल्स के साथ आ जाऊँगा।",
            defaults={'is_system_notice': False}
        )
        ChatMessage.objects.get_or_create(
            chat_room=chat_room,
            sender=plumbing_job.employer,
            message=f"[CONTRACT FORWARDED] Pre-signed P2P Contract forwarded (₹{plumbing_job.offered_price:,.2f}). Please review and sign to unlock mutual phone numbers.",
            defaults={'is_system_notice': True}
        )

        # Attach forwarded contract
        Contract.objects.update_or_create(
            chat_room=chat_room,
            defaults={
                'job': plumbing_job,
                'employer': plumbing_job.employer,
                'worker': manoj,
                'contract_text': plumbing_job.contract_terms,
                'agreed_price': plumbing_job.offered_price,
                'duration_agreed': plumbing_job.duration_text,
                'employer_signature': plumbing_job.employer_signature,
                'employer_signed_at': plumbing_job.employer_signed_at,
                'status': 'pending_worker_signature'
            }
        )

        self.stdout.write(self.style.SUCCESS("✓ Seeded active In-App Chat & Contract Handshake Pipeline."))
        self.stdout.write(self.style.SUCCESS("======================================================"))
        self.stdout.write(self.style.SUCCESS("🎉 ROJGAR SETU P2P SEEDING COMPLETED SUCCESSFULLY!"))
        self.stdout.write(self.style.SUCCESS("Demo Employer: Phone: 9811223344  Password: password123"))
        self.stdout.write(self.style.SUCCESS("Demo Worker:   Phone: 9870001111  Password: password123"))
        self.stdout.write(self.style.SUCCESS("======================================================"))
