# CRM Module

This is a CRM module for chatters and teamleads.

## Architecture

- **REST API (Django DRF)**: Used for stateless operations like fetching dialog history, logging in, and marking messages as read. This ensures we don't overload WebSockets with heavy historical data.
- **WebSockets (Django Channels)**: Used exclusively for real-time live events (new messages, unread count updates, teamlead presence/overdue updates). This keeps real-time connections lightweight and responsive.

## Prerequisites

- Docker and Docker Compose

## Запуск

1. Run the following command to start the application (Backend, Frontend, PostgreSQL, Redis):
```bash
docker-compose up --build
```
2. Once the containers are running, you need to seed the demo data. In a new terminal, run:
```bash
docker-compose exec web python manage.py seed_demo
```

### Accessing the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000

### Test Accounts

- **Teamlead**: `teamlead` / `password123`
- **Chatter 1**: `chatter1` / `password123`
- **Chatter 2**: `chatter2` / `password123`

## Emulate Incoming Messages

To simulate an incoming message from a fan and test the real-time SLA / WebSocket functionality:
1. Open http://localhost:5173 and log in as `chatter1`. You will see active dialogs.
2. In another terminal or API tool (like Postman), send a POST request to the emulate endpoint:
```bash
curl -X POST http://localhost:8000/api/emulate/incoming/ \
     -H "Content-Type: application/json" \
     -d '{"text": "Hey, I need an answer right now!"}'
```
3. You will immediately see the message appear in the chatter's UI.
4. If you wait for `OVERDUE_THRESHOLD_MINUTES` (configured in `.env`), the Teamlead monitor will highlight the dialog as overdue.

## Деплой

Приложение успешно развернуто на бесплатном хостинге Render:
- **Frontend URL**: https://crm-frontend-7dnc.onrender.com
- **Backend URL**: https://crm-backend-cxxp.onrender.com

Учетные записи для тестирования (пароль для всех: `password123`):
- `teamlead`
- `chatter1`
- `chatter2`
