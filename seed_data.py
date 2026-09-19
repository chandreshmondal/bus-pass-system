"""
Run this once after the database is created to populate it with sample
bus routes between real Mumbai BEST depots. Run from the project root:

    python seed_data.py
"""

import random
from app import create_app
from models import db, BusRoute
from stations import MUMBAI_STATIONS

# A handful of realistic source -> destination pairs with fares.
# Feel free to add more pairs from MUMBAI_STATIONS.
SAMPLE_ROUTES = [
    ("R101", "Colaba", "Andheri"),
    ("R102", "Backbay", "Ghatkopar"),
    ("R103", "Bandra", "Borivali"),
    ("R104", "Kurla", "Mulund"),
    ("R105", "Dharavi", "Vikhroli"),
    ("R106", "Mumbai Central", "Goregaon"),
    ("R107", "Wadala", "Malad"),
    ("R108", "Santacruz", "Dindoshi"),
    ("R109", "Worli", "Poisar"),
    ("R110", "Deonar", "Gorai"),
    ("R111", "Anik", "Magathane"),
    ("R112", "Oshiwara", "Pratiksha Nagar"),
    ("R113", "Majas", "Marol"),
    ("R114", "Shivaji Nagar", "Malwani"),
]


def seed():
    app = create_app()
    with app.app_context():
        added = 0
        for route_number, source, destination in SAMPLE_ROUTES:
            if BusRoute.query.filter_by(route_number=route_number).first():
                continue  # already seeded, skip

            route = BusRoute(
                route_number=route_number,
                source=source,
                destination=destination,
                fare=round(random.uniform(10, 45), 2),  # realistic BEST fare range
            )
            db.session.add(route)
            added += 1

        db.session.commit()
        print(f"Seeded {added} new routes. Total routes in DB: {BusRoute.query.count()}")


if __name__ == "__main__":
    seed()