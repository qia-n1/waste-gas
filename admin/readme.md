Admin frontend:
`C:\Users\patri\OneDrive - bjtu.edu.cn\Files\服务外包\waste-gas\admin\frontend`

Run:
`npm run dev`

Admin backend:
`C:\Users\patri\OneDrive - bjtu.edu.cn\Files\服务外包\waste-gas\admin\backend`

Run:
`python -m uvicorn main:app --host 127.0.0.1 --port 8003 --reload`

Current ports:
- `ensemble_docker`: `8000`
- `vocs_server`: `8001`
- `admin backend`: `8003`
- `admin frontend (Vite)`: `3001`

Vite proxy:
- `/api` -> `http://localhost:8003`
- `/vocs` -> `http://localhost:8001`
