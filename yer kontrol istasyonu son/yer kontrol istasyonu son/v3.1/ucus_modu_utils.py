import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UCUS_MODU_PATH = os.path.join(BASE_DIR, "ucus_modu.json")

def ucus_modu_cek():
    try:
        with open(UCUS_MODU_PATH) as f:
            return json.load(f)
    except:
        return {
            "mod": "otonom",
            "hedef_id": None,
            "devriye_merkez": None,
            "devriye_cap": None,
            "inis_nokta": None,
            "kalkis_yukseklik": None
        }

def ucus_modu_yaz(mod, hedef_id=None, devriye_merkez=None, devriye_cap=None, inis_nokta=None, kalkis_yukseklik=None):
    with open(UCUS_MODU_PATH, "w") as f:
        json.dump({
            "mod": mod,
            "hedef_id": hedef_id,
            "devriye_merkez": devriye_merkez,
            "devriye_cap": devriye_cap,
            "inis_nokta": inis_nokta,
            "kalkis_yukseklik": kalkis_yukseklik
        }, f, indent=2)