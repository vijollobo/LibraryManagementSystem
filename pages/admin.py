import streamlit as st
from functions import *
from common import *
import re
from datetime import timedelta, date
import math

Today=date.today()
sqldb=get_connection()
cursor = sqldb.cursor()

# SECURITY GATE 
if (
    "logged_in" not in st.session_state
    or not st.session_state.logged_in
    or st.session_state.role != "admin"
):
    st.error("Unauthorized access. Please login as admin.")
    st.stop()


st.set_page_config(page_title="Admin Dashboard", layout="wide")

st.title("Librarian Admin Dashboard")

# SIDEBAR 
menu = st.sidebar.radio(
    "Admin Operations",
    ['Dashboard',"Add Book", "Edit Book Details", "Delete Book", "View Books", 'Issue Book','Return Book','Issue Requested Book',"Issued Books Report",'Get Details of a particular book','View all Requested Books','Filter Book', "View All Users",'Delete User',"Broadcast Email to users","Logout"]
)


def issueBook(user=None, book=None):
    
    # Select user 
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    if user == None:
        cur.execute("SELECT username, name, email FROM users where role ='user' ORDER BY name")
        users = cur.fetchall()

        user_map = {
            f"{u['username']} — {u['name']}": u
            for u in users
        }

        user_choice = st.selectbox("Select User", list(user_map.keys()))
        user = user_map.get(user_choice)
    else:
        cur.execute("SELECT username, name, email FROM users where username=%s", (user["username"],))
        user = cur.fetchone()

    # Select available book 
    if book == None:
        cur.execute("""
            SELECT ISBN, name, native_name, author, language, publisher, cost, quantity
            FROM books
            WHERE quantity > 0
            ORDER BY name
        """)
        books = cur.fetchall()
        conn.close()

        book_map = {
            f"{b['name']} ({b['ISBN']})": b
            for b in books
        }

        book_choice = st.selectbox("Select Book", list(book_map.keys()))
        book = book_map.get(book_choice)
    else:
        cur.execute("SELECT * FROM books WHERE ISBN=%s", (book,))
        book = cur.fetchone()
        conn.close()

    if not user or not book:
        st.stop()

    #  Availability Check 
    if book['quantity'] <= 0:
        st.error(f" **Currently Unavailable:** '{book['name']}' has no copies left.")
        return False # Return False so the main menu knows it failed
    # Dates 
    issue_date = Today

    due_date = st.date_input(
        "Select Due Date",
        value=Today + timedelta(days=28),
        min_value=Today + timedelta(days=28),
        max_value=Today + timedelta(days=44)
    )

    days_issued = (due_date - issue_date).days+1

    # Cost calculation 

    probable_cost = calculate_cost(
        book_cost=book["cost"],
        issue_date=issue_date,
        due_date=due_date,
        return_date=due_date
    )

    # Display verification 
    st.markdown("### Verify Issue Details")

    st.markdown(f"""
**User:** {user['name']}  
**Username:** `{user['username']}`  

**Book Name:** {book['name']}  
**Author:** {book['author']}  
**ISBN:** `{book['ISBN']}`  
**Language:** {book['language']}  
**Publisher:** {book['publisher']}  
**Availablility** (before issue): {book['quantity']} {'book' if book['quantity'] == 1 else 'books'}  

**Issue Date:** {date2string(issue_date)}  
**Due Date:** {date2string(due_date)}  
**Total Days Issued:** {days_issued} {'day' if days_issued == 1 else 'days'} ({num2words(days_issued).capitalize()} {'day' if days_issued == 1 else 'days'}) 

**Probable Cost** (if returned on Due Date {date2string(due_date)}): **₹ {probable_cost['total_cost']}**  
**Cost in words**: {cost2word(probable_cost['total_cost'])}
""")

    # Final confirmation 
    if st.button("Issue Book"):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT issueCode FROM issued_books")
            result = cur.fetchall()
            while True:
                issue_code = generate_code(cur=cur, table="issued_books", column="issueCode")
                if not any(row[0] == issue_code for row in result):
                    break

            cur.execute("""
                INSERT INTO issued_books
                (IssueCode, ISBN, username, issueDate, dueDate, status)
                VALUES (%s,%s,%s,%s,%s,'ISSUED')
            """, (issue_code, book["ISBN"], user["username"], issue_date, due_date))

            cur.execute(
                "UPDATE books SET quantity = quantity - 1 WHERE ISBN=%s",
                (book["ISBN"],)
            )

            conn.commit()
            conn.close()

            # HTML Email 
            html_body = f"""
    <html>
    <head>
    <style>
        body {{
            font-family: Georgia, serif;
            background-color: #f8f9fa;
            color: #1c1c1c;
            line-height: 1.6;
            padding: 24px;
        }}
        .container {{
            max-width: 760px;
            margin: auto;
            background: #ffffff;
            padding: 28px 34px;
            border-radius: 8px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.08);
        }}
        h2 {{
            text-align: center;
            margin-bottom: 6px;
            letter-spacing: 0.5px;
        }}
        .subtitle {{
            text-align: center;
            font-size: 14px;
            color: #555;
            margin-bottom: 24px;
        }}
        h3 {{
            border-bottom: 1px solid #ddd;
            padding-bottom: 6px;
            margin-top: 28px;
            font-size: 18px;
        }}
        .mono {{
            font-family: 'Fira Code', monospace;
            background: #f1f3f5;
            padding: 12px 16px;
            border-radius: 6px;
            font-size: 14px;
        }}
        .book-block {{
            background: #fafafa;
            padding: 14px 18px;
            border-left: 4px solid #343a40;
            margin-top: 10px;
        }}
        .formula {{
            text-align: center;
            font-style: italic;
            background: #f6f6f6;
            padding: 12px;
            border-radius: 6px;
            margin: 12px 0;
        }}
        ul {{
            margin-top: 10px;
        }}
        footer {{
            margin-top: 30px;
            font-size: 14px;
            color: #444;
        }}
    </style>
    </head>

    <body>
    <div class="container">

        <h2>Book Issue Confirmation</h2>
        <div class="subtitle">Central Library</div>

        <p>Dear <i>{user['name']}</i>,</p>

        <p>
            We are pleased to inform you that the following book has been
            successfully issued under your library account. Kindly find the
            details below for your reference.
        </p>

        <h3>Issue Particulars</h3>
        <div class="book-block">
            <b>Issue Code</b>  : <code>{issue_code}</code><br>
            <b>Issue Date</b>  : {date2string(issue_date)}<br>
            <b>Due Date</b>    : {date2string(due_date)}<br>
            <b>Days Issued</b> : {num2words(days_issued).capitalize()} days
        </div>

        <h3>Book Information</h3>
        <div class="book-block">
            <b>Title</b> : {book['name']}<br>
            {f"<b>Title in {book['language']}</b> : {book['native_name']}<br>" if book.get('native_name',False) else ""}
            <b>Author</b> : {book['author']}<br>
            <b>ISBN</b> : <code>{book['ISBN']}</code><br>
            <b>Language</b> : {book['language']} {'('+nativeLang[book['language']]+')' if nativeLang.get(book["language"], False) or book['language'] != 'English' else ''}<br>
            <b>Publisher</b> : {book['publisher']}
        </div>

        <p><b>Probable cost upon return on the due date:</b></p>
        <div class="mono">₹ {probable_cost['total_cost']}</div>
        {cost2word(probable_cost['total_cost'])}
        <h3>Library Usage Guidelines</h3>
        <ul>
            <li>Every book entrusted to a reader shall be handled with the utmost care and reverence. Any act of defacement impairing the physical integrity of a bookshall be deemed a grave breach of conduct and shall invite strict disciplinary action.</li>
            <li>All borrowed books must be returned on or before the stipulated due date. Failure to comply shall result in the imposition of a <i>substantial and non-negotiable </i> fine, calculated in accordance with the rules of the institution. Prolonged delinquency may further entail suspension of borrowing privileges.</li>
            <li>Patrons are urged to remember that the library is a collective inheritance. Courtesy toward fellow readers, as well as toward the custodians of this institution, is not merely encouraged but expected.</li>
        </ul>

        <footer>
            <p>
                Your presence within these walls affirms our enduring mission to foster erudition, inquiry, and intellectual refinement. 
                We are deeply obliged for the respect, restraint, and conscientious regard you have shown toward our collections, 
                which are preserved not merely as objects of print, but as vessels of thought and legacy.
            </p>

            <p>
                We extend our sincere gratitude to you for making use of this Library and for upholding the dignity of this intellectual repository.
                May these halls continue to serve as a quiet refuge for inquiry and enlightenment.
            </p>

            <p>
                Thank You<br>
                Warm regards,<br>
                <b>Librarian</b><br>
                Central Library<br>
                {date2string(Today)}
            </p>
            <p><i>This is an auto-generated email. Please do not reply. Unintended inconvenience caused is deeply regretted.</i></p>
        </footer>

    </div>
    </body>
    </html>
    """


            send_email(
                user["email"],
                f"Library Book {book['name']} Issued Successfully",
                html_body,
                isHTML=True
            )

            st.success(f"Book issued successfully. A confirmation email has been sent to {user['email']}.")
            st.write(f"The Issue Code for this transaction is `{issue_code}`.")
            return True # Return True so the main menu knows it succeeded
        except Exception as e:
            st.error(f"An error occurred while issuing the book: {e}")
            return False # Return False so the main menu knows it failed
    return None




