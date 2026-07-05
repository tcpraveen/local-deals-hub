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

# Custom styling adjustments
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; }
    div[data-testid="stExpander"] { border: 1px solid #333; border-radius: 8px; background-color: #0e1117; }
    </style>
""", unsafe_allow_html=True)

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

# --- APPLICATION INTERFACE ---
st.title("⚡ Neighborhood Deals Hub")
st.caption("Your Local High-Contrast Marketplace Dashboard")

# --- FETCH DATA FIRST FOR METRICS ---
conn = get_db_connection()
cur = conn.cursor()
items = []
try:
    cur.execute("SELECT * FROM items ORDER BY id DESC;")
    items = cur.fetchall()
except Exception as e:
    st.error(f"⚠️ Error reading initial database: {e}")
finally:
    cur.close()
    conn.close()

# --- PROTOTYPE FEATURE: LIVE BUSINESS METRICS BAR ---
st.markdown("### 📊 Hub Statistics")
total_items = len(items)
total_value = sum(float(item['price']) for item in items if item.get('price'))

m_col1, m_col2, m_col3 = st.columns(3)
with m_col1:
    st.metric(label="Total Active Listings", value=f"{total_items} Items")
with m_col2:
    st.metric(label="Total Marketplace Circulation", value=f"₹{total_value:,.2f}")
with m_col3:
    st.metric(label="Active Community Hubs", value="1 (Local Area)")

st.markdown("---")

# --- EXPANDABLE POSTING FORM ---
with st.expander("➕ Post a New Deal on the Hub", expanded=False):
    st.markdown("### 📝 Enter Product Details")
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        new_title = st.text_input("Product Title", placeholder="e.g., iPhone 13 Pro Max")
        new_price = st.number_input("Price (₹)", min_value=0, step=100, value=0)
    with f_col2:
        new_cat = st.selectbox("Category", ["Electronics", "Vehicles", "Books", "Clothing & Fashion", "Household", "Others"])
        new_phone = st.text_input("WhatsApp Number (Optional)", placeholder="e.g., 919876543210")
        
    new_desc = st.text_area("Product Description", placeholder="Mention item condition, age, inclusions...")
    
    # PROTOTYPE FEATURE: PREMIUM SELLER MARKER
    st.markdown("##### 🌟 Promotion Options")
    is_premium = st.checkbox("Mark as ⭐ URGENT / FEATURED deal (Highlights your listing)")
    
    if st.button("🚀 Publish Listing", use_container_width=True):
        if not new_title or not new_desc:
            st.warning("⚠️ Please fill out both the Title and Description.")
        elif new_price <= 0:
            st.warning("⚠️ Please enter a valid price.")
        else:
            # We add the prefix [URGENT] to the description dynamically if checked so it requires no DB modifications!
            final_desc = f"🚨 [URGENT DEAL] {new_desc}" if is_premium else new_desc
            
            conn = get_db_connection()
            cur = conn.cursor()
            try:
                try:
                    cur.execute(
                        "INSERT INTO items (title, description, price, category, phone) VALUES (%s, %s, %s, %s, %s);",
                        (new_title, final_desc, new_price, new_cat, new_phone)
                    )
                except:
                    conn.rollback()
                    cur.execute(
                        "INSERT INTO items (title, description, price) VALUES (%s, %s, %s);",
                        (new_title, final_desc, new_price)
                    )
                conn.commit()
                st.success("🎉 Listing uploaded successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to save to database: {e}")
            finally:
                cur.close()
                conn.close()

# --- SEARCH & FILTER SYSTEM ---
st.markdown("### 🔍 Search & Filter Deals")
search_col, filter_col = st.columns([2, 1])

with search_col:
    search_query = st.text_input("Search listings...", placeholder="Type keywords here (e.g., MacBook, Poco)...").strip().lower()

with filter_col:
    category_filter = st.selectbox("Filter by Category", ["All Categories", "Electronics", "Vehicles", "Books", "Clothing & Fashion", "Household", "Others"])

st.markdown("### 🛍️ Available Active Listings")

# --- RENDER LOGIC WITH PREMIUM UI BORDERS ---
filtered_items = []
for item in items:
    title_match = search_query in item['title'].lower() if item.get('title') else False
    desc_match = search_query in item['description'].lower() if item.get('description') else False
    
    item_cat = item.get('category') if item.get('category') else "Others"
    category_match = (category_filter == "All Categories") or (item_cat == category_filter)
    
    if (title_match or desc_match) and category_match:
        filtered_items.append(item)

if not filtered_items:
    st.info("🛍️ No matching listings found. Try adjusting your filters!")
else:
    cols = st.columns(3)
    for idx, item in enumerate(filtered_items):
        col = cols[idx % 3]
        with col:
            # Check if this was marked as an urgent item
            is_urgent = "[URGENT DEAL]" in item['description']
            clean_desc = item['description'].replace("🚨 [URGENT DEAL] ", "")
            
            # Use Streamlit containers with dynamic custom colors for premium items
            with st.container(border=True):
                item_cat = item.get('category') if item.get('category') else "General"
                
                # Render Tag Bar
                if is_urgent:
                    st.markdown("🔥 **URGENT LISTING**")
                st.caption(f"🏷️ {item_cat}")
                
                # Title & Price
                st.markdown(f"### {item['title']}")
                st.markdown(f"#### **Price:** ₹{item['price']}")
                st.write(clean_desc)
                
                st.markdown("---")
                
                # Communication actions
                raw_phone = item.get('phone')
                if raw_phone and str(raw_phone).strip() and str(raw_phone) != "None":
                    encoded_msg = urllib.parse.quote(f"Hi, I am interested in buying your '{item['title']}' listed on the Deals Hub!")
                    st.link_button("💬 Chat on WhatsApp", f"https://wa.me/{str(raw_phone).strip()}?text={encoded_msg}", use_container_width=True)
                else:
                    st.button("📍 Available Locally", disabled=True, use_container_width=True)
