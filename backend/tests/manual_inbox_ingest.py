import asyncio, os
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")
import sys; sys.path.insert(0, "/app/backend")
from motor.motor_asyncio import AsyncIOMotorClient
import mail_inbox


async def main():
    db = AsyncIOMotorClient(os.environ['MONGO_URL'])[os.environ['DB_NAME']]
    item = await db.service_requests.find_one({"email": "vaibhav.deshmane@vametra.com"}, {"_id": 0}, sort=[("createdAt", -1)])
    rid = item["id"]; print("target", rid[:8], "ca", item.get("assignedCaEmail"))
    raw = f"""From: Vaibhav Deshmane <vaibhav.deshmane@vametra.com>
To: patnisidharth@gmail.com
Cc: admin@vametra.com
Subject: Re: Vametra Service Request · Company Registration (Shop Act / LLP / Pvt Ltd) · Allocated to Vametra CA
Date: Fri, 31 Oct 2026 03:10:00 +0530
Message-ID: <test-reply-001@mail.gmail.com>
Content-Type: text/plain; charset=utf-8

Sure will submit them by tomorrow morning.

On Thu, 30 Oct 2026 at 21:40, PatniCA <patnica@vametra.com> wrote:
> Hi, please submit the below documents for company registration.
> Ref: SR-{rid}
""".encode()
    print("ingest ->", await mail_inbox.ingest_message(raw))
    print("dupe ->", await mail_inbox.ingest_message(raw))
    it = await db.service_requests.find_one({"id": rid}, {"_id": 0, "emailActivity": {"$slice": -1}, "unreadFor": 1, "lastReplyRole": 1})
    a = it["emailActivity"][-1]; print(a["kind"], a["role"], a["byName"], repr(a["text"]), "fwd", a["forwardedTo"]); print("unreadFor", it["unreadFor"], it["lastReplyRole"])
    raw2 = raw.replace(b"test-reply-001", b"test-reply-002").replace(f"> Ref: SR-{rid}".encode(), b"").replace(b"Sure will submit", b"Second reply without ref, will submit")
    print("ingest no-ref ->", await mail_inbox.ingest_message(raw2))
    print("strip:", repr(mail_inbox.strip_quoted("Thanks!\r\n\r\n-----Original Message-----\r\nFrom: x\r\nblah")))

asyncio.run(main())
