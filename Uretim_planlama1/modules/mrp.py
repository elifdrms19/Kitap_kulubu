import numpy as np
import pandas as pd


class DynamicMRPProcessor:

    def __init__(self, bom_structure, item_master, costs=None):
        self.bom_structure = bom_structure
        self.item_master = item_master
        self.costs = costs or {"setup": 100.0, "holding": 2.0}

    def wagner_whitin(self, net_requirements):
        """
        Wagner-Whitin Dinamik Programlama Algoritması
        Toplam maliyeti (S + H) küresel olarak minimize eden optimal parti büyüklüklerini hesaplar.
        """
        N = len(net_requirements)
        if N == 0 or sum(net_requirements) == 0:
            return [0.0] * N

        S = self.costs["setup"]
        H = self.costs["holding"]

        # f[j]: j. döneme kadarki minimum toplam maliyet (1-indexed)
        f = [0.0] * (N + 1)
        # last_order[j]: j. döneme kadarki optimal son sipariş dönemi
        last_order = [0] * (N + 1)

        for j in range(1, N + 1):
            min_cost = float("inf")
            best_i = 1

            for i in range(1, j + 1):
                # i. dönemde sipariş verip i'den j'ye kadarki ihtiyaçları karşılama maliyeti
                holding_cost = sum(
                    net_requirements[k - 1] * (k - i) * H
                    for k in range(i, j + 1)
                )
                cost = f[i - 1] + S + holding_cost

                if cost < min_cost:
                    min_cost = cost
                    best_i = i

            f[j] = min_cost
            last_order[j] = best_i

        # Geriye doğru takip ederek sipariş miktarlarını belirleme
        order_quantities = [0.0] * N
        j = N
        while j > 0:
            i = last_order[j]
            qty = sum(net_requirements[i - 1 : j])
            order_quantities[i - 1] = qty
            j = i - 1

        return order_quantities

    def calculate_lot_size(
        self, method, net_requirements, current_week, lot_param, total_weeks
    ):
        needed = net_requirements[current_week]
        if needed <= 0:
            return 0.0

        S = self.costs["setup"]
        H = self.costs["holding"]

        # 1. L4L
        if method == "L4L":
            return needed

        # 2. Fixed Lot Size
        elif method == "Fixed Lot":
            lot_size = max(1.0, float(lot_param))
            return np.ceil(needed / lot_size) * lot_size

        # 3. EOQ
        elif method == "EOQ":
            avg_demand = (
                np.mean([r for r in net_requirements if r > 0])
                if any(r > 0 for r in net_requirements)
                else 100
            )
            eoq = np.sqrt((2 * avg_demand * 52 * S) / H)
            return max(needed, round(eoq, -1))

        # 4. POQ
        elif method == "POQ":
            avg_demand = (
                np.mean([r for r in net_requirements if r > 0])
                if any(r > 0 for r in net_requirements)
                else 100
            )
            eoq = np.sqrt((2 * avg_demand * 52 * S) / H)
            p_period = (
                max(1, int(round(eoq / avg_demand))) if avg_demand > 0 else 1
            )
            end_w = min(current_week + p_period, total_weeks)
            return sum(net_requirements[current_week:end_w])

        # 5. LUC
        elif method == "LUC":
            best_qty = needed
            min_unit_cost = float("inf")
            cum_qty, cum_holding = 0, 0

            for k in range(current_week, total_weeks):
                req_k = net_requirements[k]
                cum_qty += req_k
                cum_holding += req_k * (k - current_week) * H
                total_cost = S + cum_holding
                unit_cost = (
                    total_cost / cum_qty if cum_qty > 0 else float("inf")
                )

                if unit_cost <= min_unit_cost:
                    min_unit_cost = unit_cost
                    best_qty = cum_qty
                else:
                    break
            return best_qty

        # 6. LTC / PPB
        elif method in ["LTC", "PPB"]:
            best_qty = needed
            min_diff = float("inf")
            cum_qty, cum_holding = 0, 0

            for k in range(current_week, total_weeks):
                req_k = net_requirements[k]
                cum_qty += req_k
                cum_holding += req_k * (k - current_week) * H
                diff = abs(S - cum_holding)

                if diff <= min_diff:
                    min_diff = diff
                    best_qty = cum_qty
                else:
                    break
            return best_qty

        return needed

    def run_mrp(self, parent_item, gross_requirements):
        num_weeks = len(gross_requirements)
        weeks = [f"Hafta {i+1}" for i in range(num_weeks)]

        mrp_results = {}
        planned_releases = {}

        items_order = list(self.item_master.keys())

        for item in items_order:
            meta = self.item_master.get(
                item, {"lt": 1, "stock": 0, "method": "L4L", "param": 0}
            )
            lt = int(meta["lt"])
            stock = float(meta["stock"])
            method = meta.get("method", "L4L")
            lot_param = float(meta.get("param", 0))

            gross_req = [0.0] * num_weeks

            if item == parent_item:
                gross_req = [float(x) for x in gross_requirements]
            else:
                parents = self.bom_structure.get(item, [])
                for p_name, qty_per in parents:
                    if p_name in planned_releases:
                        p_releases = planned_releases[p_name]
                        for w in range(num_weeks):
                            gross_req[w] += p_releases[w] * qty_per

            # Ön Net İhtiyaç Tespiti
            temp_stock = stock
            temp_net = [0.0] * num_weeks
            for w in range(num_weeks):
                if temp_stock >= gross_req[w]:
                    temp_stock -= gross_req[w]
                else:
                    temp_net[w] = gross_req[w] - temp_stock
                    temp_stock = 0.0

            on_hand = [0.0] * num_weeks
            net_req = [0.0] * num_weeks
            planned_receipts = [0.0] * num_weeks
            planned_order_release = [0.0] * num_weeks

            # --- Wagner-Whitin Özel Çözümü ---
            if method == "Wagner-Whitin":
                ww_orders = self.wagner_whitin(temp_net)
                curr_stock = stock
                for w in range(num_weeks):
                    order_qty = ww_orders[w]
                    needed = (
                        max(0.0, gross_req[w] - curr_stock)
                        if curr_stock < gross_req[w]
                        else 0.0
                    )
                    net_req[w] = needed

                    planned_receipts[w] = order_qty
                    curr_stock = (curr_stock + order_qty) - gross_req[w]
                    on_hand[w] = max(0.0, curr_stock)

                    release_week = w - lt
                    if release_week >= 0:
                        planned_order_release[release_week] = order_qty

            else:
                # Diğer Sezgisel (Heuristic) Yöntemler
                curr_stock = stock
                for w in range(num_weeks):
                    if curr_stock >= gross_req[w]:
                        curr_stock -= gross_req[w]
                        on_hand[w] = curr_stock
                    else:
                        needed = gross_req[w] - curr_stock
                        net_req[w] = needed

                        order_qty = self.calculate_lot_size(
                            method, temp_net, w, lot_param, num_weeks
                        )
                        order_qty = max(order_qty, needed)

                        planned_receipts[w] = order_qty
                        curr_stock = (curr_stock + order_qty) - gross_req[w]
                        on_hand[w] = curr_stock

                        release_week = w - lt
                        if release_week >= 0:
                            planned_order_release[release_week] = order_qty

            planned_releases[item] = planned_order_release

            df_item = pd.DataFrame(
                {
                    "Metrik": [
                        "Brüt İhtiyaç",
                        "Hazır Envanter",
                        "Net İhtiyaç",
                        "Planlı Sipariş Alındısı",
                        "Planlı Sipariş Salımı (Çıkış)",
                    ],
                }
            )
            for w in range(num_weeks):
                df_item[weeks[w]] = [
                    gross_req[w],
                    on_hand[w],
                    net_req[w],
                    planned_receipts[w],
                    planned_order_release[w],
                ]

            mrp_results[item] = df_item

        return mrp_results