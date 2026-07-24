import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ---------------------------------------------------------
# Sayfa Konfigürasyonu
# ---------------------------------------------------------
st.set_page_config(
    page_title="Üretim Planlama & Kontrol Sistemi",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Özel CSS İle Arayüz Geliştirme
# ---------------------------------------------------------
st.markdown("""
    <style>
    .main {
        background-color: #f8fafc;
    }
    .kpi-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        border: 1px solid #e2e8f0;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .kpi-title {
        font-size: 14px;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 700;
        color: #0f172a;
        margin-top: 8px;
    }

    .header-banner {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 24px 32px;
        border-radius: 16px;
        color: white;
        margin-bottom: 28px;
        box-shadow: 0 10px 20px rgba(15, 23, 42, 0.15);
    }
    .header-banner h1 {
        margin: 0;
        font-size: 28px;
        font-weight: 700;
        color: #ffffff;
    }
    .header-banner p {
        margin-top: 6px;
        color: #94a3b8;
        font-size: 15px;
    }

    [data-testid="stSidebar"] {
        background-color: #0f172a;
    }
    [data-testid="stSidebar"] * {
        color: #f1f5f9 !important;
    }
    </style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Yardımcı Fonksiyonlar
# ---------------------------------------------------------
def safe_num(val):
    try:
        if pd.notnull(val) and str(val).strip() != "":
            return float(val)
    except ValueError:
        pass
    return 0.0


# ---------------------------------------------------------
# Sidebar / Yan Menü
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/factory.png", width=64)
    st.title("MRP II & ERP")
    st.caption("Üretim Planlama & Kontrol V2.0")
    st.markdown("---")

    selected_page = st.radio(
        "📌 Sayfa Seçimi",
        [
            "📊 Genel Bakış (Dashboard)",
            "📈 Talep Tahminleme",
            "🗓️ Ana Üretim Programı (MPS)",
            "📦 Malzeme İhtiyaç Planlama (MRP)",
            "⚙️ Çizelgeleme & İş Emirleri"
        ]
    )

    st.markdown("---")
    st.info("💡 **Bilgi:** Sistem tamamen boş veri yapısıyla çalışır. Girdiğiniz veriler canlı hesaplanır.")

# ---------------------------------------------------------
# SAYFA 1: GENEL BAKIŞ (DASHBOARD)
# ---------------------------------------------------------
if selected_page == "📊 Genel Bakış (Dashboard)":

    st.markdown("""
        <div class="header-banner">
            <h1>🏭 Üretim Kontrol & Yönetici Paneli</h1>
            <p>Siz dönem adı, planlanan ve gerçekleşen üretimi girin; Kapasite Kullanım Oranı ve grafikler otomatik hesaplansın.</p>
        </div>
    """, unsafe_allow_html=True)


    def get_clean_dash_df():
        return pd.DataFrame({
            "Dönem / Ay Adı": [""],
            "Planlanan Üretim (Kapasite)": [""],
            "Gerçekleşen Üretim": [""]
        })


    if "dash_df" not in st.session_state:
        st.session_state.dash_df = get_clean_dash_df()

    st.subheader("📝 Dönem Bazlı Üretim Veri Girişi")

    col_dash_btn1, col_dash_btn2 = st.columns([1, 4])
    with col_dash_btn1:
        if st.button("➕ Yeni Dönem / Ay Ekle"):
            new_dash_row = pd.DataFrame({
                "Dönem / Ay Adı": [""],
                "Planlanan Üretim (Kapasite)": [""],
                "Gerçekleşen Üretim": [""]
            })
            st.session_state.dash_df = pd.concat([st.session_state.dash_df, new_dash_row], ignore_index=True)
            st.rerun()

        if st.button("🗑️ Tabloyu Sıfırla"):
            st.session_state.dash_df = get_clean_dash_df()
            st.rerun()

    edited_dash = st.data_editor(
        st.session_state.dash_df,
        use_container_width=True,
        key="dash_editor"
    )
    st.session_state.dash_df = edited_dash

    valid_dash = edited_dash[
        (edited_dash["Dönem / Ay Adı"].astype(str).str.strip() != "") &
        (
                pd.to_numeric(edited_dash["Planlanan Üretim (Kapasite)"], errors='coerce').notnull() |
                pd.to_numeric(edited_dash["Gerçekleşen Üretim"], errors='coerce').notnull()
        )
        ]

    st.markdown("---")

    if valid_dash.empty:
        st.info(
            "📌 **Genel Bakış Paneli Beklemede:** Yukarıdaki tabloya istediğiniz dönem/ay isimlerini ve üretim miktarlarını giriniz.")
    else:
        computed_rows = []
        tot_actual = 0.0
        tot_planned = 0.0

        for idx, row in valid_dash.iterrows():
            period = row["Dönem / Ay Adı"]
            p_val = safe_num(row["Planlanan Üretim (Kapasite)"])
            a_val = safe_num(row["Gerçekleşen Üretim"])

            tot_planned += p_val
            tot_actual += a_val

            cap_rate = (a_val / p_val * 100) if p_val > 0 else 0.0

            computed_rows.append({
                "Dönem / Ay Adı": period,
                "Planlanan Üretim": int(p_val),
                "Gerçekleşen Üretim": int(a_val),
                "Hesaplanan Kapasite Kullanımı (%)": f"%{cap_rate:.1f}"
            })

        avg_overall_cap = (tot_actual / tot_planned * 100) if tot_planned > 0 else 0.0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Toplam Gerçekleşen Üretim</div>
                    <div class="kpi-value">{int(tot_actual):,} Adet</div>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Toplam Planlanan Kapasite</div>
                    <div class="kpi-value">{int(tot_planned):,} Adet</div>
                </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Genel Kapasite Kullanım Oranı</div>
                    <div class="kpi-value">%{avg_overall_cap:.1f}</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.subheader("📋 Hesaplanan Dönemsel Performans Tablosu")
        st.dataframe(pd.DataFrame(computed_rows), use_container_width=True, hide_index=True)

        fig_dash = go.Figure()
        fig_dash.add_trace(go.Bar(
            x=valid_dash["Dönem / Ay Adı"],
            y=[safe_num(x) for x in valid_dash["Planlanan Üretim (Kapasite)"]],
            name='Planlanan Kapasite',
            marker_color='#cbd5e1'
        ))
        fig_dash.add_trace(go.Bar(
            x=valid_dash["Dönem / Ay Adı"],
            y=[safe_num(x) for x in valid_dash["Gerçekleşen Üretim"]],
            name='Gerçekleşen Üretim',
            marker_color='#2563eb'
        ))
        fig_dash.update_layout(
            title="Dönem Bazlı Planlanan vs Gerçekleşen Üretim Grafiği",
            barmode='group',
            height=380,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_dash, use_container_width=True)

# ---------------------------------------------------------
# SAYFA 2: TALEP TAHMİNLEME
# ---------------------------------------------------------
elif selected_page == "📈 Talep Tahminleme":
    st.title("📈 Talep Tahminleme Modülü")
    st.caption("Verilerinizi ister Excel'den yükleyin, ister kopyalayıp yapıştırın, ister tablodan düzenleyin.")

    if "user_demand_list" not in st.session_state:
        st.session_state.user_demand_list = []

    col_f1, col_f2 = st.columns([1, 2])

    with col_f1:
        st.subheader("⚙️ Model Parametreleri")
        model_choice = st.selectbox(
            "Tahmin Modeli Seçin",
            [
                "Ağırlıklı Hareketli Ortalama (WMA)",
                "Basit Hareketli Ortalama (SMA)",
                "Tekli Üstel Düzleştirme (SES)",
                "Holt'un Trendli Üstel Düzleştirmesi",
                "Lineer Regresyon / Trend"
            ]
        )

        forecast_horizon = st.slider("Tahmin Ufku (Gelecek Periyot Sayısı)", 1, 12, 4)

        weights = []
        if model_choice == "Basit Hareketli Ortalama (SMA)":
            window_size = st.slider("Periyot Sayısı (N)", 2, 6, 3)

        elif model_choice == "Ağırlıklı Hareketli Ortalama (WMA)":
            window_size = st.slider("Periyot Sayısı (N)", 2, 4, 3)
            st.write("📐 **Periyot Ağırlıkları (t-1 En Son Dönemdir):**")

            w_inputs = []
            default_weight = float(round(1.0 / window_size, 2))

            for i in range(1, window_size + 1):
                w = st.number_input(
                    f"t-{i} Ağırlığı",
                    min_value=0.01,
                    max_value=1.00,
                    value=default_weight,
                    step=0.05
                )
                w_inputs.append(w)

            total_w = sum(w_inputs)
            weights = [w / total_w for w in w_inputs]
            st.caption(f"Normalize Ağırlıklar: {[round(w, 2) for w in weights]}")

        elif model_choice == "Tekli Üstel Düzleştirme (SES)":
            alpha = st.slider("Düzleştirme Katsayısı (α)", 0.01, 0.99, 0.30, step=0.05)

        elif model_choice == "Holt'un Trendli Üstel Düzleştirmesi":
            alpha = st.slider("Seviye Katsayısı (α)", 0.01, 0.99, 0.30, step=0.05)
            beta = st.slider("Trend Katsayısı (β)", 0.01, 0.99, 0.20, step=0.05)

        st.markdown("---")
        st.subheader("📊 Veri Giriş Yöntemi Seçin")

        input_method = st.radio(
            "Yöntem:",
            ["📂 Excel / CSV Dosyası Yükle", "📋 Metin Olarak Yapıştır", "✏️ Tablodan Düzenle"],
            horizontal=True
        )

        if input_method == "📂 Excel / CSV Dosyası Yükle":
            uploaded_file = st.file_uploader("Excel veya CSV dosyanızı buraya bırakın", type=["xlsx", "csv"])
            if uploaded_file is not None:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df_upload = pd.read_csv(uploaded_file)
                    else:
                        df_upload = pd.read_excel(uploaded_file)

                    numeric_cols = df_upload.select_dtypes(include=[np.number]).columns
                    if len(numeric_cols) > 0:
                        st.session_state.user_demand_list = df_upload[numeric_cols[0]].dropna().tolist()
                        st.success(f"✅ {len(st.session_state.user_demand_list)} adet talep verisi başarıyla yüklendi!")
                    else:
                        st.error("Dosyada sayısal sütun bulunamadı.")
                except Exception as e:
                    st.error(f"Dosya okuma hatası: {e}")

        elif input_method == "📋 Metin Olarak Yapıştır":
            pasted_text = st.text_area(
                "Sayıları aralarına virgül, boşluk veya yeni satır koyarak yapıştırın:",
                placeholder="Örn: 1200, 1250, 1100, 1380, 1420, 1500",
                height=120
            )
            if st.button("📥 Verileri Aktar"):
                if pasted_text.strip():
                    raw_vals = pasted_text.replace('\n', ' ').replace(',', ' ').split()
                    cleaned_vals = []
                    for v in raw_vals:
                        try:
                            cleaned_vals.append(float(v))
                        except ValueError:
                            pass
                    st.session_state.user_demand_list = cleaned_vals
                    st.success(f"✅ {len(cleaned_vals)} adet veri aktarıldı!")

        elif input_method == "✏️ Tablodan Düzenle":
            if not st.session_state.user_demand_list:
                current_df = pd.DataFrame({"Dönem": [f"Dönem {i}" for i in range(1, 13)], "Talep": [""] * 12})
            else:
                current_df = pd.DataFrame({
                    "Dönem": [f"Dönem {i + 1}" for i in range(len(st.session_state.user_demand_list))],
                    "Talep": st.session_state.user_demand_list
                })

            edited_table = st.data_editor(current_df, use_container_width=True)
            valid_rows = edited_table[pd.to_numeric(edited_table["Talep"], errors='coerce').notnull()]
            st.session_state.user_demand_list = [float(x) for x in valid_rows["Talep"].tolist()]

        if st.session_state.user_demand_list:
            if st.button("🗑️ Verileri Sıfırla"):
                st.session_state.user_demand_list = []
                st.rerun()

    with col_f2:
        hist_demand = st.session_state.user_demand_list
        n_hist = len(hist_demand)

        min_required = 4
        if model_choice in ["Basit Hareketli Ortalama (SMA)", "Ağırlıklı Hareketli Ortalama (WMA)"]:
            min_required = window_size + 1

        if n_hist < min_required:
            st.info(
                f"📌 **Hesaplama Yapılabilmesi İçin Veri Bekleniyor:**\nLütfen sol taraftan en az **{min_required} dönemlik** talep verisi yükleyin, yapıştırın veya girin.")
        else:
            forecast_values = []
            fitted_values = [None] * n_hist

            if model_choice == "Basit Hareketli Ortalama (SMA)":
                for i in range(window_size, n_hist):
                    fitted_values[i] = np.mean(hist_demand[i - window_size:i])
                last_val = np.mean(hist_demand[-window_size:])
                forecast_values = [last_val] * forecast_horizon

            elif model_choice == "Ağırlıklı Hareketli Ortalama (WMA)":
                for i in range(window_size, n_hist):
                    sub_data = hist_demand[i - window_size:i][::-1]
                    fitted_values[i] = sum(d * w for d, w in zip(sub_data, weights))

                last_sub = hist_demand[-window_size:][::-1]
                w_forecast = sum(d * w for d, w in zip(last_sub, weights))
                forecast_values = [w_forecast] * forecast_horizon

            elif model_choice == "Tekli Üstel Düzleştirme (SES)":
                fitted_values[0] = hist_demand[0]
                for i in range(1, n_hist):
                    fitted_values[i] = alpha * hist_demand[i - 1] + (1 - alpha) * fitted_values[i - 1]
                last_ses = alpha * hist_demand[-1] + (1 - alpha) * fitted_values[-1]
                forecast_values = [last_ses] * forecast_horizon

            elif model_choice == "Holt'un Trendli Üstel Düzleştirmesi":
                L = [hist_demand[0]]
                T = [hist_demand[1] - hist_demand[0]]
                fitted_values[0] = L[0]

                for i in range(1, n_hist):
                    prev_L = L[-1]
                    prev_T = T[-1]
                    val = hist_demand[i]

                    new_L = alpha * val + (1 - alpha) * (prev_L + prev_T)
                    new_T = beta * (new_L - prev_L) + (1 - beta) * prev_T

                    L.append(new_L)
                    T.append(new_T)
                    fitted_values[i] = prev_L + prev_T

                for k in range(1, forecast_horizon + 1):
                    forecast_values.append(L[-1] + k * T[-1])

            elif model_choice == "Lineer Regresyon / Trend":
                x = np.arange(1, n_hist + 1)
                y = np.array(hist_demand)
                slope, intercept = np.polyfit(x, y, 1)

                for i in range(n_hist):
                    fitted_values[i] = intercept + slope * (i + 1)
                for h in range(1, forecast_horizon + 1):
                    forecast_values.append(intercept + slope * (n_hist + h))

            labels_hist = [f"Dönem {i + 1}" for i in range(n_hist)]
            labels_fore = [f"Gelecek {i}" for i in range(1, forecast_horizon + 1)]

            df_plot_hist = pd.DataFrame({
                "Dönem": labels_hist,
                "Girilen Talep": hist_demand,
                "Model Uyum": fitted_values
            })

            df_plot_fore = pd.DataFrame({
                "Dönem": labels_fore,
                "Tahmin": forecast_values
            })

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_plot_hist["Dönem"], y=df_plot_hist["Girilen Talep"], mode='lines+markers',
                                     name='Girilen Talep', line=dict(color='#1e293b', width=2)))
            fig.add_trace(go.Scatter(x=df_plot_hist["Dönem"], y=df_plot_hist["Model Uyum"], mode='lines',
                                     name='Model Oturumu (Fitted)', line=dict(color='#f59e0b', dash='dash')))
            fig.add_trace(go.Scatter(x=df_plot_fore["Dönem"], y=df_plot_fore["Tahmin"], mode='lines+markers',
                                     name='Gelecek Tahmini', line=dict(color='#2563eb', width=3)))

            fig.update_layout(
                title=f"{model_choice} - Hesaplanan Talep & Tahmin Analizi",
                xaxis_title="Dönem",
                yaxis_title="Miktar (Adet)",
                height=420,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)

            valid_pairs = [(y_act, y_fit) for y_act, y_fit in zip(hist_demand, fitted_values) if y_fit is not None]
            if valid_pairs:
                errors = [abs(y_act - y_fit) for y_act, y_fit in valid_pairs]
                mape_list = [abs(y_act - y_fit) / y_act for y_act, y_fit in valid_pairs if y_act != 0]

                mad = np.mean(errors)
                mse = np.mean([e ** 2 for e in errors])
                mape = np.mean(mape_list) * 100 if mape_list else 0

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Ortalama Mutlak Sapma (MAD)", f"{mad:.1f}")
                m2.metric("Ortalama Karesel Hata (MSE)", f"{mse:.0f}")
                m3.metric("Yüzde Hata (MAPE)", f"%{mape:.2f}")
                m4.metric("İlk Gelecek Dönem Tahmini", f"{forecast_values[0]:.0f} Adet")

# ---------------------------------------------------------
# SAYFA 3: ANA ÜRETİM PROGRAMI (MPS)
# ---------------------------------------------------------
elif selected_page == "🗓️ Ana Üretim Programı (MPS)":
    st.title("🗓️ Ana Üretim Programı (MPS)")
    st.caption("Ürün adlarını, stok ve haftalık talepleri doğrudan boş tabloya yazabilirsiniz.")


    def get_clean_mps_df():
        return pd.DataFrame({
            "Ürün Adı": [""],
            "Mevcut Stok": [""],
            "Hafta 1": [""],
            "Hafta 2": [""],
            "Hafta 3": [""],
            "Hafta 4": [""]
        })


    if "mps_df" not in st.session_state:
        st.session_state.mps_df = get_clean_mps_df()

    col_mps1, col_mps2 = st.columns([1, 2])

    with col_mps1:
        st.subheader("🛠️ MPS Veri Girişi ve İşlemleri")
        st.caption("Tablodaki tüm hücreler tamamen boş gelir. Kendi ürünlerinizi ve verilerinizi yazabilirsiniz.")

        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("➕ Yeni Ürün Satırı Ekle"):
                new_row = pd.DataFrame({
                    "Ürün Adı": [""],
                    "Mevcut Stok": [""],
                    "Hafta 1": [""], "Hafta 2": [""], "Hafta 3": [""], "Hafta 4": [""]
                })
                st.session_state.mps_df = pd.concat([st.session_state.mps_df, new_row], ignore_index=True)
                st.rerun()

        with c_btn2:
            if st.button("🗑️ Tabloyu Temizle"):
                st.session_state.mps_df = get_clean_mps_df()
                st.rerun()

    edited_mps = st.data_editor(
        st.session_state.mps_df,
        use_container_width=True,
        key="mps_editor"
    )
    st.session_state.mps_df = edited_mps

    valid_mps = edited_mps[edited_mps["Ürün Adı"].astype(str).str.strip() != ""]

    st.markdown("---")
    st.subheader("📊 Hesaplanan Otomatik Üretim Planı (Net İhtiyaçlar)")

    if valid_mps.empty:
        st.info(
            "📌 **MPS Hesaplaması Beklemede:** Yukarıdaki tabloya ürün adı ve haftalık talep/stok verilerinizi giriniz.")
    else:
        calc_rows = []
        for idx, row in valid_mps.iterrows():
            product = str(row["Ürün Adı"])
            inv = safe_num(row["Mevcut Stok"])

            w1_req = safe_num(row["Hafta 1"])
            w2_req = safe_num(row["Hafta 2"])
            w3_req = safe_num(row["Hafta 3"])
            w4_req = safe_num(row["Hafta 4"])

            p1 = max(0.0, w1_req - inv)
            inv_after_1 = max(0.0, inv - w1_req)

            p2 = max(0.0, w2_req - inv_after_1)
            inv_after_2 = max(0.0, inv_after_1 - w2_req)

            p3 = max(0.0, w3_req - inv_after_2)
            inv_after_3 = max(0.0, inv_after_2 - w3_req)

            p4 = max(0.0, w4_req - inv_after_3)

            calc_rows.append({
                "Ürün Adı": product,
                "Başlangıç Stoğu": int(inv),
                "Hafta 1 Üretim Emri": int(p1),
                "Hafta 2 Üretim Emri": int(p2),
                "Hafta 3 Üretim Emri": int(p3),
                "Hafta 4 Üretim Emri": int(p4),
                "Aylık Toplam Net Üretim": int(p1 + p2 + p3 + p4)
            })

        df_calc_mps = pd.DataFrame(calc_rows)
        st.dataframe(df_calc_mps, use_container_width=True, hide_index=True)
        st.success("✅ Üretim gereksinimleri girdiğiniz MPS verilerine göre anlık olarak hesaplanmaktadır.")

# ---------------------------------------------------------
# SAYFA 4: MALZEME İHTİYAÇ PLANLAMA (MRP)
# ---------------------------------------------------------
elif selected_page == "📦 Malzeme İhtiyaç Planlama (MRP)":
    st.title("📦 Malzeme İhtiyaç Planlama (MRP)")
    st.caption("Kendi malzeme kodlarınızı, parçalarınızı ve temin sürelerinizi sıfırdan girip MRP hesaplatın.")

    tab1, tab2 = st.tabs(["📋 Ürün Ağacı (BOM) Tanımlama", "🔄 MRP Hesaplama Engine"])

    with tab1:
        st.subheader("🛠️ Ürün Ağacı (Bill of Materials) Oluşturun")


        def get_clean_bom_df():
            return pd.DataFrame({
                "Malzeme Kodu": [""],
                "Malzeme Adı": [""],
                "Bileşen Katsayısı (Adet)": [""],
                "Temin Süresi (Hafta)": [""]
            })


        if "bom_df" not in st.session_state:
            st.session_state.bom_df = get_clean_bom_df()

        col_bom1, col_bom2 = st.columns([1, 3])
        with col_bom1:
            if st.button("➕ Alt Parça Satırı Ekle"):
                new_bom_row = pd.DataFrame({
                    "Malzeme Kodu": [""],
                    "Malzeme Adı": [""],
                    "Bileşen Katsayısı (Adet)": [""],
                    "Temin Süresi (Hafta)": [""]
                })
                st.session_state.bom_df = pd.concat([st.session_state.bom_df, new_bom_row], ignore_index=True)
                st.rerun()

            if st.button("🗑️ BOM Tablosunu Temizle"):
                st.session_state.bom_df = get_clean_bom_df()
                st.rerun()

        edited_bom = st.data_editor(
            st.session_state.bom_df,
            use_container_width=True,
            key="bom_editor"
        )
        st.session_state.bom_df = edited_bom

    with tab2:
        st.subheader("📊 Net İhtiyaç ve Satınalma / Üretim Planı")


        def get_clean_mrp_input_df():
            valid_bom = st.session_state.bom_df[
                (st.session_state.bom_df["Malzeme Kodu"].astype(str).str.strip() != "") |
                (st.session_state.bom_df["Malzeme Adı"].astype(str).str.strip() != "")
                ]
            if not valid_bom.empty:
                codes = valid_bom["Malzeme Kodu"].tolist()
                names = valid_bom["Malzeme Adı"].tolist()
            else:
                codes = [""]
                names = [""]

            return pd.DataFrame({
                "Malzeme Kodu": codes,
                "Malzeme Adı": names,
                "Brüt İhtiyaç": [""] * len(codes),
                "Mevcut Stok": [""] * len(codes),
                "Emniyet Stoğu": [""] * len(codes)
            })


        if "mrp_input_df" not in st.session_state:
            st.session_state.mrp_input_df = get_clean_mrp_input_df()

        st.caption("✍️ Brüt ihtiyaç, mevcut stok ve emniyet stoğu değerlerini giriniz:")

        col_mrp1, col_mrp2 = st.columns([1, 3])
        with col_mrp1:
            if st.button("🔄 BOM Listesini MRP Tablosuna Senkronize Et"):
                st.session_state.mrp_input_df = get_clean_mrp_input_df()
                st.rerun()

            if st.button("🗑️ Girişleri Temizle"):
                st.session_state.mrp_input_df = get_clean_mrp_input_df()
                st.rerun()

        edited_mrp_input = st.data_editor(
            st.session_state.mrp_input_df,
            use_container_width=True,
            key="mrp_input_editor"
        )
        st.session_state.mrp_input_df = edited_mrp_input

        valid_mrp = edited_mrp_input[
            (edited_mrp_input["Malzeme Kodu"].astype(str).str.strip() != "") |
            (edited_mrp_input["Malzeme Adı"].astype(str).str.strip() != "")
            ]

        st.markdown("---")

        if valid_mrp.empty:
            st.info(
                "📌 **MRP Hesaplaması Beklemede:** Lütfen yukarıdaki tabloya malzeme detaylarınızı ve ihtiyaç rakamlarınızı giriniz.")
        else:
            mrp_results_rows = []
            today = datetime.now()

            for idx, row in valid_mrp.iterrows():
                m_code = str(row["Malzeme Kodu"]) if str(row["Malzeme Kodu"]).strip() != "" else f"M00{idx + 1}"
                m_name = str(row["Malzeme Adı"]) if str(row["Malzeme Adı"]).strip() != "" else f"Malzeme {idx + 1}"

                gross_req = safe_num(row["Brüt İhtiyaç"])
                inv = safe_num(row["Mevcut Stok"])
                safety_stock = safe_num(row["Emniyet Stoğu"])

                net_req = max(0.0, (gross_req + safety_stock) - inv)

                lead_time = 1
                bom_match = st.session_state.bom_df[st.session_state.bom_df["Malzeme Kodu"] == m_code]
                if not bom_match.empty:
                    lt_val = safe_num(bom_match["Temin Süresi (Hafta)"].values[0])
                    if lt_val > 0:
                        lead_time = int(lt_val)

                release_date = today - timedelta(weeks=lead_time)

                mrp_results_rows.append({
                    "Malzeme Kodu": m_code,
                    "Malzeme Adı": m_name,
                    "Brüt İhtiyaç": int(gross_req),
                    "Mevcut Stok": int(inv),
                    "Emniyet Stoğu": int(safety_stock),
                    "Net İhtiyaç (Sipariş Miktarı)": int(net_req),
                    "Temin Süresi": f"{lead_time} Hafta",
                    "Tavsiye Edilen Sipariş Tarihi": release_date.strftime("%Y-%m-%d") if net_req > 0 else "Gerek Yok"
                })

            df_mrp_results = pd.DataFrame(mrp_results_rows)
            st.subheader("📋 Hesaplanan MRP Sipariş ve İhtiyaç Çıktısı")
            st.dataframe(df_mrp_results, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# SAYFA 5: ÇİZELGELEME & İŞ EMİRLERİ
# ---------------------------------------------------------
elif selected_page == "⚙️ Çizelgeleme & İş Emirleri":
    st.title("⚙️ Tezgah & İstasyon Çizelgeleme")
    st.caption("İş emri detaylarını ve saatleri/zaman aralıklarını doğrudan boş tabloya yazabilirsiniz.")


    def get_clean_gantt_df():
        return pd.DataFrame({
            "İş Emri Adı": [""],
            "Makine / İstasyon": [""],
            "Başlangıç Saati": [""],
            "Bitiş Saati": [""]
        })


    if "gantt_df" not in st.session_state:
        st.session_state.gantt_df = get_clean_gantt_df()

    st.subheader("📝 İş Emri ve Tezgah Çizelgesi Veri Girişi")

    col_g1, col_g2 = st.columns([1, 4])
    with col_g1:
        if st.button("➕ İş Emri Ekle"):
            new_g_row = pd.DataFrame({
                "İş Emri Adı": [""],
                "Makine / İstasyon": [""],
                "Başlangıç Saati": [""],
                "Bitiş Saati": [""]
            })
            st.session_state.gantt_df = pd.concat([st.session_state.gantt_df, new_g_row], ignore_index=True)
            st.rerun()

        if st.button("🗑️ Çizelgeyi Temizle"):
            st.session_state.gantt_df = get_clean_gantt_df()
            st.rerun()

    edited_gantt = st.data_editor(
        st.session_state.gantt_df,
        use_container_width=True,
        key="gantt_editor"
    )
    st.session_state.gantt_df = edited_gantt

    valid_gantt = edited_gantt[
        (edited_gantt["İş Emri Adı"].astype(str).str.strip() != "") &
        (edited_gantt["Makine / İstasyon"].astype(str).str.strip() != "")
        ]

    st.markdown("---")

    if valid_gantt.empty:
        st.info(
            "📌 **Çizelgeleme Beklemede:** Yukarıdaki tabloya iş emri adı, makine/istasyon ve başlangıç/bitiş zaman verilerinizi giriniz.")
    else:
        gantt_plot_data = []
        base_date = datetime.now().strftime("%Y-%m-%d")

        for idx, row in valid_gantt.iterrows():
            task = str(row["İş Emri Adı"])
            resource = str(row["Makine / İstasyon"])
            s_time = str(row["Başlangıç Saati"]).strip() if str(row["Başlangıç Saati"]).strip() != "" else "08:00"
            e_time = str(row["Bitiş Saati"]).strip() if str(row["Bitiş Saati"]).strip() != "" else "12:00"

            gantt_plot_data.append(dict(
                Task=task,
                Start=f"{base_date} {s_time}",
                Finish=f"{base_date} {e_time}",
                Resource=resource
            ))

        df_gantt_plot = pd.DataFrame(gantt_plot_data)

        fig_gantt = px.timeline(
            df_gantt_plot,
            x_start="Start",
            x_end="Finish",
            y="Resource",
            color="Task",
            title="Dinamik Tezgah & Makine Yükleme Planı (Gantt Şeması)"
        )
        fig_gantt.update_yaxes(autorange="reversed")
        fig_gantt.update_layout(height=420, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

        st.plotly_chart(fig_gantt, use_container_width=True)