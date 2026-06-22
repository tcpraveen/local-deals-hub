import streamlit as st
import sqlite3
from datetime import time

st.set_page_config(page_title="Neighborhood Deals Hub", page_icon="🛍️", layout="wide")

# --- DATABASE SETUP ---
# Moving to v5 to clear any old conflicting database tables cleanly
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

# --- BACKEND LOGIC ---
def get_offers_by_category(category):
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

# Add fresh default deals distributed nicely across categories
cursor.execute("SELECT COUNT(*) FROM offers")
if cursor.fetchone()[0] == 0:
    starter_deals = [
        ("Sai Mobile Zone", "Gadgets & Phones", "Tempered Glass at 70% OFF clearance pricing!", "Main Bazaar", "09:30 PM", 50, 50, "sai@okaxis", "1234"),
        ("Fresh Mart Grocery", "Groceries", "Premium Britannia Biscuits at Flat 50% OFF!", "Station Road", "08:00 PM", 100, 100, "freshmart@upi", "1234"),
        ("Style Trendz Boutique", "Clothing & Fashion", "Buy 1 Get 1 Free on all summer t-shirts!", "College Road", "11:00 PM", 20, 20, "style@okicici", "1234")
    ]
    cursor.executemany("INSERT INTO offers (shop, category, offer, location, end_time, total_stock, remaining_stock, upi_id, pin) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", starter_deals)
    conn.commit()

# --- APP INTERFACE UI ---
st.title("🛍️ Neighborhood Deals Hub")
st.markdown("##### *Instantly claim flash surplus stock discounts or clear warehouse inventory nearby!*")
st.markdown("---")

# Visual Stats Cards
col1, col2 = st.columns(2)
with col1:
    st.metric(label="🏪 Active Partner Outlets", value=cursor.execute("SELECT COUNT(DISTINCT shop) FROM offers").fetchone()[0])
with col2:
    st.metric(label="⚡ Active Flash Offers Running", value=cursor.execute("SELECT COUNT(*) FROM offers WHERE remaining_stock > 0").fetchone()[0])
st.markdown("---")

# Sidebar: Strictly for posting deals
with st.sidebar:
    st.header("📢 Post a New Flash Deal")
    st.write("Launch a fast clearance sale directly to nearby buyers.")
    
    new_shop = st.text_input("Shop Name:")
    new_cat = st.selectbox("Category:", ["Groceries", "Gadgets & Phones", "Clothing & Fashion", "Cafes & Food", "Other"])
    new_location = st.text_input("Area / Street Name:")
    new_offer = st.text_area("Describe your Deal / Item Name:")
    
    col_stk, col_tim = st.columns(2)
    with col_stk:
        stock_qty = st.number_input("Stock Quantity:", min_value=1, value=10)
    with col_tim:
        new_time = st.time_input("Sale Closes At:", time(21, 00))
        formatted_time = new_time.strftime("%I:%M %p")
        
    new_upi = st.text_input("Shop UPI ID (for instant customer direct pay):")
    new_pin = st.text_input("Create Secret 4-Digit Management PIN:", type="password", max_chars=4)
    
    if st.button("Publish Offer Live", use_container_width=True):
        if new_shop and new_offer and new_location and new_upi and new_pin:
            cursor.execute(
                "INSERT INTO offers (shop, category, offer, location, end_time, total_stock, remaining_stock, upi_id, pin) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (new_shop.strip(), new_cat, new_offer, new_location, formatted_time, stock_qty, stock_qty, new_upi.strip(), new_pin.strip())
            )
            conn.commit()
            st.success(f"🎉 Live! Deal is now streaming on the feed!")
            st.rerun()
        else:
            st.error("Please fill out all fields before publishing.")

# --- NAVIGATION STRUCUTRE TABS ---
tabs = st.tabs(["🛒 Groceries", "📱 Gadgets", "👗 Fashion", "🍔 Food & Bakeries", "📦 Other Categories", "🔐 OWNER DASHBOARD"])

