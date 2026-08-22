# Ztrip Backend Platform

<p align="center">
  <b>High-performance backend API and services for the Ztrip travel and AI assistant ecosystem.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Django-5.0.14-green?style=for-the-badge&logo=django" alt="Django">
  <img src="https://img.shields.io/badge/DRF-REST_Framework-red?style=for-the-badge" alt="DRF">
  <img src="https://img.shields.io/badge/Celery-Async-orange?style=for-the-badge&logo=celery" alt="Celery">
  <img src="https://img.shields.io/badge/PostgreSQL-15-blue?style=for-the-badge&logo=postgresql" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Redis-Cache-red?style=for-the-badge&logo=redis" alt="Redis">
  <img src="https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker" alt="Docker">
</p>

---

## 🌟 Overview

**Ztrip Backend** is a robust, production-ready Django 5 application designed to power modern travel planning, AI-assisted itineraries, user gamification, real-time communication via WebSockets, and seamless payment processing.

---

## 🚀 Key Modules & Features

The project is structured into modular Django applications located inside the `apps/` directory:

| Module | Description |
| :--- | :--- |
| **`ai_plans`** | Generates and manages AI-powered customized travel itineraries and recommendations. |
| **`travel`** | Core travel management, bookings, trips, and destination operations. |
| **`location` & `saved_locations`** | Geo-location database, mapping services, and user saved spots/favorites. |
| **`coin`** | Gamification engine, XP calculation, and coin reward system (`test_add_xp.py`). |
| **`payments` & `subscriptions`** | Secure financial transactions, payment gateway integration, and subscription tiers. |
| **`users`** | Advanced user authentication, profile management, and permissions. |

---

## 🛠️ Tech Stack

- **Core Framework:** Python 3.11+, Django 5.0, Django REST Framework (DRF)
- **Real-Time & Async:** Celery, Redis, Django Channels, Daphne
- **Database & Storage:** PostgreSQL 15, MinIO / AWS S3 (via `django-storages`)
- **Audio & Media:** Edge-TTS for audio guide generation (`AUDIO_GUIDE_README.md`)
- **DevOps & Deployment:** Docker, Docker Compose, Nginx, Certbot (SSL)

---

## 📁 Project Directory Structure

```text
ztrip/
├── apps/                  # Modular Django applications
│   ├── ai_plans/          # AI travel itineraries
│   ├── coin/              # Gamification and XP system
│   ├── location/          # Locations and mapping
│   ├── payments/          # Payment processing
│   ├── saved_locations/   # User saved spots
│   ├── subscriptions/     # Subscription management
│   ├── travel/            # Trips and bookings
│   └── users/             # User accounts and auth
├── config/                # Project configuration & settings
│   ├── asgi.py            # ASGI setup (Channels/Daphne)
│   ├── celery.py          # Celery configuration
│   ├── settings.py        # Main Django settings
│   ├── urls.py            # Root URL router
│   └── wsgi.py            # WSGI setup
├── core/                  # Shared utilities, permissions & paginations
├── tests/                 # Integration and feature test scripts
│   ├── test_add_xp.py
│   ├── test_audio_guide.py
│   └── test_websocket.py
├── nginx/                 # Nginx reverse proxy configurations
├── .env.example           # Environment variable template
├── Dockerfile             # Container build instructions
├── docker-compose.yml     # Multi-container orchestration
├── Makefile               # Convenient command shortcuts
├── manage.py              # Django management CLI
└── requirements.txt       # Python dependencies
```

---

## ⚙️ Getting Started

### Prerequisites

- Python 3.11 or higher
- PostgreSQL
- Redis server
- Docker & Docker Compose (optional for containerized setup)

### 1. Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ismoilov-dev/ztrip.git
   cd ztrip
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Copy `.env.example` to `.env` and fill in your database, Redis, and service credentials:
   ```bash
   cp .env.example .env
   ```

5. **Run database migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Start the development server:**
   You can use the provided `Makefile` shortcuts:
   ```bash
   # Run Django development server & Celery worker concurrently
   make run
   
   # Or run Django alone
   make run1
   ```

---

## 🐳 Docker Deployment

To spin up the entire stack (Django, PostgreSQL, Redis, MinIO, Nginx, and Certbot):

```bash
docker-compose up --build -d
```

---

## 🧪 Testing & Documentation

- **Test Scripts:** Located in the `tests/` directory (`test_add_xp.py`, `test_audio_guide.py`, `test_websocket.py`).
- **Audio Guide Guide:** See [`AUDIO_GUIDE_README.md`](./AUDIO_GUIDE_README.md) for instructions on text-to-speech audio guides.
- **WebSocket Testing:** See [`WEBSOCKET_TESTING_GUIDE.md`](./WEBSOCKET_TESTING_GUIDE.md) for real-time WebSocket communication testing.

---

## 📄 License

This project is proprietary and confidential to **Ztrip**. All rights reserved.
