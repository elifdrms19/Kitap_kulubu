import pandas as pd
import pulp


def solve_chase_strategy(demand, days, worker_capacity, initial_workers, costs):
    """
    Sıfır Envanter (Chase) Stratejisi - Ders Notu Slayt 5
    Talebe göre tam olarak işçi sayısı ayarlanır, envanter tutulmaz.
    """
    T = len(demand)
    workers_needed = []
    hired = []
    fired = []
    current_w = initial_workers

    for t in range(T):
        req_w = round(demand[t] / (days[t] * worker_capacity))
        workers_needed.append(req_w)

        if req_w > current_w:
            hired.append(req_w - current_w)
            fired.append(0)
        else:
            hired.append(0)
            fired.append(current_w - req_w)
        current_w = req_w

    df = pd.DataFrame(
        {
            "Dönem": range(1, T + 1),
            "Talep": demand,
            "Çalışılan Gün": days,
            "Gereken İşçi": workers_needed,
            "İşe Alınan": hired,
            "İşten Çıkarılan": fired,
            "Üretim": demand,  # Sıfır envanterde üretim talebe eşittir
            "Envanter": [0] * T,
        }
    )

    # Maliyet Hesaplama
    total_hire_cost = sum(hired) * costs["hire"]
    total_fire_cost = sum(fired) * costs["fire"]
    total_labor_cost = sum(
        df["Gereken İşçi"] * days * worker_capacity * costs["labor_per_unit"]
    )
    total_cost = total_hire_cost + total_fire_cost + total_labor_cost

    return df, total_cost


def solve_level_strategy(demand, days, worker_capacity, initial_workers, costs):
    """
    Seviyelendirilmiş / Sabit İşgücü (Level) Stratejisi - Ders Notu Slayt 5
    Sabit sayıda işçi çalıştırılır, talep farkları envanter/gecikme ile telafi edilir.
    """
    T = len(demand)
    total_demand = sum(demand)
    total_days = sum(days)

    # Ortalama sabit işçi sayısı
    fixed_workers = round(total_demand / (total_days * worker_capacity))

    hired = max(0, fixed_workers - initial_workers)
    fired = max(0, initial_workers - fixed_workers)

    inventory = 0
    inv_list = []
    prod_list = []

    for t in range(T):
        prod = fixed_workers * days[t] * worker_capacity
        prod_list.append(prod)
        inventory = inventory + prod - demand[t]
        inv_list.append(inventory)

    df = pd.DataFrame(
        {
            "Dönem": range(1, T + 1),
            "Talep": demand,
            "Çalıştırılan İşçi": [fixed_workers] * T,
            "Üretim": prod_list,
            "Dönem Sonu Envanter": inv_list,
        }
    )

    # Maliyet Hesabı
    holding_cost = (
        sum([i for i in inv_list if i > 0]) * costs["holding"]
    )  # Stok tutma
    backorder_cost = (
        sum([-i for i in inv_list if i < 0]) * costs["backorder"]
    )  # Geciktirme
    labor_cost = (
        fixed_workers * total_days * worker_capacity * costs["labor_per_unit"]
    )
    hire_fire_cost = (hired * costs["hire"]) + (fired * costs["fire"])

    total_cost = holding_cost + backorder_cost + labor_cost + hire_fire_cost
    return df, total_cost


def solve_lp_optimum(demand, days, worker_capacity, initial_workers, costs):
    """
    Lineer Programlama (PuLP Optimizasyonu) - Ders Notu Slayt 3
    Toplam maliyeti en küçükleyen küresel optimum çözümü bulur.
    """
    T = len(demand)
    model = pulp.LpProblem("Toplu_Uretim_Planlama", pulp.LpMinimize)

    # Değişkenler
    P = {t: pulp.LpVariable(f"P_{t}", lowBound=0) for t in range(T)}
    W = {t: pulp.LpVariable(f"W_{t}", lowBound=0) for t in range(T)}
    H = {t: pulp.LpVariable(f"H_{t}", lowBound=0) for t in range(T)}
    L = {t: pulp.LpVariable(f"L_{t}", lowBound=0) for t in range(T)}
    I = {t: pulp.LpVariable(f"I_{t}", lowBound=0) for t in range(T)}

    # Amaç Fonksiyonu
    model += pulp.lpSum(
        [
            costs["labor_per_unit"] * P[t]
            + costs["hire"] * H[t]
            + costs["fire"] * L[t]
            + costs["holding"] * I[t]
            for t in range(T)
        ]
    )

    # Kısıtlar (Slayt 3 Formülleri)
    for t in range(T):
        # Üretim Kapasitesi Kısıtı: P_t <= n_t * W_t
        model += P[t] <= days[t] * worker_capacity * W[t]

        # İşgücü Denge Kısıtı: W_t = W_{t-1} + H_t - L_t
        prev_W = initial_workers if t == 0 else W[t - 1]
        model += W[t] == prev_W + H[t] - L[t]

        # Envanter Denge Kısıtı: I_t = I_{t-1} + P_t - D_t
        prev_I = 0 if t == 0 else I[t - 1]
        model += I[t] == prev_I + P[t] - demand[t]

    model.solve(pulp.PULP_CBC_CMD(msg=False))

    results = []
    for t in range(T):
        results.append(
            {
                "Dönem": t + 1,
                "Talep": demand[t],
                "Üretim (P)": round(P[t].varValue, 1),
                "İşçi (W)": round(W[t].varValue, 1),
                "İşe Alınan (H)": round(H[t].varValue, 1),
                "İşten Çıkarılan (L)": round(L[t].varValue, 1),
                "Envanter (I)": round(I[t].varValue, 1),
            }
        )

    return pd.DataFrame(results), pulp.value(model.objective)