# ADD BOOK 

def input_book_data(parameter):
        cursor.execute(f"SELECT DISTINCT {parameter} FROM books ORDER BY {parameter}");result = cursor.fetchall()
        data = st.selectbox(f"{parameter.title()}", tuples2list(result)+['Others (Custom)'])
        if data == 'Others (Custom)':
            data = st.text_input(f"Enter custom {parameter} name")
        return data

def input_book_lang():
    sample_languages=('Arabic', 'Axomiya', 'Awadhi', 'Bangla', 'Bodo', 'Dogri', 'English', 'French', 'Gujarati', 'Hindi', 'Hindustani', 'Kannada', 'Koshur', 
               'Konkani', 'Maithili', 'Malayalam', 'Manipuri', 'Marathi', 'Nepali', 'Odia', 'Portuguese', 'Punjabi', 'Russian', 'Sanskrit', 
               'Santhali', 'Sindhi', 'Spanish', 'Tamil', 'Telugu', 'Urdu')
    cursor.execute("SELECT DISTINCT language FROM books");result = cursor.fetchall()
    language = st.selectbox("Language",sorted(set(sample_languages) | set(tuples2list(result))) + ['Others (Custom)'])
    if language == 'Others (Custom)':
        language = st.text_input("Enter custom language")
    return language


