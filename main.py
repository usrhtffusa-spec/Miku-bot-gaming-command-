import telebot
import time
import random
import os
import certifi 
from pymongo import MongoClient
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# =========================================================
# 🔧 DNS FIX (Railway/Termux Connectivity)
# =========================================================
try:
    import dns.resolver
    dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
    dns.resolver.default_resolver.nameservers = ['8.8.8.8', '8.8.4.4']
except ImportError:
    pass

# =========================================================
# ⚙️ CONFIGURATION
# =========================================================

MONGO_URL = "mongodb+srv://usrhtffdbr:miku1234@cluster0.jhvwttf.mongodb.net/?appName=Cluster0"
BOT_TOKEN = "8533598800:AAHAISipA75ABha5vPpDafh5d6ELsVxn5IY"

OWNER_ID = 8327837344
ADMIN_IDS = [8327837344, 8279690595, 7738104912]

DAY_SECONDS = 86400
REVIVE_SECONDS = 21600

# =========================================================
# 🔌 DATABASE CONNECTION
# =========================================================
print("🔄 Connecting to MongoDB...")
try:
    client = MongoClient(MONGO_URL, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
    db = client["miku_database"]
    users_col = db["users"]
    groups_col = db["groups"]
    config_col = db["config"]
    client.admin.command('ping')
    print("✅ MongoDB Connected Successfully!")
except Exception as e:
    print(f"❌ Connection Failed: {e}")
    exit()

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# 🛍️ SHOP ITEMS
SHOP_ITEMS = {
    "rose": {"name": "Rose", "icon": "🌹", "price": 500},
    "chocolate": {"name": "Chocolate", "icon": "🍫", "price": 800},
    "ring": {"name": "Ring", "icon": "💍", "price": 2000},
    "teddy": {"name": "Teddy Bear", "icon": "🧸", "price": 1500},
    "pizza": {"name": "Pizza", "icon": "🍕", "price": 600},
    "surprise": {"name": "Surprise Box", "icon": "🎁", "price": 2500},
    "puppy": {"name": "Puppy", "icon": "🐶", "price": 3000},
    "cake": {"name": "Cake", "icon": "🎂", "price": 1000},
    "letter": {"name": "Love Letter", "icon": "💌", "price": 400},
    "cat": {"name": "Cat", "icon": "🐱", "price": 2500}
}

# =========================================================
# 🛠️ HELPER FUNCTIONS
# =========================================================

def is_admin(uid):
    return uid == OWNER_ID or uid in ADMIN_IDS

def check_admin(m):
    if is_admin(m.from_user.id): return True
    bot.reply_to(m, "⚠️ <b>Admin/Owner Command Only.</b>")
    return False

def eco_locked():
    cfg = config_col.find_one({"_id": "settings"})
    if not cfg: return False
    return cfg.get("locked", False)

def is_group_locked(chat_id):
    grp = groups_col.find_one({"_id": chat_id})
    if not grp: return False
    return grp.get("eco_disabled", False)

def track_chat(m):
    if m.chat.type != 'private':
        groups_col.update_one(
            {"_id": m.chat.id}, 
            {"$set": {"name": m.chat.title}}, 
            upsert=True
        )

def get_user(uid, name):
    uid = int(uid)
    user = users_col.find_one({"_id": uid})
    if not user:
        user = {
            "_id": uid,
            "name": name,
            "balance": 1000,
            "kills": 0,
            "status": "alive",
            "death_time": 0,
            "protection": 0,
            "last_daily": 0,
            "inventory": {}
        }
        users_col.insert_one(user)
    else:
        if user["name"] != name:
            users_col.update_one({"_id": uid}, {"$set": {"name": name}})
    return user

def check_death(uid):
    uid = int(uid)
    user = users_col.find_one({"_id": uid})
    if not user: return False
    if user["status"] == "dead":
        if time.time() > user["death_time"] + REVIVE_SECONDS:
            users_col.update_one({"_id": uid}, {"$set": {"status": "alive", "death_time": 0}})
            return False
        return True
    return False

# =========================================================
# 🆕 TRACKING HANDLERS
# =========================================================

@bot.message_handler(content_types=['new_chat_members'])
def new_member(message):
    if bot.get_me().id in [m.id for m in message.new_chat_members]:
        groups_col.update_one(
            {"_id": message.chat.id}, 
            {"$set": {"name": message.chat.title, "eco_disabled": False}}, 
            upsert=True
        )
        bot.reply_to(message, "👋 Thanks for adding me! Use /help to see commands.")

# =========================================================
# 📜 START & HELP MENU
# =========================================================

@bot.message_handler(commands=['start'])
def start(message):
    get_user(message.from_user.id, message.from_user.first_name)
    track_chat(message)
    
    text = (
        "✨ <b>Hey, I’m Miku 🌸</b>\n"
        "━━━━━━━━━━━━━━\n"
        "💗 Simple, smart & friendly chat bot\n\n"
        "• 💬 Easy conversations\n"
        "• 🎮 Games and fun features\n"
        "• 👥 Group & private support\n"
        "• 🛡 Safe and smooth experience\n\n"
        "✦ <b>Choose an option below</b>"
    )

    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💬 Talk to Miku", callback_data="talk"),
        InlineKeyboardButton("🎮 Games", callback_data="games")
    )
    kb.add(
        InlineKeyboardButton(
            "👥 Add to Group",
            url=f"https://t.me/{bot.get_me().username}?startgroup=true"
        )
    )
    kb.add(
        InlineKeyboardButton("🆘 Help", callback_data="help")
    )

    bot.send_message(message.chat.id, text, reply_markup=kb)

