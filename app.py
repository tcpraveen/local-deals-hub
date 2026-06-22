import streamlit as st
import sqlite3
from datetime import time

# --- HIGH CONVERTING PREMIUM PLATFORM CONFIG ---
st.set_page_config(
    page_title="Neighborhood Deals Hub", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- DATABASE SETUP ---
conn = sqlite3.connect("deals_v5.db", check_same_thread=False)
cursor = conn.cursor()

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

# --- NEW EXTENSION: ADVANCED ALERT TICKER BANNER ---
st.markdown("""
<div style="background-color:#fff9e6; border-left: 6px solid #ffcc00; padding: 12px; border-radius: 4px; text-align:center; margin-bottom:15px;">
    <strong style="color:#b38600; font-size:15px;">⏳ SYSTEM ALERT: Flash listings automatically reset at store closing hours. Claim vouchers before stock levels drop to zero!</strong>
</div>
""", unsafe_allow_html=True)

# --- HEADER LOGO SEGMENT ---
st.markdown("<h1 style='text-align: center; color: #17449b; font-family: sans-serif; margin-bottom: 2px;'>⚡ Super Saver Local Hub</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #555; font-size:15px; margin-top:0px;'>Direct Marketplace for Local Expiry & Surplus Inventory Clearance</p>", unsafe_allow_html=True)
st.markdown("---")

# --- INSTANT TEXT FILTER ---
search_word = st.text_input("", placeholder="🔍 Search for items, brands, local shops, or street markets...")

# --- FLIPKART NAVIGATION SEGMENTS ---
selected_tab = st.radio(
    label="Category Routing Engine:",
    options=["🛒 Groceries & Snacks", "📱 Mobile & Gadgets", "👗 Fashion & Clothes", "🍔 Bakeries & Food", "🔐 Merchant Dashboard"],
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("<br>", unsafe_allow_html=True)

# --- FLIPKART DESIGN GRID ENGINE ---
def render_flipkart_feed(db_category):
    deals = get_offers_by_category(db_category, search_word)
    if not deals:
        st.info(f"No flash deals registered in {db_category} right now.")
        return
        
    for item in deals:
        with st.container(border=True):
            # Dynamic Branding Header Badge
            st.markdown(f"""
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <span style="background-color:#e6f0ff; color:#0052cc; padding:2px 8px; border-radius:3px; font-weight:bold; font-size:11px; text-transform: uppercase;">⚡ ASSURED SAVINGS</span>
                <span style="margin-left: 10px; font-size: 16px; font-weight: bold; color: #333;">{item['shop']}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Big Bold Clear Highlight Text
            st.markdown(f"<h2 style='color:#111; font-family:sans-serif; margin-top:0px; margin-bottom:6px;'>{item['offer']}</h2>", unsafe_allow_html=True)
            
            # Sub-Metadata row
            st.markdown(f"📍 Location Corridor: **{item['location']}** | 🕒 Order Lock Window Closes: `{item['end_time']}`")
            
            # Stock Analytics Bar
            pct = int((item['remaining_stock'] / item['total_stock']) * 100)
            st.markdown(f"🔥 **Stock Status:** Only `{item['remaining_stock']}` items left (Initial Stack: {item['total_stock']})")
            st.progress(pct / 100.0)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Collapsible Premium Shopping Bag Drawer
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
                        st.success("🎉 Slot Locked! Order confirmation voucher generated securely inside network databases.")
                        st.rerun()
                    else:
                        st.error("Validation failed. Please input contact profile elements and your UPI payment reference ID.")

# Tab Routing Controller Array
if "🛒 Groceries" in selected_tab:
    render_flipkart_feed("Groceries")
elif "📱 Mobile" in selected_tab:
    render_flipkart_feed("Gadgets & Phones")
elif "👗 Fashion" in selected_tab:
    render_flipkart_feed("Clothing & Fashion")
elif "🍔 Bakeries" in selected_tab:
    render_flipkart_feed("Cafes & Food")

st.markdown(f"<h2 style='color:#ffffff; font-family:sans-serif; margin-top:0px; margin-bottom:6px;'>{item['offer']}</h2>", unsafe_allow_html=True)
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
            
            cursor.execute(
                "INSERT INTO offers (shop, category, offer, location, end_time, total_stock, remaining_stock, upi_id, pin) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (new_shop.strip(), db_cat, new_offer, new_location, formatted_time, stock_qty, stock_qty, new_upi.strip(), new_pin.strip())
            )
            conn.commit()
            st.balloons()
            st.success("🎉 Transmission successful! Listing is broadcast active.")
            st.rerun()

# Bottom Footer Disclaimer Policy
st.markdown("<br><br><hr>", unsafe_allow_html=True)
st.caption("⚖️ **Platform Legal Clause:** Neighborhood Deals Hub is an independent local inventory discovery directory utility. Customers must verify physical asset parameters and item expiration metrics directly at the checkout point prior to clearing transactions.")