if menu == "Add Book":
    st.subheader("Add New Book")
    isbn = st.text_input("13-digit ISBN",max_chars=13, placeholder="978...")
    name = st.text_input("Book Name")

    language = input_book_lang()    

    native_name = None
    if language.lower() != "english":
        native_name = st.text_input(
            "Book Name in its Native Language",
            placeholder=f"Enter the name as written in {language}"
        )

    author = input_book_data("author")
    genre =  input_book_data("genre")
    publisher = input_book_data("publisher")
    
    cost = st.number_input("Cost (₹)", min_value=0.01)
    
    quantity = st.number_input("Quantity", min_value=1, step=1)

    if st.button("Add Book"):
        if not valid_isbn(isbn):
            st.error("ISBN must be exactly 13 digits")

        else:
            if table_parameter_exists("books", "ISBN", isbn):
                st.error("A book with this ISBN already exists, kindly re-check the ISBN.")
                st.stop()
            else:
                conn = get_connection()
                cur = conn.cursor()

                try:
                    cur.execute(
                        """
                        INSERT INTO books
                        (ISBN, name, author, language, genre, publisher, cost, quantity, native_name)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (isbn, name, author, language, genre, publisher, cost, quantity, native_name)
                    )
                    conn.commit()
                    st.success("Book added successfully")
                except Exception as e:
                    st.error(e)
                finally:
                    conn.close()


# EDIT BOOK 
elif menu == "Edit Book Details":
    st.subheader("Edit Book Details")

    isbn = getISBN('Select book to edit')
        
    fields=['Name', 'Native Name', 'Author', 'Language', 'Genre', 'Publisher', 'Cost', 'Quantity']
    cursor.execute(f"SELECT language FROM books WHERE ISBN=%s", (isbn,))
    result = cursor.fetchone()
    if result and result[0].lower() == "english": fields.remove('Native Name')
    field = st.selectbox("Select field to edit",fields).lower()

    cursor.execute(f"SELECT {field} FROM books WHERE ISBN=%s", (isbn,))
    result = cursor.fetchone()
    if result: 
        st.write(f"Current **{field}** of the book is **{result[0]}**")
    if field in {"author", "genre", "publisher"}:
        new_value = input_book_data(field)
    elif field == "language": 
        new_value = input_book_lang()
    elif field in {"cost", "quantity"}:
        new_value = st.number_input(f"Enter new {field}", min_value=0.01 if field=="cost" else 1, step=0.01 if field=="cost" else 1)
    else:
        new_value = st.text_input(f"Enter new {field} of the book")

    if st.button("Update"):
        if not valid_isbn(isbn):
            st.error("Invalid ISBN")
        else:
            conn = get_connection()
            cur = conn.cursor()

            try:
                cur.execute(
                    f"UPDATE books SET {field}=%s WHERE ISBN=%s",
                    (new_value, isbn)
                )
                conn.commit()
                st.success("Book updated successfully")
            except Exception as e: st.error(e)
            finally: conn.close()

# DELETE BOOK 
elif menu == "Delete Book":
    st.subheader("Delete Book")
    isbn = getISBN("Select book to delete")     

    if st.button("Delete"):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM books WHERE ISBN=%s", (isbn,))
        conn.commit()
        conn.close()

        st.success("Book deleted successfully")

# GET DETAILS OF A PARTICULAR BOOK
elif menu == 'Get Details of a particular book':
    getBookDetails()


# ---------- ISSUE BOOK ----------
elif menu == "Issue Book":
    st.subheader("Issue Book")
    issueBook()
#ISSUE REQUESTED BOOK
elif menu == "Issue Requested Book":
    st.subheader("Issue Requested Book")
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT r.requestID, r.username, r.ISBN, r.requestDate, u.name AS user_name, b.name AS book_name, b.quantity AS book_quantity
        FROM requested_books r
        JOIN users u ON r.username = u.username
        JOIN books b ON r.ISBN = b.ISBN
        ORDER BY r.requestDate
    """)
    requests = cur.fetchall()

    if not requests:
        st.info("No pending book requests found.")
        st.stop()

    request_map = {
        f"{req['requestID']}: {req['book_name']} by {req['user_name']} on {date2string(req['requestDate'])} {'(OUT OF STOCK)' if req['book_quantity'] == 0 else ''}": req
        for req in requests
    }

    selection = st.selectbox("Select Book Request to Issue", list(request_map.keys()))
    selected_request = request_map.get(selection)

    if selected_request:
        if selected_request['book_quantity'] <= 0:
            st.warning("This book is currently unavailable.")
            if st.button("Cancel and delete this Request"):
                    cur.execute("DELETE FROM requested_books WHERE requestID = %s", (selected_request["requestID"],))
                    conn.commit()
                    st.info("Request cancelled and removed from queue.")
                    st.rerun()
        else:
            # 2. Call the issue function
            # We pass the dictionary for user and the ISBN for book
            status = issueBook(user=selected_request, book=selected_request["ISBN"])
            
            # 3. Handle the return state
            if status == True:
                # Only delete the request if the database update in issueBook was successful
                cur.execute("DELETE FROM requested_books WHERE requestID = %s", (selected_request["requestID"],))
                conn.commit()
                st.success("Request queue updated.")
                st.rerun()
            elif status == False:
                st.error("The issuing process failed. Please check system logs.")
            # If status is None, we do nothing (the user hasn't clicked 'Confirm' yet)      
