import streamlit as st
import random as rand
import string
import re
from datetime import date
from dateutil.relativedelta import relativedelta
from functions import * 

Today = date.today()

st.set_page_config(page_title="Library Management System", layout="centered")
st.title("Library Management System")

# SESSION INIT

for key in ["logged_in", "username", "role", "otp", "verified_user", "email_verified"]:
    if key not in st.session_state:
        st.session_state[key] = None


# HELPERS

def authenticate(username, password):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT password_hash, role FROM users WHERE username=%s", (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    if row["password_hash"] == hash_password(password):
        return row["role"]
    return None

def accept_phone():
    phone = st.text_input("Phone Number", max_chars=10)
    if phone:
        if re.match(r'^[6-9]\d{9}$', phone):
            if table_parameter_exists("users","phone", phone):
                st.error("Phone number already registered")
                return None
            return phone
        st.error("Invalid phone number (must start with 6–9 and be 10 digits)")
    return None


def email_verificationOTP(name: str, email: str) -> bool:
    """
    Sends OTP to the given email and verifies it.
    Returns True if verified, else False.
    """

    #  SESSION INIT 
    for key, default in {
        "email_otp": None,
        "email_otp_sent": False,
        "email_verified": False
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default

    # SEND OTP 
    if not st.session_state.email_verified:

        if not st.session_state.email_otp_sent:
            if st.button("Send OTP to email"):
                st.session_state.email_otp = str(rand.randint(100000, 999999))
                st.session_state.email_otp_sent = True

                send_email(
                    email,
                    "Email Verification OTP",
                    f"""
Dear {name},

Your One-Time Password (OTP) for email verification is:

    {st.session_state.email_otp}

Please enter this OTP in the application.
Do not share this OTP with anyone.

Warm regards,
Librarian
Central Library
{date2string(Today)}
"""
                )
                st.success(f"OTP sent to {email}")

        # OTP INPUT (STATE-DRIVEN) 
        if st.session_state.email_otp_sent:

            st.markdown("### Enter 6-digit OTP")

            otp_input = st.text_input(
                "OTP",
                max_chars=6,
                placeholder="XXXXXX",
                help="Enter the 6-digit numeric OTP sent to your email"
            )

            if otp_input:
                if not otp_input.isdigit():
                    st.error("OTP must contain digits only")
                elif len(otp_input) != 6:
                    st.error("OTP must be exactly 6 digits")
                elif otp_input == st.session_state.email_otp:
                    st.session_state.email_verified = True
                    st.success("Email verified successfully")
                else:
                    st.error("Incorrect OTP")

    return st.session_state.email_verified

def accept_email(name: str):
    email = st.text_input("E-mail address").strip().lower()

    # 1. Empty input → do nothing
    if not email:
        return None

    # 2. Format validation
    if not validate_email(email):
        st.error("Invalid email format")
        return None

    # 3. Uniqueness check
    if table_parameter_exists("users", "email", email):
        st.error("Email already registered")
        return None

    st.success("Valid email address, verification required")

    # 4. Trigger OTP workflow ONLY for valid + unique email
    verified = email_verificationOTP(name, email)

    # 5. Return only after verification
    if verified:
        return email

    return None


    

# --------------------------------------------------
# MAIN MENU
# --------------------------------------------------
choice = st.radio("Choose Action", ["Sign In", "Sign Up", "Forgot Password", "Change Password"])

# ==================================================
# SIGN IN
# ==================================================
if choice == "Sign In":

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if not username or not password:
            st.error("All fields required")
        else:
            role = authenticate(username, password)
            if not role:
                st.error("Invalid username or password")
            else:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = role

                if role == "admin":
                    st.switch_page("pages/admin.py")
                else:
                    st.switch_page("pages/users.py")

# ==================================================
# SIGN UP (USER ONLY)
# ==================================================
elif choice == "Sign Up":

    st.subheader("Create New User Account")

    username = st.text_input("Username (5–20 characters, no spaces)").strip()

    if username:
        if " " in username:
            st.error("Username must not contain spaces")
        elif not (5 <= len(username) <= 20):
            st.error("Username length must be between 5 and 20 characters")
        elif table_parameter_exists("users","username", username):
            st.error("Username already exists")

    name = st.text_input("Full Name",placeholder='Vijol Lobo').title().strip()
    email = accept_email(name)
    phone = accept_phone()
    gender = st.selectbox("Gender", ("Cisgender Male","Cisgender Female", 'Transgender Male', 'Transgender Female', 'Non-Binary', 'Genderfluid', 'Bigender', 'Agender','Intergender',"Prefer not to say","Custom"))
    if gender == "Custom":
        gender = st.text_input("Please specify your gender")

    dob = st.date_input(
        "Date of Birth",
        Today - relativedelta(years=12),
        min_value=date(1900, 1, 1),
        max_value=Today - relativedelta(years=12)
    )
    password = st.text_input("Password", type="password")

    questions = (
        "My favourite teacher",
        "My best friend's name",
        "My favourite food",
        "My favourite artist",
        "My nickname"
    )

    q_text = st.selectbox("Security Question", questions)
    q_ans = st.text_input("Answer")

    if st.button("Create Account"):
        if not all([username, name, email, phone, password, q_ans]):
            st.error("All fields are mandatory")
        elif not st.session_state.email_verified:
            st.error("Email not verified")
        else:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO users
                (username, name, email, phone, gender, dob, password_hash, role, security_q, security_ans)
                VALUES (%s,%s,%s,%s,%s,%s,%s,'user',%s,%s)
                """,
                (
                    username, name, email, phone, gender, dob,
                    hash_password(password), questions.index(q_text)+1, q_ans
                )
            )
            conn.commit()
            conn.close()

            send_email(
                email,
                f"Library Account Created — Thank You {name} for registering with us",
                f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Library Account Created</title>
</head>
<body style="font-family: Georgia, 'Times New Roman', serif; background-color:#f7f7f7; margin:0; padding:0;">

  <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center" style="padding:30px;">
        <table width="650" cellpadding="20" cellspacing="0" style="background-color:#ffffff; border-radius:6px; box-shadow:0 2px 6px rgba(0,0,0,0.1);">

          <!-- Header -->
          <tr>
            <td align="center">
              <h2 style="margin-bottom:5px;">Central Library</h2>
              <p style="margin-top:0; font-style:italic; color:#555;">
                Account Creation Confirmation
              </p>
              <hr>
            </td>
          </tr>

          <!-- Greeting -->
          <tr>
            <td>
              <p>Dear <strong>{name}</strong>,</p>

              <p>
                We are pleased to inform you that your library account has been
                <strong>successfully created</strong>. Below are the credentials
                and details associated with your membership.
              </p>
            </td>
          </tr>

          <!-- Credentials -->
          <tr>
            <td>
              <h3> Login Credentials</h3>
              <pre style="background:#f2f2f2; padding:12px; border-radius:4px; font-family:'Fira Code', monospace;">
Username           : <b>{username}</b>
Password           : <b>{password}</b>
Role               : User
Security Question  : {q_text}
Answer             : {q_ans}
              </pre>

              <p style="color:#b00020;">
             Please store these credentials securely and do not share them with anyone.
              </p>
            </td>
          </tr>

          <!-- Stored Details -->
          <tr>
            <td>
              <h3>Your Details on Record</h3>
              <pre style="background:#f9f9f9; padding:12px; border-radius:4px; font-family:'Times New Roman', serif;">
<b>Name</b>          : {name}
<b>Email</b>         : {email}
<b>Phone</b>         : {phone}
<b>Gender</b>        : {gender}
<b>Date of Birth</b> : {date2string(dob)}
<b>Age</b>           : {calculateAge(dob)} years
              </pre>
            </td>
          </tr>

          <!-- Literary Message -->
          <tr>
            <td>
              <p>
                At our library, we endeavor to cultivate an unparalleled repository
                of knowledge—meticulously curated to serve scholars, thinkers,
                and discerning bibliophiles alike.
              </p>

              <p>
                Your membership marks the commencement of a new intellectual voyage,
                replete with erudition and discovery. From timeless classics and rare
                manuscripts to contemporary and avant-garde works, our collection
                awaits your exploration.
              </p>

              <p>
                Should you require any assistance or guidance, our dedicated team
                stands ready to serve you with diligence and alacrity.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td>
              <hr>
              <p style="font-size:13px; color:#666;">
                This is an auto-generated email. Any inconvenience caused is deeply regretted.
              </p>

              <p>
                With warm regards,<br>
                <strong>Librarian</strong><br>
                Central Library<br>
                {date2string(Today)}
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>

</body>
</html>
""",
    isHTML=True
            )

            st.success(f"Account created successfully. Confirmation email sent at {email}. Please sign in.")

