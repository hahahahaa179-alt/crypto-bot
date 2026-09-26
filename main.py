import os
import requests
from google import genai

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

def kirim_ke_discord(pesan):
    if len(pesan) > 2000:
        for i in range(0, len(pesan), 1900):
            payload = {"content": pesan[i:i+1900]}
            requests.post(DISCORD_WEBHOOK_URL, json=payload)
    else:
        payload = {"content": pesan}
        requests.post(DISCORD_WEBHOOK_URL, json=payload)

def jalankan_screening():
    print("🔍 Mengambil data dari DefiLlama...")
    url = "https://api.llama.fi/overview/fees?excludeTotalDataChart=true"
    response = requests.get(url).json()
    protocols = response.get("protocols", [])

    candidates = []
    for p in protocols:
        name = p.get("name", "Unknown")
        symbol = str(p.get("symbol", "-"))
        rev_30d = p.get("revenue30d") or p.get("totalRevenue30d") or 0
        mcap = p.get("mcap") or 0

        if rev_30d > 0 and mcap > 0 and symbol not in ["-", "None", ""]:
            annual_rev = rev_30d * 12
            candidates.append({
                "name": name,
                "symbol": symbol,
                "mcap_raw": mcap,
                "mcap_m": round(mcap / 1_000_000, 2),
                "rev_m": round(annual_rev / 1_000_000, 2)
            })

    top_rev = sorted(candidates, key=lambda x: x["rev_m"], reverse=True)[:30]
    sorted_by_mcap = sorted(top_rev, key=lambda x: x["mcap_raw"], reverse=True)
    
    high_mcap_5 = sorted_by_mcap[:5]
    low_mcap_5 = sorted_by_mcap[-5:]

    text_high = "\n".join([f"- **{g['name']} ({g['symbol']})**: Mcap = ${g['mcap_m']}M | Revenue = ${g['rev_m']}M/thn" for g in high_mcap_5])
    text_low = "\n".join([f"- **{g['name']} ({g['symbol']})**: Mcap = ${g['mcap_m']}M | Revenue = ${g['rev_m']}M/thn" for g in low_mcap_5])

    prompt = f"""
Anda adalah Analis Kripto Senior. Berikut data real-time protokol crypto berevenue tinggi dari DefiLlama:

📌 **5 KOIN MARKET CAP TINGGI (LARGE CAP / BLUECHIP):**
{text_high}

📌 **5 KOIN MARKET CAP RENDAH (LOW CAP / POTENSI GEM):**
{text_low}

Tugas Anda:
1. **Analisis Koin Market Cap Tinggi:** Pilih koin terbaik berdasarkan rasio pendapatan vs market cap.
2. **Analisis Koin Market Cap Rendah:** Pilih koin yang paling potensial / undervalued.
3. **Kesimpulan & Rekomendasi:** Berikan insight singkat dan jelas untuk trader/investor.

Gunakan format teks Markdown yang rapi dengan emoji agar enak dibaca di Discord.
"""

    res = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=prompt,
    )

    pesan_akhir = f"📊 **[SCREENING KRIPTO OTOMATIS - UPDATE BERKALA]** 📊\n\n{res.text}"
    kirim_ke_discord(pesan_akhir)
    print("✅ Berhasil dikirim ke Discord!")

if __name__ == "__main__":
    jalankan_screening()
