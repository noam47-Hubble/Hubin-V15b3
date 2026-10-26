"""HUBIN — sample data loader: 9 hubs (3 professional, 3 business, 3 social) with random registrants.
Every sample hub belongs to the person who loads it (so they keep full management rights)."""
import base64
import random
import time
import uuid
from urllib.parse import quote

from models import (db, User, Card, CardPhoto, Hub, HubBlock, HubOpenPost, HubPresence, BoardMessage, Favorite,
                    HubBan, PrivateMessage, ContactShare, gen_hub_serial, gen_presence_code)

FIRST = ["נועה", "דניאל", "מאיה", "יובל", "תמר", "איתי", "שירה", "עמית", "רוני", "גל", "הילה", "אורי", "ליאור", "מורן", "אלון", "דנה", "ניצן", "יעל", "רן", "מיכל",
         "אסף", "נטע", "עידו", "קרן", "תומר", "שקד", "אביב", "לינוי", "בן", "טל", "אופיר", "עדי", "רותם", "מתן", "ענת", "גילי", "אריאל", "ספיר", "יונתן", "הדר"]
LAST = ["כהן", "לוי", "מזרחי", "פרץ", "ביטון", "דהן", "אברהם", "פרידמן", "אזולאי", "מלכה", "גולן", "שמעון", "אוחנה", "חדד", "בן דוד", "רוזן", "שפירא", "קפלן", "נחום", "אשכנזי",
        "סבן", "עמר", "ברק", "יוסף", "שלום", "זיו", "אלבז", "טל", "גבאי", "רביבו"]
TITLES = ["מנכ״ל", "סמנכ״ל שיווק", "מנהלת מוצר", "ראש צוות פיתוח", "יועץ עסקי", "מנהלת משאבי אנוש", "אנליסטית נתונים", "מהנדס תוכנה", "מעצבת UX", "מנהל מכירות",
          "יזם", "משקיעה", "CISO", "מנהל פרויקטים", "מרצה", "רופאה", "חוקר", "מנהלת תפעול"]
COMPANIES = ["טכנו-דאטה", "ענן ישראל", "סייבר-שילד", "ביונט", "נקסוס", "אלפא-סטארט", "בלו-וייב", "אופק מערכות", "דיגיטל פלוס", "גרין-אנרג׳י", "מדיקל-לינק", "פינטק-IL", "אורבן-לאב", "קוד-אקדמי"]
NICK = ["הנסיך", "הקפטן", "זאב", "דובי", "ברקי", "הכוכב", "פיצי", "שמש", "אריה", "נינג׳ה", "מלכת הכיתה", "רץ", "גולש", "הצל", "ירוק"]
BIOS = ["אוהב קפה טוב ושיחות טובות", "תמיד בדרך לעוד אירוע", "מחפש שותפים לרעיונות", "כאן בשביל הכיף", "מתעניין בטכנולוגיה וקהילה", "אוהבת לטייל ולפגוש אנשים", "פה בשביל הנטוורקינג", "חובב ספורט מושבע"]
MOODS = ["", "", "", "😀", "😎", "🥳", "💪", "🎯", "☕", "🚀"]
PALETTE = ["#2D8CE6", "#e8a33d", "#3ecf7a", "#8e5bd8", "#e0494e", "#17a2b8", "#f06595", "#5c7cfa", "#20c997", "#ff922b"]

BOARD_TEXTS = {
    "professional": ["מישהו יודע באיזה אולם ההרצאה הבאה?", "תודה על המפגש בדוכן הסטארטאפים, נשמח להמשיך את השיחה", "מחפשים שותף פיתוח לפרויקט בתחום ה-AI, מוזמנים לפנות", "מישהו רוצה להצטרף לארוחת צהריים ב-13:00?", "ההרצאה של הפתיחה הייתה מעולה!", "יש מקום פנוי באולם B", "מי מגיע למפגש הנטוורקינג בערב?"],
    "business": ["שלום, האם יש מבצע השבוע?", "היה מעולה, תודה!", "מישהו יודע אם פתוח גם בשישי?", "אשמח להמלצה על המנה הכי טובה", "הגעתי היום לראשונה, מקום נהדר", "יש חניה בסביבה?", "תודה על השירות המצוין"],
    "social": ["מי מגיע הערב? 🙌", "אני ליד הכניסה, חולצה כחולה", "מישהו עם מקום פנוי ברכב?", "איזה אווירה!", "נפגשים בשער בעוד עשר דקות", "מישהו ראה את דנה?", "תמונות מהערב בדרך 📸"],
}
POSTS = ["הנה עדכון קצר מהשטח", "מצאתי את זה מעניין, שווה לראות", "מי שמחפש חניה - החניון הצפוני פנוי", "שאלה לקהילה: מה הכי כדאי לראות כאן?", "תודה לכל מי שהצטרף היום"]

