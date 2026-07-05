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

# DEFAULT AUTH PASSWORD
SHOPKEEPER_PASSWORD = "shop123"

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

# --- FETCH ALL DATA ---
conn = get_db_connection()
cur = conn.cursor()
items = []
try:
    cur.execute("SELECT * FROM items ORDER BY id DESC;")
    items = cur.fetchall()
except Exception as e:
    st.error(f"⚠️ Error reading database: {e}")
finally:
    cur.close()
    conn.close()

# --- APPLICATION INTERFACE ---
st.title("⚡ Neighborhood Deals Hub")
st.caption("Your Local High-Contrast Marketplace Dashboard")

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

# --- PASSWORD PROTECTED POSTING FORM ---
with st.expander("➕ Shopkeeper Menu: Post a New Deal", expanded=False):
    st.markdown("### 📝 Enter Product Details")
    
    form_password = st.text_input("🔑 Enter Shopkeeper Password to Post", type="password")
    
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        new_title = st.text_input("Product Title", placeholder="e.g., iPhone 13 Pro Max")
        new_price = st.number_input("Price (₹)", min_value=0, step=100, value=0)
    with f_col2:
        new_cat = st.selectbox("Category", ["Electronics", "Vehicles", "Books", "Clothing & Fashion", "Household", "Others"])
        new_phone = st.text_input("WhatsApp Number", placeholder="e.g., 919876543210")
        
    new_desc = st.text_area("Product Description", placeholder="Mention item condition, age, inclusions...")
    
    st.markdown("##### 💳 E-Commerce Integrations")
    custom_pay_url = st.text_input("🔗 Razorpay/Stripe Payment Link (Optional)", placeholder="e.g., https://rzp.io/l/your_product_link")
    
    is_premium = st.checkbox("Mark as ⭐ URGENT / FEATURED deal")
    
    if st.button("🚀 Publish Listing", use_container_width=True):
        if form_password != SHOPKEEPER_PASSWORD:
            st.error("❌ Incorrect Shopkeeper Password! Access Denied.")
        elif not new_title or not new_desc:
            st.warning("⚠️ Please fill out both the Title and Description.")
        elif new_price <= 0:
            st.warning("⚠️ Please enter a valid price.")
        else:
            final_desc = new_desc
            if is_premium:
                final_desc = f"🚨 [URGENT DEAL] {final_desc}"
            if custom_pay_url:
                final_desc = f"{final_desc} |PAY_URL:{custom_pay_url.strip()}|"
                
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
st.markdown("---")
st.markdown("### 🔍 Search & Filter Deals")
search_col, filter_col = st.columns([2, 1])

with search_col:
    search_query = st.text_input("Search listings...", placeholder="Type keywords here...").strip().lower()

with filter_col:
    category_filter = st.selectbox("Filter by Category", ["All Categories", "Electronics", "Vehicles", "Books", "Clothing & Fashion", "Household", "Others"])

st.markdown("### 🛍️ Available Active Listings")

# --- RENDER LOGIC ---
filtered_items = []
for item in items:
    title_match = search_query in item['title'].lower() if item.get('title') else False
    desc_match = search_query in item['description'].lower() if item.get('description') else False
    
    item_cat = item.get('category') if item.get('category') else "Others"
    category_match = (category_filter == "All Categories") or (item_cat == category_filter)
    
    if (title_match or desc_match) and category_match:
        filtered_items.append(item)

if not filtered_items:
    st.info("🛍️ No matching listings found.")
else:
    cols = st.columns(3)
    for idx, item in enumerate(filtered_items):
        col = cols[idx % 3]
        with col:
            raw_desc = item['description']
            is_urgent = "[URGENT DEAL]" in raw_desc
            
            pay_url = ""
            if "|PAY_URL:" in raw_desc:
                parts = raw_desc.split("|PAY_URL:")
                clean_desc = parts[0].replace("🚨 [URGENT DEAL] ", "")
                pay_url = parts[1].replace("|", "").strip()
            else:
                clean_desc = raw_desc.replace("🚨 [URGENT DEAL] ", "")
            
            with st.container(border=True):
                item_cat = item.get('category') if item.get('category') else "General"
                if is_urgent:
                    st.markdown("🔥 **URGENT LISTING**")
                st.caption(f"🏷️ {item_cat}")
                st.markdown(f"### {item['title']}")
                st.markdown(f"#### **Price:** ₹{item['price']}")
                st.write(clean_desc)
                st.markdown("---")
                
                # --- FIXED: Added unique key strings to avoid element conflicts ---
                if pay_url:
                    st.link_button("💳 Instant Booking / Pay Now", pay_url, use_container_width=True, type="primary", key=f"pay_btn_{item['id']}")
                
                raw_phone = item.get('phone')
                if raw_phone and str(raw_phone).strip() and str(raw_phone) != "None":
                    encoded_msg = urllib.parse.quote(f"Hi, I am interested in buying your '{item['title']}'!")
                    st.link_button("💬 Chat on WhatsApp", f"https://wa.me/{str(raw_phone).strip()}?text={encoded_msg}", use_container_width=True, key=f"wa_btn_{item['id']}")
                elif not pay_url:
                    st.button("📍 Available Locally", disabled=True, use_container_width=True, key=f"local_btn_{item['id']}")

# --- PASSWORD PROTECTED DELETE SYSTEM ---
st.markdown("---")
with st.expander("🗑️ Shopkeeper Menu: Remove Listings", expanded=False):
    st.markdown("### 🔐 Inventory Controls")
    delete_password = st.text_input("🔑 Enter Shopkeeper Password to Enable Deletion", type="password")
    
    if delete_password == SHOPKEEPER_PASSWORD:
        if not items:
            st.info("No items in inventory to delete.")
        else:
            st.warning("Clicking a red delete button below will remove the product permanently from the app.")
            for row in items:
                del_col1, del_col2 = st.columns([4, 1])
                with del_col1:
                    st.write(f"📦 **{row['title']}** — ₹{row['price']} (ID: {row['id']})")
                with del_col2:
                    if st.button(f"🗑️ Delete", key=f"del_{row['id']}", type="primary", use_container_width=True):
                        conn = get_db_connection()
                        cur = conn.cursor()
                        try:
                            cur.execute("DELETE FROM items WHERE id = %s;", (row['id'],))
                            conn.commit()
                            st.success(f"Removed listing successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error executing deletion: {e}")
                        finally:
                            cur.close()
                            conn.close()
    elif delete_password != "":
        st.error("❌ Incorrect Password!")
