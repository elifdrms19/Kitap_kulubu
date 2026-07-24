import pandas as pd
import numpy as np


def calculate_mps_and_atp(periods, forecast, orders, initial_inventory, lot_size):
    """
    Ana Üretim Programı (MPS) ve Satışa Hazır Miktar (ATP) Hesabı - Ders Notu Slayt 4
    """
    n = len(periods)

    inventory = [0] * n
    mps = [0] * n
    atp = [0] * n

    current_inv = initial_inventory

    for t in range(n):
        # O dönem için beklenen maksimum talep (Sipariş ya da Tahmin'den büyük olanı)
        demand = max(forecast[t], orders[t])

        # Projeksiyon stok hesabı
        proj_inv = current_inv - demand

        # Stok eksiye düşüyorsa MPS sipariş açar
        if proj_inv < 0:
            # Parti büyüklüğüne (Lot size) göre gerekli MPS miktarı
            needed_lots = int(np.ceil(abs(proj_inv) / lot_size))
            mps_quantity = needed_lots * lot_size
        else:
            mps_quantity = 0

        mps[t] = mps_quantity
        current_inv = current_inv + mps_quantity - demand
        inventory[t] = current_inv

    # ATP (Available-to-Promise) Hesabı
    # Slayt 4: ATP, bir sonraki MPS verilen döneme kadarki kesinleşmiş siparişler düşülerek bulunur.
    for t in range(n):
        if t == 0:
            # İlk dönem için: (Başlangıç Stoğu + MPS) - (Sonraki MPS'e kadarki Toplam Siparişler)
            # Sonraki MPS dönemini bul
            next_mps_indices = [i for i in range(1, n) if mps[i] > 0]
            next_mps_t = next_mps_indices[0] if next_mps_indices else n

            sum_orders = sum(orders[0:next_mps_t])
            atp[t] = (initial_inventory + mps[0]) - sum_orders
        elif mps[t] > 0:
            # Sonraki MPS dönemini bul
            next_mps_indices = [i for i in range(t + 1, n) if mps[i] > 0]
            next_mps_t = next_mps_indices[0] if next_mps_indices else n

            sum_orders = sum(orders[t:next_mps_t])
            atp[t] = mps[t] - sum_orders
        else:
            atp[t] = 0

    df_mps = pd.DataFrame({
        "Hafta / Dönem": periods,
        "Talep Tahmini": forecast,
        "Müşteri Siparişleri": orders,
        "Projeksiyon Envanter": inventory,
        "MPS (Planlanan Üretim)": mps,
        "ATP (Satışa Hazır Miktar)": atp
    })

    return df_mps