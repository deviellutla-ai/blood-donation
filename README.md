# 🩸 Blood Donation Management System

A web-based Blood Donation Management System built using **Python Flask** and **SQLite**. This application connects blood donors with people in need, allowing users to register as donors, request blood, search for available donors, and manage blood requests through an admin dashboard.

---

## 📌 Features

### 👤 User Features
- User Registration & Login
- Secure Password Hashing
- Donor Dashboard
- Update Donation Availability
- Search Donors by Blood Group and City
- Request Blood
- View Blood Request Status
- Donation History
- Contact Form

### 👨‍💼 Admin Features
- Admin Dashboard
- View Total Donors
- View Available Donors
- Monitor Blood Requests
- Update Request Status
- Blood Group Statistics
- Daily Donation Statistics

---

## 🛠️ Technologies Used

- Python 3
- Flask
- SQLite3
- HTML5
- CSS3
- JavaScript
- Jinja2 Templates
- Werkzeug Security

---

## 📂 Project Structure

```
Blood-Donation-Management-System/
│
├── app.py
├── blood_donation.db
├── templates/
│   ├── home.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── donors.html
│   ├── request_blood.html
│   ├── request_status.html
│   ├── history.html
│   ├── contact.html
│   ├── about.html
│   ├── admin.html
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
└── README.md
```

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Blood-Donation-Management-System.git
```

### 2. Navigate to the Project Folder

```bash
cd Blood-Donation-Management-System
```

### 3. Create a Virtual Environment (Optional)

Windows

```bash
python -m venv venv
venv\Scripts\activate
```

Linux/Mac

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install flask werkzeug
```

### 5. Run the Application

```bash
python app.py
```

The application will start at

```
http://127.0.0.1:5000
```

---

## 🗄️ Database

The application automatically creates an SQLite database named:

```
blood_donation.db
```

Tables created:

- Users
- Blood Requests
- Donation History
- Contact Messages

---

## 🔐 Authentication

- Secure password hashing using Werkzeug.
- Session-based authentication.
- Separate access for Admin and Donors.

---

## 📈 Future Improvements

- Email Notifications
- SMS Alerts
- Blood Camp Management
- Google Maps Integration
- Hospital Portal
- OTP Verification
- Dashboard Charts
- REST API Support

---

## 📸 Screenshots

Add screenshots of:

- Home Page
- Login Page
- Registration Page
- Donor Dashboard
- Search Donors
- Blood Request Form
- Admin Dashboard

---

## 🤝 Contributing

1. Fork the repository.
2. Create a feature branch.

```bash
git checkout -b feature-name
```

3. Commit your changes.

```bash
git commit -m "Added new feature"
```

4. Push to your branch.

```bash
git push origin feature-name
```

5. Open a Pull Request.

---

## 📄 License

This project is developed for educational and academic purposes.

---

## 👩‍💻 Author

**Ellutla Devi**

Bachelor of Technology (Electronics and Communication Engineering)

GitHub: https://github.com/devi

---

## ⭐ Support

If you found this project helpful, please give it a ⭐ on GitHub!
