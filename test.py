from functions import *
import streamlit as st
conn = get_connection()
cur = conn.cursor(dictionary=True)
isbn = '9874125202363'#input("13-digit ISBN of the book whose details you wish to find: ")
    
cur.execute(
    "SELECT * FROM books WHERE isbn = %s",
    (isbn,)
)

book = cur.fetchone()
conn.close()
print(book)