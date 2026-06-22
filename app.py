import streamlit as st
import sqlite3
from datetime import time

# --- HIGH END INFRASTRUCTURE CONFIG ---
st.set_page_config(
    page_title="Neighborhood Deals Hub", 
    page_icon="🛍️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DATABASE INTEGRATION ---
conn = sqlite3.connect("deals_v5.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop TEXT,
    category TEXT,
    offer TEXT,
    location TEXT,
    end_time TEXT,
    total_stock INTEGER,
    remaining_stock INTEGER,
    upi_id TEXT,
    pin TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    offer_id INTEGER,
    customer_name TEXT,
    customer_phone TEXT,
    quantity INTEGER,
    txn_id TEXT
)
""")
conn.commit()

# --- BACKEND LOGIC FILTERS ---
def get_offers_by_category(category, search_query=""):
    if search_query:
        cursor.execute("""
            SELECT id, shop, category, offer, location, end_time, total_stock, remaining_stock, upi_id 
            FROM offers 
            WHERE category = ? AND remaining_stock > 0 
            AND (LOWER(shop) LIKE ? OR LOWER(offer) LIKE ? OR LOWER(location) LIKE ?)
            ORDER BY id DESC
        """, (category, f"%{search_query.lower()}%", f"%{search_query.lower()}%", f"%{search_query.lower()}%"))
    else:
        cursor.execute("SELECT id, shop, category, offer, location, end_time, total_stock, remaining_stock, upi_id FROM offers WHERE category = ? AND remaining_stock > 0 ORDER BY id DESC", (category,))
    
    rows = cursor.fetchall()
    return [{"id": row[0], "shop": row[1], "category": row[2], "offer": row[3], "location": row[4], "end_time": row[5], "total_stock": row[6], "remaining_stock": row[7], "upi_id": row[8]} for row in rows]

def get_owner_offers(shop_name, pin):
    cursor.execute("SELECT id, shop, category, offer, total_stock, remaining_stock FROM offers WHERE LOWER(shop) = ? AND pin = ? ORDER BY id DESC", (shop_name.lower().strip(), pin.strip()))
    rows = cursor.fetchall()
    return [{"id": row[0], "shop": row[1], "category": row[2], "offer": row[3], "total_stock": row[4], "remaining_stock": row[5]} for row in rows]

def get_bookings_for_offer(offer_id):
    cursor.execute("SELECT customer_name, customer_phone, quantity, txn_id FROM bookings WHERE offer_id = ?", (offer_id,))
    return cursor.fetchall()

def process_booking(offer_id, name, phone, qty, txn, current_remaining):
    new_remaining = current_remaining - qty
    cursor.execute("UPDATE offers SET remaining_stock = ? WHERE id = ?", (new_remaining, offer_id))
    cursor.execute("INSERT INTO bookings (offer_id, customer_name, customer_phone, quantity, txn_id) VALUES (?, ?, ?, ?, ?)", (offer_id, name, phone, qty, txn))
    conn.commit()

def delete_offer(offer_id):
    cursor.execute("DELETE FROM offers WHERE id = ?", (offer_id,))
    cursor.execute("DELETE FROM bookings WHERE offer_id = ?", (offer_id,))
    conn.commit()

# --- ANIMATED WELCOME BANNER INTERFACE ---
st.markdown("# 🛍️ Neighborhood Deals Hub")
st.markdown("### *Instantly claim flash surplus stock discounts or clear warehouse inventory nearby!*")

# Animated welcome popups for instant visual appeal
st.toast("👋 Welcome to the Hub! Live marketplace active.", icon="🚀")

# Visual Metrics Dashboard Layout
st.markdown("### 📊 Live Network Activity Counter")
col_metric1, col_metric2 = st.columns(2)
with col_metric1:
    st.metric(label="🏪 Verified Active Retail Partners", value=cursor.execute("SELECT COUNT(DISTINCT shop) FROM offers").fetchone()[0], delta="Live Active", delta_color="normal")
with col_metric2:
    st.metric(label="⚡ Active Flash Inventory Offers", value=cursor.execute("SELECT COUNT(*) FROM offers WHERE remaining_stock > 0").fetchone()[0], delta="Available", delta_color="inverse")
st.markdown("---")

# Sidebar: Perfectly structured Upload Interface
with st.sidebar:
    st.markdown("## 📢 Post a New Flash Deal")
    st.write("Stream a targeted discount asset matrix straight to nearby buyers instantly.")
    
    new_shop = st.text_input("🏪 Shop Name:")
    new_cat = st.selectbox("📦 Business Category:", ["Groceries", "Gadgets & Phones", "Clothing & Fashion", "Cafes & Food", "Other"])
    new_location = st.text_input("📍 Area / Street Name:")
    new_offer = st.text_area("📝 Describe the Flash Deal / Item:")
    
    col_stk, col_tim = st.columns(2)
    with col_stk:
        stock_qty = st.number_input("📦 Stock Qty:", min_value=1, value=10)
    with col_tim:
        new_time = st.time_input("⏰ Sale Closes:", time(21, 00))
        formatted_time = new_time.strftime("%I:%M %p")
        
    new_upi = st.text_input("💳 Shop UPI ID (For Direct Payments):")
    new_pin = st.text_input("🔑 Create Secret 4-Digit Management PIN:", type="password", max_chars=4)
    
    if st.button("🚀 Publish Offer Live", use_container_width=True):
        if new_shop and new_offer and new_location and new_upi and new_pin:
            # High-end success notification animations
            with st.spinner("Broadcasting offer data lines to cloud grid..."):
                cursor.execute(
                    "INSERT INTO offers (shop, category, offer, location, end_time, total_stock, remaining_stock, upi_id, pin) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (new_shop.strip(), new_cat, new_offer, new_location, formatted_time, stock_qty, stock_qty, new_upi.strip(), new_pin.strip())
                )
                conn.commit()
            st.balloons() # Premium full-screen celebration animation!
            st.success(f"🎉 Success! Deal is now streaming on the local live grid!")
            st.rerun()
        else:
            st.error("⚠️ Incomplete payload. Please verify all data blocks are configured.")

# Global Search Filter
search_word = st.text_input("🔍 Search for a specific item, shop name, or market street name:", placeholder="e.g., Biscuits, Sai Mobile, Station Road...")

# --- NAVIGATIONAL HIGH-CONTRAST STREAM TABS ---
tabs = st.tabs(["🛒 Groceries", "📱 Gadgets", "👗 Fashion", "🍔 Food & Bakeries", "📦 Other Categories", "🔐 OWNER DASHBOARD"])

def display_customer_tab(category_name, search_query):
    deals = get_offers_by_category(category_name, search_query)
    if not deals:
        st.info(f"No active flash {category_name.lower()} deals matching your search parameters right now.")
        return
        
    for item in deals:
        # High-design border matrix box container
        with st.container(border=True):
            left_info, right_booking = st.columns([4, 3])
            
            with left_info:
                st.markdown(f"### 🏪 {item['shop']}")
                st.markdown(f"#### 💰 **SPECIAL OFFER:** {item['offer']}")
                st.write(f"📍 **Market Location:** {item['location']} | ⏰ **Flash Window Closes At:** `{item['end_time']}`")
                
                # Visual micro-analytics stock meter animation bar
                pct = int((item['remaining_stock'] / item['total_stock']) * 100)
                st.markdown(f"📊 **Inventory Level:** {item['remaining_stock']} left out of {item['total_stock']} units available")
                st.progress(pct / 100.0)
                
            with right_booking:
                st.markdown("##### ⚡ Instant Booking & Claim Portal")
                c_name = st.text_input("Your Full Name:", key=f"name_{item['id']}")
                c_phone = st.text_input("WhatsApp Number:", key=f"phone_{item['id']}")
                c_qty = st.number_input("Quantity to Claim:", min_value=1, max_value=item['remaining_stock'], value=1, key=f"qty_{item['id']}")
                
                st.markdown(f"💳 **Pay via UPI app to target ID:** `{item['upi_id']}`")
                txn_id = st.text_input("Enter 12-Digit UPI Transaction UTR No:", key=f"txn_{item['id']}", placeholder="Copy from GPay/PhonePe status screen")
                
                if st.button("Confirm Payment & Lock Order Vouchers", key=f"btn_{item['id']}", use_container_width=True):
                    if c_name and c_phone and txn_id:
                        with st.spinner("Locking transaction verification array..."):
                            process_booking(item['id'], c_name, c_phone, c_qty, txn_id, item['remaining_stock'])
                        st.snow() # Micro-celebration confirmation animation!
                        st.success(f"✅ Slot Reserved! Present this screen summary directly to the merchant counter interface!")
                        st.rerun()
                    else:
                        st.error("⚠️ Verification failed. Input contact profile fields and complete UPI confirmation code.")

# Category matrix bindings
with tabs[0]: display_customer_tab("Groceries", search_word)
with tabs[1]: display_customer_tab("Gadgets & Phones", search_word)
with tabs[2]: display_customer_tab("Clothing & Fashion", search_word)
with tabs[3]: display_customer_tab("Cafes & Food", search_word)
with tabs[4]: display_customer_tab("Other", search_word)

# 6. ENHANCED MANAGEMENT UTILS
with tabs[5]:
    st.header("🔐 Store Manager Verification Center")
    st.write("Authenticate credentials to view customer orders or shut down listings.")
    
    mgr_col1, mgr_col2 = st.columns(2)
    with mgr_col1:
        chk_shop = st.text_input("Registered Shop Name Name:", key="mgr_shop")
    with mgr_col2:
        chk_pin = st.text_input("Management Secret 4-Digit PIN:", type="password", max_chars=4, key="mgr_pin")
    
    if chk_shop and chk_pin:
        owner_deals = get_owner_offers(chk_shop, chk_pin)
        if owner_deals:
            st.success(f"🔒 Encryption match. Pulling ledger sheets for '{chk_shop}':")
            for deal in owner_deals:
                with st.container(border=True):
                    st.markdown(f"#### 📦 Active Pipeline: {deal['offer']}")
                    st.write(f"Remaining Storage Inventory Units: `{deal['remaining_stock']}` / {deal['total_stock']} units cataloged.")
                    
                    orders = get_bookings_for_offer(deal['id'])
                    if orders:
                        st.markdown("📥 **Incoming Client Paid Booking Slips:**")
                        for ord in orders:
                            st.info(f"👤 Name: {ord[0]} | 📞 Contact: {ord[1]} | 🛍️ Claimed Batch: {ord[2]} | 💳 Verification Code: {ord[3]}")
                    else:
                        st.caption("No custom customer reservations recorded for this item matrix yet.")
                        
                    if st.button("🗑️ Wipe Deal & Terminate Listing", key=f"own_del_{deal['id']}", use_container_width=True):
                        delete_offer(deal['id'])
                        st.toast("Listing array destroyed.", icon="✂️")
                        st.rerun()
                st.markdown("---")
        else:
            st.error("Authentication rejected. Invalid shop index signature or secret configuration PIN.")

# Bottom Disclaimers Line
st.markdown("<br><br><hr>", unsafe_allow_html=True)
st.caption("⚖️ **Platform Disclaimer:** Neighborhood Deals Hub is an independent local inventory discovery directory platform. Customers must verify item quality, condition, and packaging parameters directly at the checkout point prior to paying merchants.")