# FORGOT PASSWORD

elif choice == "Forgot Password":

    st.subheader("Forgot Password")

    # ----------------- STEP 1: VERIFY USERNAME -----------------
    username = st.text_input("Username")

    if st.button("Verify Username"):
        if not table_parameter_exists("users", "username", username):
            st.error("Username not found")
        else:
            st.session_state.verified_user = username
            st.success("Username verified")

    # ----------------- STEP 2: SECURITY QUESTION -----------------
    if st.session_state.verified_user:

        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT security_q, security_ans, email FROM users WHERE username=%s",
            (st.session_state.verified_user,)
        )
        user = cur.fetchone()
        conn.close()

        q_reverse = (
            "My favourite teacher",
            "My best friend's name",
            "My favourite food",
            "My favourite artist",
            "My nickname"
        )

        st.markdown(f"**Security Question:** {q_reverse[user['security_q'] - 1]}")
        ans = st.text_input("Your Answer")

        if ans and ans.strip().lower() == user["security_ans"].lower():

            st.success("Security answer verified")

            # ----------------- STEP 3: SEND OTP -----------------
            if not st.session_state.fp_otp_sent:
                if st.button("Send OTP"):
                    st.session_state.fp_otp = str(rand.randint(100000, 999999))
                    st.session_state.fp_otp_sent = True

                    send_email(
                        user["email"],
                        "Password Reset OTP",
                        f"""
Dear {st.session_state.verified_user},

Your One-Time Password (OTP) for password reset is:

    {st.session_state.fp_otp}

Do not share this OTP with anyone.

Regards,
Central Library
"""
                    )
                    st.success("OTP sent to registered email")

            # ----------------- STEP 4: VERIFY OTP -----------------
            if st.session_state.fp_otp_sent:
                otp = st.text_input("Enter OTP", max_chars=6)
                new_pwd = st.text_input("New Password", type="password")

                if st.button("Reset Password"):
                    if otp != st.session_state.fp_otp:
                        st.error("Invalid OTP")
                    elif len(new_pwd) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute(
                            "UPDATE users SET password_hash=%s WHERE username=%s",
                            (hash_password(new_pwd), st.session_state.verified_user)
                        )
                        conn.commit()
                        conn.close()

                        st.success("Password reset successfully")

                        # -------- CLEANUP --------
                        st.session_state.verified_user = None
                        st.session_state.fp_otp = None
                        st.session_state.fp_otp_sent = False


