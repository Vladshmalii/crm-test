from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from crm.choices import SenderType, UserRole
from crm.models import Dialog, Fan, Message, Persona, User


class Command(BaseCommand):
    help = 'Seed demo data for CRM'

    def handle(self, *args, **options):
        if User.objects.filter(username='chatter1').exists():
            self.stdout.write(self.style.SUCCESS('Demo data already exists! Skipping seed.'))
            return

        self.stdout.write('Creating Users...')
        User.objects.create_user(username='teamlead', password='password123', role=UserRole.TEAMLEAD)
        chatter1 = User.objects.create_user(username='chatter1', password='password123', role=UserRole.CHATTER)
        chatter2 = User.objects.create_user(username='chatter2', password='password123', role=UserRole.CHATTER)

        self.stdout.write('Creating Personas...')
        persona1 = Persona.objects.create(name='Alice')
        persona2 = Persona.objects.create(name='Bob')

        self.stdout.write('Creating Fans and Dialogs...')
        fans = [Fan.objects.create(internal_id=f'fan_{i}', name=f'Fan {i}') for i in range(5)]

        d1 = Dialog.objects.create(persona=persona1, fan=fans[0], chatter=chatter1)
        d2 = Dialog.objects.create(persona=persona1, fan=fans[1], chatter=chatter1)
        d3 = Dialog.objects.create(persona=persona2, fan=fans[2], chatter=chatter1)
        d4 = Dialog.objects.create(persona=persona2, fan=fans[3], chatter=chatter2)

        self.stdout.write('Creating Messages...')
        now = timezone.now()

        Message.objects.create(dialog=d1, sender_type=SenderType.FAN, text='Hello Alice!', created_at=now - timedelta(minutes=10))
        Message.objects.create(dialog=d1, sender_type=SenderType.CHATTER, text='Hi there!', created_at=now - timedelta(minutes=5))
        d1.last_message_at = now - timedelta(minutes=5)
        d1.unread_count = 0
        d1.save(update_fields=['last_message_at', 'unread_count'])

        Message.objects.create(dialog=d2, sender_type=SenderType.FAN, text='Are you there?', created_at=now - timedelta(minutes=15))
        d2.last_message_at = now - timedelta(minutes=15)
        d2.unread_count = 1
        d2.save(update_fields=['last_message_at', 'unread_count'])

        Message.objects.create(dialog=d3, sender_type=SenderType.FAN, text='I have a question.', created_at=now - timedelta(minutes=20))
        d3.last_message_at = now - timedelta(minutes=20)
        d3.unread_count = 1
        d3.save(update_fields=['last_message_at', 'unread_count'])

        Message.objects.create(dialog=d4, sender_type=SenderType.FAN, text='Hey Bob', created_at=now - timedelta(minutes=2))
        d4.last_message_at = now - timedelta(minutes=2)
        d4.unread_count = 1
        d4.save(update_fields=['last_message_at', 'unread_count'])

        self.stdout.write(self.style.SUCCESS('Successfully seeded demo data!'))
        self.stdout.write('Test accounts:')
        self.stdout.write('Teamlead: teamlead / password123')
        self.stdout.write('Chatter: chatter1 / password123')
        self.stdout.write('Chatter: chatter2 / password123')
