# 📊 Retail Demand Anomaly Detection

> *Because if your sales spike by 400% on a random Tuesday, it’s either a viral TikTok or a data entry error. Usually the latter.*

<div align="center">

</div>

---

## 🧐 What is this?

Let’s be honest: retail data is a chaotic mess of seasonal trends, supply chain hiccups, and human error. Identifying a real "anomaly" is like trying to find a needle in a haystack while the haystack is on fire.

**Retail Demand Anomaly Detection** is a full-stack ML solution designed to parse messy sales data and scream "Wait, that’s not right!" when it sees a deviation. It doesn't just find spikes; it uses **Isolation Forests** to distinguish between a successful marketing campaign and a genuine demand outlier. It even calculates a "Waste Risk" score to tell you exactly how much money you're throwing in the bin.

---

## ✨ Key Features

* **Unsupervised Anomaly Detection**: Uses Isolation Forests to catch unusual sales spikes, drops, or stocking patterns without needing labeled "bad" data.
* **Waste Risk Engine**: A rule-based scoring system (0-100) that factors in current waste, historical trends, and perishability to provide urgent markdown recommendations.
* **Synthetic Data Generation**: Includes a generator that mimics real-world retail patterns, weekends, and seasonality so you can test without real data.
* **RESTful API**: Flask-based endpoints for detecting anomalies, calculating risk, and triggering retraining.
* **Automated Feature Engineering**: Automatically handles cyclical encoding (sine/cosine) for dates and rolling windows for sales trends.

---

## 📂 Project Structure

I've mapped out the guts of this repo. If you can't find the entry point, that's a *you* problem.

```bash
retail-demand-anamoly-detection/
├── src/
│   ├── app.py                # Flask API & endpoint definitions
│   ├── anomaly_detector.py   # Isolation Forest model wrapper
│   ├── waste_predictor.py    # Rule-based risk & recommendation logic
│   ├── feature_engineering.py# Temporal and rolling statistics pipeline
│   ├── data_generator.py     # Synthetic retail data engine
│   └── database.py           # SQLite manager for sales and predictions
├── tests/
│   └── test_system.py        # Integration tests for the API
├── Dockerfile                # Multi-stage-ish slim Python build
├── docker-compose.yml        # Service orchestration
├── Makefile                  # Shortcuts for the lazy (install, test, run)
└── requirements.txt          # The usual suspects (Scikit-Learn, Pandas, Flask)

```

---

## 🛠 Tech Stack

| Component | Technology | Why? |
| --- | --- | --- |
| **Language** | Python 3.9 | Because doing math in anything else is masochism. |
| **API** | Flask | Lightweight and doesn't get in the way. |
| **Machine Learning** | Scikit-Learn | Specifically `IsolationForest` for outlier detection. |
| **Data Handling** | Pandas & NumPy | Wrangling dataframes like a digital cowboy. |
| **Storage** | SQLite | Zero-config database for local persistence. |

---

## 💿 Installation & Setup

Want to find some anomalies? Follow these steps. If you see a `ModuleNotFoundError`, re-read step 2 very slowly.

### 1. Clone the Repo

```bash
git clone https://github.com/ankitmahendru/retail-demand-anamoly-detection.git
cd retail-demand-anamoly-detection

```

### 2. The "I hate Docker" Method (Local)

```bash
make install # Installs requirements.txt
make run     # Starts the Flask app on port 5000

```

### 3. The "I love Containers" Method (Docker)

```bash
make docker-run # Builds and starts the system via docker-compose

```

---

## 🎮 API Endpoints

| Endpoint | Method | Description |
| --- | --- | --- |
| `/health` | `GET` | Checks if the model is loaded and ready. |
| `/detect-anomalies` | `POST` | Identifies outliers in a date range for a specific store. |
| `/waste-risk` | `POST` | Calculates 0-100 risk levels and gives markdown advice. |
| `/generate-data` | `POST` | Injects synthetic data and triggers model retraining. |

## 🤝 Contribution Guide

Think my math is off? Or maybe the Isolation Forest is too "contaminated"?

1. **Fork it.**
2. **Branch it** (`git checkout -b feature/isolation-forest-pro`).
3. **Commit it** (Keep it clean, or I'll reject it).
4. **Push it.**
5. **PR it.**

---

<div align="center">

**Made with love (and high-variance data) by PadhoAI** ❤️

</div>
