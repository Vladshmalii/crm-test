from unittest import mock

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from crm.choices import MessageStatus, SenderType, UserRole
from crm.models import Dialog, Fan, Message, Persona, User


class UserModelTest(TestCase):
    def test_is_chatter(self):
        user = User(role=UserRole.CHATTER)
        self.assertTrue(user.is_chatter)
        self.assertFalse(user.is_teamlead)

    def test_is_teamlead(self):
        user = User(role=UserRole.TEAMLEAD)
        self.assertTrue(user.is_teamlead)
        self.assertFalse(user.is_chatter)


class DialogModelTest(TestCase):
    def setUp(self):
        self.persona = Persona.objects.create(name='Alice')
        self.fan = Fan.objects.create(internal_id='fan_1', name='Fan 1')
        self.chatter = User.objects.create_user(
            username='chatter1', password='test', role=UserRole.CHATTER,
        )

    def test_dialog_str(self):
        dialog = Dialog.objects.create(
            persona=self.persona, fan=self.fan, chatter=self.chatter,
        )
        self.assertIn('Alice', str(dialog))
        self.assertIn('Fan 1', str(dialog))

    def test_unique_persona_fan(self):
        Dialog.objects.create(persona=self.persona, fan=self.fan, chatter=self.chatter)
        with self.assertRaises(Exception):
            Dialog.objects.create(persona=self.persona, fan=self.fan, chatter=self.chatter)


class AuthAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.chatter = User.objects.create_user(
            username='chatter1', password='testpass', role=UserRole.CHATTER,
        )
        self.teamlead = User.objects.create_user(
            username='teamlead1', password='testpass', role=UserRole.TEAMLEAD,
        )

    def test_login_returns_token_with_role(self):
        response = self.client.post('/api/auth/login/', {
            'username': 'chatter1',
            'password': 'testpass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_invalid_credentials(self):
        response = self.client.post('/api/auth/login/', {
            'username': 'chatter1',
            'password': 'wrongpass',
        })
        self.assertEqual(response.status_code, 401)


class DialogViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.chatter = User.objects.create_user(
            username='chatter1', password='testpass', role=UserRole.CHATTER,
        )
        self.teamlead = User.objects.create_user(
            username='teamlead1', password='testpass', role=UserRole.TEAMLEAD,
        )
        self.persona = Persona.objects.create(name='Alice')
        self.fan = Fan.objects.create(internal_id='fan_1', name='Fan 1')
        self.dialog = Dialog.objects.create(
            persona=self.persona, fan=self.fan, chatter=self.chatter,
        )

    def test_chatter_can_list_dialogs(self):
        self.client.force_authenticate(user=self.chatter)
        response = self.client.get('/api/dialogs/')
        self.assertEqual(response.status_code, 200)

    def test_teamlead_cannot_list_dialogs(self):
        self.client.force_authenticate(user=self.teamlead)
        response = self.client.get('/api/dialogs/')
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_cannot_list_dialogs(self):
        response = self.client.get('/api/dialogs/')
        self.assertEqual(response.status_code, 401)

    def test_chatter_can_delete_dialog(self):
        self.client.force_authenticate(user=self.chatter)
        response = self.client.delete(f'/api/dialogs/{self.dialog.id}/')
        self.assertEqual(response.status_code, 204)

    def test_chatter_sees_only_own_dialogs(self):
        chatter2 = User.objects.create_user(
            username='chatter2', password='testpass', role=UserRole.CHATTER,
        )
        self.client.force_authenticate(user=chatter2)
        response = self.client.get('/api/dialogs/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get('results', [])), 0)


class MarkDialogReadTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.chatter = User.objects.create_user(
            username='chatter1', password='testpass', role=UserRole.CHATTER,
        )
        self.persona = Persona.objects.create(name='Alice')
        self.fan = Fan.objects.create(internal_id='fan_1', name='Fan 1')
        self.dialog = Dialog.objects.create(
            persona=self.persona, fan=self.fan, chatter=self.chatter, unread_count=5,
        )

    def test_mark_read_resets_counter(self):
        self.client.force_authenticate(user=self.chatter)
        response = self.client.post(f'/api/dialogs/{self.dialog.id}/read/')
        self.assertEqual(response.status_code, 200)
        self.dialog.refresh_from_db()
        self.assertEqual(self.dialog.unread_count, 0)


class TeamleadOverviewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.teamlead = User.objects.create_user(
            username='teamlead1', password='testpass', role=UserRole.TEAMLEAD,
        )
        self.chatter = User.objects.create_user(
            username='chatter1', password='testpass', role=UserRole.CHATTER,
        )

    @mock.patch('crm.api.frontend.restful.views.views.presence_service')
    def test_teamlead_can_access_overview(self, mock_presence):
        mock_presence.get_online_statuses.return_value = {self.chatter.id: True}
        self.client.force_authenticate(user=self.teamlead)
        response = self.client.get('/api/teamlead/overview/')
        self.assertEqual(response.status_code, 200)

    def test_chatter_cannot_access_overview(self):
        self.client.force_authenticate(user=self.chatter)
        response = self.client.get('/api/teamlead/overview/')
        self.assertEqual(response.status_code, 403)


@override_settings(CHANNEL_LAYERS={'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}})
class EmulateIncomingTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.chatter = User.objects.create_user(
            username='chatter1', password='testpass', role=UserRole.CHATTER,
        )

    def test_emulate_requires_auth(self):
        response = self.client.post('/api/emulate/incoming/', {'text': 'test'})
        self.assertEqual(response.status_code, 401)

    def test_emulate_creates_message(self):
        self.client.force_authenticate(user=self.chatter)
        response = self.client.post('/api/emulate/incoming/', {
            'text': 'Hello from fan',
            'force_new': True,
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('message_id', response.data)
        self.assertIn('dialog_id', response.data)

        msg = Message.objects.get(id=response.data['message_id'])
        self.assertEqual(msg.text, 'Hello from fan')
        self.assertEqual(msg.sender_type, SenderType.FAN)
