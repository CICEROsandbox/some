import streamlit as st
import streamlit_authenticator as stauth
from modules.bluesky_api import get_posts, schedule_reposts

# Load credentials and config from secrets
names = [st.secrets["auth"]["name"]]
usernames = [st.secrets["auth"]["username"]]
hashed_passwords = [st.secrets["auth"]["password_hash"]]
cookie_name = st.secrets["cookie"]["name"]
cookie_key = st.secrets["cookie"]["key"]

# Set up the authenticator
authenticator = stauth.Authenticate(
    names, usernames, hashed_passwords,
    cookie_name, cookie_key, cookie_expiry_days=30
)

def main():
    st.title("Bluesky Repost Scheduler")
    
    name, authentication_status, username = authenticator.login('Login', 'main')

    if authentication_status:
        authenticator.logout('Logout', 'sidebar')
        st.sidebar.write(f'Welcome *{name}*')
        display_posts()
    elif authentication_status == False:
        st.error('Username/password is incorrect')
    elif authentication_status == None:
        st.warning('Please enter your username and password')

def display_posts():
    api_key = st.secrets["bluesky"]["api_key"]
    posts = get_posts(api_key)
    selected_posts = []
    for post in posts:
        if st.checkbox(f"{post['author']}: {post['content']}", key=post['id']):
            selected_posts.append(post)
    if st.button("Schedule Reposts"):
        schedule_reposts(selected_posts, api_key)
        st.success("Reposts scheduled successfully!")

if __name__ == "__main__":
    main()
