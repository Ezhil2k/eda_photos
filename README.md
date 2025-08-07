# EDA Photos Project

This project is a web application for managing and searching photos using advanced image processing techniques. It includes a FastAPI backend, a Next.js frontend, and a PostgreSQL database.

## Project Structure

```
.
├── README.md
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── api/ # routes: auth, images, search
│       ├── db/ # models, session, migrations
│       ├── services/ # CLIP/FAISS, face clustering (stub)
│       └── utils/ # EXIF and file handling
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── pages/
└── images/ # volume for uploaded images
```

## Setup Instructions

1. **Docker Setup:**
   - Use Docker Compose to orchestrate the services.
   - Ensure volumes are set up for persistent data and image uploads.

2. **Backend:**
   - FastAPI with SQLAlchemy and Alembic for database migrations.
   - JWT authentication for user management.

3. **Frontend:**
   - Next.js application for the user interface.

4. **Database:**
   - PostgreSQL running in a Docker container.

5. **Image Processing:**
   - Extract EXIF metadata on upload.
   - Prepare structure for FAISS/CLIP embeddings.

6. **Running the Application:**
   - Use `docker-compose up --build` to start the application.