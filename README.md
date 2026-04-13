# 📰 SENTIMENT AWARE FAKE NEWS DETECTION USING BLOCKCHAIN

## 🚀 Live Demo

🔗 https://fake-detection-blockchain.onrender.com/

---

## 📌 Project Overview

This project is a **Fake News Detection Web Application** that combines:

* 🧠 **Machine Learning (ML)**
* 🤖 **Google Gemini AI (LLM)**
* 🔗 **Blockchain Technology**

The system allows users to submit news articles, analyze their authenticity, and store verified data securely on a blockchain.

Blockchain ensures **transparency, immutability, and trust**, making it suitable for verifying content authenticity.

---

## 🎯 Features

### 👤 User Roles

* **Admin**
* **Reporter**
* **User**

### 📰 Core Functionalities

* ✅ News Submission by Reporters
* 🤖 AI-based Fake News Detection (Gemini API)
* 📊 Sentiment Analysis using ML
* 🔍 Detailed Fact Checking
* 🔗 Blockchain Storage for Verified News
* 🔐 Authentication System (Login/Register)
* 📜 News Feed & Detail View

---

## 🧠 Technologies Used

### 🔹 Backend

* Python (Flask)
* SQLite Database
* Gunicorn (Production Server)

### 🔹 Frontend

* HTML, CSS, JavaScript
* Jinja Templates

### 🔹 AI / ML

* Scikit-learn
* Google Generative AI (Gemini)

### 🔹 Blockchain

* Custom Python-based Blockchain implementation

---

## ⚙️ System Architecture

1. User submits news
2. ML model analyzes sentiment
3. Gemini AI checks authenticity
4. News stored in database
5. Verified news added to blockchain

---

## 📂 Project Structure

```
fake-detection-blockchain/
│
├── app.py
├── blockchain.py
├── requirements.txt
├── runtime.txt
├── .env
│
├── ml_models/
│   ├── sentiment_model.pkl
│   ├── fake_news_model.pkl
│
├── templates/
├── static/
└── database.db
```

---

## 🔧 Installation (Local Setup)

```bash
git clone https://github.com/prashanthpmg/fake-detection-blockchain.git
cd fake-detection-blockchain

pip install -r requirements.txt
python app.py
```

---

## 🔐 Environment Variables

```
SECRET_KEY=your_secret_key
DATABASE=database.db
UPLOAD_FOLDER=static/uploads
GEMINI_API_KEY=your_api_key
MODEL_NAME=gemini-2.5-flash-lite
```

---

## ☁️ Deployment

* 🌐 Render
* 🐍 Python 3.11
* ⚙️ Gunicorn

---

## 📸 Screenshots

### 🏠 Home Page

![Home Page](https://github.com/user-attachments/assets/9d548c54-a84d-4045-a8a5-069131884e4a)

---

### 🧑‍💻 Reporter Dashboard

![Reporter Dashboard](https://github.com/user-attachments/assets/image\(14\).png)

---

### 🛠️ Admin Dashboard

![Admin Dashboard](https://github.com/user-attachments/assets/image\(15\).png)

---

### 📰 News Display

![News Feed](https://github.com/user-attachments/assets/image\(16\).png)

---

### 🔗 Blockchain Verified News

![Blockchain View](https://github.com/user-attachments/assets/image\(17\).png)

---

## 🚨 Limitations

* SQLite not scalable for production
* Blockchain is simulated
* AI output depends on prompt quality

---

## 🔮 Future Enhancements

* 🔗 Ethereum Smart Contracts
* 📱 Mobile App
* 🌍 Real-time News APIs
* 📊 Analytics Dashboard
* 🧠 Advanced ML Models

---

## 👨‍💻 Author

**Prashanth M**

---

## 📜 License

Educational and academic use only.

---

## 💡 Conclusion

Fake news is a critical issue. By combining:

* AI & ML → Detection
* Blockchain → Trust

This project delivers a **secure and intelligent verification system**.

---
