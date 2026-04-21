import asyncio
import sys
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st
import pandas as pd
from pipeline.tasks import process_search_tasks_async, save_watchlist_products
from database.queries import get_session

st.set_page_config(page_title="Product Search", layout="wide")
st.title("🔍 Product Search")
if 'selected_asins' not in st.session_state:
    st.session_state.selected_asins = set()
st.caption("Cari produk di Amazon dan langsung pantau harganya")


session = get_session()

# ─── Search Input ─────────────────────────────────────────────────────────────
with st.container():
    col1, col2, col3 = st.columns([6, 2, 1])

    with col1:
        keyword = st.text_input(label="Cari Produk", placeholder="🔍 Cari produk...", label_visibility="collapsed")

    with col2:
        max_results = st.selectbox("Jumlah Hasil", [5, 10, 20], index=1, label_visibility="collapsed")

    with col3:
        search_clicked = st.button("Search", width='stretch')    


# ─── Search Results ───────────────────────────────────────────────────────────
if search_clicked and keyword:
    st.session_state.selected_asins = set()
    st.session_state["search_results"] = set()
    for key in list(st.session_state.keys()):
        if key.startswith("check_"):
            del st.session_state[key]
    
    with st.spinner(f'Mencari "{keyword}" di Amazon...'):
        # Pakai async version dari Streamlit
        results = asyncio.run(
            process_search_tasks_async(keyword=keyword, max_results=max_results)
        )
    if not results:
        st.error("Tidak ada hasil ditemukan. Coba keyword lain.")
        st.stop()

    st.success(f"Ditemukan {len(results)} produk untuk keyword **{keyword}**")
    st.divider()

    # ─── Tampilkan hasil sebagai cards ────────────────────────────────────────
    # Simpan hasil ke session state supaya tidak hilang saat user klik tombol
    st.session_state["search_results"] = results
    st.session_state["keyword"] = keyword

if "search_results" in st.session_state:
    results = st.session_state["search_results"]

    # Checkbox untuk pilih produk yang mau dipantau
    st.subheader("Hasil Pencarian")
    st.caption("Centang produk yang mau ditambahkan ke watchlist kamu")
    
    col1, col2, col3 = st.columns([1,1,3])

    with col1:
        if st.button("Select All"):
            for p in results:
                asin = p["ASIN"]
                st.session_state[f"check_{asin}"] = True
            
            st.session_state.selected_asins = set(p["ASIN"] for p in results)

    with col2:
        if st.button("Clear"):
            for p in results:
                asin = p["ASIN"]
                st.session_state[f"check_{asin}"] = False
            st.session_state.selected_asins = set()

    with col3:
        st.caption(f"{len(st.session_state.selected_asins)} produk dipilih")

    with st.form('select_products_form'):
        for i, product in enumerate(results):
            # print(product)
            # print('============================')
            col1, col2, col3 = st.columns([0.5, 3, 1.5])
            asin = product['ASIN']
            with col1:
                checked = st.checkbox(
                    f"Choose {asin}",
                    key=f"check_{asin}",
                    value=asin in st.session_state.selected_asins,
                    label_visibility='collapsed'
                )
                if checked:
                    st.session_state.selected_asins.add(asin)
                else:
                    st.session_state.selected_asins.discard(asin)
                st.image(product.get("image_url"), width=80)

            with col2:
                st.markdown(f"**{product['title']}**" if product['title'] else "No title")
                
                rating_stars = "⭐" * int(product['rating']) if product['rating'] else 0
                prime_badge = "🟡 Prime" if product['is_prime'] else ""
                st.caption(f"{rating_stars} {product['rating']} · {product['review_count']} reviews · {prime_badge}")

            with col3:
                price_display = f"${product['price']:.2f}" if product['price'] else "N/A"
                st.metric("Harga", price_display)

            st.divider()
        
        st.form_submit_button("Submit", disabled=True)

    # ─── Tombol tambah ke watchlist ───────────────────────────────────────────
    submitted = st.button('➕ Add to Watchlist!')
    if submitted and keyword:
        if not st.session_state.selected_asins:
            st.warning('Pilih minimal 1 produk dulu')
        else:
            with st.spinner("Menyimpan produk ke database..."):
                save_products = asyncio.run(
                    save_watchlist_products(st.session_state.selected_asins, keyword)
                )

                if not save_products:
                    st.error("Error in saving watchlist products.")
                else:
                    st.success(f"✅ {save_products} produk berhasil ditambahkan!")
                # st.session_state.run_save = True
            st.session_state.selected_asins = set()
    
    # ─── Tabel ringkasan ──────────────────────────────────────────────────────

    st.markdown("""
        <style>
        /* Menyembunyikan tombol submit form agar tidak terlihat sama sekali */
        div[data-testid="stFormSubmitButton"] {
            display: none;
        }
        </style>
        """, unsafe_allow_html=True)

    st.divider()
    st.subheader("Ringkasan Hasil")

    df = pd.DataFrame([{
        "ASIN": p["ASIN"],
        "Produk": p["title"][:80] if p["title"] else "-",
        "Harga": f"${p['price']:.2f}" if p["price"] else "N/A",
        "Rating": p["rating"] or 0,
        "Reviews": p["review_count"] or 0,
        "Prime": "✅" if p["is_prime"] else "❌",
    } for p in results])

    st.dataframe(df, width="stretch", hide_index=True)

    # Export CSV
    import io
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="⬇️ Download CSV",
        data=csv_buffer.getvalue(),
        file_name=f"search_{st.session_state.get('keyword', 'results')}.csv",
        mime="text/csv",
    )



session.close()