# Iter78 UI seed/cleanup helper: `python iter78_seed_ui.py seed|clean`
import os, sys, requests
from dotenv import load_dotenv
from pymongo import MongoClient
load_dotenv("/app/frontend/.env"); load_dotenv("/app/backend/.env")
B = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
db = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
if sys.argv[1] == "seed":
    ids = []
    for n in ("TEST_iter78UI New", "TEST_iter78UI Done"):
        r = requests.post(f"{B}/api/service-request", json={"service": "iec-registration", "name": n, "email": "vaibhav.deshmane@vametra.com", "phone": "9000000000"}, timeout=90)
        ids.append(r.json()["id"])
    db.service_requests.update_one({"id": ids[1]}, {"$set": {"status": "completed"}})
    print(" ".join(ids))
else:
    print(db.service_requests.delete_many({"name": {"$regex": "^TEST_iter78"}}).deleted_count,
          db.leads.delete_many({"name": {"$regex": "^TEST_iter78"}}).deleted_count)
