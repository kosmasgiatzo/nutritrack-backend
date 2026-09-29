# 🥗 NutriTrack Backend API

Το backend API της εφαρμογής **NutriTrack**, σχεδιασμένο για τη διαχείριση χρηστών, πιστοποίηση (authentication) και καταγραφή διατροφικών δεδομένων/γευμάτων.

---

## 🛠️ Τεχνολογικό Stack
- **Framework:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL
- **ORM & Migrations:** SQLAlchemy, Alembic
- **Authentication:** JWT (JSON Web Tokens) & Passlib (bcrypt)
- **Containerization & Deployment:** Docker, Render

---

## 🚀 Live API Endpoints & Docs
- **Base URL:** `https://nutritrack-backend-jbcg.onrender.com/api/v1`
- **Interactive Swagger Docs:** [Swagger UI](https://nutritrack-backend-jbcg.onrender.com/docs)
- **Alternative Redoc:** [Redoc](https://nutritrack-backend-jbcg.onrender.com/redoc)

> *Σημείωση: Λόγω φιλοξενίας στο free tier του Render, το backend ενδέχεται να χρειαστεί ~50 δευτερόλεπτα για cold start αν δεν έχει δεχθεί πρόσφατα αιτήματα.*

---

## 📂 Δομή Έργου
```text
nutritrack-backend/
├── alembic/              # Database migration scripts
├── app/
│   ├── api/              # API Endpoints & Routes (Auth, Nutrition, Users)
│   ├── core/             # Configuration, security & JWT settings
│   ├── models/           # SQLAlchemy database models
│   ├── schemas/          # Pydantic validation schemas
│   └── main.py           # FastAPI entrypoint
├── Dockerfile            # Production container configuration
├── docker-compose.yml    # Local development container setup
├── requirements.txt      # Project dependencies
└── alembic.ini           # Alembic config