# RETURN BOOK
if menu == "Return Book":
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    st.header("Return Issued Book")
    # 1. FETCH ACTIVE ISSUE CODES
    cur.execute("""
    SELECT IssueCode
    FROM issued_books
    WHERE status = 'ISSUED'
    ORDER BY issueDate DESC
""")
    rows = cur.fetchall()

    issue_codes = [row["IssueCode"] for row in rows]

    if not issue_codes:
        st.info("No active issued books found.")
        st.stop()

    issue_code = st.selectbox(
        "Select Issue Code",
        issue_codes
    )

    # 2. FETCH ISSUE DETAILS
    cur.execute("""
        SELECT 
            ib.IssueCode,
            ib.issueDate,
            ib.dueDate,
            b.ISBN,
            b.name AS book_name,
            b.native_name AS book_native_name,
            b.author,
            b.language,
            b.publisher,
            b.cost AS book_cost,
            u.name AS user_name,
            u.email
        FROM issued_books ib
        JOIN books b ON ib.ISBN = b.ISBN
        JOIN users u ON ib.username = u.username
        WHERE ib.IssueCode = %s
          AND ib.status = 'ISSUED'
    """, (issue_code,))

    issue = cur.fetchone()

    if not issue:
        st.error("Invalid or already returned issue code.")
        st.stop()

    return_date = date.today()

    # 3. COST CALCULATION
    cost = calculate_cost(
        book_cost=issue["book_cost"],
        issue_date=issue["issueDate"],
        due_date=issue["dueDate"],
        return_date=return_date
    )

    # 4. DISPLAY BREAKDOWN
    st.subheader("Issue Particulars")
    st.write(f"**Issue Code:** {issue_code}")
    st.write(f"**Issued To:** {issue['user_name']}")
    st.write(f"**Issue Date:** {date2string(issue['issueDate'])}")
    st.write(f"**Due Date:** {date2string(issue['dueDate'])}")
    st.write(f"**Return Date:** {date2string(return_date)}")

    st.subheader("Book Details")
    st.write(f"**Title:** {issue['book_name']}")
    st.write(f"**Author:** {issue['author']}")
    st.write(f"**Language:** {issue['language']}")
    st.write(f"**Publisher:** {issue['publisher']}")
    st.write(f"**ISBN:** {issue['ISBN']}")

    st.subheader("Cost Particulars")
    col1, col2, col3 = st.columns(3)

    col1.metric("Total Days", cost["total_days"])
    col2.metric("Allowed Days", cost["allowed_days"])
    col3.metric("Late Days", cost["late_days"])

    col1.metric("Base Cost (₹)", cost["base_cost"])
    col2.metric("Late Fee (₹)", cost["late_fee"])
    col3.metric("Total Cost (₹)", cost["total_cost"])

    st.write(f"**Total Cost in Words:** {cost2word(cost['total_cost'])}")
    # -------------------------------------------------
    # 5. ADMIN CONFIRMATION
    # -------------------------------------------------
    st.warning("This action is irreversible.")

    if st.button("Return Book"):
        # DATABASE UPDATES
        cur.execute("""
            UPDATE issued_books
            SET returnDate = %s,
                accruedCost = %s,
                accruedFine = %s,
                status = 'RETURNED'
            WHERE issueCode = %s
        """, (
            return_date,
            cost["total_cost"],
            cost["late_fee"],
            issue_code
        ))

        cur.execute("""
            UPDATE books
            SET quantity = quantity + 1
            WHERE ISBN = %s
        """, (issue["ISBN"],))

        conn.commit()

        # EMAIL CONTENT (HTML)
        email_body = f"""
        <html>
        <head>
<style>
    body {{
        font-family: Georgia, serif;
        background-color: #f8f9fa;
        color: #1c1c1c;
        line-height: 1.6;
        padding: 24px;
    }}
    .container {{
        max-width: 760px;
        margin: auto;
        background: #ffffff;
        padding: 28px 34px;
        border-radius: 8px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.08);
    }}
    h2 {{
        text-align: center;
        margin-bottom: 6px;
        letter-spacing: 0.5px;
    }}
    .subtitle {{
        text-align: center;
        font-size: 14px;
        color: #555;
        margin-bottom: 24px;
    }}
    h3 {{
        border-bottom: 1px solid #ddd;
        padding-bottom: 6px;
        margin-top: 28px;
        font-size: 18px;
    }}
    .mono {{
        font-family: 'Fira Code', monospace;
        background: #f1f3f5;
        padding: 12px 16px;
        border-radius: 6px;
        font-size: 14px;
    }}
    .book-block {{
        background: #fafafa;
        padding: 14px 18px;
        border-left: 4px solid #343a40;
        margin-top: 10px;
    }}
    .formula {{
        text-align: center;
        font-style: italic;
        background: #f6f6f6;
        padding: 12px;
        border-radius: 6px;
        margin: 12px 0;
    }}
    ul {{
        margin-top: 10px;
    }}
    footer {{
        margin-top: 30px;
        font-size: 14px;
        color: #444;
    }}
</style>
</head>
        <body style="font-family:Georgia,serif; line-height:1.6;">
        <div class="container">

            <h2>Book Return Confirmation</h2>

            <p>Dear <i>{issue['user_name']}</i>,</p>

            {"""I extend my sincere gratitude for your exemplary <i>punctilious adherence</i>  in returning the issued book. 
             Your adherence to the prescribed return schedule reflects a commendable sense of responsibility, 
             and the meticulous condition in which the book has been preserved stands as a testament to your conscientious 
             <i>bibliophilic stewardship</i>."""
            if not cost["late_days"] 
            else
            """We acknowledge the successful return of the issued volume and appreciate the care exercised in maintaining its physical condition.
            However, as the book was returned beyond the stipulated due date, a nominal charge has been levied in accordance with institutional 
            policy to account for the extended retention period and associated administrative considerations."""
            }

            <p>
            However, I must bring to your <i>august attention</i> the pecuniary aspect
            attendant to this transaction. A nominal fee, amounting to
            <b>{cost2word(cost["total_cost"])}</b>, has been incurred. This modest sum is requisite
            to defray the administrative and restorative endeavors our institution
            undertakes to maintain the sanctity and longevity of our literary corpus.
            </p>

            <h3>Issue Particulars</h3>
    <div class="book-block">
<b>Issue Code</b>    : <code>{issue_code}</code><br>
<b>Issue Date</b>    : {date2string(issue['issueDate'])}<br>
<b>Due Date</b>      : {date2string(issue['dueDate'])}<br>
<b>Return Date</b>   : {date2string(return_date)}<br>
<b>Total Days</b>    : {cost["total_days"]} {'day' if cost["total_days"] == 1 else 'days'}<br>
<b>Late Days</b>    : {cost["late_days"]} {'day' if cost["late_days"] == 1 else 'days'}<br>
            </div>

            <h3>Book Details</h3>
            <div class="book-block">
<b>Title</b> : {issue['book_name']}<br>
{f"<b>Title in {issue['language']}</b> : {issue['book_native_name']}<br>" if issue.get('book_native_name',False) else ""}
<b>Author</b>      : {issue['author']}<br>
<b>Language</b> : {issue['language']} {'('+nativeLang[issue['language']]+')' if nativeLang.get(issue["language"], False) or issue['language'] != 'English' else ''}<br>
<b>Publisher</b>   : {issue['publisher']}<br>
<b>ISBN</b>        : <code>{issue['ISBN']}</code><br>
            </div>

            <h3>Cost Invoice</h3>
            <div class="book-block">
<b>Base Cost</b>  : ₹ {cost["base_cost"]} <br>
<b>Late Fee</b>    : ₹ {cost["late_fee"]}<br>
-------------------------<br>
<b>Total Cost</b>  : ₹ {cost["total_cost"]}<br>
            </div>

            <p>
            We sincerely appreciate your continued engagement with our library
            and look forward to accompanying you on many more literary pursuits.
            </p>

        <p>
            Thank You<br>
            Warm regards,<br>
            <b>Librarian</b><br>
            Central Library<br>
            {date2string(Today)}
        </p>
        <p><i>This is an auto-generated email. Please do not reply. Unintended inconvenience caused is deeply regretted.</i></p>
        </div>
        </body>
        </html>
        """

        send_email(
            email_receiver=issue["email"],
            subject="Book Returned Successfully – Invoice Enclosed",
            body=email_body,
            isHTML=True
        )

        st.success(f"Book returned successfully and confirmation email sent to {issue['email']}.")

