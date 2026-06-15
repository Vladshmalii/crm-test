import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from crm.models import User, Model, Fan, Dialog, Message

class Command(BaseCommand):
    help = 'Seed demo data for CRM'

    def handle(self, *args, **options):
        self.stdout.write("Deleting old data...")
        User.objects.all().delete()
        Model.objects.all().delete()
        Fan.objects.all().delete()
        
        self.stdout.write("Creating Users...")
        teamlead = User.objects.create_user(username='teamlead', password='password123', role='teamlead')
        chatter1 = User.objects.create_user(username='chatter1', password='password123', role='chatter')
        chatter2 = User.objects.create_user(username='chatter2', password='password123', role='chatter')
        
        self.stdout.write("Creating Models...")
        model1 = Model.objects.create(name='Alice')
        model2 = Model.objects.create(name='Bob')
        
        self.stdout.write("Creating Fans and Dialogs...")
        fans = []
        for i in range(5):
            fans.append(Fan.objects.create(internal_id=f'fan_{i}', name=f'Fan {i}'))
            
        # Dialogs for chatter 1
        d1 = Dialog.objects.create(model=model1, fan=fans[0], chatter=chatter1)
        d2 = Dialog.objects.create(model=model1, fan=fans[1], chatter=chatter1)
        d3 = Dialog.objects.create(model=model2, fan=fans[2], chatter=chatter1)
        
        # Dialogs for chatter 2
        d4 = Dialog.objects.create(model=model2, fan=fans[3], chatter=chatter2)
        
        self.stdout.write("Creating Messages...")
        now = timezone.now()
        
        # Normal dialog
        Message.objects.create(dialog=d1, sender_type='fan', text='Hello Alice!', created_at=now - timedelta(minutes=10))
        Message.objects.create(dialog=d1, sender_type='chatter', text='Hi there!', created_at=now - timedelta(minutes=5))
        d1.last_message_at = now - timedelta(minutes=5)
        d1.unread_count = 0
        d1.save()
        
        # Overdue dialog (Wait time > OVERDUE_THRESHOLD_MINUTES)
        Message.objects.create(dialog=d2, sender_type='fan', text='Are you there?', created_at=now - timedelta(minutes=15))
        d2.last_message_at = now - timedelta(minutes=15)
        d2.unread_count = 1
        d2.save()

        # Another overdue dialog
        Message.objects.create(dialog=d3, sender_type='fan', text='I have a question.', created_at=now - timedelta(minutes=20))
        d3.last_message_at = now - timedelta(minutes=20)
        d3.unread_count = 1
        d3.save()
        
        # Normal dialog
        Message.objects.create(dialog=d4, sender_type='fan', text='Hey Bob', created_at=now - timedelta(minutes=2))
        d4.last_message_at = now - timedelta(minutes=2)
        d4.unread_count = 1
        d4.save()
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded demo data!'))
        self.stdout.write("Test accounts:")
        self.stdout.write("Teamlead: teamlead / password123")
        self.stdout.write("Chatter: chatter1 / password123")
        self.stdout.write("Chatter: chatter2 / password123")
