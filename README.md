# 📌 Admin Panel for User Deposits & Loan Management

## 🏦 Overview
This is a **comprehensive admin panel** designed to manage deposits and loans for registered users. The admin has complete control over approving loans, adding deposits, retrieving records, and generating reports in **PDF format**. The system ensures real-time calculations before confirming transactions to maintain accuracy.

---

## 🔥 Features

### ➤ Deposit Management
✅ **Add Deposit**: Admin can add deposits for registered users.
✅ **Automatic Breakdown**: Deposits are split into:
   - **Fixed Deposit**
   - **Loan Interest (if applicable)**
   - **Late Payment Fine (if applicable)**
✅ **Real-time Calculation**: Before submission, the breakdown is shown to the admin.
✅ **Retrieve User Deposits**: Admin can fetch individual user deposit details using their name.
✅ **Monthly Deposit Reports**: Retrieve deposits of all users for a particular month in **PDF format**.
✅ **Undo Deposit**: If a mistake is made, the deposit can be deleted, restoring previous values.

### ➤ Loan Management
✅ **Loan Approval**: Admin can approve loans for registered users.
✅ **Retrieve Loan Info**: Generate a **PDF report** of loan details for any user.
✅ **Undo Loan Approval**: If a mistake is made, deleting a loan approval restores previous values.

---

## 🛠️ Tech Stack
- **Backend**: Python, Flask
- **Database**: MySQL
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **PDF Generation**: ReportLab / wkhtmltopdf
- **Deployment**: Hosted on PythonAnywhere


## 📂 Installation Guide

1️⃣ **Clone the Repository**
```sh
 git clone https://github.com/darshanchouthai/SocietyAccountHandle.git
 cd SocietyAccountHandle
```

2️⃣ **Install Dependencies**
```sh
 pip install -r requirements.txt
```

3️⃣ **Configure Database**
- Import `database.sql` into MySQL
- Update `config.py` with database credentials

4️⃣ **Run the Application**
```sh
 python app.py
```

5️⃣ **Access the Admin Panel**
- Open browser and visit: `http://localhost:5000/admin`

---

## 📝 Usage Guide
1. **Register Users**: Users must be registered before deposits or loans can be managed.
2. **Adding Deposits**: Enter the deposit amount, and the system calculates breakdowns automatically.
3. **Approving Loans**: Select a user and approve loans based on eligibility.
4. **Retrieving Information**:
   - Fetch **user deposit history** via name.
   - Generate **loan reports** in **PDF format**.
   - View **monthly deposit summaries** in **PDF format**.
5. **Undo Actions**: Mistaken transactions (deposit or loan approval) can be undone, restoring previous values.

---

## 🎯 Future Enhancements
- 📊 **Graphical Dashboard** for better data visualization.
- 🔔 **Automated Notifications** for due payments.
- 🔍 **Advanced Search & Filters** for faster data retrieval.

---

## 📧 Support
For any issues, feel free to **open an issue** or contact us at [darshanchouthai@gmail.com](mailto:darshanchouthai@gmail.com).

📌 **Contributions are welcome!** Feel free to fork and submit PRs. 🚀