# ISSUED BOOKS REPORT
elif menu == "Issued Books Report":

    st.subheader("Issued Books Report")

    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    
    # CURRENTLY ISSUED BOOKS

    cur.execute("""
        SELECT 
            ib.IssueCode,
            ib.issueDate,
            ib.dueDate,
            u.username,
            u.name AS user_name,
            b.ISBN,
            b.name AS book_name,
            b.author,
            b.language
        FROM issued_books ib
        JOIN users u ON ib.username = u.username
        JOIN books b ON ib.ISBN = b.ISBN
        WHERE ib.status = 'ISSUED'
        ORDER BY ib.issueDate DESC
    """)
    issued_books = cur.fetchall()

    st.markdown("### Currently Issued Books")
    if issued_books:
        st.dataframe(
            issued_books,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No books are currently issued.")

    # RETURNED BOOKS HISTORY
    cur.execute("""
        SELECT 
            ib.IssueCode,
            ib.issueDate,
            ib.dueDate,
            ib.returnDate,
            ib.accruedCost,
            ib.accruedFine,
            u.username,
            u.name AS user_name,
            b.ISBN,
            b.name AS book_name
        FROM issued_books ib
        JOIN users u ON ib.username = u.username
        JOIN books b ON ib.ISBN = b.ISBN
        WHERE ib.status = 'RETURNED'
        ORDER BY ib.returnDate DESC
    """)
    returned_books = cur.fetchall()

    st.markdown("### Returned Books History")
    if returned_books:
        st.dataframe(
            returned_books,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No returned book records found.")

    conn.close()


# VIEW BOOKS 
elif menu == "View Books":

    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM books ORDER BY name")
    data = cur.fetchall()
    conn.close()
    st.subheader(f"{num2words(len(data)).capitalize()} Books Available")
    st.dataframe(data)

elif menu == "View All Users":
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT username,name,email,phone,gender,dob,role FROM users WHERE role='user' ORDER BY name")

    users = cur.fetchall()
    conn.close()

    if not users:
        st.warning("No user accounts found.")
        

    st.subheader("All User Accounts")
    st.dataframe(
        users,
        use_container_width=True,
        hide_index=True
    )
# VIEW ALL REQUESTED BOOKS
elif menu == "View all Requested Books":
    st.subheader("All Book Requests")

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT r.requestID, r.username, r.ISBN, r.requestDate, u.name AS user_name, b.name AS book_name
        FROM requested_books r
        JOIN users u ON r.username = u.username
        JOIN books b ON r.ISBN = b.ISBN
        ORDER BY r.requestDate
    """)
    requests = cur.fetchall()

    conn.close()

    if not requests:
        st.info("No pending book requests found.")
    else:
        st.dataframe(
            requests,
            use_container_width=True,
            hide_index=True
        )

# DELETE USER
elif menu == "Delete User":
    st.subheader("Delete User Account")

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT username, name, email FROM users where role ='user' ORDER BY name")
    users = cur.fetchall()

    user_map = {
        f"{u['username']} — {u['name']}": u
        for u in users
    }

    user_choice = st.selectbox("Select User to Delete", list(user_map.keys()))
    user = user_map.get(user_choice)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT 1 FROM issued_books WHERE username=%s AND status='ISSUED'", (user["username"],))
    res = cur.fetchone()
    conn.close()
    if res is not None:
        st.error("This user has issued books and hence cannot be deleted.")
    if st.button("Delete User"):
        conn = get_connection()
        cur = conn.cursor()
        # Delete user account
        cur.execute("DELETE FROM users WHERE username=%s", (user["username"],))
        # Delete requested books history
        cur.execute("DELETE FROM requested_books WHERE username=%s",(user["username"],))
        # Delete returned book history
        cur.execute("DELETE FROM issued_books WHERE username=%s AND status='RETURNED'",(user["username"],))
        conn.commit()
        conn.close()

        st.success(f"User account `{user['username']}` deleted successfully.")

        send_email(
            user["email"],
            f"Thank You {user['name']} for Being a Valued Member of our Library",
            f"""
Dear {user['name']},

I trust this missive finds you in fine fettle. It is with a blend of melancholy and profound gratitude that we acknowledge your decision to part ways with our Library.

Your esteemed patronage has been a cornerstone of our literary community, and your departure leaves an indelible void. Your engagement and erudition have lent a rarefied air to our humble establishment, for which we are eternally grateful.
As you embark upon new odysseys, please be assured that the portals of our Library shall ever remain ajar to welcome your return. Your contributions have not only enriched our collection but have also invigorated the intellectual vigour of our fellowship.
Should you possess any observations or suggestions that might aid us in refining our services, we entreat you to impart them. Your perspicacity and discerning eye are of immeasurable value to us.

With heartfelt thanks and the very best of wishes for your future endeavors,

Warm regards,
Librarian
Central Library
{date2string(Today)}

This is an auto-generated email. Inconvenience caused is deeply regretted.
            """,
        )



# FILTER BOOKS
elif menu == "Filter Book":
    filterBooks()

# DASHBOARD 
elif menu == "Dashboard":

    st.subheader("Library Analytics Overview")

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # ---------- METRICS ----------
    cur.execute("SELECT COUNT(*) as total_books FROM books")
    total_books = cur.fetchone()["total_books"]

    cur.execute("SELECT SUM(quantity) as total_copies FROM books")
    total_copies = cur.fetchone()["total_copies"] or 0

    cur.execute("SELECT COUNT(*) as total_users FROM users WHERE role='user'")
    total_users = cur.fetchone()["total_users"]

    cur.execute("SELECT COUNT(*) as active_issues FROM issued_books WHERE status='ISSUED'")
    active_issues = cur.fetchone()["active_issues"]

    cur.execute("""
        SELECT COUNT(*) as overdue
        FROM issued_books
        WHERE status='ISSUED' AND dueDate < %s
    """, (Today,))
    overdue_books = cur.fetchone()["overdue"]

    # ---------- METRIC CARDS ----------
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total Titles", total_books)
    col2.metric("Total Copies", int(total_copies))
    col3.metric("Registered Users", total_users)
    col4.metric("Currently Issued", active_issues)
    col5.metric("Overdue Books", overdue_books)

    st.markdown("---")

    # ---------- LOW STOCK ALERT ----------
    cur.execute("""
        SELECT ISBN, Name, Quantity 
        FROM books
        WHERE quantity <= 5
        ORDER BY quantity
    """)
    low_stock = cur.fetchall()

    st.markdown("### Low Stock Books")
    if low_stock:
        st.dataframe(low_stock, use_container_width=True, hide_index=True)
    else:
        st.success("All books sufficiently stocked.")

    st.markdown("---")

    # ---------- ISSUE TREND (Last 7 Days) ----------
    cur.execute("""
        SELECT issueDate, COUNT(*) as count
        FROM issued_books
        WHERE issueDate >= %s
        GROUP BY issueDate
        ORDER BY issueDate
    """, (Today - timedelta(days=7),))

    issue_data = cur.fetchall()

    if issue_data:
        import pandas as pd
        df = pd.DataFrame(issue_data)
        df["issueDate"] = pd.to_datetime(df["issueDate"])

        st.markdown("### Issues in Last 7 Days")
        st.line_chart(df.set_index("issueDate"))
    else:
        st.info("No book issues in the last 7 days.")

    st.markdown("---")

    # ---------- TOP BORROWED BOOKS ----------
    cur.execute("""
        SELECT b.ISBN, b.Name, COUNT(*) as `Times Issued`
        FROM issued_books ib
        JOIN books b ON ib.ISBN = b.ISBN
        GROUP BY ib.ISBN
        ORDER BY `Times Issued` DESC
        LIMIT 5
    """)
    top_books = cur.fetchall()

    st.markdown("### Most Borrowed Books")
    if top_books:
        st.dataframe(top_books, use_container_width=True, hide_index=True)
    else:
        st.info("No borrowing history yet.")

    conn.close()

elif menu=="Broadcast Email to users":
    st.subheader("Broadcast Email System")

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Fetch users
    cur.execute("SELECT username, name, email FROM users WHERE role='user' ORDER BY name")
    users = cur.fetchall()
    conn.close()

    if not users:
        st.warning("No users found.")
        st.stop()

    user_map = {f"{u['name']} ({u['username']})": u for u in users}

    # ---------------- TARGET SELECTION ----------------
    st.markdown("### Select Recipients")

    send_to_all = st.checkbox("Send to All Users")

    selected_users = []

    if send_to_all:
        selected_users = users

        exclude = st.multiselect(
            "Deselect Specific Users",
            list(user_map.keys())
        )

        selected_users = [
            u for u in users
            if f"{u['name']} ({u['username']})" not in exclude
        ]

    else:
        selected = st.multiselect(
            "Select Users",
            list(user_map.keys())
        )
        selected_users = [user_map[s] for s in selected]

    st.info(f"Total Recipients: {len(selected_users)}")

    if not selected_users:
        st.stop()

    # ---------------- EMAIL FORMAT ----------------
    st.markdown("### Compose Message")

    subject = st.text_input("Email Subject")

    use_html = st.toggle("Send as HTML Email")

    default_template = f"""Dear {{name}},

We hope this message finds you well.

[Write your announcement here]

Warm regards,
Librarian
Central Library
{date2string(date.today())}
"""

    if not use_html:
        body = st.text_area(
            "Draft Email (Plain Text)",
            value=default_template,
            height=300
        )
    else:
        html_template = f"""
<html>
<body style="font-family:Georgia,serif; line-height:1.6;">
<p>Dear {{name}},</p>

<p>We hope this message finds you well.</p>

<p>[Write your announcement here]</p>

<br>
<p>
Warm regards,<br>
<b>Librarian</b><br>
Central Library<br>
{date2string(date.today())}
</p>
</body>
</html>
"""
        body = st.text_area(
            "Draft Email (HTML Mode)",
            value=html_template,
            height=400
        )

    # ---------------- PREVIEW ----------------
    st.markdown("### Preview (Sample User)")

    sample_user = selected_users[0]

    preview_content = body.replace("{name}", sample_user["name"])

    if use_html:
        wrapped_preview = f"""
        <div style="
            background-color: white;
            color: black;
            padding: 25px;
            border-radius: 8px;
            font-family: Georgia, 'Times New Roman', serif;
            min-height: 250px;
        ">
            {preview_content}
        </div>
        """
        
        st.components.v1.html(
            wrapped_preview,
            height=400,
            scrolling=True
        )

    else:
        st.code(preview_content)
    # ---------------- CONFIRMATION ----------------
    st.markdown("---")
    confirm = st.checkbox("I confirm this broadcast is correct.")

    if st.button("Send Broadcast"):
        if not confirm:
            st.error("Please confirm before sending.")
            st.stop()

        if not subject.strip():
            st.error("Subject cannot be empty.")
            st.stop()

        success_count = 0

        for user in selected_users:
            try:
                personalized_body = body.replace("{name}", user["name"])

                send_email(
                    email_receiver=user["email"],
                    subject=subject,
                    body=personalized_body,
                    isHTML=use_html
                )

                success_count += 1
            except Exception as e:
                st.error(f"Failed for {user['email']}: {e}")

        st.success(f"Broadcast sent successfully to {success_count} {'user' if success_count==1 else 'users'}.")
# LOGOUT 
elif menu == "Logout":
    st.session_state.clear()
    st.switch_page("main.py")