def display_customer_tab(category_name):
    deals = get_offers_by_category(category_name)
    if not deals:
        st.info(f"No flash {category_name.lower()} deals running in this area right now.")
        return
        
    for item in deals:
        # Neat clean box container structure
        with st.container(border=True):
            left_info, right_booking = st.columns([4, 3])
            
            with left_info:
                st.markdown(f"### 🏪 {item['shop']}")
                st.subheader(f"🔥 {item['offer']}")
                st.markdown(f"📍 **Location:** {item['location']} | ⏰ **Closes At:** `{item['end_time']}`")
                
                # Visual stock tracker gauge
                pct = int((item['remaining_stock'] / item['total_stock']) * 100)
                st.markdown(f"📦 **Inventory Tracker:** {item['remaining_stock']} left out of {item['total_stock']}")
                st.progress(pct / 100.0)
                
            with right_booking:
                st.markdown("##### ⚡ Instant Booking Portal")
                c_name = st.text_input("Your Full Name:", key=f"name_{item['id']}")
                c_phone = st.text_input("WhatsApp Number:", key=f"phone_{item['id']}")
                c_qty = st.number_input("Qty to Claim:", min_value=1, max_value=item['remaining_stock'], value=1, key=f"qty_{item['id']}")
                
                st.markdown(f"💳 **Pay via UPI app to:** `{item['upi_id']}`")
                txn_id = st.text_input("Enter 12-Digit UPI Ref / UTR No:", key=f"txn_{item['id']}")
                
                if st.button("Confirm Payment & Lock Order", key=f"btn_{item['id']}", use_container_width=True):
                    if c_name and c_phone and txn_id:
                        process_booking(item['id'], c_name, c_phone, c_qty, txn_id, item['remaining_stock'])
                        st.success(f"✅ Reserved! Show this verification screen to the shopkeeper at the counter!")
                        st.rerun()
                    else:
                        st.error("Please provide contact details and UTR number to complete reservation.")

# Direct individual tab distribution mapping
with tabs[0]: display_customer_tab("Groceries")
with tabs[1]: display_customer_tab("Gadgets & Phones")
with tabs[2]: display_customer_tab("Clothing & Fashion")
with tabs[3]: display_customer_tab("Cafes & Food")
with tabs[4]: display_customer_tab("Other")

# 6. ENHANCED MANAGEMENT PANEL
with tabs[5]:
    st.header("🔐 Store Manager Verification Center")
    st.write("Log in to check incoming transactional customer claims or pull down your listings.")
    
    mgr_col1, mgr_col2 = st.columns(2)
    with mgr_col1:
        chk_shop = st.text_input("Registered Shop Name:", key="mgr_shop")
    with mgr_col2:
        chk_pin = st.text_input("Secret 4-Digit PIN:", type="password", max_chars=4, key="mgr_pin")
    
    if chk_shop and chk_pin:
        owner_deals = get_owner_offers(chk_shop, chk_pin)
        if owner_deals:
            st.success(f"🔒 Identity Authenticated. Displaying live inventory files for '{chk_shop}':")
            for deal in owner_deals:
                with st.container(border=True):
                    st.markdown(f"#### 📦 Live Offer: {deal['offer']}")
                    st.write(f"Current Available Store Inventory: `{deal['remaining_stock']}` / {deal['total_stock']} items remaining.")
                    
                    orders = get_bookings_for_offer(deal['id'])
                    if orders:
                        st.markdown("📥 **Incoming Paid Reservations:**")
                        for ord in orders:
                            st.info(f"👤 Name: {ord[0]} | 📞 Phone: {ord[1]} | 🛍️ Claimed Qty: {ord[2]} | 💳 UTR ID: {ord[3]}")
                    else:
                        st.caption("No custom customer reservations recorded for this item yet.")
                        
                    if st.button("🗑️ Wipe Deal & Terminate Listing", key=f"own_del_{deal['id']}", use_container_width=True):
                        delete_offer(deal['id'])
                        st.toast("Listing removed permanently.")
                        st.rerun()
                st.markdown("---")
        else:
            st.error("No valid secure records match that shop name/PIN combination.")
            