PLACES = {
    "expo": (32.1069, 34.8083, "מרכז הירידים, תל אביב"), "jlm": (31.7885, 35.2037, "בנייני האומה, ירושלים"), "tlv": (32.0738, 34.7922, "בית התפוצות, תל אביב"),
    "diz": (32.0795, 34.7745, "דיזנגוף 120, תל אביב"), "rlz": (32.0900, 34.8010, "רחוב ביאליק 8, רמת גן"), "hrz": (32.1665, 34.8430, "הרצליה פיתוח"),
    "blm": (32.0554, 34.7625, "אצטדיון בלומפילד, יפו"), "yrk": (32.1000, 34.8000, "פארק הירקון, תל אביב"), "bch": (32.0809, 34.7650, "חוף גורדון, תל אביב"),
}


def _svg(s):
    return "data:image/svg+xml;base64," + base64.b64encode(s.encode("utf-8")).decode()


def avatar(rnd, seed_color=None):
    c1 = seed_color or rnd.choice(PALETTE); c2 = rnd.choice(PALETTE)
    skin = rnd.choice(["#f2c9a0", "#e0ac7e", "#c68642", "#8d5524", "#ffdbb0"]); hair = rnd.choice(["#2b1d12", "#4a2f1b", "#b0722f", "#1a1a1a", "#d9b46c"])
    return _svg(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>'
                f'<rect width="120" height="120" fill="url(#g)"/><path d="M20 120c0-26 18-40 40-40s40 14 40 40z" fill="#243b6b"/><circle cx="60" cy="52" r="24" fill="{skin}"/><path d="M36 50c0-18 12-26 24-26s24 8 24 26c-8-8-14-12-24-12s-16 4-24 12z" fill="{hair}"/></svg>')


