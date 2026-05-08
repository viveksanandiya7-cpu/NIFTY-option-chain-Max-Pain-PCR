from datetime import datetime, timedelta
import urllib.parse
import requests

API_BASE = "https://api.upstox.com/v2"


def get_option_chain(access_token, expiry_date):
    instrument_key = urllib.parse.quote("NSE_INDEX|Nifty 50", safe="")
    expiry = expiry_date.strftime("%Y-%m-%d")
    url = f"{API_BASE}/option/chain?instrument_key={instrument_key}&expiry_date={expiry}"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    resp = requests.get(url, headers=headers, timeout=15)
    if resp.status_code == 401:
        raise Exception(f"Access token expired or invalid (HTTP 401). Generate a new one in Upstox dashboard.")
    resp.raise_for_status()
    return resp.json()


def parse_chain_data(api_response):
    chain = {}
    for item in api_response.get("data", []):
        strike = item.get("strike_price") or item.get("strike")
        ce = item.get("call_options", {}).get("market_data", {})
        pe = item.get("put_options", {}).get("market_data", {})

        chain[strike] = {
            "CE": {
                "oi": ce.get("oi", 0) or 0,
                "ltp": ce.get("ltp", 0) or 0,
                "vol": ce.get("volume", 0) or 0,
            },
            "PE": {
                "oi": pe.get("oi", 0) or 0,
                "ltp": pe.get("ltp", 0) or 0,
                "vol": pe.get("volume", 0) or 0,
            },
        }

    return chain


def calculate_max_pain(chain):
    strikes = sorted(chain.keys())
    if len(strikes) < 2:
        return None

    min_pain = float("inf")
    max_pain_strike = None

    for s in strikes:
        pain = 0.0
        for k in strikes:
            ce_oi = chain[k]["CE"]["oi"] or 0
            pe_oi = chain[k]["PE"]["oi"] or 0
            if k > s:
                pain += ce_oi * (k - s)
            elif k < s:
                pain += pe_oi * (s - k)
        if pain < min_pain:
            min_pain = pain
            max_pain_strike = s

    return max_pain_strike


def calculate_pcr(chain):
    total_ce_oi = sum((v["CE"]["oi"] or 0) for v in chain.values())
    total_pe_oi = sum((v["PE"]["oi"] or 0) for v in chain.values())
    total_ce_vol = sum((v["CE"]["vol"] or 0) for v in chain.values())
    total_pe_vol = sum((v["PE"]["vol"] or 0) for v in chain.values())

    return {
        "pcr_oi": round(total_pe_oi / total_ce_oi, 2) if total_ce_oi else 0.0,
        "pcr_vol": round(total_pe_vol / total_ce_vol, 2) if total_ce_vol else 0.0,
    }


def get_summary(chain):
    max_ce_strike = max_ce_oi = 0
    max_pe_strike = max_pe_oi = 0

    for strike, data in chain.items():
        ce_oi = data["CE"]["oi"] or 0
        pe_oi = data["PE"]["oi"] or 0
        if ce_oi > max_ce_oi:
            max_ce_oi = ce_oi
            max_ce_strike = strike
        if pe_oi > max_pe_oi:
            max_pe_oi = pe_oi
            max_pe_strike = strike

    max_pain = calculate_max_pain(chain)
    pcr = calculate_pcr(chain)

    return {
        "max_ce_strike": max_ce_strike,
        "max_ce_oi": max_ce_oi,
        "max_pe_strike": max_pe_strike,
        "max_pe_oi": max_pe_oi,
        "max_pain": max_pain,
        "pcr_oi": pcr["pcr_oi"],
        "pcr_vol": pcr["pcr_vol"],
    }


def print_chain(chain, expiry):
    from tabulate import tabulate

    strikes = sorted(chain.keys())
    rows = []
    for s in strikes:
        ce = chain[s]["CE"]
        pe = chain[s]["PE"]
        rows.append([
            int(s),
            ce["oi"] or 0,
            ce["vol"] or 0,
            pe["oi"] or 0,
            pe["vol"] or 0,
        ])

    now = datetime.now().strftime("%H:%M:%S")
    expiry_str = expiry.strftime("%d-%b-%Y")
    summary = get_summary(chain)

    print(f"\n{'=' * 60}")
    print(f"  NIFTY - Weekly: {expiry_str}  @  {now}")
    print(f"{'=' * 60}")
    print(tabulate(
        rows,
        headers=["Strike", "CE OI", "CE Vol", "PE OI", "PE Vol"],
        tablefmt="simple",
        numalign="right",
    ))
    print(f"{'-' * 60}")
    print(f"  Max Call OI:  {summary['max_ce_strike']:.0f}  "
          f"(OI: {summary['max_ce_oi']:,})")
    print(f"  Max Put OI:   {summary['max_pe_strike']:.0f}  "
          f"(OI: {summary['max_pe_oi']:,})")
    mp = summary["max_pain"]
    print(f"  Max Pain:     {mp:.0f}" if mp else "  Max Pain:     N/A")
    print(f"  PCR (OI):     {summary['pcr_oi']}")
    print(f"  PCR (Vol):    {summary['pcr_vol']}")
    print(f"{'-' * 60}\n")