@bot.message_handler(commands=['help'])
def help_cmd(message):
    text = (
        "📖 <b>Help Menu</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        "👤 <b>User Commands</b>\n"
        "🏠 /start – Main Menu\n"
        "❓ /help – Show command list\n"
        "🎁 /daily – Daily reward\n"
        "💰 /bal – Check balance\n"
        "🗡️ /rob – Rob money\n"
        "☠️ /kill – Kill user\n"
        "🛡️ /protect – Buy shield\n"
        "🛒 /items – Shop\n"
        "🎀 /gift – Gift item\n"
        "🏆 /toprich – Leaderboard\n"
        "❤️ /revive – Revive yourself/friend ($400)\n\n"
        "👥 <b>Group Admin Commands</b>\n"
        "🚫 /close – Disable games\n"
        "✅ /open – Enable games\n\n"
        "🫡 <b>Admin / Owner Commands</b>\n"
        "💸 /transfer – Manage Money\n"
        "🛡️ /giveprot – Give Protection\n"
        "💔 /breakshield – Remove Protection\n"
        "🔒 /lockeconomy – Lock Economy\n"
        "🔓 /unlockeconomy – Unlock Economy\n"
        "📢 /broadcast – Send Message/Media to All"
    )
    bot.send_message(message.chat.id, text)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "help":
        help_cmd(call.message)
        bot.answer_callback_query(call.id)
    elif call.data == "games":
        game_text = (
            "🎮 <b>Gaming Commands:</b>\n"
            "/daily — Daily reward\n"
            "/bal — Check balance\n"
            "/rob — Rob money\n"
            "/kill — Kill user\n"
            "/protect — Buy shield\n"
            "/items — Shop\n"
            "/gift — Gift item\n"
            "/toprich — Leaderboard"
        )
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, game_text)
    elif call.data == "talk":
        talk_text = "💬 <b>Chatting:</b>\nJust add me to a group and say <i>Hello Miku</i>!"
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, talk_text)

# =========================================================
# 👤 USER COMMANDS
# =========================================================

def can_play(m):
    track_chat(m)
    if eco_locked(): 
        bot.reply_to(m, "🔒 Global Economy is locked by Owner.")
        return False
    if m.chat.type != 'private' and is_group_locked(m.chat.id):
        bot.reply_to(m, "🚫 Economy commands are disabled in this group.")
        return False
    return True

