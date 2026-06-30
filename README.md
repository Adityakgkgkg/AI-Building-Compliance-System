# AI-Driven Context-Aware System for Automated Building Plan Compliance and 3D Urban Integration

A full-stack application that automates building plan compliance checking using AI, integrates GIS data for context-aware analysis, and provides 3D urban visualization.

**Final Year AI & ML Project — Sprint 1 (Foundation)**

---

## 🏗️ Project Overview

Traditional building plan compliance checking is manual, slow, and error-prone. This system automates the workflow:

1. **Upload** IFC/DXF building plan files
2. **Parse** building metadata and structural data (Sprint 2)
3. **Check** compliance against building codes (Sprint 3)
4. **Analyze** geographic context with GIS data (Sprint 4)
5. **Visualize** in 3D within the urban environment (Sprint 5)
6. **Report** results with AI-powered recommendations (Sprint 5)

---

## 📁 Folder Structure

```
AI-Building-Compliance-System/
├── backend/                      # FastAPI Backend
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── __init__.py   # V1 router (aggregates all endpoints)
│   │   │       ├── health.py     # GET /api/v1/health
│   │   │       └── upload.py     # POST /api/v1/upload
│   │   ├── core/
│   │   │   ├── config.py         # Pydantic settings (loads .env)
│   │   │   └── database.py       # SQLAlchemy engine + session
│   │   ├── models/               # ORM models (Sprint 2+)
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── services/             # Business logic (Sprint 2+)
│   │   └── utils/                # Utility helpers
│   ├── tests/                    # Test package
│   ├── uploads/                  # Uploaded files (gitignored)
│   ├── .env                      # Environment variables
│   ├── main.py                   # FastAPI entry point
│   └── requirements.txt          # Python dependencies
│
├── frontend/                     # Next.js Frontend
│   ├── app/
│   │   ├── about/page.tsx        # About page
│   │   ├── dashboard/page.tsx    # Dashboard (Coming Soon cards)
│   │   ├── upload/page.tsx       # Upload page
│   │   ├── error.tsx             # Global error boundary
│   │   ├── globals.css           # Design system + global styles
│   │   ├── layout.tsx            # Root layout (Navbar + Footer)
│   │   ├── not-found.tsx         # 404 page
│   │   └── page.tsx              # Home / landing page
│   ├── components/
│   │   ├── DashboardCard.tsx     # Reusable dashboard card
│   │   ├── FileDropzone.tsx      # Drag-and-drop upload
│   │   ├── Footer.tsx            # Site footer
│   │   └── Navbar.tsx            # Navigation bar
│   ├── hooks/
│   │   └── useUpload.ts          # Upload hook with progress
│   ├── services/
│   │   └── api.ts                # Axios instance + API functions
│   ├── types/
│   │   └── index.ts              # Shared TypeScript interfaces
│   ├── .env.local                # Frontend environment variables
│   └── package.json
│
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **npm**

### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload --port 8000
```

The API will be available at **http://localhost:8000**
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

The app will be available at **http://localhost:3000**

---

## 🔌 API Endpoints

| Method | Endpoint           | Description                        |
|--------|--------------------|------------------------------------|
| GET    | `/api/v1/health`   | Health check → `{"status":"running"}` |
| POST   | `/api/v1/upload`   | Upload IFC/DXF file → metadata     |

### Upload Response

```json
{
  "filename": "building_plan.ifc",
  "size": 1048576,
  "type": ".ifc",
  "upload_time": "2025-01-01T12:00:00Z"
}
```

---

## ⚙️ Configuration

### Backend (`.env`)

| Variable             | Default                    | Description               |
|----------------------|----------------------------|---------------------------|
| `APP_NAME`           | AI Building Compliance...  | Application name          |
| `BACKEND_PORT`       | 8000                       | Server port               |
| `FRONTEND_URL`       | http://localhost:3000       | CORS allowed origin       |
| `DATABASE_URL`       | sqlite:///./app.db         | Database connection       |
| `UPLOAD_DIR`         | uploads                    | Upload directory path     |
| `ALLOWED_EXTENSIONS` | .ifc,.dxf                  | Accepted file types       |
| `MAX_UPLOAD_SIZE_MB` | 100                        | Max file size in MB       |

### Frontend (`.env.local`)

| Variable              | Default                          | Description      |
|-----------------------|----------------------------------|------------------|
| `NEXT_PUBLIC_API_URL` | http://localhost:8000/api/v1     | Backend API URL  |

---

## 🗺️ Roadmap

| Sprint | Focus                  | Status      |
|--------|------------------------|-------------|
| 1      | Foundation & UI        | ✅ Complete |
| 2      | IFC/DXF Parsing        | 🔜 Next     |
| 3      | Compliance Engine      | 📋 Planned  |
| 4      | GIS Integration        | 📋 Planned  |
| 5      | AI & 3D Visualization  | 📋 Planned  |

---

## 🌿 Git Branches

| Branch               | Purpose                           |
|----------------------|-----------------------------------|
| `main`               | Production-ready releases         |
| `develop`            | Active development integration    |
| `feature/parser`     | IFC/DXF parsing module            |
| `feature/compliance` | Compliance checking engine        |
| `feature/gis`        | GIS context integration           |
| `feature/frontend`   | Frontend enhancements             |

---

## 📄 License

This project is developed as a Final Year AI & ML academic project.
