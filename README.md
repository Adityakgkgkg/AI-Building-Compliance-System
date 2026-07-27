# AI-Driven Context-Aware System for Automated Building Plan Compliance and 3D Urban Integration

A full-stack application that automates building plan compliance checking using AI, integrates GIS data for context-aware analysis, and provides 3D urban visualization.

**Final Year AI & ML Project — Sprint 1 (Foundation) + Module 1 (IFC Parser)**

---

## 🏗️ Project Overview

Traditional building plan compliance checking is manual, slow, and error-prone. This system automates the workflow:

1. **Upload** IFC/DXF building plan files
2. **Parse** building metadata and structural data ✅ **(Module 1 complete)**
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
│   │   │       └── upload.py     # POST /api/v1/upload (generic)
│   │   ├── parser/               # ✅ Module 1: IFC Parser
│   │   │   ├── __init__.py       # Package init, exports router
│   │   │   ├── router.py         # 4 REST endpoints (thin layer)
│   │   │   ├── service.py        # ParserService — pipeline orchestrator
│   │   │   ├── file_loader.py    # IFCFileLoader — validate & save uploads
│   │   │   ├── metadata_extractor.py  # Extract project/building/site info
│   │   │   ├── element_extractor.py   # Count walls/doors/windows etc.
│   │   │   ├── serializer.py     # Assemble ParseResult from extractor outputs
│   │   │   ├── schemas.py        # Pydantic models (stable JSON contract)
│   │   │   ├── models.py         # IFCFileRecord + ParsedFileStore
│   │   │   └── utils.py          # safe_get, unit scale, geometry helpers
│   │   ├── core/
│   │   │   ├── config.py         # Pydantic settings (loads .env)
│   │   │   └── database.py       # SQLAlchemy engine + session
│   │   ├── models/               # ORM models (Sprint 3+)
│   │   ├── schemas/              # Global Pydantic schemas (Sprint 1)
│   │   ├── services/             # Global services (Sprint 3+)
│   │   └── utils/                # Utility helpers
│   ├── tests/
│   │   └── parser/               # ✅ Module 1 tests
│   │       ├── conftest.py       # Fixtures: minimal IFC, TestClient
│   │       ├── test_upload.py    # Upload validation tests
│   │       └── test_parse.py     # Parse + GET endpoint tests
│   ├── uploads/
│   │   └── ifc/                  # IFC files keyed by UUID (gitignored)
│   ├── .env                      # Environment variables
│   ├── main.py                   # FastAPI entry point
│   └── requirements.txt          # Python dependencies
│
├── frontend/                     # Next.js Frontend
│   ├── app/
│   │   ├── about/page.tsx        # About page
│   │   ├── dashboard/page.tsx    # Dashboard
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

# Install dependencies (includes IfcOpenShell)
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload --port 8000
```

### Installing IfcOpenShell

`ifcopenshell` is included in `requirements.txt` and installs via pip on most platforms:

```bash
pip install ifcopenshell
```

**If pip installation fails** (some Linux/macOS environments), use the official IfcOpenShell builds:

```bash
# Option 1 — conda (cross-platform)
conda install -c conda-forge ifcopenshell

# Option 2 — download prebuilt wheel from:
# https://github.com/IfcOpenShell/IfcOpenShell/releases
# Then install locally:
pip install path/to/ifcopenshell-*.whl
```

> **Python version note:** IfcOpenShell wheels are available for Python 3.10, 3.11, and 3.12.
> Make sure your virtual environment matches one of these versions.

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

### Sprint 1 — Foundation

| Method | Endpoint         | Description                           |
|--------|------------------|---------------------------------------|
| GET    | `/api/v1/health` | Health check → `{"status":"running"}` |
| POST   | `/api/v1/upload` | Upload IFC/DXF file → metadata        |

### Module 1 — IFC Parser

| Method | Endpoint                            | Description                              |
|--------|-------------------------------------|------------------------------------------|
| POST   | `/api/v1/parser/upload`             | Upload `.ifc` file → `file_id`           |
| POST   | `/api/v1/parser/parse/{file_id}`    | Parse IFC → full `ParseResult` JSON      |
| GET    | `/api/v1/parser/building/{file_id}` | Get building metadata only               |
| GET    | `/api/v1/parser/elements/{file_id}` | Get element counts only                  |

### Module 1 — ParseResult Contract

The stable JSON contract consumed by all future modules:

```json
{
  "building": {
    "project_name": "Commercial Tower A",
    "building_name": "Tower Block 1",
    "site_name": "Plot 42, Business District",
    "description": "Mixed-use commercial tower",
    "schema": "IFC4",
    "storeys": 3,
    "units": "METRE",
    "owner": "ACME Architecture Firm"
  },
  "elements": {
    "walls": 42,
    "doors": 15,
    "windows": 18,
    "slabs": 4,
    "columns": 12,
    "beams": 20,
    "roofs": 1,
    "stairs": 2,
    "spaces": 10,
    "openings": 5
  },
  "geometry": {
    "gross_floor_area": 1250.0,
    "height": 12.5,
    "storey_heights": [3.5, 3.5, 3.0],
    "footprint": 450.0,
    "bounding_box": {
      "min_x": 0.0, "min_y": 0.0, "min_z": 0.0,
      "max_x": 30.0, "max_y": 20.0, "max_z": 12.5
    }
  }
}
```

> **Note:** All `geometry` fields default to `null` when 3D geometry is unavailable in the IFC file.

### Running Tests

```bash
cd backend
pytest tests/parser/ -v
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

| Sprint    | Focus                     | Status         |
|-----------|---------------------------|----------------|
| 1         | Foundation & UI           | ✅ Complete    |
| Module 1  | IFC Parser                | ✅ Complete    |
| Sprint 3  | Compliance Engine         | 📋 Planned     |
| Sprint 4  | GIS Integration           | 📋 Planned     |
| Sprint 5  | AI & 3D Visualization     | 📋 Planned     |

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
