# Real BEST (Brihanmumbai Electric Supply & Transport) depot list,
# used to populate the source/destination dropdown and to generate
# sample routes in seed_data.py

BEST_DEPOTS = [
    {"name": "Backbay",          "covers": "South Mumbai - Nariman Point, Mantralaya, Cuffe Parade, C'gate Stn, Colaba"},
    {"name": "Colaba",           "covers": "Colaba, Navy Nagar, Walkeshwar, Malabar Hill"},
    {"name": "Mumbai Central",   "covers": "Fort, Lamington Road, Ballard Pier, Mazgaon, Tardeo, Nehru Centre, Byculla"},
    {"name": "Worli",            "covers": "Worli, Worli Naka, Prabhadevi, Lower Parel"},
    {"name": "Wadala",           "covers": "Dadar TT, Dadar (W), Wadala, Worli, Prabhadevi"},
    {"name": "Bandra",           "covers": "Bandra internals, Khar, Reclamation, Mount Mary, Linking Road, CBD Belapur"},
    {"name": "Santacruz",        "covers": "Wadala, Walkeshwar, JVPD, Juhu, Colaba, BARC"},
    {"name": "Oshiwara",         "covers": "Andheri (W), Lokhandwala, Juhu, Versova, 4 & 7 Bungalows, Mantralaya"},
    {"name": "Goregaon",         "covers": "Link Road via Goregaon, Andheri, S'cruz, Vile Parle to Mantralaya, Hutatma Chowk"},
    {"name": "Malad",            "covers": "Link Road via Malad (W) Station, Mindspace, Goregaon Station"},
    {"name": "Poisar",           "covers": "Kandivali, Malad, Borivali till Andheri Juhu"},
    {"name": "Malwani",          "covers": "Mainly Malad area, some buses to Antop Hill & Wadala"},
    {"name": "Gorai",            "covers": "Mainly Borivali west, some buses to Mulund"},
    {"name": "Magathane",        "covers": "North Mumbai - Kandivali, Borivali, Dahisar, Mira Road, Bhayander (eastern belt)"},
    {"name": "Dindoshi",         "covers": "Eastern belt via Malad, Goregaon, Andheri, and Vashi"},
    {"name": "Majas",            "covers": "Andheri east - Chakala, Mahakali Caves, Powai, Chandivali, SEEPZ"},
    {"name": "Marol",            "covers": "Andheri east via Airport, Colaba, Worli, Vikhroli, Ghatkopar, Mulund"},
    {"name": "Dharavi",          "covers": "Bandra east, Bandra-Kurla Complex, Mahim, Kurla, Byculla, VT, Mantralaya"},
    {"name": "Anik",             "covers": "Long distance - Mantralaya, Mazgaon, Trombay, WTC, Wadala"},
    {"name": "Pratiksha Nagar",  "covers": "Long distance - Byculla, Worli, Dadar, Walkeshwar"},
    {"name": "Kurla",            "covers": "Eastern areas - Kurla, Mulund, Andheri E, Vidya Vihar, Chembur, Worli"},
    {"name": "Ghatkopar",        "covers": "Vashi, Vikhroli, Town, Andheri east, Nerul, Bandra"},
    {"name": "Shivaji Nagar",    "covers": "Long distance - Mantralaya, Fort, Borivali, Bandra, WTC, Worli, Andheri east"},
    {"name": "Deonar",           "covers": "Long distance - Colaba, Ballard Pier, Byculla, Wadala, Thane, Nerul, Vashi"},
    {"name": "Vikhroli",         "covers": "Short routes - Vikhroli, Ghatkopar, Mulund, Chembur"},
    {"name": "Mulund",           "covers": "Mulund, Bandra, Thane, SEEPZ, Andheri east, Bhandup"},
    {"name": "Kalakilla",        "covers": "Not specified"},
]

# Flat list of just the names - handy for a simple dropdown
MUMBAI_STATIONS = [depot["name"] for depot in BEST_DEPOTS]