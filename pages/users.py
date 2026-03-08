import streamlit as st
from functions import *
from common import *
import re
from datetime import timedelta, date
import math
# SECURITY GATE 
if (
    "logged_in" not in st.session_state
    or not st.session_state.logged_in
    or st.session_state.role != "user"
):
    st.error("Unauthorized access. Please login as a user.")
    st.stop()

if "edit_profile_mode" not in st.session_state:
    st.session_state.edit_profile_mode = False

st.set_page_config(page_title="User Dashboard", layout="wide")

st.title("User Dashboard")

menu = st.sidebar.radio(
    "User Actions",
    [
        'Profile',
        "Search Books",
        "Books Issued to Me",
        "Request a Book",
        "Issued Books History",
        "Get Book Details",
        'Change Password',
        "Logout"
    ]
)

username = st.session_state.username

if menu == "Search Books":
    filterBooks()

elif menu == "Books Issued to Me":
    st.subheader("Books Currently Issued to You")

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT 
            ib.IssueCode,
            ib.issueDate,
            ib.dueDate,
            b.ISBN,
            b.name AS book_name,
            b.author,
            b.language
        FROM issued_books ib
        JOIN books b ON ib.ISBN = b.ISBN
        WHERE ib.username = %s AND ib.status = 'ISSUED'
        ORDER BY ib.issueDate DESC
    """, (username,))

    books = cur.fetchall()
    conn.close()

    if books:
        st.dataframe(books, use_container_width=True, hide_index=True)
    else:
        st.info("No books currently issued to you.")


elif menu == "Request a Book":
    st.subheader("Request a Book")

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT ISBN, name, author, language, quantity
        FROM books
        ORDER BY name
    """)
    books = cur.fetchall()

    book_map = {
        f"{b['name']} — {b['author']} ({b['ISBN']})": b
        for b in books
    }

    selection = st.selectbox("Select Book", book_map.keys())
    book = book_map[selection]

    st.markdown("### Book Details")
    st.write(f"**Title:** {book['name']}")
    st.write(f"**Author:** {book['author']}")
    st.write(f"**Language:** {book['language']}")
    st.write(f"**Available Copies:** {book['quantity']}")

    if book["quantity"] == 0:
        st.warning("This book is currently unavailable. You may still place a request.")
    
    if st.button("Request Book"):
        request_id = generate_code(cur=cur, table="requested_books", column="requestID")
        today = date.today()

        cur.execute("""
            INSERT INTO requested_books (requestID, username, ISBN, requestDate)
            VALUES (%s, %s, %s, %s)
        """, (
            request_id,
            username,
            book["ISBN"],
            today
        ))

        conn.commit()
        conn.close()

        st.success(
            f"Book request submitted successfully.\n\n"
            f"**Request Code:** `{request_id}`\n"
            f"**Request Date:** {date2string(today)}"
        )


