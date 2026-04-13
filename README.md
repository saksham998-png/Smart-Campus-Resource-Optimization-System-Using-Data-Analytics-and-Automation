# 🏫 Smart Campus Resource Optimization System

### *Using Data Analytics & Automation*

---

## 📌 Overview

The **Smart Campus Resource Optimization System** is a web-based application built using **Flask** that analyzes campus resource usage — including electricity, water, and classroom utilization — and provides actionable insights along with intelligent recommendations.

The goal is to help institutions **optimize resource consumption, reduce wastage, and improve operational efficiency** through data-driven decision-making.

---

## 🚀 Key Features

### ⚡ Electricity Analytics

* Total and average consumption tracking
* Building-wise comparison
* Weekly usage trends
* Wastage detection (based on usage patterns)

---

### 💧 Water Monitoring

* Building-wise water consumption
* Comparative analysis across campus

---

### 🏫 Classroom Utilization

* Utilization percentage calculation
* Identification of underutilized buildings
* Space optimization insights

---

### 📊 Interactive Dashboard

* Clean and intuitive UI
* Dynamic charts using real-time processed data
* Block-level drill-down analysis

---

### 🤖 Smart Suggestions Engine

* Automated recommendations for:

  * Energy saving
  * Maintenance actions
  * Space optimization
* Based on detected inefficiencies and patterns

---

### 🔐 Authentication System

* Basic login system using session management

---

## 🛠️ Tech Stack

| Layer         | Technology Used       |
| ------------- | --------------------- |
| Backend       | Python, Flask         |
| Frontend      | HTML, CSS, JavaScript |
| Data          | Pandas                |
| Dataset       | Excel (.xlsx), CSV    |
| Visualization | Chart.js              |

---

## 📂 Project Structure

```
Smart-Campus-Resource-Optimization-System/
│── app.py
│── one.py
│── dataset.csv
│── smart_campus_200_row_dataset.xlsx
│── requirements.txt
│
├── static/
│   └── style.css
│
├── templates/
│   ├── login.html
│   ├── dashboard.html
│   ├── electricity.html
│   ├── water.html
│   ├── classrooms.html
│   └── suggestions.html
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the repository

```bash
git clone https://github.com/saksham998-png/Smart-Campus-Resource-Optimization-System-Using-Data-Analytics-and-Automation.git
cd smart-campus-system
```

### 2️⃣ Create virtual environment (recommended)

```bash
python -m venv venv
```

**Activate:**

* Windows:

```bash
venv\Scripts\activate
```

* Mac/Linux:

```bash
source venv/bin/activate
```

---

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Run the application

```bash
python app.py
```

---

### 5️⃣ Open in browser

```
http://127.0.0.1:5000/
```

---

## 📊 Dataset Details

The system uses:

* `smart_campus_200_row_dataset.xlsx`
* `dataset.csv`

### Key Fields:

* Building
* Electricity_Units
* Water_Usage_Liters
* Rooms_Used
* Total_Rooms
* Date

---

## 💡 Insights Generated

* Building with highest electricity consumption
* Most efficient (low usage) building
* Daily/weekly usage trends
* Underutilized classrooms
* Resource wastage detection
* Optimization suggestions

---

## 🔮 Future Enhancements

* 🔌 Integration with IoT sensors (real-time data)
* 📡 Live monitoring dashboard
* 🤖 Machine Learning-based predictions
* 🔐 Role-based authentication (Admin/User)
* 📱 Fully responsive mobile UI

---

## 🎯 Project Goal

To transform raw campus data into **meaningful insights and actionable decisions**, enabling smarter and more sustainable campus management.

## 👥👥 Team Members

1. Saksham Kumar (2301730151)
2. Meenakshi (2301730200)
3. Raksha Sinha (2301730177)
4. Srishti Kainth (2301730175)