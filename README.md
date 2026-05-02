# 🛒 Price Comparison Pro

A full-stack web application that compares product prices across **Amazon, Flipkart, Ajio, Meesho**, and official brand stores in real-time.

![Tech Stack](https://img.shields.io/badge/Backend-Flask%20%7C%20Python-blue?style=flat-square)
![Tech Stack](https://img.shields.io/badge/Frontend-React%20%7C%20Vite-61DAFB?style=flat-square)
![Tech Stack](https://img.shields.io/badge/Database-SQLite-lightgrey?style=flat-square)

---

## ✨ Features

- 🔍 **Real-time price comparison** across 4+ major e-commerce sites
- ⚡ **Parallel scraping** — all sites fetched simultaneously
- 🏆 **Best Deal highlighting** with gold badge
- 💰 **Savings calculator** — shows how much you save vs highest price
- 🎨 **Premium glassmorphic dark UI** with smooth animations
- 🔽 **Sort** by price (Low → High / High → Low)
- 🔢 **Max price filter**
- 🕐 **1-hour caching** for repeat searches
- 👤 **User auth** (register/login with JWT)
- 📜 **Search history** stored per user

---

## 🗂️ Project Structure

```
Price/
├── backend/               # Flask REST API
│   ├── app.py             # Main Flask server & API routes
│   ├── scraper.py         # Web scrapers (Amazon, Flipkart, Ajio, Meesho)
│   └── requirements.txt   # Python dependencies
│
├── frontend/              # React + Vite app
│   ├── src/
│   │   ├── App.jsx        # Main React component
│   │   └── index.css      # Global styles (glassmorphism UI)
│   └── package.json
│
└── Pricecomparison.py     # Original Tkinter app (legacy reference)
```

---

## 🚀 Running Locally

### Prerequisites
- Python 3.9+
- Node.js 18+

### Step 1 — Start the Backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```
> API will run at **http://localhost:5000**

### Step 2 — Start the Frontend

```bash
cd frontend
npm install
npm run dev
```
> App will open at **http://localhost:5173**

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/search?q=product` | Search and compare prices |
| `POST` | `/api/register` | Register a new user |
| `POST` | `/api/login` | Login and receive JWT token |
| `GET` | `/api/history` | Get user's search history (auth required) |

---

## ☁️ Deployment

| Component | Platform | Notes |
|-----------|----------|-------|
| **Backend** | [Render](https://render.com) | Free tier, set start command to `gunicorn app:app` |
| **Frontend** | [Vercel](https://vercel.com) | Auto-detects Vite, free |

> ⚠️ Before deploying, update the API URL in `frontend/src/App.jsx` from `http://localhost:5000` to your Render backend URL.

---

## 🧰 Tech Stack

- **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Bcrypt, PyJWT, BeautifulSoup4, Requests
- **Frontend:** React, Vite, Axios, Lucide React
- **Database:** SQLite (via SQLAlchemy ORM)
- **Scraping:** requests + BeautifulSoup with parallel ThreadPoolExecutor

---

## 👨‍💻 Author

Built as a student project to learn full-stack web development.  
Feel free to fork and contribute! 🙌
