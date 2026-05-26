# TRUTHO — "Truth Has No Face."

Anonymous social reporting platform for exposing corruption, injustice, crime and public safety issues.

---

## Project Structure

```
trutho/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── database.py              # PostgreSQL connection + SQLAlchemy
│   ├── models.py                # Database tables (User, Post, Comment, Reaction)
│   ├── schemas.py               # Pydantic request/response models
│   ├── auth.py                  # JWT + bcrypt authentication
│   ├── websocket_manager.py     # Live WebSocket broadcast
│   ├── ranking.py               # Trending score algorithm
│   ├── moderation.py            # Spam / doxxing / content filter
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env                     # ← Edit this with your DB credentials
│   ├── uploads/                 # Media files stored here
│   ├── routes/
│   │   ├── auth_routes.py       # /auth/register /auth/login /auth/me
│   │   ├── post_routes.py       # /posts CRUD + like/dislike
│   │   ├── comment_routes.py    # /comments
│   │   ├── websocket_routes.py  # /ws/feed
│   │   └── admin_routes.py      # /admin/* moderation
│   └── utils/
│       ├── anonymous_names.py   # Random username generator
│       ├── image_cleaner.py     # EXIF metadata stripping
│       └── security.py          # Secure filenames
├── frontend/
│   └── index.html               # Complete frontend (connects to backend)
├── docker-compose.yml
├── setup_windows.bat
└── run_backend.bat
```

---

## Setup on Windows 11

### Prerequisites

1. **Python 3.11+** — https://python.org/downloads (check "Add to PATH")
2. **PostgreSQL 16** — https://postgresql.org/download/windows
   - During install, set a password for the `postgres` user (remember it)
   - Default port: 5432
3. **Git** (optional) — https://git-scm.com

---

### Step 1 — Create the Database

Open **pgAdmin** or **psql** and run:

```sql
CREATE DATABASE trutho;
```

Or via psql command prompt:
```
psql -U postgres
CREATE DATABASE trutho;
\q
```

---

### Step 2 — Configure Environment

Edit `backend/.env`:

```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/trutho
SECRET_KEY=generate-a-random-64-character-string-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE_MB=50
ENVIRONMENT=development
```

Replace `YOUR_PASSWORD` with your PostgreSQL password.

To generate a good SECRET_KEY, run in Python:
```python
import secrets; print(secrets.token_hex(32))
```

---

### Step 3 — Install & Run

Double-click `setup_windows.bat` OR run manually:

```bat
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Then start the server:

```bat
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or just double-click `run_backend.bat`.

---

### Step 4 — Open the Frontend

Open `frontend/index.html` in your browser.

The frontend is already configured to connect to `http://localhost:8000`.

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register (username optional — auto-generated) |
| POST | `/auth/login` | Login |
| GET | `/auth/me` | Get current user |
| GET | `/auth/suggest-username` | Get 6 random anonymous names |

### Posts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/posts` | Get all posts (filter: `?category=Corruption&search=keyword`) |
| GET | `/posts/trending` | Trending posts by score |
| GET | `/posts/stats` | Platform stats |
| GET | `/posts/{id}` | Get one post + increment views |
| POST | `/posts` | Create post (multipart form, auth optional) |
| POST | `/posts/{id}/like` | Like (auth required) |
| POST | `/posts/{id}/dislike` | Dislike (auth required) |
| DELETE | `/posts/{id}` | Delete own post |

### Comments
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/comments/{post_id}` | Get comments for a post |
| POST | `/comments/{post_id}` | Post a comment (auth optional) |
| DELETE | `/comments/{id}` | Delete own comment |

### Admin (requires admin account)
| Method | Endpoint | Description |
|--------|----------|-------------|
| DELETE | `/admin/post/{id}` | Remove any post |
| DELETE | `/admin/comment/{id}` | Remove any comment |
| POST | `/admin/ban/{user_id}` | Ban a user |
| POST | `/admin/unban/{user_id}` | Unban a user |
| POST | `/admin/verify/{post_id}` | Moderator-verify a post |
| GET | `/admin/stats` | Platform statistics |

### WebSocket
| Endpoint | Description |
|----------|-------------|
| `ws://localhost:8000/ws/feed` | Live feed — receives new_post, new_comment, reaction_update events |

---

## Making an Admin Account

After registering normally, run this in psql:

```sql
UPDATE users SET is_admin = TRUE WHERE username = 'your_username';
```

---

## Docker Deployment (Recommended for Production)

```bash
docker-compose up --build
```

This starts PostgreSQL + backend automatically.

---

## Deploy to Railway

1. Push the `backend/` folder to GitHub
2. Create new Railway project → Deploy from GitHub
3. Add PostgreSQL plugin
4. Set environment variables (copy from `.env`)
5. Railway auto-detects Dockerfile and deploys

---

## Deploy to Render

1. Push `backend/` to GitHub
2. New Web Service → Docker runtime
3. Set `DATABASE_URL` from Render's PostgreSQL addon
4. Set all other env vars
5. Deploy

---

## Security Features

- ✅ JWT authentication (no sessions)
- ✅ bcrypt password hashing
- ✅ EXIF/GPS stripping from all images (Pillow + piexif)
- ✅ Secure random filenames for uploads
- ✅ Content moderation (banned words, doxxing detection, spam)
- ✅ XSS sanitization on all text input
- ✅ Rate limiting via SlowAPI
- ✅ CORS configured
- ✅ SQL injection protected (SQLAlchemy ORM)
- ✅ No IP addresses stored
- ✅ No real identity required (username + password only)
- ✅ Anonymous usernames auto-generated if not provided
- ✅ File type + size validation on uploads

---

## Frontend JavaScript API Examples

```javascript
const API = 'http://localhost:8000';

// Register
const res = await fetch(`${API}/auth/register`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({ password: 'mypassword123' })  // username optional
});
const { access_token, username } = await res.json();

// Post a report with image
const fd = new FormData();
fd.append('title', 'Corruption at city hall');
fd.append('category', 'Corruption');
fd.append('body', 'Full detailed report here...');
fd.append('media', imageFile);  // optional
await fetch(`${API}/posts`, {
  method: 'POST',
  headers: { Authorization: `Bearer ${access_token}` },
  body: fd
});

// Like a post
await fetch(`${API}/posts/1/like`, {
  method: 'POST',
  headers: { Authorization: `Bearer ${access_token}` }
});

// WebSocket live feed
const ws = new WebSocket('ws://localhost:8000/ws/feed');
ws.onmessage = (e) => {
  const { type, data } = JSON.parse(e.data);
  if (type === 'new_post') console.log('New report:', data.title);
  if (type === 'new_comment') console.log('New comment:', data.body);
};
```

---

## Categories

- Corruption
- Crime
- Harassment
- Road Problem
- Government Issue
- Scam
- Environment
- Education
- Healthcare
- Police Abuse
- Public Safety

---

*Trutho — Truth Has No Face.*











"""  run backend-- cd "c:\Users\USER\Downloads\trutho_complete (1)\trutho\backend"; & "C:/Users/USER/AppData/Local/Microsoft/WindowsApps/python3.11.exe" -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 """