elif menu == "Issued Books History":
    st.subheader("Previously Issued Books")

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT 
            ib.IssueCode,
            ib.issueDate,
            ib.returnDate,
            ib.accruedCost,
            ib.accruedFine,
            b.name AS book_name,
            b.author
        FROM issued_books ib
        JOIN books b ON ib.ISBN = b.ISBN
        WHERE ib.username = %s AND ib.status = 'RETURNED'
        ORDER BY ib.returnDate DESC
    """, (username,))

    history = cur.fetchall()
    conn.close()

    if history:
        st.dataframe(history, use_container_width=True, hide_index=True)
    else:
        st.info("No previous issue records found.")


elif menu == "Get Book Details":
    getBookDetails()

elif menu == 'Profile':
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT username, name, email, phone, gender, dob
        FROM users WHERE username = %s
    """, (username,))  
    profile = cur.fetchone()

    if profile:
        # --- Header Section ---
        st.markdown(f"## Namaskar, {profile['name']}!")
        st.markdown("---")

        # --- Profile Card Layout ---
        # Create two columns: Left for Avatar/Name, Right for Details
        col1, col2 = st.columns([1, 2])

        with col1:
            # Display a placeholder avatar based on gender
            avatar_url = "https://www.w3schools.com/howto/img_avatar.png" if profile['gender'] == 'Cisgender Male' else "https://www.w3schools.com/howto/img_avatar2.png" if profile['gender'] =='Cisgender Female' else 'https://static.thenounproject.com/png/4216248-200.png'
            st.image(avatar_url, width=150)
            st.subheader(profile['username'])
            #st.caption(f"Member since: {date.today().year}") # Or fetch actual joining date

        with col2:
            st.markdown("### Personal Information")
            
            # Using a table-like display with markdown for alignment
            info_df = {
                "Field": ["Full Name", "Email Address", "Phone Number", "Gender", "Date of Birth"],
                "Details": [
                    profile['name'],
                    profile['email'],
                    profile['phone'],
                    profile['gender'],
                    date2string(profile['dob']) if profile['dob'] else "Not Set"
                ]
            }
            
            # Display data in a clean key-value format
            for i in range(len(info_df["Field"])):
                st.markdown(f"**{info_df['Field'][i]}:** {info_df['Details'][i]}")

        st.markdown("---")

        # Stats Section 
        st.markdown("###  Library Activity")
        c1, c2, c3 = st.columns(3)

        cur.execute("SELECT COUNT(*) AS count FROM issued_books WHERE username = %s AND status = 'ISSUED'", (username,))
        issued_count = cur.fetchone()['count']
        cur.execute("SELECT COUNT(*) AS count FROM issued_books WHERE username = %s ", (username,))
        total_issued_count = cur.fetchone()['count']
        cur.execute("SELECT COUNT(*) AS count FROM requested_books WHERE username = %s", (username,))
        requested_count = cur.fetchone()['count']
        c1.metric("Books Currently  Issued", issued_count) 
        c2.metric("Pending Requests", requested_count)
        c3.metric("Total Books Issued so far", total_issued_count)

        # Action Buttons 
        st.markdown("<br>", unsafe_allow_html=True)
        edit_col, logout_col = st.columns([1, 5])
        # EDIT PROFILE 

        st.markdown("<br>", unsafe_allow_html=True)
        edit_col, logout_col = st.columns([1, 5])

        with edit_col:
            if st.button("Edit Profile"):
                st.session_state.edit_profile_mode = True

        # EDIT FORM 
        if st.session_state.edit_profile_mode:

            st.markdown("### Edit Profile")

            with st.form("edit_profile_form"):

                new_name = st.text_input("Full Name", value=profile["name"])
                new_email = st.text_input("Email", value=profile["email"])
                new_phone = st.text_input("Phone", value=profile["phone"])
                new_gender = st.selectbox(
                    "Gender",
                   ("Cisgender Male","Cisgender Female", 'Transgender Male', 'Transgender Female', 'Non-Binary', 'Genderfluid', 'Bigender', 'Agender','Intergender',"Prefer not to say","Custom")
    ,
                    index=["Cisgender Male", "Cisgender Female", 'Transgender Male', 'Transgender Female', 'Non-Binary', 'Genderfluid', 'Bigender', 'Agender','Intergender',"Prefer not to say","Custom"].index(profile["gender"])
                    if profile["gender"] in ["Cisgender Male", "Cisgender Female", 'Transgender Male', 'Transgender Female', 'Non-Binary', 'Genderfluid', 'Bigender', 'Agender','Intergender',"Prefer not to say","Custom"]
                    else 0
                )
                new_dob = st.date_input(
                    "Date of Birth",
                    value=profile["dob"] if profile["dob"] else None
                )

                save_btn = st.form_submit_button("Save Changes")
                cancel_btn = st.form_submit_button("Cancel")

            if cancel_btn:
                st.session_state.edit_profile_mode = False
                st.rerun()

            if save_btn:

                if not new_name.strip():
                    st.error("Name cannot be empty.")

                else:
                    conn = get_connection()
                    cur = conn.cursor(dictionary=True)
                    cur.execute("SELECT email, phone FROM users WHERE username=%s", (username,))
                    current_data = cur.fetchone()
                    conn.close()

                    email_changed = new_email.strip() != current_data["email"]
                    phone_changed = new_phone.strip() != current_data["phone"]

                    # -------- EMAIL VERIFICATION --------
                    if email_changed:
                        st.info("Email change requires verification.")
                        if not accept_email(new_name, new_email):
                            st.stop()

                    # -------- PHONE VERIFICATION --------
                    if phone_changed:
                        st.info("Phone change requires verification.")
                        if not accept_phone():
                            st.stop()

                    # -------- UPDATE DATABASE --------
                    conn = get_connection()
                    cur = conn.cursor()

                    cur.execute("""
                        UPDATE users
                        SET name=%s, email=%s, phone=%s, gender=%s, dob=%s
                        WHERE username=%s
                    """, (
                        new_name.strip(),
                        new_email.strip(),
                        new_phone.strip(),
                        new_gender,
                        new_dob,
                        username
                    ))

                    conn.commit()
                    conn.close()

                    st.success("Profile updated successfully!")
                    st.session_state.edit_profile_mode = False
                    st.rerun()
                
    else:
        st.error("User profile not found.")
    conn.close()

