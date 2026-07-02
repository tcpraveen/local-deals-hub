import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import urllib.parse

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

# --- FEATURE 1: ALL-IN-ONE UPGRADED POSTING FORM ---
st.markdown("---")
with st.expander("➕ Post a New Deal on the Hub", expanded=False):
    st.markdown("#### Enter your product and contact details:")
    
    # Grid for organized input form
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        new_title = st.text_input("Product Title", placeholder="e.g., iPhone 13 Pro Max")
        new_price = st.number_input("Price (₹)", min_value=0, step=1, value=0)
    with f_col2:
        # Category Dropdown selection
        new_cat = st.selectbox("Category", ["Electronics", "Vehicles", "Books", "Clothing & Fashion", "Household", "Others"])
        # WhatsApp Contact details
        new_phone = st.text_input("WhatsApp Number (with country code)", placeholder="e.g., 919876543210")
        
    new_desc = st.text_area("Product Description", placeholder="Mention item condition, age, inclusions...")
    
    submit_button = st.button("🚀 Publish Listing")
    
    if submit_button:
        if not new_title or not new_desc or not new_phone:
            st.warning("⚠️ Please fill out the Title, Description, and WhatsApp Number.")
        elif new_price <= 0:
            st.warning("⚠️ Please enter a price greater than 0.")
        else:
            conn = get_db_connection()
            cur = conn.cursor()
            try:
                # Inserting all fields into the updated database structure
                cur.execute(
                    "INSERT INTO items (title, description, price, category, phone) VALUES (%s, %s, %s, %s, %s);",
                    (new_title, new_desc, new_price, new_cat, new_phone)
                )
                conn.commit()
                st.success("🎉 Listing uploaded successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to post item to database: {e}")
            finally:
                cur.close()
                conn.close()

# --- FEATURE 2: SEARCH & FILTER SYSTEM ---
st.markdown("### 🔍 Search & Filter Deals")
search_col, filter_col = st.columns([2, 1])

with search_col:
    search_query = st.text_input("Search listings by keywords...", placeholder="Type here to search (e.g., MacBook, iPhone)...").strip().lower()

with filter_col:
    category_filter = st.selectbox("Filter by Category", ["All Categories", "Electronics", "Vehicles", "Books", "Clothing & Fashion", "Household", "Others"])

st.markdown("---")
st.markdown("### 🛍️ Available Active Listings")

# --- FETCH AND RENDER LOGIC ---
conn = get_db_connection()
cur = conn.cursor()

try:
    cur.execute("SELECT * FROM items ORDER BY id DESC;")
    items = cur.fetchall()
    
    # Client-side filtering logic based on user inputs
    filtered_items = []
    for item in items:
        title_match = search_query in item['title'].lower() if item.get('title') else False
        desc_match = search_query in item['description'].lower() if item.get('description') else False
        
        # Check category constraint
        item_cat = item.get('category', 'Others')
        category_match = (category_filter == "All Categories") or (item_cat == category_filter)
        
        if (title_match or desc_match) and category_match:
            filtered_items.append(item)

    if not filtered_items:
        st.info("🛍️ No matching active listings available right now. Try adjusting your filters!")
    else:
        # Create a beautiful responsive 3-column grid layout
        cols = st.columns(3)
        for idx, item in enumerate(filtered_items):
            col = cols[idx % 3]
            with col:
                # Generate clean WhatsApp API click-to-chat links
                raw_phone = item.get('phone', '').strip()
                encoded_msg = urllib.parse.quote(f"Hi! I'm interested in buying your listed item: {item['title']} for ₹{item['price']}. Is it still available?")
                wa_link = f"https://wa.me/{raw_phone}?text={encoded_msg}" if raw_phone else "#"
                
                # HTML template card with custom category badge and bright contact button
                st.markdown(
                    f"""
                    <div style="border: 2px solid #fff; padding: 15px; border-radius: 8px; margin-bottom: 25px; background-color: #111; display: flex; flex-direction: column; justify-content: space-between;">
                        <div>
                            <span style="background-color: #2e7d32; color: white; padding: 3px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold;">🏷️ {item.get('category', 'General')}</span>
                            <h3 style="margin-top: 10px; margin-bottom: 5px;">📦 {item['title']}</h3>
                            <p style="font-size: 1.3em; color: #ffeb3b; margin: 5px 0;"><b>Price:</b> ₹{item['price']}</p>
                            <p style="color: #ddd; font-size: 0.95em;">{item['description']}</p>
                        </div>
                        <div style="margin-top: 15px;">
                            <hr style="border-color: #333; margin-bottom: 15px;">
                            <a href="{wa_link}" target="_blank" style="text-decoration: none;">
                                <div style="background-color: #25D366; color: black; text-align: center; padding: 10px; border-radius: 5px; font-weight: bold; font-size: 1em; cursor: pointer;">
                                    💬 Contact via WhatsApp
                                </div>
                            </a>
                        </div>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
except Exception as e:
    st.error(f"⚠️ Error running query: {e}")
finally:
    cur.close()
    conn.close()
