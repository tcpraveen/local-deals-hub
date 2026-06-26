import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import time

# --- PRODUCTION PLATFORM CONFIGURATION ---
st.set_page_config(
    page_title="Neighborhood Deals Hub", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

import os

# Try reading from Render first, fall back to Streamlit secrets if not found
db_link = os.getenv("db_url") or st.secrets.get("db_url")

if not db_link:
    st.error("🔑 Database Secret Missing! Please configure 'db_url' environment variable.")
    st.stop()
db_link = "postgresql://postgres:Tcpraveen%402008@db.jjecrbcacxaxzzpgvwbx.supabase.co:5432/postgres"
try:
    db_link = st.secrets["db_url"]
except Exception:
    st.error("🔑 Database Secret Missing! Please configure 'db_url' inside your Streamlit Cloud Settings panel.")
    st.stop()

def get_connection():
    return psycopg2.connect(db_link, check_same_thread=False if hasattr(psycopg2, 'check_same_thread') else None)

# Automatically create structural cloud data tables if they don't exist
try:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS offers (
        id SERIAL PRIMARY KEY,
        shop TEXT NOT NULL,
        category TEXT NOT NULL,
        offer TEXT NOT NULL,
        location TEXT NOT NULL,
        end_time TEXT NOT NULL,
        total_stock INTEGER NOT NULL,
        remaining_stock INTEGER NOT NULL,
        upi_id TEXT NOT NULL,
        pin TEXT NOT NULL
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id SERIAL PRIMARY KEY,
        offer_id INTEGER NOT NULL,
        customer_name TEXT NOT NULL,
        customer_phone TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        txn_id TEXT NOT NULL
    )
    """)
    conn.commit()
    cursor.close()
    conn.close()
except Exception as database_error:
    st.error(f"❌ Server Connection Error: {database_error}")
    st.stop()

# --- BACKEND LOGIC FILTERS (POSTGRES ENGINE) ---
def get_offers_by_category(category, search_query=""):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    if search_query:
        query = """
            SELECT id, shop, category, offer, location, end_time, total_stock, remaining_stock, upi_id 
            FROM offers 
            WHERE category = %s AND remaining_stock > 0 
            AND (LOWER(shop) LIKE %s OR LOWER(offer) LIKE %s OR LOWER(location) LIKE %s)
            ORDER BY id DESC
        """
        like_val = f"%{search_query.lower()}%"
        cursor.execute(query, (category, like_val, like_val, like_val))
    else:
        cursor.execute("SELECT id, shop, category, offer, location, end_time, total_stock, remaining_stock, upi_id FROM offers WHERE category = %s AND remaining_stock > 0 ORDER BY id DESC", (category,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def get_owner_offers(shop_name, pin):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT id, shop, category, offer, total_stock, remaining_stock FROM offers WHERE LOWER(shop) = %s AND pin = %s ORDER BY id DESC", (shop_name.lower().strip(), pin.strip()))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def get_bookings_for_offer(offer_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT customer_name, customer_phone, quantity, txn_id FROM bookings WHERE offer_id = %s", (offer_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def process_booking(offer_id, name, phone, qty, txn, current_remaining):
    conn = get_connection()
    cursor = conn.cursor()
    new_remaining = current_remaining - qty
    cursor.execute("UPDATE offers SET remaining_stock = %s WHERE id = %s", (new_remaining, offer_id))
    cursor.execute("INSERT INTO bookings (offer_id, customer_name, customer_phone, quantity, txn_id) VALUES (%s, %s, %s, %s, %s)", (offer_id, name, phone, qty, txn))
    conn.commit()
    cursor.close()
    conn.close()

def delete_offer(offer_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM offers WHERE id = %s", (offer_id,))
    cursor.execute("DELETE FROM bookings WHERE offer_id = %s", (offer_id,))
    conn.commit()
    cursor.close()
    conn.close()

# --- SYSTEM ALERT BANNER ---
st.markdown("""
<div style="background-color:#fff9e6; border-left: 6px solid #ffcc00; padding: 12px; border-radius: 4px; text-align:center; margin-bottom:15px;">
    <strong style="color:#b38600; font-size:15px;">⏳ SYSTEM ALERT: Flash listings automatically reset at store closing hours. Claim vouchers before stock levels drop to zero!</strong>
</div>
""", unsafe_allow_html=True)

# --- HEADER LOGO SEGMENT ---
st.markdown("<h1 style='text-align: center; color: #1e88e5; font-family: sans-serif; margin-bottom: 2px;'>⚡ Super Saver Local Hub</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #bbbbbb; font-size:15px; margin-top:0px;'>Direct Marketplace for Local Expiry & Surplus Inventory Clearance</p>", unsafe_allow_html=True)
st.markdown("---")

# --- INSTANT SEARCH BOX ---
search_word = st.text_input("", placeholder="🔍 Search for items, brands, local shops, or street markets...")

# --- FLIPKART NAVIGATION BAR ---
selected_tab = st.radio(
    label="Category Routing Engine:",
    options=["🛒 Groceries & Snacks", "📱 Mobile & Gadgets", "👗 Fashion & Clothes", "🍔 Bakeries & Food", "🔐 Merchant Dashboard"],
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("<br>", unsafe_allow_html=True)

# --- FLIPKART STYLE DESIGN ENGINE ---
def render_flipkart_feed(db_category):
    deals = get_offers_by_category(db_category, search_word)
    if not deals:
        st.info(f"No flash deals registered in {db_category} right now.")
        return
        
    for item in deals:
        with st.container(border=True):
            # FIXED: Bright white contrast shop header styling
            st.markdown(f"""
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <span style="background-color:#0052cc; color:#ffffff; padding:2px 8px; border-radius:3px; font-weight:bold; font-size:11px; text-transform: uppercase;">⚡ ASSURED SAVINGS</span>
                <span style="margin-left: 10px; font-size: 18px; font-weight: bold; color: #ffffff;">{item['shop']}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # FIXED: Glowing high-contrast white layout text for your deal description
            st.markdown(f"<h2 style='color:#ffffff; font-family:sans-serif; margin-top:0px; margin-bottom:10px; font-size:24px;'>{item['offer']}</h2>", unsafe_allow_html=True)
            st.markdown(f"📍 Location Corridor: <b style='color:#ffcc00;'>{item['location']}</b> | 🕒 Order Lock Window Closes: <b style='color:#ffcc00;'>{item['end_time']}</b>", unsafe_allow_html=True)
            
            pct = int((item['remaining_stock'] / item['total_stock']) * 100)
            st.markdown(f"🔥 **Stock Status:** Only `{item['remaining_stock']}` items left (Initial Stack: {item['total_stock']})")
            st.progress(pct / 100.0)
            st.markdown("<br>", unsafe_allow_html=True)
            
            with st.expander("⚡ Claim Vouchers Instantly"):
                c_name = st.text_input("Buyer Full Name:", key=f"name_{item['id']}")
                c_phone = st.text_input("WhatsApp Mobile Line:", key=f"phone_{item['id']}")
                c_qty = st.number_input("Units to Reserve:", min_value=1, max_value=item['remaining_stock'], value=1, key=f"qty_{item['id']}")
                
                st.markdown(f"💳 **Payment Gateway Method:** Clear the order cost to Shop UPI: `{item['upi_id']}` via GPay/PhonePe App.")
                txn_id = st.text_input("Enter 12-Digit UPI Transaction UTR Reference Code:", key=f"txn_{item['id']}", placeholder="Enter valid transaction identifier")
                
                if st.button("Secure Order Slot", key=f"btn_{item['id']}", use_container_width=True):
                    if c_name and c_phone and txn_id:
                        process_booking(item['id'], c_name, c_phone, c_qty, txn_id, item['remaining_stock'])
                        st.balloons()
                        st.success("🎉 Slot Locked! Order confirmation voucher generated securely inside your cloud storage database.")
                        st.rerun()
                    else:
                        st.error("Validation failed. Please input contact profile elements and your UPI payment reference ID.")

# Tab Engine Distributor
if "🛒 Groceries" in selected_tab:
    render_flipkart_feed("Groceries")
elif "📱 Mobile" in selected_tab:
    render_flipkart_feed("Gadgets & Phones")
elif "👗 Fashion" in selected_tab:
    render_flipkart_feed("Clothing & Fashion")
elif "🍔 Bakeries" in selected_tab:
    render_flipkart_feed("Cafes & Food")

# --- MERCHANT SECURITY CENTRE ---
elif "🔐 Merchant" in selected_tab:
    st.header("🔐 Store Manager Verification Center")
    st.write("Authenticate credentials to audit customer orders or shut down listings.")
    
    mgr_col1, mgr_col2 = st.columns(2)
    with mgr_col1:
        chk_shop = st.text_input("Registered Shop Identity Name:", key="mgr_shop")
    with mgr_col2:
        chk_pin = st.text_input("Management Account Secret PIN:", type="password", max_chars=4, key="mgr_pin")
    
    if chk_shop and chk_pin:
        owner_deals = get_owner_offers(chk_shop, chk_pin)
        if owner_deals:
            st.success(f"🔒 Encryption verification matched. Pulling ledger sheets for '{chk_shop}':")
            for deal in owner_deals:
                with st.container(border=True):
                    st.markdown(f"#### 📦 Active Pipeline: {deal['offer']}")
                    st.write(f"Current Available Store Inventory: `{deal['remaining_stock']}` / {deal['total_stock']} units remaining.")
                    
                    orders = get_bookings_for_offer(deal['id'])
                    if orders:
                        st.markdown("📥 **Incoming Paid Reservations Log:**")
                        for ord in orders:
                            st.info(f"👤 Name: {ord[0]} | 📞 Contact Line: {ord[1]} | 🛍️ Claimed Batch: {ord[2]} | 💳 Verification Code: {ord[3]}")
                    else:
                        st.caption("No custom customer reservations recorded for this item matrix yet.")
                        
                    if st.button("🗑️ Wipe Deal & Terminate Listing", key=f"own_del_{deal['id']}", use_container_width=True):
                        delete_offer(deal['id'])
                        st.toast("Listing data points cleared completely.")
                        st.rerun()
        else:
            st.error("Authentication rejected. Invalid shop credentials combination.")

# --- PERSISTENT OPERATIONAL SIDEBAR ---
with st.sidebar:
    st.header("➕ Stream a New Clearance Sale")
    st.write("Upload your item clearance inventory statistics directly here.")
    
    new_shop = st.text_input("🏪 Shop Name:")
    new_cat = st.selectbox("📦 Category Type:", ["Groceries", "Gadgets & Phones", "Clothing & Fashion", "Cafes & Food", "Other"])
    new_location = st.text_input("📍 Area Corridor Name:")
    new_offer = st.text_area("📝 Describe the Flash Deal Offer:")
    
    col_stk, col_tim = st.columns(2)
    with col_stk:
        stock_qty = st.number_input("📦 Base Stock Qty:", min_value=1, value=10)
    with col_tim:
        new_time = st.time_input("⏰ Active Session Closes:", time(21, 00))
        formatted_time = new_time.strftime("%I:%M %p")
        
    new_upi = st.text_input("💳 Merchant Target UPI Address:")
    new_pin = st.text_input("🔑 Setup 4-Digit Configuration PIN:", type="password", max_chars=4)
    
    if st.button("🚀 Broadcast Live Feed", use_container_width=True):
        if new_shop and new_offer and new_location and new_upi and new_pin:
            db_cat = "Other"
            if new_cat == "Groceries": db_cat = "Groceries"
            elif new_cat == "Gadgets & Phones": db_cat = "Gadgets & Phones"
            elif new_cat == "Clothing & Fashion": db_cat = "Clothing & Fashion"
            elif new_cat == "Cafes & Food": db_cat = "Cafes & Food"
            
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO offers (shop, category, offer, location, end_time, total_stock, remaining_stock, upi_id, pin) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (new_shop.strip(), db_cat, new_offer, new_location, formatted_time, stock_qty, stock_qty, new_upi.strip(), new_pin.strip())
            )
            conn.commit()
            cursor.close()
            conn.close()
            
            st.balloons()
            st.success("🎉 Transmission successful! Listing is broadcast active.")
            st.rerun()

# Bottom Footer Disclaimer Policy
st.markdown("<br><br><hr>", unsafe_allow_html=True)
st.caption("⚖️ **Platform Legal Clause:** Neighborhood Deals Hub is an independent local inventory discovery directory utility. Customers must verify physical asset parameters and item expiration metrics directly at the checkout point prior to clearing transactions.")
