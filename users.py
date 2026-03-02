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


st.set_page_config(page_title="User Dashboard", layout="wide")

st.title("User Dashboard")

menu = st.sidebar.radio(
    "User Actions",
    [
        "Search Books",
        "Books Issued to Me",
        "Request a Book",
        "Issued Books History",
        "Get Book Details",
        'Profile',
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
            avatar_url = "https://www.w3schools.com/howto/img_avatar.png" if profile['gender'] == 'Cisgender Male' else "https://www.w3schools.com/howto/img_avatar2.png"
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
        with edit_col:
            if st.button("Edit Profile"):
                st.info("Edit functionality coming soon!")
    else:
        st.error("User profile not found.")
    conn.close()

# LOGOUT 
elif menu == "Logout":
    st.session_state.clear()
    st.switch_page("main.py")
