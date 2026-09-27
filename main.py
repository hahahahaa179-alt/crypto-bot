import os
import time
import requests
from google import genai

def kirim_ke_discord(pesan):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("❌ ERROR: DISCORD_WEBHOOK_URL tidak ditemukan di Secrets GitHub!")
        raise Exception("DISCORD_WEBHOOK_URL tidak ditemukan di Secrets GitHub!")

    chunks = [pesan[i:i+1900] for i in range(0, len(pesan), 1900)] if len(pesan) > 2000 else [pesan]
    
    for idx, chunk in enumerate(chunks):
        response = requests.post(webhook_url, json={"content": chunk})
        if response.status_code not in [200, 204]:
            print(f"❌ Gagal Kirim ke Discord ({response.status_code}): {response.text}")
            response.raise_for_status()

def ambil_data_defillama_revenue():
    """Mengambil Protocol Revenue & Fees harian dari DefiLlama (SOP Langkah 3)"""
    try:
        url = "https://api.llama.fi/overview/fees?dataType=dailyRevenue"
        res = requests.get(url, timeout=15)
        if res.status_code == 200:
            protocols = res.json().get("protocols", [])
            protocols = sorted(protocols, key=lambda x: x.get("dailyRevenue", 0) or 0, reverse=True)
            
            data_formatted = []
            for item in protocols[:8]:
                name = item.get("name", "Unknown")
                symbol = item.get("symbol", "N/A")
                daily_rev = item.get("dailyRevenue", 0) or 0
                daily_fees = item.get("dailyFees", 0) or 0
                data_formatted.append(f"- **{name} ({symbol})**: Daily Revenue ~${daily_rev:,.0f} | Daily Fees ~${daily_fees:,.0f}")
            return "\n".join(data_formatted)
    except Exception as e:
        print(f"⚠️ Gagal ambil data DefiLlama Revenue: {e}")
    return "Data Revenue DefiLlama tidak tersedia."

def ambil_data_coingecko_metrics():
    """Mengambil Data Large Cap & Mid/Small Cap dari CoinGecko (SOP Langkah 1 & 2)"""
    try:
        url_large = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1&sparkline=false"
        url_small = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=6&sparkline=false"
        
        res_large = requests.get(url_large, timeout=15)
        res_small = requests.get(url_small, timeout=15)
        
        coins = []
        if res_large.status_code == 200:
            coins.extend(res_large.json())
        if res_small.status_code == 200:
            coins.extend(res_small.json())

        data_formatted = []
        for c in coins:
            name = c.get("name")
            symbol = c.get("symbol", "").upper()
            mcap = c.get("market_cap", 0) or 0
            vol = c.get("total_volume", 0) or 0
            total_supply = c.get("total_supply") or c.get("max_supply") or 0
            circ_supply = c.get("circulating_supply", 0) or 0
            
            vol_mcap_ratio = (vol / mcap * 100) if mcap > 0 else 0
            supply_pct = (circ_supply / total_supply * 100) if total_supply > 0 else 100
            
            data_formatted.append(
                f"- **{name} ({symbol})** [MCap: ${mcap:,.0f}]: Vol/MCap = **{vol_mcap_ratio:.2f}%** | Supply Beredar = **{supply_pct:.1f}%**"
            )
        return "\n".join(data_formatted)
    except Exception as e:
        print(f"⚠️ Gagal ambil data CoinGecko: {e}")
    return "Data CoinGecko tidak tersedia."

def jalankan_screening():
    try:
        print("🔍 Mengambil data dari DefiLlama & CoinGecko...")
        revenue_data = ambil_data_defillama_revenue()
        metrics_data = ambil_data_coingecko_metrics()

        prompt = f"""
Anda adalah Analis Kripto Senior. Terapkan **SOP 5-Langkah Screening Altcoin** pada data pasar berikut:

📊 **1. DATA DEFILLAMA (Protocol/Chain Daily Revenue & Real Yield):**
{revenue_data}

📈 **2. DATA COINGECKO (Volume/MCap Ratio & Supply Unlock Status):**
{metrics_data}

---

🎯 **INSTRUKSI SCREENING BERDASARKAN 5 SOP:**
1. **Volume/MCap Ratio Check:** Filter altcoin dengan rasio Volume/Market Cap mendekati atau di atas 5%.
2. **Circulating Supply Check:** Filter altcoin dengan circulating supply tinggi (>70%) untuk menghindari risiko dump token unlock.
3. **Revenue & Utility Check:** Tentukan mana proyek/chain yang menghasilkan Real Revenue & Fees harian secara konsisten di DefiLlama.
4. **News & Fundamental Adoption Check:** Berikan 1-2 poin fundamental proyek yang berpotensi menjadi pemenang di market.
5. **Chart Altcoin vs BTC (Pair ALT/BTC):** Sertakan instruksi teknikal singkat untuk mengecek pair ALT/BTC di TradingView (apakah bertahan di atas EMA 13/21 & Support).

Tuliskan analisis dalam format Markdown yang rapi, padat, profesional, dan mudah dibaca di Discord.
"""

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise Exception("GEMINI_API_KEY tidak ditemukan di Secrets GitHub!")

        client = genai.Client(api_key=api_key)

        res = None
        for percobaan in range(3):
            try:
                res = client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=prompt,
                )
                break
            except Exception as e:
                print(f"⚠️ Server sibuk (Percobaan {percobaan + 1}/3). Menunggu 15 detik...")
                if percobaan < 2:
                    time.sleep(15)
                else:
                    raise e

        if not res or not res.text:
            raise Exception("Respon dari Gemini kosong!")

        pesan_akhir = f"📊 **[ALTCOIN SCREENING - 5 SOP FILTER]**\n\n{res.text}"
        kirim_ke_discord(pesan_akhir)
        print("✅ Berhasil dikirim ke Discord!")

    except Exception as err:
        print(f"❌ Error: {err}")
        raise err

if __name__ == "__main__":
    jalankan_screening()
