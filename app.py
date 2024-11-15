# app.py

import streamlit as st
from modules.bluesky_api import get_posts, schedule_reposts

api_key = st.secrets["bluesky"]["api_key"]
username = st.secrets["auth"]["username"]
password = st.secrets["auth"]["password"]

def main():
    st.title("Bluesky Repost Scheduler")
    
    # Authentication
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    if not st.session_state['authenticated']:
        login()
    else:
        display_posts()

def login():
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == st.secrets["auth"]["username"] and password == st.secrets["auth"]["password"]:
            st.session_state['authenticated'] = True
            st.experimental_rerun()
        else:
            st.error("Incorrect username or password")

def display_posts():
    posts = get_posts()
    selected_posts = []
    for post in posts:
        if st.checkbox(f"{post['author']}: {post['content']}", key=post['id']):
            selected_posts.append(post)
    if st.button("Schedule Reposts"):
        schedule_reposts(selected_posts)
        st.success("Reposts scheduled successfully!")

if __name__ == "__main__":
    main()