@bot.message_handler(commands=['daily'])
def daily(m):
    if not can_play(m): return
    uid = m.from_user.id
    u = get_user(uid, m.from_user.first_name)

    if check_death(uid): return bot.reply_to(m, "💀 <b>You are dead!</b>\nUse /revive to come back.")

    if time.time() - u["last_daily"] < DAY_SECONDS:
        rem = int(DAY_SECONDS - (time.time() - u["last_daily"]))
        hours, mins = rem // 3600, (rem % 3600) // 60
        return bot.reply_to(m, f"⏳ Come back in <b>{hours}h {mins}m</b>")

    users_col.update_one(
        {"_id": uid},
        {"$inc": {"balance": 1500}, "$set": {"last_daily": time.time()}}
    )
    bot.reply_to(m, "✅ You received: <b>$1500</b> daily reward!")

@bot.message_handler(commands=['bal', 'balance'])
def bal(m):
    track_chat(m)
    if m.reply_to_message:
        uid = m.reply_to_message.from_user.id
        name = m.reply_to_message.from_user.first_name
    else:
        uid = m.from_user.id
        name = m.from_user.first_name

    u = get_user(uid, name)
    check_death(uid)
    
    rank = users_col.count_documents({"balance": {"$gt": u["balance"]}}) + 1
    status = "dead" if check_death(uid) else "alive"

    msg = (
        f"👤 <b>Name:</b> {u['name']}\n"
        f"💰 <b>Total Balance:</b> ${u['balance']}\n"
        f"🏆 <b>Global Rank:</b> {rank}\n"
        f"❤️ <b>Status:</b> {status}\n"
        f"⚔️ <b>Kills:</b> {u['kills']}"
    )
    bot.reply_to(m, msg)

@bot.message_handler(commands=['revive'])
def revive(m):
    if not can_play(m): return
    sender_id = m.from_user.id
    sender = get_user(sender_id, m.from_user.first_name)
    
    cost = 400
    if sender["balance"] < cost:
        return bot.reply_to(m, f"❌ You need ${cost} to revive.")

    if m.reply_to_message:
        target_id = m.reply_to_message.from_user.id
        target = get_user(target_id, m.reply_to_message.from_user.first_name)
        if target["status"] == "alive":
            return bot.reply_to(m, f"⚠️ <b>{target['name']}</b> is already alive!")
        users_col.update_one({"_id": target_id}, {"$set": {"status": "alive", "death_time": 0}})
        users_col.update_one({"_id": sender_id}, {"$inc": {"balance": -cost}})
        bot.reply_to(m, f"🚑 You revived <b>{target['name']}</b> for ${cost}!")
    else:
        if sender["status"] == "alive":
            return bot.reply_to(m, "⚠️ You are already alive!")
        users_col.update_one({"_id": sender_id}, {"$set": {"status": "alive", "death_time": 0}, "$inc": {"balance": -cost}})
        bot.reply_to(m, f"❤️ You revived yourself! -${cost}")

@bot.message_handler(commands=['rob'])
def rob(m):
    if not can_play(m): return
    if not m.reply_to_message: return bot.reply_to(m, "⚠️ Reply to a user.")
    
    r_id = m.from_user.id
    v_id = m.reply_to_message.from_user.id
    if r_id == v_id: return bot.reply_to(m, "⚠️ Cannot rob yourself.")

    robber = get_user(r_id, m.from_user.first_name)
    victim = get_user(v_id, m.reply_to_message.from_user.first_name)

    # ✅ DEAD CHECK REMOVED
    if time.time() < victim["protection"]: return bot.reply_to(m, f"🛡️ <b>{victim['name']}</b> is protected.")

    try: amt = int(m.text.split()[1])
    except: amt = 1000

    if amt <= 0: return bot.reply_to(m, "❌ Invalid amount.")
    if victim["balance"] <= 0: return bot.reply_to(m, "❌ Victim has no money.")

    taken = min(amt, victim["balance"])

    users_col.update_one({"_id": r_id}, {"$inc": {"balance": taken}})
    users_col.update_one({"_id": v_id}, {"$inc": {"balance": -taken}})

    bot.reply_to(m, f"💸 Robbed <b>${taken}</b> from {victim['name']}")

