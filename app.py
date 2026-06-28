import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import os

# --- PRODUCTION PLATFORM CONFIGURATION ---
st.set_page_config(
    page_title="Neighborhood Deals Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- DIRECT DATABASE CONFIGURATION FOR RENDER ---
db_url_raw = os.getenv("db_url")
# This line automatically deletes any accidental hidden spaces or line breaks
db_link = db_url_raw.strip() if db_url_raw else None

if not db_link:
    st.error("🔑 Database Secret Missing! Please configure 'db_url' environment variable inside your Render dashboard.")
    st.stop()

# --- DATABASE CONNECTION FUNCTION ---
def get_db_connection():
    try:
        conn = psycopg2.connect(db_link, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        st.error(f"❌ Server Connection Error: {e}")
        st.stop()

# --- APPLICATION INTERFACE & LOGIC ---
st.title("⚡ Neighborhood Deals Hub")
st.subheader("Your Local High-Contrast Marketplace Dashboard")

# Fetch and display items from database
conn = get_db_connection()
cur = conn.cursor()

try:
    cur.execute("SELECT * FROM items ORDER BY id DESC;")
    items = cur.fetchall()
    
    if not items:
        st.info("🛍️ No active listings available right now. Check back soon!")
    else:
        # Create a grid layout for marketplace items
        cols = st.columns(3)
        for idx, item in enumerate(items):
            col = cols[idx % 3]
            with col:
                st.markdown(
                    f"""
                    <div style="border: 2px solid #fff; padding: 15px; border-radius: 8px; margin-bottom: 15px; background-color: #111;">
                        <h3>📦 {item['title']}</h3>
                        <p><b>Price:</b> ₹{item['price']}</p>
                        <p><b>Description:</b> {item['description']}</p>
                        <p style="color: #00ff00;"><b>📍 Location:</b> {item.get('location', 'Local Area')}</p>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
except Exception as e:
    st.error(f"⚠️ Error running query: {e}")
finally:
    cur.close()
    conn.close()
