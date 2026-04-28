import streamlit as st
import pandas as pd
from database.queries import get_session, get_price_alerts

st.set_page_config(page_title="Price Alerts", layout="wide")
st.title("🚨 Price Alerts")
st.caption("Produk kompetitor yang harganya turun signifikan")

session = get_session()

# ─── Threshold slider ─────────────────────────────────────────────────────────
threshold = st.slider(
    "Minimum penurunan harga (%)",
    min_value=1,
    max_value=50,
    value=5,
    step=1,
    help="Hanya tampilkan produk yang harganya turun lebih dari nilai ini"
)

# ─── Alert table ─────────────────────────────────────────────────────────────
alerts = get_price_alerts(session, threshold_pct=threshold)

if not alerts:
    st.success(f"Tidak ada produk yang harganya turun lebih dari {threshold}% saat ini.")
else:
    st.warning(f"Ditemukan {len(alerts)} alert!")

    rows = []
    for row in alerts:
        drop_pct = (row.prev_price - row.price) / row.prev_price * 100
        rows.append({
            "ASIN": row.asin,
            "Produk": row.title[:60],
            "Brand": row.brand or "-",
            "Harga Sekarang": f"${row.price:.2f}",
            "Harga Sebelumnya": f"${row.prev_price:.2f}",
            "Turun": f"{drop_pct:.1f}%",
            "Waktu": row.scraped_at,
        })

    df = pd.DataFrame(rows)

    # Highlight baris dengan penurunan terbesar
    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        column_config={
            "Turun": st.column_config.TextColumn(
                "Turun",
                help="Persentase penurunan harga"
            ),
            "Waktu": st.column_config.DatetimeColumn(
                "Waktu",
                format="DD/MM/YYYY HH:mm"
            )
        }
    )

    # Export CSV
    import io
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="⬇️ Download Alert CSV",
        data=csv_buffer.getvalue(),
        file_name="price_alerts.csv",
        mime="text/csv",
    )

session.close()