@bot.message_handler(commands=['kill'])
def kill(m):
    if not can_play(m): return
    if not m.reply_to_message: return bot.reply_to(m, "⚠️ Reply to a user.")

    k_id = m.from_user.id
    v_id = m.reply_to_message.from_user.id
    if k_id == v_id: return bot.reply_to(m, "⚠️ Cannot kill yourself.")

    killer = get_user(k_id, m.from_user.first_name)
    victim = get_user(v_id, m.reply_to_message.from_user.first_name)

    if check_death(k_id): return bot.reply_to(m, "💀 <b>You are dead!</b>")
    if check_death(v_id): return bot.reply_to(m, "💀 <b>Victim is already dead.</b>")
    if time.time() < victim["protection"]: return bot.reply_to(m, f"🛡️ <b>{victim['name']}</b> is protected.")

    reward = random.randint(200, 600)
    users_col.update_one({"_id": k_id}, {"$inc": {"kills": 1, "balance": reward}})
    users_col.update_one({"_id": v_id}, {"$set": {"status": "dead", "death_time": time.time()}})

    bot.reply_to(m, f"🔪 Killed {victim['name']} | Earned: <b>${reward}</b>")

@bot.message_handler(commands=['protect'])
def protect(m):
    if not can_play(m): return
    uid = m.from_user.id
    u = get_user(uid, m.from_user.first_name)

    if check_death(uid): return bot.reply_to(m, "💀 Dead users cannot buy protection.")
    
    if u["protection"] > time.time():
        return bot.reply_to(m, "🛡️ You are already protected!")

    try: plan = m.text.split()[1].lower()
    except: return bot.reply_to(m, "⚠️ Usage: /protect 1d | 2d | 3d")

    costs = {"1d": 500, "2d": 1000, "3d": 1500}
    durs = {"1d": DAY_SECONDS, "2d": DAY_SECONDS*2, "3d": DAY_SECONDS*3}

    if plan not in costs: return bot.reply_to(m, "❌ Invalid plan.")
    if u["balance"] < costs[plan]: return bot.reply_to(m, "❌ Not enough money.")

    new_time = time.time() + durs[plan]
    users_col.update_one(
        {"_id": uid},
        {"$inc": {"balance": -costs[plan]}, "$set": {"protection": new_time}}
    )
    bot.reply_to(m, f"🛡️ Protected for <b>{plan}</b>.")

@bot.message_handler(commands=['give'])
def give(m):
    if not can_play(m): return
    if not m.reply_to_message: return bot.reply_to(m, "⚠️ Reply to a user.")
    try: amt = int(m.text.split()[1])
    except: return bot.reply_to(m, "❌ Usage: /give <amount>")
    
    if amt <= 0: return bot.reply_to(m, "❌ Invalid amount.")
    s_id, r_id = m.from_user.id, m.reply_to_message.from_user.id
    sender = get_user(s_id, m.from_user.first_name)
    receiver = get_user(r_id, m.reply_to_message.from_user.first_name)
    
    if sender["balance"] < amt: return bot.reply_to(m, "❌ Not enough money.")
    
    users_col.update_one({"_id": s_id}, {"$inc": {"balance": -amt}})
    users_col.update_one({"_id": r_id}, {"$inc": {"balance": amt}})
    bot.reply_to(m, f"💸 Gave <b>${amt}</b> to {receiver['name']}")

@bot.message_handler(commands=['items', 'shop'])
def shop(m):
    if not can_play(m): return
    text = "🛒 <b>ITEM SHOP</b>\n\n"
    for k, v in SHOP_ITEMS.items():
        text += f"{v['icon']} <b>{v['name']}</b> — ${v['price']}\n"
    text += "\n🎁 Usage: /gift (reply) itemname"
    bot.reply_to(m, text)

