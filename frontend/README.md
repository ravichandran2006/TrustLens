# TrustLens Frontend & Chrome Extension

React UI for TrustLens — matches the dashboard design and connects to the FastAPI backend.

## Quick Start (Web Dev Mode)

1. Start the backend:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. Install and run the frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. Open http://localhost:5173 — paste agreement text and click **Analyze**.

## Chrome Extension

### Build

```bash
cd frontend
npm install
npm run build
```

This outputs the UI to `extension/dist/`.

### Load in Chrome

1. Open `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked**
4. Select the `extension/` folder

### Usage

1. Navigate to a page with terms/privacy policy
2. Click the TrustLens icon to open the **side panel**
3. Click **Extract from Page** to pull text, or paste manually
4. Click **Analyze** to get risks, trust score, and recommendations
5. Use the Q&A panel to ask follow-up questions

## API Configuration

| Environment | URL |
|-------------|-----|
| Local dev (web) | `http://127.0.0.1:8000` (via Vite proxy or direct) |
| Extension | `http://127.0.0.1:8000` (via background service worker) |

To change the API URL for web dev, create `frontend/.env`:
```
VITE_API_BASE=http://127.0.0.1:8000
```

For the extension, edit `extension/background.js` → `API_BASE`.

For production, update both and add your deployed URL to `host_permissions` in `manifest.json`.

## Project Structure

```
frontend/
  src/
    App.jsx              # Main dashboard
    api/client.js        # API client (web + extension)
    components/          # UI sections matching the design
    styles/              # CSS

extension/
  manifest.json          # Chrome MV3 manifest
  background.js          # API proxy (bypasses CORS)
  content.js             # Page text extraction
  dist/                  # Built UI (after npm run build)
  icons/                 # Extension icons
```

## Backend Endpoints Used

- `POST /api/analyze` — analyze agreement text
- `POST /api/question` — Q&A on analyzed agreement
- `GET /health` — health check