elif menu == "Change Password":

    st.subheader("Change Password")

    # STEP 1 — Verify current password
    old_pwd = st.text_input("Current Password", type="password")

    if not old_pwd:
        st.info("Enter your current password to proceed.")
        st.stop()

    role = authenticate(username, old_pwd)

    if not role:
        st.error("Incorrect current password.")
        st.stop()

    # STEP 2 — Security Question
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT security_q, security_ans, name, email FROM users WHERE username=%s",
        (username,)
    )
    row = cur.fetchone()
    conn.close()

    q_reverse = {
        1:"My favourite teacher",
        2:"My best friend's name",
        3:"My favourite food",
        4:"My favourite artist",
        5:"My nickname"
    }

    st.write("Security Question:", q_reverse[row["security_q"]])
    ans = st.text_input("Answer")

    if not ans:
        st.stop()

    if ans.strip().lower() != row["security_ans"].strip().lower():
        st.error("Incorrect security answer.")
        st.stop()

    st.markdown("---")
    st.markdown("### Set New Password")

    new_pwd = st.text_input("New Password", type="password")
    confirm_pwd = st.text_input("Confirm New Password", type="password")

    def strong_password(p):
        return (
            len(p) >= 8 and
            re.search(r"[A-Z]", p) and
            re.search(r"[a-z]", p) and
            re.search(r"\d", p) and
            re.search(r"[!@#$%^&*(),.?\":{}|<>]", p)
        )

    if st.button("Change Password"):

        if new_pwd != confirm_pwd:
            st.error("Passwords do not match.")
            st.stop()

        error = validate_password_strength(new_pwd)
        if error:
            st.error(error)
            st.stop()
            
        if new_pwd == old_pwd:
            st.warning("New password cannot be same as old password.")
            st.stop()

        # UPDATE PASSWORD
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET password_hash=%s WHERE username=%s",
            (hash_password(new_pwd), username)
        )
        conn.commit()
        conn.close()

        # Send safe email (NO password inside)
        send_email(
            row["email"],
            "Library Account Password Changed Successfully",
            f"""
Dear {row["name"]},

This is to inform you that your Library account password
was changed successfully on {date2string(date.today())}.

If you did NOT perform this action,
please contact the Librarian immediately.

Warm regards,
Librarian
Central Library
"""
        )

        st.success("Password changed successfully. Confirmation email sent.")
        st.rerun()
# LOGOUT 
elif menu == "Logout":
    st.session_state.clear()
    st.switch_page("main.py")
