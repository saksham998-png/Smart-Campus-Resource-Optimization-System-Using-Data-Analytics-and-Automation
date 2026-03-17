🏫 Smart Campus Resource Optimization System

Using Data Analytics and Automation

📌 Overview

The Smart Campus Resource Optimization System is a web-based application built using Flask that analyzes campus resource usage (electricity, water, and classroom utilization) and provides insights along with intelligent suggestions to improve efficiency.

This project leverages data analytics to help institutions make informed decisions for sustainable campus management.

🚀 Features

⚡ Electricity Usage Analysis

Total and average consumption

Building-wise comparison

Daily trends

💧 Water Usage Monitoring

Building-wise water consumption analysis

🏫 Classroom Utilization

Calculates utilization percentage

Identifies underutilized buildings

📊 Interactive Dashboard

Visual representation of data

Clean and user-friendly UI

🤖 Automated Suggestions

Smart recommendations for:

Energy saving

Space optimization

Maintenance planning

🔐 Login System

Basic session-based authentication

🛠️ Tech Stack

Backend: Python, Flask

Frontend: HTML, CSS

Data Processing: Pandas

Dataset: Excel (.xlsx) and CSV files

📂 Project Structure
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
⚙️ Installation & Setup

Clone the repository

git clone https://github.com/your-username/smart-campus-system.git
cd smart-campus-system

Create a virtual environment (optional but recommended)

python -m venv venv
source venv/bin/activate   # For Linux/Mac
venv\Scripts\activate      # For Windows

Install dependencies

pip install -r requirements.txt

Run the application

python app.py

Open your browser and go to:

http://127.0.0.1:5000/
📊 Dataset Details

The system uses:

smart_campus_200_row_dataset.xlsx

dataset.csv

Key Fields:

Building

Electricity_Units

Water_Usage_Liters

Rooms_Used

Total_Rooms

Date

💡 Example Insights Generated

Building with highest electricity consumption

Buildings with lowest utilization

Daily electricity trends

Resource optimization suggestions

🔮 Future Enhancements

Integration with IoT sensors

Real-time data tracking

Machine Learning-based predictions

Role-based authentication system

Mobile-friendly UI