# CHANGE PASSWORD (NO OTP)
elif choice == "Change Password":

    username = st.text_input("Username")
    old_pwd = st.text_input("Current Password", type="password")

    role = authenticate(username, old_pwd)

    if role:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT security_q, security_ans, name, email FROM users WHERE username=%s",
            (username,)
        )
        row = cur.fetchone()
        conn.close()

        q_reverse = {1:"My favourite teacher",2:"My best friend's name",3:"My favourite food",4:"My favourite artist",5:"My nickname"}
        st.write("Security Question:", q_reverse[row["security_q"]])
        ans = st.text_input("Answer")

        if ans == row["security_ans"]:
            new_pwd = st.text_input("New Password", type="password")
            if st.button("Change Password"):
                conn = get_connection()
                cur = conn.cursor()
                cur.execute(
                    "UPDATE users SET password_hash=%s WHERE username=%s",
                    (hash_password(new_pwd), username)
                )
                conn.commit()
                conn.close()

                send_email(
    row["email"],
    "Library Account Password Changed",
    f"""
Dear {row["name"]},

This is to inform you that the password for your Library account
has been changed successfully.

Account Details:
----------------
Username      : {username}
Old Password  : {old_pwd}
New Password  : {new_pwd}

If you did NOT request or authorize this change, please contact the Librarian or
Library Administration immediately for assistance.

Regards,
Librarian
Central Library
{date2string(Today)}

This is an auto-generated email. Please do not reply. Unintended inconvenience caused is deeply regretted.
"""
)

