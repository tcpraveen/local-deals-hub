# --- NEW FEATURE: RATINGS & REVIEWS SYSTEM ---
item_id = item['id']  # Gets the database ID of the current item

# 1. Fetch existing reviews from Supabase for this specific item
try:
    reviews_response = supabase.table("feedback").select("*").eq("item_id", item_id).execute()
    reviews = reviews_response.data
except Exception as e:
    reviews = []

# 2. Calculate and display the dynamic average star rating
if reviews:
    avg_rating = sum([r['rating'] for r in reviews]) / len(reviews)
    stars = "⭐" * int(round(avg_rating))
    st.markdown(f"**Rating:** {stars} ({avg_rating:.1f}/5 based on {len(reviews)} reviews)")
else:
    st.markdown("*No ratings yet. Be the first to review!*")

# 3. Create an Expandable Review Form under each item
with st.expander("📝 Write a Customer Review"):
    with st.form(key=f"review_form_{item_id}", clear_on_submit=True):
        # Star dropdown and text box
        user_rating = st.selectbox("Select Stars", [5, 4, 3, 2, 1], key=f"stars_{item_id}")
        user_comment = st.text_input("Your review comment...", placeholder="e.g., Authentic condition, great seller!", key=f"comment_{item_id}")
        
        submit_review = st.form_submit_with_clicks = st.form_submit_button("Submit Review")
        
        if submit_review:
            if user_comment.strip() == "":
                st.warning("Please type a comment before submitting.")
            else:
                # Insert data straight into your new Supabase table!
                new_review = {
                    "item_id": item_id,
                    "rating": user_rating,
                    "comment": user_comment
                }
                try:
                    supabase.table("feedback").insert(new_review).execute()
                    st.success("Review submitted! Refresh the page to see it.")
                except Exception as e:
                    st.error(f"Database Error: {e}")

# 4. (Optional) Show a list of recent comments
if reviews:
    with st.expander("💬 View Recent Comments"):
        for r in reviews[-3:]:  # Shows the last 3 comments left by buyers
            st.caption(f"{'⭐' * r['rating']} — \"{r['comment']}\"")
# ---------------------------------------------
