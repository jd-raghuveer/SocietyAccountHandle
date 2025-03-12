# 💰 **Deposit and Loan Management System**

Welcome to the **Deposit and Loan Management System**! This platform empowers administrators to manage deposits, loans, and user financial information efficiently, with real-time calculations and detailed PDF reports.

---

## 🌟 **Features**

### 📥 **Deposit Management**
- **Add Deposits**:
  - Breakdowns include:
    - **Fixed Deposit**
    - **Interest on Loan** (if applicable)
    - **Fine for Late Payment**
  - Real-time calculations ensure accuracy before adding.
- **View Individual Deposit Details**:
  - Search by user name to retrieve:
    - **Fixed Deposit**
    - **Fine**
    - **Total Amount Received**
    - **Installment**
    - **Date**
    - **Loan Amount Before** and **After**.
- **Retrieve Monthly Deposits**:
  - Generate a **PDF Report** containing deposit information for all users of a particular month.

---

### 💳 **Loan Management**
- **Approve Loans**:
  - Admins can approve loans for registered users.
- **Retrieve Loan Information**:
  - Generate **PDF Reports** with detailed loan data.
- **Delete Loan Records**:
  - In case of errors, admins can delete loan approvals, resetting all fields to their previous state.

---

### 🛠️ **Error Handling**
- Admins can:
  - **Delete Deposits** or **Loan Approvals** in case of mistakes, restoring fields to their original state.

---

## ⚙️ **Tech Stack**
- **Backend**: Python Flask
- **Frontend**: HTML, CSS, Bootstrap
- **Database**: MySQL (using MySQL Connector)
- **PDF Generation**: ReportLab / Flask-WeasyPrint (or any library used for PDF generation)
- **Real-Time Calculations**: JavaScript / Backend Logic

---

## 🚀 **Getting Started**

### 📋 Prerequisites
- Python 3.x
- MySQL Server
- Virtual Environment (optional but recommended)

### 📥 Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/darshanchouthai/SocietyAccountHandle.git
   ```
2. Navigate to the project directory:
   ```bash
   cd SocietyAccountHandle
   ```
3. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Set up environment variables:
   - Create a `.env` file in the root directory.
   - Add the following variables:
     ```
     SECRET_KEY=your_secret_key
     MYSQL_HOST=localhost
     MYSQL_USER=your_mysql_user
     MYSQL_PASSWORD=your_mysql_password
     MYSQL_DB=deposit_loan_db
     ```

---

## ▶️ **Run the Application**
1. Start the development server:
   ```bash
   flask run
   ```
2. Access the platform in your browser:
   ```
   http://127.0.0.1:5000
   ```

---

## 🌐 **Features Overview**

### 💰 **Deposit Workflow**
- Admins can add deposits for users.
- Real-time calculations ensure the correct breakdown of:
  - **Fixed Deposit**
  - **Interest (if applicable)**
  - **Fine (if applicable)**
- Deposit details can be retrieved:
  - Individually by user name.
  - Monthly for all users in **PDF format**.

### 💳 **Loan Workflow**
- Admins can approve loans for users.
- Loan information is retrievable in **PDF format**.
- If errors occur, loan approvals can be deleted, resetting related data.

### 📜 **PDF Reporting**
- Monthly deposits and individual user deposits can be exported to PDFs with:
  - **Fixed Deposit**
  - **Fine**
  - **Total Amount Received**
  - **Installment**
  - **Date**
  - **Loan Before and After**
- Loan reports can also be generated as PDFs.

### 🛠️ **Error Handling**
- Mistakes in deposits or loan approvals can be resolved by:
  - Deleting the corresponding record.
  - Restoring all related fields to their pre-transaction state.

---

## 🌐 **Deployment**
- Use a production server like Gunicorn for Flask.
- Deploy to platforms like **Heroku, AWS, or Azure**.
- Set environment variables appropriately.

---

## 🤝 **Contributing**
We welcome contributions to enhance this platform. To contribute:
1. Fork the repository.
2. Create a feature branch:
   ```bash
   git checkout -b feature-branch-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add: Description of changes"
   ```
4. Push your changes:
   ```bash
   git push origin feature-branch-name
   ```
5. Open a **Pull Request**.

---

## 📜 **License**
This project is licensed under the **MIT License**.

---

## 📧 **Contact**
For inquiries or feedback, contact us at:
**darshanchouthai@gmail.com**

---

🌟 **Thank You for Using the Platform!** 🚀

Your trusted companion for managing deposits and loans effectively.

