# AI-Based Intrusion Detection System (IDS)

This project implements a machine learning-based Intrusion Detection System using the NSL-KDD dataset to identify anomalous network activity.

## 🚀 Features
- Anomaly detection using Isolation Forest
- FastAPI backend for real-time predictions
- REST API for detecting suspicious network traffic
- Lightweight and deployable system

## 🧠 Tech Stack
- Python
- FastAPI
- Scikit-learn
- Pandas, NumPy

## 📊 Dataset
- NSL-KDD (Network Intrusion Detection dataset)

## 🔧 How to Run

```bash
pip install -r requirements.txt
uvicorn app:app --reload