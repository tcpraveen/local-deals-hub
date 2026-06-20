import streamlit as st
import sqlite3
from datetime import datetime, time

st.set_page_config(page_title="Local Deals Hub", page_icon="🛍️", layout="wide")

# --- DATABASE SETUP ---
conn = sqlite3.connect("deals.db", check_same_thread=False)
cursor = conn.cursor()

# Upgraded database table to store the secret PIN and the specific closing time
cursor.execute("""
CREATE TABLE IF NOT EXISTS offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop TEXT,
    category TEXT,
    offer TEXT,
    location TEXT,
    end_time TEXT,
    pin TEXT
)
""")
conn.commit()

def get_all_offers():
    cursor.execute("SELECT id, shop, category, offer, location, end_time, pin FROM offers ORDER BY id DESC")
    rows = cursor.fetchall()
    return [{"id": row[0], "shop": row[1], "category": row[2], "offer": row[3], "location": row[4], "end_time": row[5], "pin": row[6]} for row in rows]

def get_total_deals_count():
    cursor.execute("SELECT COUNT(*) FROM offers")
    return cursor.fetchone()[0]

def get_unique_shops_count():
    cursor.execute("SELECT COUNT(DISTINCT shop) FROM offers")
    return cursor.fetchone()[0]

def delete_offer(offer_id):
    cursor.execute("DELETE FROM offers WHERE id = ?", (offer_id,))
    conn.commit()

# Add default starter deals if completely empty
cursor.execute("SELECT COUNT(*) FROM offers")
if cursor.fetchone()[0] == 0:
    starter_deals = [
        ("Sai Mobile Zone", "Gadgets & Phones", "Flat 10% OFF on all smartphone accessories!", "Main Bazaar", "22:00", "0000"),
        ("Fresh Mart Grocery", "Groceries", "100 Packets of Premium Biscuits at 50% OFF!", "Station Road", "21:00", "0000"),
        ("Style Trendz Boutique", "Clothing & Fashion", "Buy 1 Get 1 Free on summer t-shirts!", "College Road", "23:00", "0000")
    ]
    cursor.executemany("INSERT INTO offers (shop, category, offer, location, end_time, pin) VALUES (?, ?, ?, ?, ?, ?)", starter_deals)
    conn.commit()

# --- APP INTERFACE ---
st.title("🛍️ Neighborhood Deals Hub")
st.subheader("Grab massive daily discounts and save local shops from stock surplus losses!")

# Founder Insights Dashboard
st.markdown("### 📊 Business Overview (Founder Insights)")
col1, col2 = st.columns(2)
with col1:
    st.metric(label="🏪 Total Active Partners (Shops)", value=get_unique_shops_count())
with col2:
    st.metric(label="🔥 Total Live Offers Running", value=get_total_deals_count())
st.markdown("---")

# Sidebar for Shop Owners
with st.sidebar:
    st.header("📢 Shop Owner Portal")
    st.write("Clear your surplus stock instantly to nearby bargain hunters!")
    
    new_shop = st.text_input("Shop Name:")
    new_cat = st.selectbox("Shop Category:", ["Groceries", "Gadgets & Phones", "Clothing & Fashion", "Cafes & Food", "Other"])
    new_location = st.text_input("Area / Street Name:")
    new_offer = st.text_area("Describe your Discount Offer (e.g., 50% off biscuits):")
    
    # NEW FEATURE: Select a specific flash sale end time
    new_time = st.time_input("What time does this flash sale end tonight?", time(21, 00))
    formatted_time = new_time.strftime("%I:%M %p")
    
    # NEW FEATURE: Security PIN setup
    new_pin = st.text_input("Set a secret 4-digit PIN (to delete this deal later):", type="password", max_chars=4)
    
    if st.button("Publish Offer Live"):
        if new_shop and new_offer and new_location and new_pin:
            cursor.execute(
                "INSERT INTO offers (shop, category, offer, location, end_time, pin) VALUES (?, ?, ?, ?, ?, ?)",
                (new_shop, new_cat, new_offer, new_location, formatted_time, new_pin)
            )
            conn.commit()
            st.success(f"🎉 Live! Flash deal uploaded successfully!")
            st.rerun()
        else:
            st.error("Please fill out all fields and set a secret PIN.")

# Main Dashboard for Local Residents
st.header("🔥 Active Local Discounts")
search_query = st.text_input("🔍 Search for a shop, category, stock item, or area:")

live_offers = get_all_offers()

filtered_offers = [
    o for o in live_offers 
    if search_query.lower() in o["shop"].lower() 
    or search_query.lower() in o["category"].lower()
    or search_query.lower() in o["location"].lower()
    or search_query.lower() in o["offer"].lower()
]

if filtered_offers:
    for item in filtered_offers:
        with st.container():
            text_col, action_col = st.columns([4, 2])
            
            with text_col:
                st.markdown(f"### 🏪 {item['shop']} — *{item['category']}*")
                st.info(f"💰 **DEAL:** {item['offer']}")
                st.warning(f"⏳ **⚡ FLASH DEAL CLOSES AT:** {item['end_time']} | 📍 **Location:** {item['location']}")
            
            with action_col:
                st.write("") 
                # Secure Deletion block
                input_pin = st.text_input("Enter Shop PIN to remove:", type="password", max_chars=4, key=f"pin_input_{item['id']}")
                if st.button("🗑️ Confirm Removal", key=f"del_{item['id']}"):
                    if input_pin == item['pin']:
                        delete_offer(item['id'])
                        st.toast("Deal successfully verified and removed!")
                        st.rerun()
                    else:
                        st.error("⚠️ Incorrect PIN! Only the owner who posted this can remove it.")
            st.markdown("---")
else:
    st.warning("No active flash deals match your search.")
    
