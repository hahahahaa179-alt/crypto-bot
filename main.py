def ambil_data_coingecko_metrics():
    """Mengambil Data Large Cap (Top 10) & Mid/Small Cap (Rank 50-60) dari CoinGecko"""
    try:
        # 1. Ambil Large Cap (Halaman 1, 10 Koin)
        url_large = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1&sparkline=false"
        # 2. Ambil Mid/Small Cap (Halaman 1, Rank 50-60)
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
            
            # SOP 1: Vol/MCap ratio (~5%)
            vol_mcap_ratio = (vol / mcap * 100) if mcap > 0 else 0
            
            # SOP 2: Supply unlock % (>70%)
            supply_pct = (circ_supply / total_supply * 100) if total_supply > 0 else 100
            
            data_formatted.append(
                f"- **{name} ({symbol})** [MCap: ${mcap:,.0f}]: Vol/MCap = **{vol_mcap_ratio:.2f}%** | Supply Beredar = **{supply_pct:.1f}%**"
            )
        return "\n".join(data_formatted)
    except Exception as e:
        print(f"⚠️ Gagal ambil data CoinGecko: {e}")
    return "Data CoinGecko tidak tersedia."
