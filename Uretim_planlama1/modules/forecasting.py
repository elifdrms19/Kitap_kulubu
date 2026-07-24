import numpy as np
import pandas as pd


def calculate_metrics(actual, forecast):
    """MAD, MSE ve MAPE hata kriterlerini hesaplar."""
    actual = np.array(actual, dtype=float)
    forecast = np.array(forecast, dtype=float)

    valid_mask = ~np.isnan(actual) & ~np.isnan(forecast)
    act = actual[valid_mask]
    frc = forecast[valid_mask]

    n = len(act)
    if n == 0:
        return {"MAD": np.nan, "MSE": np.nan, "MAPE": np.nan}

    errors = act - frc
    mad = np.mean(np.abs(errors))
    mse = np.sum(errors**2) / (n - 1) if n > 1 else np.mean(errors**2)
    mape = np.mean(np.abs(errors / act)) * 100

    return {"MAD": round(mad, 2), "MSE": round(mse, 2), "MAPE": round(mape, 2)}


class DemandForecaster:

    def __init__(self, data):
        """Kullanıcıdan gelen dinamik talep listesi/dizisi."""
        self.data = np.array(data, dtype=float)
        self.n = len(data)

    def moving_average(self, period=3):
        forecasts = [np.nan] * self.n
        for t in range(period, self.n):
            forecasts[t] = np.mean(self.data[t - period : t])
        metrics = calculate_metrics(self.data[period:], forecasts[period:])
        return forecasts, metrics

    def weighted_moving_average(self, weights=[0.2, 0.3, 0.5]):
        weights = np.array(weights)
        period = len(weights)
        forecasts = [np.nan] * self.n
        for t in range(period, self.n):
            forecasts[t] = np.sum(self.data[t - period : t] * weights)
        metrics = calculate_metrics(self.data[period:], forecasts[period:])
        return forecasts, metrics

    def simple_exponential_smoothing(self, alpha=0.5):
        forecasts = [np.nan] * self.n
        forecasts[0] = self.data[0]
        for t in range(1, self.n):
            forecasts[t] = forecasts[t - 1] + alpha * (
                self.data[t - 1] - forecasts[t - 1]
            )
        metrics = calculate_metrics(self.data, forecasts)
        return forecasts, metrics

    def linear_regression(self):
        x = np.arange(1, self.n + 1)
        y = self.data
        x_mean, y_mean = np.mean(x), np.mean(y)

        b = (np.sum(x * y) - self.n * x_mean * y_mean) / (
            np.sum(x**2) - self.n * (x_mean**2)
        )
        a = y_mean - b * x_mean

        forecasts = a + b * x
        metrics = calculate_metrics(y, forecasts)
        return forecasts, metrics, a, b

    def holt_exponential_smoothing(self, alpha=0.3, beta=0.1):
        _, _, a0, b0 = self.linear_regression()
        a = [0.0] * self.n
        b = [0.0] * self.n
        forecasts = [np.nan] * self.n

        a[0] = alpha * self.data[0] + (1 - alpha) * (a0 + b0)
        b[0] = beta * (a[0] - a0) + (1 - beta) * b0
        forecasts[0] = a0 + b0

        for t in range(1, self.n):
            forecasts[t] = a[t - 1] + b[t - 1]
            a[t] = alpha * self.data[t] + (1 - alpha) * (a[t - 1] + b[t - 1])
            b[t] = beta * (a[t] - a[t - 1]) + (1 - beta) * b[t - 1]

        metrics = calculate_metrics(self.data, forecasts)
        return forecasts, metrics

    def evaluate_and_comment(self):
        """Verileri tüm yöntemlerle çalıştırır, en iyisini seçer ve METİNSEL YORUM üretir."""
        results = {}

        # Modelleri çalıştırıyoruz
        ma_f, ma_m = self.moving_average(period=3)
        wma_f, wma_m = self.weighted_moving_average(weights=[0.2, 0.3, 0.5])
        ses_f, ses_m = self.simple_exponential_smoothing(alpha=0.4)
        lr_f, lr_m, a, b = self.linear_regression()
        holt_f, holt_m = self.holt_exponential_smoothing(alpha=0.3, beta=0.1)

        results["Hareketli Ortalama (3 Dönem)"] = {
            "forecast": ma_f,
            "metrics": ma_m,
        }
        results["Ağırlıklı Hareketli Ortalama"] = {
            "forecast": wma_f,
            "metrics": wma_m,
        }
        results["Basit Üstel Düzeltme (α=0.4)"] = {
            "forecast": ses_f,
            "metrics": ses_m,
        }
        results["Doğrusal Regresyon"] = {"forecast": lr_f, "metrics": lr_m}
        results["Holt Çift Üstel Düzeltme"] = {
            "forecast": holt_f,
            "metrics": holt_m,
        }

        # En düşük MAPE değerine sahip modeli buluyoruz
        best_model = min(
            results.keys(), key=lambda k: results[k]["metrics"]["MAPE"]
        )
        best_mape = results[best_model]["metrics"]["MAPE"]

        # YORUM MOTORU (Mühendislik Yorumu Oluşturma)
        comment = f"📊 **VERİ ANALİZİ VE DEĞERLENDİRME RAPORU**\n\n"
        comment += (
            f"• **Veri Seti Büyüklüğü:** Toplam {self.n} dönemlik talep verisi incelendi.\n"
        )
        comment += (
            f"• **Trend Eğilimi (Eğim/b):** {round(b, 2)} birim/dönem. "
        )

        if abs(b) > 2.0:
            if b > 0:
                comment += "Veride **belirgin bir YÜKSELEN TREND** var. Bu nedenle sabit zaman serisi modelleri (Basit Ortalamalar) talebin gerisinde kalabilir.\n"
            else:
                comment += "Veride **DÜŞEN BİR TREND** gözlenmektedir.\n"
        else:
            comment += "Veride belirgin bir trend yok, talepler **sabit bir seviye etrafında** dalgalanmaktadır.\n"

        comment += f"\n🏆 **EN BAŞARILI TAHMİN MODELİ:** **{best_model}**\n"
        comment += f"• **Ortalama Mutlak Yüzdeli Hata (MAPE):** %{best_mape}\n"
        comment += f"• **Tavsiye:** Bu veri seti için en az sapmayı {best_model} sağladığı için Toplu Üretim Planlama (APP) modülüne aktarılacak gelecek dönem taleplerinde bu modelin çıktısı temel alınmalıdır."

        return results, best_model, comment


# --- DİNAMİK KULLANICI GİRDİSİ TESTİ ---
if __name__ == "__main__":
    print("--- DİNAMİK TALEP TAHMİN SİSTEMİ ---")
    user_input = input(
        "Lütfen geçmiş talep verilerini aralarında virgül koyarak girin\n(Örn: 100, 120, 135, 150, 160, 175): "
    )

    try:
        # Kullanıcının girdiği metni sayı listesine çeviriyoruz
        data_list = [float(x.strip()) for x in user_input.split(",")]

        if len(data_list) < 4:
            print(
                "\n⚠️ Anlamlı bir tahmin yapabilmek için en az 4 dönemlik veri giriniz."
            )
        else:
            forecaster = DemandForecaster(data_list)
            results, best_model, comment = forecaster.evaluate_and_comment()

            print("\n" + "=" * 50)
            print(comment)
            print("=" * 50)

    except ValueError:
        print("\n❌ Hata: Lütfen sadece sayısal değerler giriniz!")