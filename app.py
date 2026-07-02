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

# --- NEW: FORM TO POST A DEAL ---
st.markdown("---")
with st.expander("➕ Post a New Deal on the Hub", expanded=False):
    st.markdown("#### Enter your product details below:")
    
    # Form input fields matching your Supabase columns
    new_title = st.text_input("Product Title", placeholder="e.g., iPhone 13 Pro Max")
    new_price = st.number_input("Price (₹)", min_value=0, step=1, value=0)
    new_desc = st.text_area("Product Description", placeholder="Mention item condition, age, inclusions...")
    
    submit_button = st.button("🚀 Publish Listing")
    
    if submit_button:
        if not new_title or not new_desc:
            st.warning("⚠️ Please fill out both the Title and Description before publishing.")
        elif new_price <= 0:
            st.warning("⚠️ Please enter a price greater than 0.")
        else:
            # Connect to database and save the listing
            conn = get_db_connection()
            cur = conn.cursor()
            try:
                cur.execute(
                    "INSERT INTO items (title, description, price) VALUES (%s, %s, %s);",
                    (new_title, new_desc, new_price)
                )
                conn.commit() # Save changes permanently
                st.success("🎉 Listing uploaded successfully!")
                st.rerun()    # Refresh page to show the item instantly
            except Exception as e:
                st.error(f"❌ Failed to post item to database: {e}")
            finally:
                cur.close()
                conn.close()

st.markdown("### 🛍️ Available Active Listings")

# --- FETCH AND DISPLAY ITEMS ---
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
                        <h3 style="margin-top:0;">📦 {item['title']}</h3>
                        <p style="font-size: 1.2em; color: #ffeb3b;"><b>Price:</b> ₹{item['price']}</p>
                        <p><b>Description:</b> {item['description']}</p>
                        <p style="color: #00ff00; margin-bottom:0;"><b>📍 Location:</b> Local Area</p>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
except Exception as e:
    st.error(f"⚠️ Error running query: {e}")
finally:
    cur.close()
    conn.close()
