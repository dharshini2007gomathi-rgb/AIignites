# Ayurveda Skill Mapping & Internship Portal

**SIH 2026** — Smart India Hackathon project for Ayurveda students (BAMS/MD/PhD).

A full-stack platform where students assess skills, identify gaps, get learning recommendations, and match with internships/jobs using AI-powered weighted cosine similarity.

## Features

- **Role-based access**: Student, Industry, Faculty, Admin
- **Skill Assessment**: 50-question questionnaire across 6 categories
- **Skill Gap Analysis**: Radar charts and gap visualization (Chart.js)
- **Smart Matching**: Weighted cosine similarity for opportunity recommendations
- **Application Tracking**: Full lifecycle from Pending → Selected/Rejected
- **Digital Portfolio**: Shareable public portfolio pages
- **Admin Analytics**: Skill gaps, industry demand, platform metrics
- **REST API**: Complete API for all core features

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 4.2 + Django REST Framework |
| Frontend | HTML, CSS, JavaScript, Bootstrap 5 |
| Database | SQLite (dev) / PostgreSQL (production) |
| Charts | Chart.js |
| Deployment | Railway / Render ready |

## Quick Start

### 1. Clone and setup

```bash
cd "ayurveda project"
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Environment variables

```bash
copy .env.example .env   # Windows
# cp .env.example .env   # Linux/Mac
```

Edit `.env` with your settings. Defaults work for local SQLite development.

### 3. Database setup

```bash
python manage.py migrate
python manage.py seed_data
```

### 4. Run development server

```bash
python manage.py runserver
```

Open **http://127.0.0.1:8000**

### Demo Accounts

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Student | demo_student | demo123 |
| Industry | demo_industry | demo123 |

## Bulk Student Import

Generate and import synthetic student records:

```bash
# Generate CSV with 100 students (default)
python manage.py import_students --count 100

# Generate CSV only (no import)
python manage.py import_students --count 10000 --generate-only

# Import from existing CSV
python manage.py import_students --csv data/synthetic_students.csv

# Import 10,000 students (generates CSV if missing)
python manage.py import_students --count 10000
```

## Running Tests

```bash
python manage.py test skills
```

Tests cover:
- Assessment scoring (scale, yes/no)
- Weighted cosine similarity matching
- Skill gap identification
- Assessment submission flow

## API Endpoints

Base URL: `/api/`

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register new user |
| POST | `/api/auth/login/` | Login |
| POST | `/api/auth/logout/` | Logout |
| GET | `/api/auth/profile/` | Current user profile |

### Students
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/students/` | List students (admin) |
| GET/PUT | `/api/students/{id}/` | Student detail/update |
| GET | `/api/students/{id}/skills/` | Student skills |
| GET | `/api/students/{id}/portfolio/` | Portfolio data |

### Skills & Assessment
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/skills/` | List skills |
| POST | `/api/skills/assess/` | Submit assessment |
| GET | `/api/skills/gap-analysis/{student_id}/` | Gap analysis |

### Opportunities
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/opportunities/` | List/create opportunities |
| GET | `/api/opportunities/recommended/{student_id}/` | AI recommendations |
| GET | `/api/opportunities/match-score/{student_id}/{opp_id}/` | Match score |

### Applications & Courses
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/applications/` | List/create applications |
| PUT | `/api/applications/{id}/status/` | Update status |
| GET | `/api/courses/recommended/{student_id}/` | Course recommendations |

### Analytics (Admin)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/overview/` | Platform overview |
| GET | `/api/analytics/skill-gaps/` | Common skill gaps |
| GET | `/api/analytics/industry-demand/` | Skill demand trends |

## Deployment

### Railway / Render

1. Set environment variables from `.env.example`
2. Configure PostgreSQL:
   ```
   DB_ENGINE=django.db.backends.postgresql
   DB_NAME=your_db
   DB_USER=your_user
   DB_PASSWORD=your_password
   DB_HOST=your_host
   DB_PORT=5432
   ```
3. Build command: `pip install -r requirements.txt && python manage.py migrate && python manage.py seed_data`
4. Start command: `gunicorn ayurveda_portal.wsgi`

### Production checklist

- Set `DEBUG=False`
- Generate a strong `SECRET_KEY`
- Configure real email backend
- Set `ALLOWED_HOSTS` to your domain
- Run `python manage.py collectstatic`

## Project Structure

```
ayurveda project/
├── accounts/          # Auth, roles, email verification
├── students/          # Student profiles, portfolio
├── skills/            # Skills, assessments, matching algorithm
├── opportunities/     # Industries, faculty, opportunities
├── applications/      # Applications, internship tracking
├── courses/           # Learning resources
├── analytics/         # Admin analytics API
├── portal/            # Frontend views
├── templates/         # HTML templates (Bootstrap 5)
├── static/            # CSS, JS
├── ayurveda_portal/   # Django settings, URLs
├── requirements.txt
├── Procfile
└── README.md
```

## Skill Matching Algorithm

The core matching engine uses **weighted cosine similarity**:

1. Compare student skill scores vs opportunity requirements
2. Apply importance weights per skill
3. Calculate cosine similarity → match percentage (0-100%)
4. Identify skill gaps (required - current) for course recommendations

See `skills/services.py` for implementation.

## License

Built for SIH 2026 — Educational/Hackathon project.
