import streamlit as st
from functions import *
import pandas as pd
def getBookDetails():
    st.subheader("Get Book Details by ISBN")
    isbn = getISBN("Select book to view details")

    if st.button("Fetch Book Details"):
        if not isbn or len(isbn) != 13 or not isbn.isdigit():
            st.error("Please enter a valid 13-digit ISBN.")
        else:
            conn = get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT * FROM books WHERE isbn = %s",
                (isbn,)
            )

            book = cur.fetchone()
            conn.close()
            if not book:
                st.error("Book not found.")
            else:
                # BOOK DETAILS 
                st.subheader("Book Details")
                st.markdown("---")

                language_display = nativeLang.get(book["language"], False)

                # TITLE 
                if book["language"].lower() == "english" or not book.get("native_name"):
                    # English book
                    st.markdown(
                        f"<h2 style='text-align:center;'>{book['name']}</h2>",
                        unsafe_allow_html=True
                    )
                else:
                    # Non-English book
                    st.markdown(
                        f"<h2 style='text-align:center;'>{book['name']}</h2>",
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        f"<p style='text-align:center; font-size:30px; color:gray;'>"
                        f"{book['native_name']}</p>",
                        unsafe_allow_html=True
                    )

                st.markdown(
                    f"<p style='text-align:center; font-size:14px;'>ISBN : {book['ISBN']}</p>",
                    unsafe_allow_html=True
                )

                st.markdown("---")

                # TWO COLUMN LAYOUT 
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### Bibliographic Info")
                    st.markdown(f"""
                    **Author** : {book['author']}  
                    **Language** : {book['language']} {'('+language_display+')' if language_display else ""}  
                    **Genre** : {book['genre']}  
                    **Publisher** : {book['publisher']}
                    """)

                with col2:
                    st.markdown("### Availability")

                    # COST 
                    st.markdown("#### Cost of the book")
                    st.metric(label="Cost", value=f"₹ {book['cost']:.2f}")
                    st.caption(cost2word(book["cost"]))

                    st.markdown("")  # spacing

                    # QUANTITY 
                    st.markdown("#### Quantity Available")
                    qty = book["quantity"]
                    st.metric(label=f"Available Books", value=f"{qty} {"book" if qty == 1 else "books"}")
                    st.caption(f"{num2words(qty).capitalize()} {"book" if qty == 1 else "books"} available")
                st.markdown("---")

def filterBooks():
    st.subheader("Filter Books")

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    parameters = ["Name", "Author", "Language", "Genre", "Publisher", "Cost", "Quantity"]
    choice = st.selectbox("Filter by", parameters)

    query = None
    values = None

    # NAME → TEXT SEARCH
    if choice == "Name":
        name = st.text_input("Enter book name (partial allowed)")
        if name:
            query = """
                SELECT * FROM books
                WHERE name LIKE %s
                ORDER BY name
            """
            values = (f"%{name}%",)
    # AUTHOR / LANGUAGE / GENRE / PUBLISHER
    elif choice in {"Author", "Language", "Genre", "Publisher"}:
        field = choice.lower()

        cur.execute(f"SELECT DISTINCT {field} FROM books ORDER BY {field}")
        options = [row[field] for row in cur.fetchall()]

        selected = st.selectbox(f"Select {choice}", options)

        query = f"""
            SELECT * FROM books
            WHERE {field} = %s
            ORDER BY name
        """
        values = (selected,)

    elif choice == "Cost":
        cur.execute("SELECT MIN(cost), MAX(cost) FROM books")
        min_cost, max_cost = cur.fetchone().values()

        cost_range = st.slider(
            "Select cost range (₹)",
            float(min_cost),
            float(max_cost),
            (float(min_cost), float(max_cost))
        )

        query = """
            SELECT * FROM books
            WHERE cost BETWEEN %s AND %s
            ORDER BY cost
        """
        values = cost_range

    # QUANTITY RANGE
    elif choice == "Quantity":
        cur.execute("SELECT MIN(quantity), MAX(quantity) FROM books")
        min_q, max_q = cur.fetchone().values()

        qty_range = st.slider(
            "Select quantity range",
            int(min_q),
            int(max_q),
            (int(min_q), int(max_q))
        )

        query = """
            SELECT * FROM books
            WHERE quantity BETWEEN %s AND %s
            ORDER BY quantity DESC
        """
        values = qty_range

    # EXECUTE QUERY
    if query and st.button("Apply Filter"):
        cur.execute(query, values)
        results = cur.fetchall()

        if results:
            st.success(f"{len(results)} {('book' if len(results) == 1 else 'books')} found")
            st.dataframe(results, use_container_width=True, hide_index=True)
        else:
            st.warning("No books match the selected criterion.")

    conn.close()

