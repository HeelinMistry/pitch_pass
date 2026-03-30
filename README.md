# 🏟️ PitchPass | Pro WebAuthn Sports Engine

PitchPass is a high-performance event management system for local sports communities. It eliminates traditional passwords in favor of **WebAuthn (Passkeys)**, providing a frictionless, hardware-secured experience for hosting and joining matches.

## 🚀 Architectural Evolution
The project has graduated from a rapid-prototype mock-DB to a structured **FastAPI + SQLAlchemy** architecture, utilizing a versioned API pattern to ensure scalable frontend-backend synchronization.

---

## 🛠️ Technical Stack
* **Backend:** FastAPI (Python 3.11+)
* **Database:** SQLite w/ SQLAlchemy ORM (Migrated from `db.json`)
* **Authentication:** PyWebAuthn (Level 3 Standard)
* **Session Management:** Starlette SessionMiddleware (Signed Cookies)
* **Frontend:** Tailwind CSS, ES6 Modules, Space Grotesk/Manrope Typography

---

## 🏗️ Core Architecture

### 1. Unified Authentication Flow
PitchPass uses a two-step cryptographic handshake:
1.  **Challenge:** The server generates a unique challenge for a username, encoded as a UTF-8 string to ensure JSON-safe session storage.
2.  **Verification:** The client signs the challenge via `SimpleWebAuthnBrowser`. The server verifies the signature against the hardware-backed public key stored in the `Passkey` table and issues a JWT.



### 2. Data Model (`tables.py`)
* **Users:** Unique identities linked to biometric credentials.
* **Passkeys:** Stores `credential_id`, `public_key` (Base64), and `sign_count` for replay protection.
* **Matches:** Metadata-rich entities (sport, duration, cost, roster limits).
* **MatchPlayers:** Relationship table managing "Confirmed" vs "Waitlisted" status.

---

## 🛰️ API Reference (v1)

### Authentication
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/auth/register/options/{user}` | Generate Passkey creation challenge. |
| `POST` | `/api/v1/auth/register/verify` | Verify hardware signature & create user. |
| `GET` | `/api/v1/auth/login/options/{user}` | Fetch allowed credentials for biometric prompt. |
| `POST` | `/api/v1/auth/login/verify` | Verify assertion & return JWT. |

### Matches
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/matches` | List all matches (Host or Participant filter). |
| `POST` | `/api/v1/matches/create` | Deploy a new match (Protected). |
| `POST` | `/api/v1/matches/{id}/toggle-join` | Atomic join/leave logic. |
| `POST` | `/api/v1/matches/{id}/toggle-cancel` | Atomic cancel/restore logic. |

---

## 📂 Project Structure
```text
fastapi_backend/
├── app/
│   ├── api/v1/         # Versioned controllers (auth.py, matches.py)
│   ├── core/           # Security, JWT, & WebAuthn utils
│   ├── db/             # SQLAlchemy (database.py, tables.py)
│   └── main.py         # App entry, CORS, & Session Middleware
├── static/
│   ├── js/             # Modular JS (api.js, auth.js, dashboard.js)
│   └── css/            # Tailwind & PitchPass branding
└── requirements.txt    # FastAPI, pywebauthn, sqlalchemy
```

---

## 📝 Critical Implementation Notes
* **Serialization Integrity:** All WebAuthn challenges are converted from `bytes` to `base64/string` during session storage to prevent JSON serialization errors in FastAPI/Starlette.
* **Cross-Origin Security:** `api.js` utilizes `credentials: 'include'` to ensure session cookies are passed correctly across the `v1` API surface.
* **Stigmergic Development:** This README serves as the source of truth for task breakdown. Use GitHub Issues to track the transition of remaining endpoints to the `v1` prefix.

---

## 🛠️ Development Setup

1.  **Install Environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Run Server:**
    ```bash
    uvicorn app.main:app --reload --port 8000
    ```
