# 🏟️ PitchPass | Scalable WebAuthn API

PitchPass is a high-performance event management system designed for local sports communities. It replaces traditional password-based systems with **WebAuthn (Passkeys)** to provide a frictionless, secure, and modern experience for hosting and joining matches.

## 🚀 Project Status: Pre-Deployment
The project currently utilizes a **Vectorized Mock Database** (`db.json`) for rapid prototyping and low-latency response times, making it ideal for the initial Raspberry Pi deployment phase.

---

## 🛠️ Technical Stack
* **Backend:** FastAPI (Python 3.10+)
* **Authentication:** PyWebAuthn (Passkey standard)
* **Security:** JWT (JSON Web Tokens) with RS256/HS256
* **Database:** `db.json` (JSON-based document store)
* **Frontend:** Tailwind CSS, Space Grotesk/Manrope Typography

---

## 🏗️ Core Architecture

### 1. Authentication Flow (WebAuthn)
PitchPass uses a two-step cryptographic handshake:
1.  **Challenge:** The server generates a unique challenge for a specific username and stores it in the database.
2.  **Verification:** The client signs the challenge using the device's hardware-backed passkey. The server verifies the signature and issues a JWT.

### 2. Data Model (`db.json`)
The system tracks four primary entities:
* **Users:** Linked via unique UUIDs.
* **Passkeys:** Stores public keys, credential IDs, and sign counts.
* **Matches:** Contains game metadata (sport, location, cost, roster limits).
* **Match Players:** A join table managing the relationship between users and games.

---

## 🔌 API Endpoints

### Authentication (`/api/auth`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/register/options/{user}` | Generate Passkey registration options. |
| `POST` | `/register/verify` | Verify and save new Passkey credentials. |
| `GET` | `/login/options/{user}` | Generate authentication options for a user. |
| `POST` | `/login/verify` | Verify login and return a Bearer JWT. |

### Matches & Dashboard (`/api`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/dashboard/matches` | Returns all matches the user is hosting or joining. |
| `POST` | `/matches` | Create a new match (protected). |
| `GET` | `/matches/{id}` | Detailed roster and game info. |
| `POST` | `/matches/{id}/toggle-join` | Atomic join/leave logic for games. |
| `DELETE` | `/matches/{id}` | Cancel a match (Host only). |

---

## 📂 Project Structure
```text
PitchPass/
├── app/
│   ├── api/            # Route controllers (login, register, matches)
│   ├── core/           # Security & JWT utilities
│   ├── db/             # Mock DB logic and db.json
│   └── main.py         # Application entry point & dependencies
├── static/             # Frontend assets (dashboard.html, login.html)
└── requirements.txt    # FastAPI, PyWebAuthn, python-jose
```

---

## 🛠️ Development Setup

1.  **Install Dependencies:**
    ```bash
    pip install fastapi uvicorn python-jose[cryptography] pywebauthn pydantic
    ```

2.  **Run the API:**
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```

3.  **Run the UI:**
    ```bash
    # From the project root
    python3 -m http.server 3000
    ```

---

## 📝 Recent Implementation Notes
* **Unified Identity:** The system now consistently uses UUIDs for `user_id` across JWT claims and database records to prevent identity mismatch.
* **Atomic Updates:** `save_db(db)` is called after every state change to ensure data persistence during the development cycle.
* **CORS Configuration:** Fully configured to allow communication between the local dev server (`:3000`) and the API (`:8000`).

---
