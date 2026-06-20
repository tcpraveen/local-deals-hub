import streamlit as st
import sqlite3

st.set_page_config(page_title="Local Deals Hub", page_icon="🛍️", layout="wide")

# --- DATABASE SETUP ---
conn = sqlite3.connect("deals.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shop TEXT,
    category TEXT,
    offer TEXT,
    location TEXT
)
""")
conn.commit()

# Pull offers including their unique database ID
def get_all_offers():
    cursor.execute("SELECT id, shop, category, offer, location FROM offers ORDER BY id DESC")
    rows = cursor.fetchall()
    return [{"id": row[0], "shop": row[1], "category": row[2], "offer": row[3], "location": row[4]} for row in rows]

def get_total_deals_count():
    cursor.execute("SELECT COUNT(*) FROM offers")
    return cursor.fetchone()[0]

def get_unique_shops_count():
    cursor.execute("SELECT COUNT(DISTINCT shop) FROM offers")
    return cursor.fetchone()[0]

# DATABASE DELETE FUNCTION
def delete_offer(offer_id):
    cursor.execute("DELETE FROM offers WHERE id = ?", (offer_id,))
    conn.commit()

# Add default starter deals if completely empty
cursor.execute("SELECT COUNT(*) FROM offers")
if cursor.fetchone()[0] == 0:
    starter_deals = [
        ("Sai Mobile Zone", "Gadgets & Phones", "Flat 10% OFF on all smartphone accessories!", "Main Bazaar"),
        ("Style Trendz Boutique", "Clothing & Fashion", "Buy 1 Get 1 Free on summer t-shirts!", "College Road"),
        ("Fresh Mart", "Groceries", "Free delivery + 5% discount on bills above ₹500", "Station Road")
    ]
    cursor.executemany("INSERT INTO offers (shop, category, offer, location) VALUES (?, ?, ?, ?)", starter_deals)
    conn.commit()

# --- APP INTERFACE ---
st.title("🛍️ Neighborhood Deals Hub")
st.subheader("Skip the expensive social media ads. See real-time offers from local shops nearby!")

# Founder Insights Dashboard
st.markdown("### 📊 Business Overview (Founder Insights)")
col1, col2 = st.columns(2)
with col1:
    st.metric(label="🏪 Total Active Partners (Shops)", value=get_unique_shops_count())
with col2:
    st.metric(label="🔥 Total Live Offers Running", value=get_total_deals_count())
st.markdown("---")

# Create Sidebar for Shop Owners to post discounts
with st.sidebar:
    st.header("📢 Shop Owner Portal")
    st.write("Post your discount here instantly to reach all local customers for free!")
    
    new_shop = st.text_input("Shop Name:")
    new_cat = st.selectbox("Shop Category:", ["Gadgets & Phones", "Clothing & Fashion", "Groceries", "Cafes & Food", "Other"])
    new_location = st.text_input("Area / Street Name:")
    new_offer = st.text_area("Describe your Discount Offer:")
    
    if st.button("Publish Offer Live"):
        if new_shop and new_offer and new_location:
            cursor.execute(
                "INSERT INTO offers (shop, category, offer, location) VALUES (?, ?, ?, ?)",
                (new_shop, new_cat, new_offer, new_location)
            )
            conn.commit()
            st.success(f"🎉 Success! '{new_shop}' offer is now saved permanently!")
            st.rerun()
        else:
            st.error("Please fill out all fields to publish.")

# Main Dashboard for Local Residents
st.header("🔥 Active Local Discounts")
search_query = st.text_input("🔍 Search for a shop, category, or area:")

live_offers = get_all_offers()

filtered_offers = [
    o for o in live_offers 
    if search_query.lower() in o["shop"].lower() 
    or search_query.lower() in o["category"].lower()
    or search_query.lower() in o["location"].lower()
]

if filtered_offers:
    for item in filtered_offers:
        with st.container():
            text_col, btn_col = st.columns([5, 1])
            
            with text_col:
                st.markdown(f"### 🏪 {item['shop']} — *{item['category']}*")
                st.info(f"💰 **OFFER:** {item['offer']}")
                st.caption(f"📍 Location: {item['location']}")
            
            with btn_col:
                st.write("") 
                st.write("") 
                if st.button("🗑️ Remove", key=f"del_{item['id']}"):
                    delete_offer(item['id'])
                    st.toast(f"Removed deal from {item['shop']}!")
                    st.rerun()
            st.markdown("---")
else:
    st.warning("No active discounts match your search. Try checking another category!")