@bot.message_handler(commands=['gift'])
def gift(m):
    if not can_play(m): return
    if not m.reply_to_message: return bot.reply_to(m, "⚠️ Reply to gift.")
    try: item = m.text.split(maxsplit=1)[1].lower()
    except: return bot.reply_to(m, "⚠️ Usage: /gift <itemname>")
    
    key = next((k for k, v in SHOP_ITEMS.items() if k in item or v['name'].lower() in item), None)
    if not key: return bot.reply_to(m, "❌ Item not found.")
    
    s_id, r_id = m.from_user.id, m.reply_to_message.from_user.id
    sender = get_user(s_id, m.from_user.first_name)
    rec = get_user(r_id, m.reply_to_message.from_user.first_name)
    
    price = SHOP_ITEMS[key]['price']
    if sender["balance"] < price: return bot.reply_to(m, "❌ Not enough money.")
    
    users_col.update_one({"_id": s_id}, {"$inc": {"balance": -price}})
    users_col.update_one({"_id": r_id}, {"$inc": {f"inventory.{key}": 1}})
    bot.reply_to(m, f"🎁 {sender['name']} gifted {SHOP_ITEMS[key]['icon']} to {rec['name']}!")

@bot.message_handler(commands=['toprich'])
def toprich(m):
    top_users = users_col.find().sort("balance", -1).limit(10)
    msg = "🏆 <b>Top Richest:</b>\n"
    for i, u in enumerate(top_users, 1):
        msg += f"{i}. {u['name']} — ${u['balance']}\n"
    bot.reply_to(m, msg)

@bot.message_handler(commands=['topkill'])
def topkill(m):
    top_users = users_col.find().sort("kills", -1).limit(10)
    msg = "💀 <b>Top Killers:</b>\n"
    for i, u in enumerate(top_users, 1):
        msg += f"{i}. {u['name']} — {u['kills']} Kills\n"
    bot.reply_to(m, msg)

# =========================================================
# ⚙️ GROUP ADMIN COMMANDS (CLOSE/OPEN)
# =========================================================

@bot.message_handler(commands=['close', 'open'])
def toggle_group_eco(m):
    if m.chat.type == 'private':
        return bot.reply_to(m, "❌ This command is for Groups only.")
    
    user_stat = bot.get_chat_member(m.chat.id, m.from_user.id).status
    if user_stat not in ['administrator', 'creator'] and not is_admin(m.from_user.id):
        return bot.reply_to(m, "⚠️ <b>Admin Command only.</b>")
        
    is_close = m.text.startswith("/close")
    groups_col.update_one(
        {"_id": m.chat.id}, 
        {"$set": {"eco_disabled": is_close, "name": m.chat.title}}, 
        upsert=True
    )
    if is_close:
        bot.reply_to(m, "🚫 All Economy commands disabled")
    else:
        bot.reply_to(m, "✅ All Economy commands enabled.")

# =========================================================
# 👑 BOT ADMIN COMMANDS (BROADCAST FIXED)
# =========================================================

@bot.message_handler(commands=['reset'])
def reset_eco(m):
    if m.from_user.id != OWNER_ID:
        return bot.reply_to(m, "⚠️ <b>Owner Command only.</b>")
    users_col.delete_many({})
    bot.reply_to(m, "♻️ All economy data has been reset.")

