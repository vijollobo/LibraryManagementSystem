# Library Management System

A **full-stack Library Management System** built using _Streamlit (Python)_ for the application layer and _MySQL_ for persistent data storage. The system implements a _role-based authentication model_ supporting _administrators and library users_, enabling efficient management of books, members, issuing workflows, and communication through automated email notifications.

The project demonstrates principles of modular architecture, _database-driven application design, secure authentication practices_, and _interactive web interfaces_ using Streamlit.

This repository serves as a _demonstration-grade implementation_ intended for learning, experimentation, and portfolio display rather than production deployment.

# Features
## Authentication System

The system implements a credential-based authentication workflow with role separation.

### Sign In
* Users authenticate using username and password.
* If the credentials correspond to the default administrator:
```
Username: admin
Password: admin@123
```
the system logs in as an **Administrator**.

Otherwise, authentication occurs against the _users table in MySQL_, and the user is logged in with _standard user privileges_.

### Sign Up (User Registration)

The system allows creation of new user accounts with:
* Username validation
* Email verification
* Phone number validation
* Gender selection
* Date of birth validation
* Password hashing
* Security question setup
After successful registration:
* A _confirmation email_ is sent to the registered email address.
* The user can log in immediately after verification.

### Forgot Password

The system implements a multi-stage password recovery workflow:
1. Username verification
2. Security question validation
3. Email OTP verification
4. Password reset
This ensures multi-factor identity verification before password modification.

## Admin Dashboard
After authentication as Administrator, the system exposes the following administrative operations:

* Dashboard
* Add Book
* Edit Book Details
* Delete Book
* View Books
* Issue Book
* Return Book
* Issue Requested Book
* Issued Books Report
* Get Details of a Particular Book
* View All Requested Books
* Filter Book
* View All Users
* Delete User
* Broadcast Email to Users
* Logout

### Key Administrative Capabilities
#### Book Management
* Add new books
* Update book metadata
* Delete books
* View complete catalogue
#### Circulation Management
* Issue books to users
* Accept book returns
* Maintain issuing records
* Generate issued books reports
#### Request Management
* View user book requests
* Approve and issue requested books
#### User Management
* View registered users
* Delete user accounts
#### Communication System
* Broadcast email notifications to multiple users
* Supports HTML email templates

## User Dashboard

Once logged in as a standard user, the interface provides the following functionalities:

* Profile
* Search Books
* Books Issued to Me
* Request a Book
* Issued Books History
* Get Book Details
* Change Password
* Logout

### Key User Capabilities
#### Profile Management
* View personal information
* Update profile details
* Change account password
#### Book Discovery
* Search books using filters
* Retrieve detailed book information
#### Borrowing Operations
* View books currently issued
* Access issuing history
#### Book Request System
* Submit book requests for unavailable titles

# System Architecture
The application follows a modular architecture separating core responsibilities:
```
LibraryManagementSystem
│
├── main.py
│   Entry point for the application
│
├── functions.py
│   Contains utility functions including:
│   • Authentication
│   • Database queries
│   • Email services
│   • Validation helpers
│
├── common.py
│   Shared utilities and helper methods
│
├── library.sql
│   MySQL schema and database initialization
│
├── requirements.txt
│   Python dependencies
│
└── pages
    ├── admin.py
    │   Admin dashboard implementation
    │
    └── users.py
        User dashboard implementation
```
Technology Stack
|      Layer     |           Technology           |
|:--------------:|:------------------------------:|
| Frontend       | Streamlit                      |
| Backend        | Python                         |
| Database       | MySQL                          |
| Email Service  | SMTP                           |
| Authentication | Custom credential verification |
| Deployment     | Local environment              |

