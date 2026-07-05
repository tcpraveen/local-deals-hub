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

# FIXED AUTH PASSWORDS FOR SECURITY
SHOPKEEPER_PASSWORD = "shop123"
TRUSTED_VENDOR_KEY = "trust789"

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
st.caption("Your Local High-Contrast Trusted Marketplace Dashboard")

# --- PROTOTYPE FEATURE: LIVE BUSINESS METRICS BAR ---
st.markdown("### 📊 Hub Statistics")
total_items = len(items)
max_item_price = max([float(item['price']) for item in items if item.get('price')], default=100000.0)
total_value = sum(float(item['price']) for item in items if item.get('price'))

m_col1, m_col2, m_col3 = st.columns(3)
with m_col1:
    st.metric(label="Total Active Listings", value=f"{total_items} Items")
with m_col2:
    st.metric(label="Total Marketplace Circulation", value=f"₹{total_value:,.2f}")
with m_col3:
    st.metric(label="Active Verified Partners", value="Trusted Local Shops")

st.markdown("---")

# --- EXPANDED POSTING FORM WITH PHOTO INTEGRATION ---
with st.expander("➕ Shopkeeper Menu: Post a New Deal", expanded=False):
    st.markdown("### 📝 Enter Product Details")
    
    form_password = st.text_input("🔑 Enter Shopkeeper Password to Post", type="password")
    vendor_key = st.text_input("⭐ Enter Trusted Vendor Verification Key (Optional)", type="password")
    
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        new_title = st.text_input("Product Title", placeholder="e.g., iPhone 13 Pro Max")
        new_price = st.number_input("Price (₹)", min_value=0, step=100, value=0)
    with f_col2:
        new_cat = st.selectbox("Category", ["Electronics", "Vehicles", "Books", "Clothing & Fashion", "Household", "Others"])
        new_phone = st.text_input("WhatsApp Number", placeholder="e.g., 919876543210")
        
    new_desc = st.text_area("Product Description", placeholder="Mention item condition, age, inclusions...")
    
    # NEW UPGRADE: Photo link input field
    st.markdown("##### 🖼️ Visuals & E-Commerce")
    new_photo = st.text_input("🔗 Product Image URL (Optional)", placeholder="Paste an image link from web (e.g., https://images.unsplash.com/...)")
    custom_pay_url = st.text_input("🔗 Secure Booking Link (Optional)", placeholder="e.g., https://rzp.io/l/...")
    
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
            # Embed image URL cleanly inside description to ensure database compatibility
            if new_photo:
                final_desc = f"{final_desc} |IMG_URL:{new_photo.strip()}|"
            
            final_cat = f"{new_cat} |VERIFIED|" if vendor_key == TRUSTED_VENDOR_KEY else new_cat
                
            conn = get_db_connection()
            cur = conn.cursor()
            try:
                try:
                    cur.execute(
                        "INSERT INTO items (title, description, price, category, phone) VALUES (%s, %s, %s, %s, %s);",
                        (new_title, final_desc, new_price, final_cat, new_phone)
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

# --- SEARCH & FILTER SYSTEM WITH SLIDER ---
st.markdown("---")
st.markdown("### 🔍 Filter Controls")
search_col, filter_col, price_col = st.columns([2, 1, 1])

with search_col:
    search_query = st.text_input("Search listings...", placeholder="Type keywords here...").strip().lower()

with filter_col:
    category_filter = st.selectbox("Filter by Category", ["All Categories", "Electronics", "Vehicles", "Books", "Clothing & Fashion", "Household", "Others"])

with price_col:
    # UPGRADE: Dynamic Price Slider based on current inventory max value
    max_slider_value = max(max_item_price, 500.0)
    price_filter = st.slider("Max Budget (₹)", min_value=0.0, max_value=max_slider_value, value=max_slider_value, step=500.0)

st.markdown("### 🛍️ Available Active Listings")

# --- RENDER LOGIC ---
filtered_items = []
for item in items:
    title_match = search_query in item['title'].lower() if item.get('title') else False
    desc_match = search_query in item['description'].lower() if item.get('description') else False
    
    raw_cat = item.get('category')
    clean_cat = str(raw_cat).split(" |VERIFIED|")[0] if raw_cat else "Others"
    category_match = (category_filter == "All Categories") or (clean_cat == category_filter)
    
    # Filter out items that cost more than user's slider setting
    item_price = float(item['price']) if item.get('price') else 0.0
    price_match = item_price <= price_filter
    
    if (title_match or desc_match) and category_match and price_match:
        filtered_items.append(item)

if not filtered_items:
    st.info("🛍️ No listings match your filters or budget range.")
else:
    cols = st.columns(3)
    for idx, item in enumerate(filtered_items):
        col = cols[idx % 3]
        with col:
            raw_desc = item['description'] if item.get('description') else ""
            is_urgent = "[URGENT DEAL]" in raw_desc
            
            # Safe URL parsing strings logic
            pay_url = ""
            if "|PAY_URL:" in raw_desc:
                pay_url = raw_desc.split("|PAY_URL:")[1].split("|")[0].strip()
                
            img_url = ""
            if "|IMG_URL:" in raw_desc:
                img_url = raw_desc.split("|IMG_URL:")[1].split("|")[0].strip()
            
            # Clean text block description for output window display
            clean_desc = raw_desc.replace("🚨 [URGENT DEAL] ", "")
            if "|PAY_URL:" in clean_desc:
                clean_desc = clean_desc.split("|PAY_URL:")[0]
            if "|IMG_URL:" in clean_desc:
                clean_desc = clean_desc.split("|IMG_URL:")[0]
            
            raw_cat = item.get('category')
            raw_cat_str = str(raw_cat) if raw_cat is not None else "General"
            is_verified = " |VERIFIED|" in raw_cat_str
            display_cat = raw_cat_str.replace(" |VERIFIED|", "")
            
            with st.container(border=True):
                t_col1, t_col2 = st.columns([1, 1])
                with t_col1:
                    st.caption(f"🏷️ {display_cat}")
                with t_col2:
                    if is_verified:
                        st.markdown("<span style='color: #00ff00; font-weight: bold;'>🛡️ VERIFIED</span>", unsafe_allow_html=True)
                    else:
                        st.caption("👤 Peer Listing")
                
                # Dynamic Image rendering fallback element
                if img_url:
                    st.image(img_url, use_container_width=True)
                else:
                    st.markdown("<div style='background-color:#222;height:120px;border-radius:5px;display:flex;align-items:center;justify-content:center;color:#666;'>📷 No Image Provided</div>", unsafe_allow_html=True)
                        
                if is_urgent:
                    st.markdown("🔥 **URGENT LISTING**")
                st.markdown(f"### {item['title']}")
                st.markdown(f"#### **Price:** ₹{item['price']}")
                st.write(clean_desc)
                
                report_msg = urllib.parse.quote(f"REPORT: Listing ID {item['id']} is flagged.")
                st.markdown(f"<a href='https://wa.me/919876543210?text={report_msg}' style='color: #ff4b4b; font-size: 0.85em; text-decoration: none;'>⚠️ Report Damaged/Fake</a>", unsafe_allow_html=True)
                st.markdown("---")
                
                if pay_url:
                    st.link_button("💳 Secure Booking / Pay Now", pay_url, use_container_width=True, type="primary", key=f"pay_btn_{item['id']}")
                
                raw_phone = item.get('phone')
                if raw_phone and str(raw_phone).strip() and str(raw_phone) != "None":
                    encoded_msg = urllib.parse.quote(f"Hi, I am interested in checking out your '{item['title']}'!")
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
            st.warning("Clicking a red delete button below will remove the product permanently.")
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
