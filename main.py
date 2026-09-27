import os
import time
import requests
from google import genai

def kirim_ke_discord(pesan):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("❌ DISCORD_WEBHOOK_URL tidak ditemukan di Secrets!")
        return

    # Discord memiliki batasan maksimal 2000 karakter per pesan
    if len(pesan) > 2000:
        for i in range(0, len(pesan), 1900):
            requests.post(webhook_url, json={"content": pesan[i:i+1900]})
    else:
        requests.post(webhook_url, json={"content": pesan})

def jalankan_screening():
    try:
        # 1. Ambil data dari API DefiLlama
        res_llama = requests.get("https://api.llama.fi/protocols", timeout=15)
        protocols = res_llama.json()[:10] if res_llama.status_code == 200 else []

        high_cap_list = []
        low_cap_list = []

        for item in protocols:
            tvl = item.get("tvl", 0)
            name = item.get("name", "Unknown")
            symbol = item.get("symbol", "N/A")
            if tvl > 500000000:
                high_cap_list.append(f"- **{name} ({symbol})**: TVL ${tvl:,.0f}")
            else:
                low_cap_list.append(f"- **{name} ({symbol})**: TVL ${tvl:,.0f}")

        text_high = "\n".join(high_cap_list) if high_cap_list else "Data tidak tersedia"
        text_low = "\n".join(low_cap_list) if low_cap_list else "Data tidak tersedia"

        # 2. Definisikan Prompt
        prompt = f"""
Anda adalah Analis Kripto Senior. Berikut data pasar terbaru dari DefiLlama:

📌 **5 KOIN/PROTOKOL MARKET CAP TINGGI (LARGE CAP):**
{text_high}

📌 **5 KOIN/PROTOKOL MARKET CAP RENDAH (LOW CAP / POTENSIAL):**
{text_low}

Tugas Anda:
1. **Analisis Koin Market Cap Tinggi:** Pilih mana yang paling solid & alasannya.
2. **Analisis Koin Market Cap Rendah:** Pilih mana yang memiliki potensi risk/reward paling menarik.
3. **Kesimpulan & Rekomendasi:** Berikan insight singkat dan keputusan entri.

Gunakan format teks Markdown yang rapi dengan bullet points dan emoji yang sesuai. Buat ringkas dan padat.
"""

        # 3. Inisialisasi Gemini Client
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise Exception("GEMINI_API_KEY tidak ditemukan di Secrets GitHub!")

        client = genai.Client(api_key=api_key)

        # 4. Panggil Gemini API (menggunakan gemini-3.8-flash dan Retry Loop)
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

        # 5. Kirim Hasil Akhir ke Discord
        pesan_akhir = f"📊 **[SCREENING KRIPTO OTOMATIS]**\n\n{res.text}"
        kirim_ke_discord(pesan_akhir)
        print("✅ Berhasil dikirim ke Discord!")

    except Exception as err:
        pesan_error = f"⚠️ **Terjadi error pada sistem screening:** {err}"
        kirim_ke_discord(pesan_error)
        print(f"❌ Error: {err}")
        raise err

if __name__ == "__main__":
    jalankan_screening()

