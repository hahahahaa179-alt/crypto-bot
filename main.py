import os
import time
import requests
from google import genai

def kirim_ke_discord(pesan):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("❌ ERROR: DISCORD_WEBHOOK_URL tidak ditemukan di Secrets GitHub!")
        raise Exception("DISCORD_WEBHOOK_URL tidak ditemukan di Secrets GitHub!")

    # Memecah pesan jika melebihi batasan 2000 karakter Discord
    chunks = [pesan[i:i+1900] for i in range(0, len(pesan), 1900)] if len(pesan) > 2000 else [pesan]
    
    for idx, chunk in enumerate(chunks):
        response = requests.post(webhook_url, json={"content": chunk})
        if response.status_code not in [200, 204]:
            print(f"❌ Gagal Kirim ke Discord ({response.status_code}): {response.text}")
            response.raise_for_status()

def ambil_data_defillama_revenue():
    """Mengambil Protocol Revenue & Fees harian dari DefiLlama (SOP Real Yield & Utility)"""
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
                data_formatted.append(f"- **{name} ({symbol})**: Daily Rev ~${daily_rev:,.0f} | Daily Fees ~${daily_fees:,.0f}")
            return "\n".join(data_formatted)
    except Exception as e:
        print(f"⚠️ Gagal ambil data DefiLlama Revenue: {e}")
    return "Data Revenue DefiLlama tidak tersedia."

def ambil_data_coingecko_metrics():
    """Mengambil Big Caps (Top 10) & Small Caps (Rank 50-60) untuk menerapkan Elevator Concept"""
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
                f"- **{name} ({symbol})** [MCap: ${mcap:,.0f}]: Vol/MCap = **{vol_mcap_ratio:.2f}%** | Circulating = **{supply_pct:.1f}%**"
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

        # Build Prompt berdasarkan Kombinasi SOP Filter + Sistem 3-Lapis (Xander Crypto)
        prompt = f"""
Anda adalah Analis Kripto Senior. Terapkan **Sistem Filter 3 Lapis & Elevator Concept (Xander Crypto Strategy)** pada data pasar berikut:

📊 **1. DATA DEFILLAMA (Protocol Real Revenue & Fees):**
{revenue_data}

📈 **2. DATA COINGECKO (Volume/MCap, Supply Unlock, & Cap Category):**
{metrics_data}

---

🎯 **PETUNJUK FILTER 3 LAPIS & EVALUASI:**

**LAPIS 1: NARRATIVE & SECTOR FILTER**
- Identifikasi narasi/sektor yang memimpin pasar saat ini (AI, RWA, DeFi, L1/L2, Meme, dll.).
- Pastikan narasi berada pada fase awal/tersebar (bukan fase Klimaks/Puncak/Cuci Piring).

**LAPIS 2: RELATIVE STRENGTH vs BITCOIN (ALT/BTC)**
- Wajib menyaring koin yang memperlihatkan struktur **outperform terhadap BTC** (Chart `ALT/BTC` uptrend/di atas EMA 13/21). Jika `ALT/BTC` merosot, eliminasi koin tersebut.

**ELEVATOR CONCEPT (KATEGORI CAP):**
- Pilih koin dari kategori **Big Cap** (untuk stabilitas & tren awal) dan **Small Cap** (untuk potensi profit eksplosif).
- **Abaikan Mid-Cap** (Death Zone).

**PARAMATER TAMBAHAN (SOP METRICS):**
- Volume/MCap Ratio $\approx 5\%$ atau lebih.
- Circulating Supply $>70\%$ (Aman dari risiko token dump).

**LAPIS 3: STRATEGI EKSEKUSI & EXIT PLAN**
- Sertakan panduan harga entry/support teknikal serta strategi **DCA Sell (Take Profit Bertahap)** untuk diputar kembali (*flip*) ke Bitcoin.

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
                    model='gemini-3.8-flash',
                    contents=prompt,
                )
                break
            except Exception as e:
                print(f"⚠️ Server sibuk (Percobaan {percobaan + 1}/3). Menunggu 10 detik...")
                if percobaan < 2:
                    time.sleep(10)
                else:
                    raise e

        if not res or not res.text:
            raise Exception("Respon dari Gemini kosong!")

        pesan_akhir = f"🚀 **[ALTCOIN SCREENER - SISTEM 3 LAPIS XANDER CRYPTO]**\n\n{res.text}"
        kirim_ke_discord(pesan_akhir)
        print("✅ Berhasil dikirim ke Discord!")

    except Exception as err:
        print(f"❌ Error: {err}")
        raise err

if __name__ == "__main__":
    jalankan_screening()