# Installation Guide
## 1. Clone the Repository
```
git clone https://github.com/vijollobo/LibraryManagementSystem.git
cd LibraryManagementSystem
```
## 2. Create Virtual Environment (Recommended)
```
python -m venv venv
```
Activate it:
Windows
```
venv\Scripts\activate
```
Linux / macOS
```
source venv/bin/activate
```
## 3️. Install Dependencies
```
pip install -r requirements.txt
```
## Database Setup (MySQL)
The project uses **MySQL** for persistent storage.
### Step 1 — Open MySQL Command Line Client
```
mysql -u root -p
```
Enter your MySQL password.
### Step 2 — Create Database
```
CREATE DATABASE library;
```
### Step 3 — Select Database
```
USE library;
```
### Step 4 — Import SQL Schema
Navigate to the repository directory and run:
```
mysql -u root -p library < library.sql
```
Alternatively inside MySQL CLI:
```
SOURCE path/to/library.sql;
```
This script will automatically create:
* Users table
* Books table
* Issued books records
* Request tables
* Required relational constraints

## Configure Database Connection
Ensure that the database credentials inside functions.py match your local MySQL configuration.
Example:
```
mysql.connector.connect(
    host="localhost",
    user="root",
    password="yourpassword",
    database="library"
)
```
## Email Configuration
The system sends emails for:
* Account creation
* OTP verification
* Broadcast notifications

Configure SMTP credentials inside the email utility function in `functions.py`.

Example configuration:
```
EMAIL_ADDRESS = "your_email@gmail.com"
EMAIL_PASSWORD = "app_password"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
```
### Generating a Gmail App Password
Google no longer allows applications to authenticate using your regular Gmail account password. Instead, you must generate a Gmail App Password.

### ⚠️ Important:
This password is NOT your Gmail login password.
It is a separate 16-character password generated specifically for third-party applications.

Generating a Gmail App Password

Google no longer allows applications to authenticate using your regular Gmail account password. Instead, you must generate a Gmail App Password.

⚠️ Important:
This password is NOT your Gmail login password.
It is a separate 16-character password generated specifically for third-party applications.

#### Step 1 — Enable Two-Factor Authentication
1. You may skip this step if you already have your two-factor authentication; else, follow teh following steps.
2. Go to your [Google Account settings](https://myaccount.google.com/security)
3. Navigate to Signing in to Google
4. Enable 2-Step Verification

#### Step 2 — Generate an App Password
1. Visit [link](https://myaccount.google.com/apppasswords)
2. Select:
```
App: Mail
Device: Other
```
3. Enter a name such as:
```
LibraryManagementSystem
```
4. Click **Generate**
Google will provide a 16-character **App Password** similar to:
```
abcd efgh ijkl mnop
```
#### Step 3 — Use the App Password in the Project

Replace the `EMAIL_PASSWORD` field with the generated password:
```
EMAIL_PASSWORD = "abcdefghijklmnop"
```
Refrain from using spaces when copying it into the code.

#### ⚠️ Security Notice
* Do NOT use your Gmail login password in this project.
* Only use the App Password generated by Google.
* Never commit real email credentials to a public GitHub repository.
For better security, you may store credentials in environment variables instead of directly inside the source code.

# Running the Application
Start the Streamlit server:
```
streamlit run main.py
```
The application will launch in your browser:
```
http://localhost:8501
```
 Demo Credentials
Administrator login:

Username: admin
Password: admin@123
These credentials are included only for **demonstration purposes**.

# Example Workflow
Typical application usage follows the sequence:
1. User signs up
2. Email verification confirms registration
3. User logs in
4. Admin adds books
5. Users search and request books
6. Admin approves requests and issues books
7. Users return books
8. Admin generates reports

# Security Considerations
The system implements several security practices:
* Password hashing
* Email verification
* OTP based password reset
* Role-based access control
* Session management via Streamlit session state
However, the project is intended as an educational prototype and may require additional security hardening before production deployment.

# Author
Developed by: Vijol Lobo

GitHub Repository: https://github.com/vijollobo/LibraryManagementSystem