@bot.message_handler(commands=['broadcast'])
def broadcast(m):
    if not check_admin(m): return
    
    if m.reply_to_message:
        msg_id = m.reply_to_message.message_id
        from_chat = m.chat.id
        is_reply = True
        msg_text = None
    elif len(m.text.split()) > 1:
        msg_text = m.text.split(maxsplit=1)[1]
        is_reply = False
    else:
        return bot.reply_to(m, "⚠️ <b>Usage:</b>\n1. Reply to media/text with /broadcast\n2. Type /broadcast <message>")

    status_msg = bot.reply_to(m, "📢 Broadcast started...")
    
    sent = 0
    failed = 0
    
    # Get Targets
    targets = []
    for u in users_col.find({}, {"_id": 1}): targets.append(u["_id"])
    for g in groups_col.find({}, {"_id": 1}): targets.append(g["_id"])
    
    for chat_id in targets:
        try:
            if is_reply:
                bot.copy_message(chat_id, from_chat, msg_id)
            else:
                bot.send_message(chat_id, msg_text)
            sent += 1
            time.sleep(0.05)
        except:
            failed += 1
            
    bot.edit_message_text(f"✅ Broadcast Complete!\n📢 Sent to: {sent}\n❌ Failed: {failed}", m.chat.id, status_msg.message_id)

@bot.message_handler(commands=['transfer'])
def transfer(m):
    if not check_admin(m): return
    if not m.reply_to_message: return bot.reply_to(m, "⚠️ Reply to user.")
    try: amt = int(m.text.split()[1])
    except: return bot.reply_to(m, "❌ Usage: /transfer <amount>")
    
    target_id = m.reply_to_message.from_user.id
    target_name = m.reply_to_message.from_user.first_name
    get_user(target_id, target_name)

    users_col.update_one({"_id": target_id}, {"$inc": {"balance": amt}})
    action = "Added" if amt > 0 else "Removed"
    bot.reply_to(m, f"💰 <b>{action} ${abs(amt)}</b> to {target_name}'s balance.")

@bot.message_handler(commands=['forcerev'])
def forcerev(m):
    if not check_admin(m): return
    if not m.reply_to_message: return bot.reply_to(m, "⚠️ Reply to user.")
    tid = m.reply_to_message.from_user.id
    get_user(tid, "User")
    users_col.update_one({"_id": tid}, {"$set": {"status": "alive", "death_time": 0}})
    bot.reply_to(m, "🚑 Force Revived.")

@bot.message_handler(commands=['forcekill'])
def forcekill(m):
    if not check_admin(m): return
    if not m.reply_to_message: return bot.reply_to(m, "⚠️ Reply to user.")
    tid = m.reply_to_message.from_user.id
    get_user(tid, "User")
    users_col.update_one({"_id": tid}, {"$set": {"status": "dead", "death_time": time.time()}})
    bot.reply_to(m, "☠️ Force Killed.")

@bot.message_handler(commands=['giveprot'])
def giveprot(m):
    if not check_admin(m): return
    if not m.reply_to_message: return bot.reply_to(m, "⚠️ Reply to user.")
    tid = m.reply_to_message.from_user.id
    target = get_user(tid, m.reply_to_message.from_user.first_name)
    
    new_prot = time.time() + (DAY_SECONDS * 2)
    users_col.update_one({"_id": tid}, {"$set": {"protection": new_prot}})
    bot.reply_to(m, f"🛡️ Given 2 Days Protection to {target['name']}.")

@bot.message_handler(commands=['breakshield'])
def breakprot(m):
    if not check_admin(m): return
    if not m.reply_to_message: return bot.reply_to(m, "⚠️ Reply to user.")
    tid = m.reply_to_message.from_user.id
    target = get_user(tid, m.reply_to_message.from_user.first_name)
    
    users_col.update_one({"_id": tid}, {"$set": {"protection": 0}})
    bot.reply_to(m, f"🛡️ Protection Removed from {target['name']}.")

@bot.message_handler(commands=['lockeconomy'])
def lockeco(m):
    if not check_admin(m): return
    config_col.update_one({"_id": "settings"}, {"$set": {"locked": True}}, upsert=True)
    bot.reply_to(m, "🔒 Economy LOCKED.")

@bot.message_handler(commands=['unlockeconomy'])
def unlockeco(m):
    if not check_admin(m): return
    config_col.update_one({"_id": "settings"}, {"$set": {"locked": False}}, upsert=True)
    bot.reply_to(m, "🔓 Economy UNLOCKED.")

print("🚀 Miku Bot (Final GitHub Ready) is Online...")
bot.infinity_polling()