def hub_bg(c1, c2, kind):
    shapes = "".join(f'<circle cx="{random.randint(0,1200)}" cy="{random.randint(0,800)}" r="{random.randint(40,220)}" fill="#ffffff" opacity="{random.choice([.04,.06,.09])}"/>' for _ in range(14))
    lines = "".join(f'<path d="M{random.randint(0,1200)} 0L{random.randint(0,1200)} 800" stroke="#fff" stroke-opacity=".05" stroke-width="{random.randint(2,14)}"/>' for _ in range(8)) if kind != "social" else ""
    return _svg(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 800" preserveAspectRatio="xMidYMid slice"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs><rect width="1200" height="800" fill="url(#g)"/>{shapes}{lines}</svg>')


def hub_logo(letters, c1, c2):
    return _svg(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs><rect width="120" height="120" rx="26" fill="url(#g)"/><text x="60" y="76" font-family="Arial,sans-serif" font-size="46" font-weight="700" fill="#fff" text-anchor="middle">{letters}</text></svg>')


HUBS = [
    # ---- professional
    dict(key="cyber", type="professional", name="CyberTech Israel 2026", tag="כנס הסייבר והאבטחה הגדול בישראל", dates="10-11.11.2026", place="expo", tpl="corporate_classic", c=("#0b3d91", "#071a3a"), logo="CT",
         presence="both", approve=True, n=(70, 110), org="צוות CyberTech",
         blocks=[("תוכנית הכנס", "09:00 רישום וקפה\n10:00 פתיחה וברכות\n10:45 הרצאת מליאה: איומי העתיד\n12:30 ארוחת צהריים\n14:00 סדנאות מקבילות", "other", True), ("מפת האולם", "אולם A - קומה 1 · אולם B - קומה 2 · יריד הסטארטאפים - קומה 0", "other", False),
                 ("דוברים", "ד״ר דנה רוזן - אבטחת ענן\nיובל ברק - Zero Trust\nמיכל גולן - רגולציה", "other", False), ("נותני חסות", "ענן ישראל · סייבר-שילד · נקסוס", "other", False), ("לוח שיתופי", "", "open", False), ("צור קשר", "info@cybertech.example", "other", False)]),
    dict(key="health", type="professional", name="כנס רפואת העתיד", tag="HealthTech Summit - חדשנות בבריאות דיגיטלית", dates="03.12.2026", place="tlv", tpl="creator_purple", c=("#5b2a86", "#1d0f3a"), logo="HT",
         presence="code", approve=True, n=(50, 85), org="הפורום לרפואה דיגיטלית",
         blocks=[("לוח זמנים", "08:30 התכנסות\n09:30 מושב ראשון - AI בדימות\n11:30 פאנל: פרטיות מטופלים\n13:30 סיכום", "other", True), ("מציגים", "מדיקל-לינק · ביונט · פינטק-IL", "other", False), ("מפה", "בית התפוצות, כניסה ראשית מצד צפון", "other", False), ("לוח שיתופי", "", "open", False)]),
    dict(key="startup", type="professional", name="פסגת הסטארטאפים ירושלים", tag="משקיעים פוגשים יזמים", dates="20.12.2026", place="jlm", tpl="logistics_red", c=("#a32d2d", "#3a0e0e"), logo="SP",
         presence="none", approve=False, n=(35, 60), org="ערן ושות׳", pending=5,
         blocks=[("תוכנית היום", "10:00 פיצ׳ים של 20 סטארטאפים\n13:00 מפגש משקיעים\n16:00 נטוורקינג", "other", True), ("רשימת משקיעים", "אלפא-סטארט · בלו-וייב · אורבן-לאב", "other", False), ("לינק לאתר האירוע", "https://example.com/startup-summit", "other", False)]),
    # ---- business
    dict(key="cafe", type="business", name="קפה ספרים - דיזנגוף", tag="קפה, ספרים ואנשים טובים", dates="", place="diz", tpl="community_dynamic", c=("#0f6e56", "#08362b"), logo="קס",
         presence="location", approve=True, n=(30, 55), org="נועה ויובל, בעלי המקום", radius=120,
         blocks=[("תפריט", "קפה הפוך 14 · שקשוקה 42 · סלט ירוק 38 · עוגת גבינה 28", "other", True), ("שעות פעילות", "א-ה 07:00-23:00 · ו 07:00-16:00 · שבת 09:00-23:00", "other", False), ("מבצעים", "קפה + עוגה ב-35 ₪ בשעות הבוקר", "other", False), ("לוח שיתופי", "", "open", False), ("צור קשר", "03-5551234", "other", False)]),
    dict(key="gym", type="business", name="סטודיו כושר Pulse", tag="אימון קבוצתי ואישי", dates="", place="rlz", tpl="minimalist_dark", c=("#e24b4a", "#12141f"), logo="PS",
         presence="none", approve=True, n=(40, 70), org="צוות Pulse",
         blocks=[("מערכת שעות", "א, ג, ה: 06:30 קרוספיט · 18:00 יוגה\nב, ד: 07:00 פילאטיס · 19:00 HIIT", "other", True), ("מנויים ומחירים", "כניסה בודדת 60 ₪ · חודשי 350 ₪ · שנתי 3,200 ₪", "other", False), ("צוות המאמנים", "גל · מורן · אסף · הילה", "other", False), ("לוח שיתופי", "", "open", False)]),
    dict(key="bike", type="business", name="פדל - חנות אופניים וסדנה", tag="אופניים, תיקונים וקהילת רוכבים", dates="", place="hrz", tpl="logistics_red", c=("#c0392b", "#3d1410"), logo="פד",
         presence="location", approve=True, n=(25, 45), org="אלון, בעל החנות", radius=150,
         blocks=[("מוצרים ושירותים", "אופני כביש · אופני הרים · חשמליים · תיקונים תוך יום", "other", True), ("שעות פעילות", "א-ה 09:00-19:00 · ו 09:00-14:00", "other", False), ("מבצעים", "טיפול שנתי ב-199 ₪ עד סוף החודש", "other", False), ("מפה", "הרצליה פיתוח, ליד תחנת הרכבת", "other", False)]),
    # ---- social
    dict(key="stadium", type="social", name="בלומפילד - שער 5", tag="כדורגל · משחק הערב", dates="", place="blm", tpl="community_dynamic", c=("#1b7a3e", "#0a2f18"), logo="B5", glow=True,
         presence="location", approve=True, n=(45, 80), org="חבורת שער 5", radius=500,
         blocks=[("תוכנית הערב", "18:00 התכנסות בשער · 19:30 שריקת פתיחה · 22:00 חגיגות", "other", True), ("מפה", "שער 5, צד מזרחי של האצטדיון", "other", False), ("לוח שיתופי", "", "open", False)]),
    dict(key="reunion", type="social", name="מפגש מחזור י״ב 2006", tag="20 שנה לסיום - ערב נוסטלגיה", dates="14.01.2027", place="bch", tpl="creator_purple", c=("#6a3fb0", "#241047"), logo="20", glow=True,
         presence="none", approve=True, n=(30, 55), org="ועדת המחזור",
         blocks=[("תוכנית האירוע", "20:00 קבלת פנים · 21:00 סרטון זכרונות · 22:00 ריקודים", "other", True), ("לינק לקבוצה", "https://example.com/reunion", "other", False), ("לוח שיתופי", "", "open", False)]),
    dict(key="run", type="social", name="ריצת בוקר פארק הירקון", tag="כל שבת ב-07:00 · כל הקצבים", dates="", place="yrk", tpl="corporate_classic", c=("#1769aa", "#0a2a4a"), logo="🏃", glow=True,
         presence="code", approve=True, n=(25, 50), org="קבוצת הרצים",
         blocks=[("מסלול השבוע", "10 ק״מ סביב הפארק · נקודת מים בקילומטר 5", "other", True), ("לוח שיתופי", "", "open", False), ("צור קשר", "הצטרפו לקבוצת הריצה", "other", False)]),
]


def _pool(rnd, n):
    out, used = [], set()
    while len(out) < n:
        nm = rnd.choice(FIRST) + " " + rnd.choice(LAST)
        if nm in used:
            continue
        used.add(nm); out.append(nm)
    return out


def _make_user(rnd, name):
    u = User(device_id="demo-" + uuid.uuid4().hex, reg_name=name, is_demo=True)
    db.session.add(u); db.session.flush()
    photo = avatar(rnd) if rnd.random() < 0.65 else ""
    cards = {}
    for typ in ("business", "social"):
        c = Card(user_id=u.id, card_type=typ, is_active=(typ == "business"), is_open_to_contact=rnd.random() < 0.92, card_name=name.split()[0] + ("1" if typ == "business" else "2"),
                 name=name, name_visible=True, mood=rnd.choice(MOODS))
        if typ == "business":
            c.title, c.title_visible = rnd.choice(TITLES), True
            c.company, c.company_visible = rnd.choice(COMPANIES), True
            if rnd.random() < .4:
                c.phone, c.phone_visible = "05%d-%07d" % (rnd.choice([0, 2, 4, 8]), rnd.randint(1000000, 9999999)), True
            if rnd.random() < .3:
                c.linkedin, c.linkedin_visible = "linkedin.com/in/" + uuid.uuid4().hex[:8], True
        else:
            c.nickname, c.nickname_visible = rnd.choice(NICK), rnd.random() < .6
            c.bio, c.bio_visible = rnd.choice(BIOS), True
        db.session.add(c); db.session.flush()
        if photo:
            db.session.add(CardPhoto(card_id=c.id, url=photo, is_visible=True, is_profile_photo=True, order=0))
        cards[typ] = c
    return u, cards


def seed(owner):
    """Create the 9 sample hubs (owned by `owner`) with random registrants. Returns a summary."""
    rnd = random.Random()
    now = time.time()
    own_cards = Card.query.filter_by(user_id=owner.id).all()
    if not own_cards:
        raise ValueError("נא ליצור כרטיס אישי לפני טעינת האבי דוגמה")
    biz = next((c for c in own_cards if c.card_type == "business" and c.is_active), None) or next((c for c in own_cards if c.card_type == "business"), None)
    soc = next((c for c in own_cards if c.is_active), None) or own_cards[0]
    pool = []
    for nm in _pool(rnd, 150):
        pool.append(_make_user(rnd, nm))
    summary = []
    for spec in HUBS:
        lat, lng, addr = PLACES[spec["place"]]
        serial = gen_hub_serial()
        while Hub.query.filter_by(serial=serial).first():
            serial = gen_hub_serial()
        oc = (biz or soc) if spec["type"] != "social" else soc
        hub = Hub(owner_user_id=owner.id, owner_card_id=oc.id, name=spec["name"], serial=serial, hub_type=spec["type"], tagline=spec["tag"], event_dates=spec["dates"],
                  location=addr, loc_address=addr, organizer_names=spec["org"], auto_approve=spec["approve"], is_published=True, template_id=spec["tpl"],
                  presence_mode=spec["presence"], loc_lat=lat + rnd.uniform(-.0006, .0006), loc_lng=lng + rnd.uniform(-.0006, .0006), loc_radius=spec.get("radius", 250),
                  presence_code=gen_presence_code(), background_image_url=hub_bg(spec["c"][0], spec["c"][1], spec["type"]), logo_url=hub_logo(spec["logo"], spec["c"][0], spec["c"][1]),
                  glow=bool(spec.get("glow")), card_enabled=True, card_use_hub_bg=True, card_message=rnd.choice(["ברוכים הבאים! נעים שהצטרפתם", "שמחים לראות אתכם כאן", "היכנסו, הכול מוכן בשבילכם"]), is_demo=True)
        db.session.add(hub); db.session.flush()
        blocks = []
        for i, (title, content, cat, pinned) in enumerate(spec["blocks"]):
            b = HubBlock(hub_id=hub.id, title=title, content=content, category=cat, is_default=pinned, order=i, is_visible=True)
            db.session.add(b); db.session.flush(); blocks.append(b)
        k = rnd.randint(*spec["n"])
        crowd = rnd.sample(pool, k)
        pres = []
        for u, cards in crowd:
            c = cards["social"] if spec["type"] == "social" else cards["business"]
            physical = rnd.random() < .28
            p = HubPresence(hub_id=hub.id, user_id=u.id, card_id=c.id, status="green" if c.is_open_to_contact else "red", is_physical=physical, physical_ts=now + 30 * 86400 if physical else 0.0,
                            is_live=False, approval_status="approved", joined_at=now - rnd.randint(600, 6 * 86400), last_seen=now - rnd.randint(0, 3600), demo=True)
            db.session.add(p); pres.append((u, c))
        for u, cards in rnd.sample(pool, spec.get("pending", 0)):
            c = cards["business"]
            db.session.add(HubPresence(hub_id=hub.id, user_id=u.id, card_id=c.id, status="green", approval_status="pending", is_live=False, joined_at=now - rnd.randint(60, 3000), demo=True))
        for _ in range(rnd.randint(6, 12)):
            u, c = rnd.choice(pres)
            db.session.add(BoardMessage(hub_id=hub.id, sender_user_id=u.id, sender_card_id=c.id, text=rnd.choice(BOARD_TEXTS[spec["type"]]), ts=now - rnd.randint(120, 7 * 3600)))
        for b in blocks:
            if b.category == "open":
                for _ in range(rnd.randint(3, 5)):
                    u, c = rnd.choice(pres)
                    db.session.add(HubOpenPost(hub_id=hub.id, block_id=b.id, user_id=u.id, card_id=c.id, text=rnd.choice(POSTS), ts=now - rnd.randint(300, 5 * 3600)))
        # the owner is registered in his own hub as well
        db.session.add(HubPresence(hub_id=hub.id, user_id=owner.id, card_id=oc.id, status="green", approval_status="approved", is_live=False, joined_at=now - 86400, demo=False))
        summary.append({"hub_id": hub.id, "name": hub.name, "type": hub.hub_type, "serial": hub.serial, "registered": k + 1})
    db.session.commit()
    return summary


def clear(owner, everyone=False):
    """Delete the sample hubs (of `owner`, or all of them) and the sample people that no longer belong anywhere."""
    q = Hub.query.filter_by(is_demo=True)
    if not everyone:
        q = q.filter_by(owner_user_id=owner.id)
    ids = [h.id for h in q.all()]
    for hid in ids:
        for model in (HubOpenPost, BoardMessage, Favorite, HubBan, HubPresence, HubBlock):
            model.query.filter_by(hub_id=hid).delete()
        PrivateMessage.query.filter_by(hub_id=hid).update({PrivateMessage.hub_id: None})
        ContactShare.query.filter_by(hub_id=hid).update({ContactShare.hub_id: None})
        Hub.query.filter_by(id=hid).delete()
    db.session.commit()
    if not Hub.query.filter_by(is_demo=True).count():
        for u in User.query.filter_by(is_demo=True).all():
            if PrivateMessage.query.filter((PrivateMessage.from_user_id == u.id) | (PrivateMessage.to_user_id == u.id)).first() or ContactShare.query.filter_by(from_user_id=u.id).first():
                continue      # somebody interacted with this person: keep (still harmless)
            cids = [c.id for c in Card.query.filter_by(user_id=u.id).all()]
            if cids:
                CardPhoto.query.filter(CardPhoto.card_id.in_(cids)).delete(synchronize_session=False)
            Card.query.filter_by(user_id=u.id).delete()
            db.session.delete(u)
        db.session.commit()
    return len(ids)
