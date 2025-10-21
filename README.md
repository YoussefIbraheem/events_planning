# 🎟️ Events Planning API

A scalable, production-grade **event management and ticketing system** built with **Django REST Framework**.  
This project demonstrates clean architecture, service-layer abstraction, background processing with **Celery**, and robust caching powered by **Redis** — all production-ready and fully tested.

[<img src="https://fetch.usebruno.com/button.svg" alt="Fetch in Bruno" width="130" height="30">](https://fetch.usebruno.com?url=https%3A%2F%2Fgithub.com%2FYoussefIbraheem%2Fevents_planning.git "target=_blank rel=noopener noreferrer")

---

## 🚀 Features

- **Events Management** – Organisers can create, update, and list events.  
- **Tickets System** – Auto-generated unique tickets per event, including reservation and sale flow.  
- **Orders & Checkout Flow** – Full order lifecycle: pending → reserved → paid → cancelled.  
- **Soft Deletes** – Implemented on `CustomUser` model using `deleted_at` timestamp.  
- **Celery Integration** – Background job for releasing expired ticket reservations.  
- **Django-Celery-Beat** – Periodic tasks for automatic system maintenance.  
- **Redis Caching** – Improves performance for high-read endpoints (events, orders).  
- **RESTful API Docs** – Auto-generated Swagger UI served at root `/`.  
- **Complete Test Coverage** – Comprehensive `pytest` suite for services and endpoints.  
- **Clean Architecture** – Dedicated service layers (`OrderService`, `TicketService`) for clear business logic separation.

---

## 🏗️ Project Structure

```bash

events_planning_django/
├── app/
│   ├── models.py
│   ├── services/
│   │   ├── orders.py
│   │   └── tickets.py
│   ├── signals.py
│   ├── tasks.py
│   ├── factories/
│   └── tests/
│       ├── test_apis.py
│       ├── test_order_service.py
│       └── test_ticket_service.py
├── events_planning_django/
│   ├── settings.py
│   ├── celery.py
│   └── urls.py
├── project_design.excalidraw
├── requirements.txt
├── manage.py
└── Events Planning API (Bruno)/

````

---

## ⚙️ Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/YoussefIbraheem/events_planning.git
cd events_planning
````

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🧠 Environment Configuration

Create a `.env` file in the project root with the following:

```env
DJANGO_SETTINGS_MODULE=events_planning_django.settings
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

---

## 🐳 Docker Setup (Celery + Redis)

This project includes **Celery workers** and **Celery Beat** schedulers for background jobs.

### 1. Build and run Redis

```bash
docker run -d --name redis -p 6379:6379 redis
```

### 2. Start Celery workers and beat

In separate terminals:

```bash
celery -A events_planning_django worker -l info -n worker
celery -A events_planning_django beat -l info -n beat
```

---

## 🧾 API Documentation

Once the server is running, visit:

```bash
http://localhost:8000/
```

You’ll see the **Swagger UI** automatically loaded with all available endpoints.

---

## 🧩 Bruno Collection

You can import the Bruno API collection to test all endpoints easily:

[<img src="https://fetch.usebruno.com/button.svg" alt="Fetch in Bruno" width="130" height="30">](https://fetch.usebruno.com?url=https%3A%2F%2Fgithub.com%2FYoussefIbraheem%2Fevents_planning.git "target=_blank rel=noopener noreferrer")

The collection is available in:

```bash
Events Planning API (Bruno)/
```

---

## 🧰 Running Tests

Run the full suite of API and service layer tests:

```bash
pytest
```

Tests cover:

* Ticket reservation, release, and finalization
* Order creation and update logic
* API authentication and validation
* Caching and Celery background operations

---

## 🧠 Caching Strategy

* Event and Order list endpoints are cached for **2 hours** via `django-redis`.
* Critical CRUD operations (create/update/delete) trigger **cache invalidation** through Django signals.
* Cached data ensures high performance without stale reads.

---

## ⏰ Background Jobs (Celery Beat)

| Task                                           | Frequency   | Description                   |
| ---------------------------------------------- | ----------- | ----------------------------- |
| `app.tasks.release_expired_tickets`            | every 60s   | Releases expired reservations |
| `events_planning_django.celery.check_schedule` | every 5 min | Logs system heartbeat         |

---

## 🧩 Visuals

All design visuals are stored in:

```bash
project_design.excalidraw
```

Includes:

* Full UML Diagram (models and relationships)
* Service layer flowcharts (OrderService, TicketService)
* System architecture overview

---

## 🪶 Tech Stack

* **Backend:** Django, Django REST Framework
* **Cache & Queue:** Redis
* **Async Tasks:** Celery + Django-Celery-Beat
* **Testing:** Pytest
* **Docs:** Swagger UI
* **DB:** SQLite (default, easily switchable to PostgreSQL)

---

## 🧩 Future Improvements

* Replace SQLite with PostgreSQL for production
* Integrate email notifications on order completion
* Add metrics dashboards for organisers
* Implement role-based permissions for admin control

---

## 💡 Quick Commands

| Command                                           | Description            |
| ------------------------------------------------- | ---------------------- |
| `python manage.py runserver`                      | Start local server     |
| `celery -A events_planning_django worker -l info` | Start Celery worker    |
| `celery -A events_planning_django beat -l info`   | Start Celery scheduler |
| `pytest`                                          | Run all tests          |
| `python manage.py shell`                          | Open Django shell      |

---

## 🧾 Requirements File

To export dependencies after installing new packages:

```bash
pip freeze > requirements.txt
```

---

## 🧭 License

This project is open-source and intended for educational and portfolio demonstration purposes.

---

✅ **Ready to Launch:**
Clone → Install → Run → Explore Swagger → Import Bruno Collection → Test.

---

```markdown
🔥 “Events Planning API” — a full production-grade Django backend demonstrating modern architecture, caching, and background task orchestration.
```

---
