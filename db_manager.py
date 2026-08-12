import json
import os

DB_FILE = "database.json"

def load_database():
    """Carica le notizie salvate dal file JSON."""
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Impossibile leggere il DB: {e}")
        return []

def save_database(data):
    """Salva la lista di notizie aggiornata nel file JSON."""
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"[ERROR] Impossibile salvare il DB: {e}")

def sync_news_with_db(new_items):
    """
    Sincronizza le nuove notizie estratte con il DB.
    Aggiunge solo quelle non ancora presenti (deduplicazione per URL).
    """
    db_items = load_database()
    existing_links = {item.get("link") for item in db_items if item.get("link")}
    
    added_count = 0
    for item in new_items:
        if item and item.get("link") not in existing_links:
            db_items.append(item)
            existing_links.add(item["link"])
            added_count += 1
            
    if added_count > 0:
        save_database(db_items)
        
    return db_items, added_count