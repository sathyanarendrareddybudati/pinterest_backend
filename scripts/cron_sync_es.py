import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.models import Pin
from app.services.search_service import index_pin
from app.services.visual_search import visual_search
import urllib.request
import traceback

def sync_pins_to_es():
    """
    Periodic cron job to sync PostgreSQL pins and extract visual embeddings
    into the Elasticsearch Cluster.
    """
    db: Session = SessionLocal()
    print(f"[{datetime.now()}] Starting Elasticsearch Background Sync...")
    pins = db.query(Pin).all()
    
    success_count = 0
    fail_count = 0

    for pin in pins:
        try:
            req = urllib.request.Request(pin.image_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                image_bytes = response.read()
            embedding = visual_search.encode_image(image_bytes)
            
            index_pin(pin.id, pin.title, pin.description, embedding)
            
            print(f"Successfully Indexed Pin: {pin.id}")
            success_count += 1

        except Exception as e:
            print(f"Failed to index Pin {pin.id}: {str(e)}")
            fail_count += 1
            
    print(f"[{datetime.now()}] Sync Complete. Success: {success_count}, Failed: {fail_count}")

if __name__ == "__main__":
    sync_pins_to_es()