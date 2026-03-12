# Poker YOLO Labeling App

Annotation platform for poker mobile app screenshots with schema-aware suggestions and YOLO export.

## Quick Start

### With Docker

```bash
cd app
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

### Local Development

**Backend:**

```bash
cd backend
conda env create -f environment.yml
conda activate poker-labeling
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:5173 with API proxy to backend.

### Run Tests

```bash
cd backend
conda activate poker-labeling
pytest tests/ -v
```

## Usage

### 1. Create a Project

- Open the app at http://localhost:3000
- Click **"New Project"** and provide a name, description, and image folder path (relative paths are stored under `datasets/`)
- The image directory is auto-created when you create the project

### 2. Add Images

Two options:

- **Upload from browser:** Click **"Upload Images"** in the project header to select `.png`, `.jpg`, `.jpeg`, or `.webp` files from your computer
- **Import from folder:** Copy images into the project's image directory, then click **"Import from Folder"** to scan and register them

### 3. Label Images

- Select an image from the **left queue panel**
- The image loads in the center canvas with auto-fit

#### Canvas Navigation

| Control | Action |
|---------|--------|
| **Mouse drag** (Pan mode) | Move the image around |
| **Scroll wheel** | Zoom in/out at cursor position |
| **Arrow keys** | Pan the image |
| **Ctrl + / Ctrl -** | Zoom in / out |
| **Ctrl + 0** | Fit image to view |
| **Middle mouse button** | Pan (any mode) |
| **Space + drag** | Pan (any mode) |

#### Drawing & Editing

| Control | Action |
|---------|--------|
| **H** or Pan button | Switch to Pan mode (default) |
| **D** or Draw button | Switch to Draw mode |
| **Click + drag** (Draw mode) | Draw a new bounding box |
| **Click a box** | Select it (works in any mode) |
| **Drag selected box** | Move it |
| **Drag corner/edge handles** | Resize the selected box |
| **Click background** | Deselect |
| **Delete** | Delete selected box |

#### Toolbar (top-left overlay)

- **Pan icon** — hand tool for moving the image (default)
- **Draw icon** — dashed rectangle tool for drawing bounding boxes
- **- / +** — zoom out / in
- **Zoom %** — current zoom level
- **Fit** — fit image to viewport
- **1:1** — original size (100%)
- **Arrow buttons** — pan left/up/down/right

### 4. Assign Labels

- Use the **right sidebar** to assign labels from the taxonomy dropdown
- Number shortcuts **1-9** for quick label selection
- Schema suggestions appear after saving — click "Assign" to apply

### 5. Save & Export

- Press **Ctrl+S** to save (autosave runs every 3 seconds)
- Export to **YOLO format** or **JSON** via the sidebar buttons

## Keyboard Shortcuts Reference

| Key | Action |
|-----|--------|
| H | Pan mode |
| D | Draw mode |
| Arrow keys | Pan image |
| Ctrl + / Ctrl - | Zoom in / out |
| Ctrl + 0 | Fit to view |
| Space (hold) + drag | Pan (any mode) |
| Scroll wheel | Zoom at cursor |
| Delete | Delete selected box |
| Ctrl + S | Save annotations |
| 1-9 | Quick label select |

## Architecture

- **Frontend:** React + TypeScript + Vite + Konva.js + Zustand + Tailwind CSS + React Query
- **Backend:** FastAPI + SQLAlchemy (async) + SQLite
- **Reverse Proxy:** Nginx (Docker only, port 3000 -> frontend + `/api/` -> backend)
- **Config:** Shared JSON files for taxonomy, schemas, and regions (`shared/` directory)

## Docker Volumes

| Host Path | Container Path | Purpose |
|-----------|---------------|---------|
| `./backend/data` | `/app/data` | SQLite database |
| `./shared` | `/app/shared` | Taxonomy, schemas, region configs |
| `./datasets` | `/app/datasets` | Project image storage |

## File Upload Limits

- Nginx is configured with `client_max_body_size 500M` to support large batch uploads
- Proxy timeouts set to 300s for large file transfers
