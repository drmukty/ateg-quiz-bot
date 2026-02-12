import os
import sys
import time
import random
import sqlite3
import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8276735681:AAE5JJT8dLHN6fEFIkEtI8SM2cZa8t83aa8"
GROUP_CHAT_ID = "@ATEGDV_official"  # YOUR GROUP - CHANGED!

# ==================== SETUP LOGGING ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== DATABASE SETUP ====================
def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect('quiz_bot.db', check_same_thread=False)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, 
                  username TEXT, 
                  first_name TEXT,
                  joined_date DATE)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS points
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER, 
                  points INTEGER, 
                  week_start DATE,
                  question_id INTEGER,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS questions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  question TEXT, 
                  option1 TEXT, option2 TEXT, option3 TEXT, option4 TEXT,
                  correct_option INTEGER)''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized")

# ==================== ADD ALL 80 ATEG QUESTIONS ====================
def add_questions():
    """Add all ATEG questions to database"""
    conn = sqlite3.connect('quiz_bot.db', check_same_thread=False)
    c = conn.cursor()
    
    c.execute("DELETE FROM questions")
    
    questions = [
        # Questions 1-10
        (1, "In most traditional housing systems, rent is treated as:",
         "An investment", "A loan repayment", "A terminal expense", "Equity contribution", 3),
        (2, "ATEG reframes rent primarily as:",
         "Debt repayment", "Equity financing", "A circulating economic input", "Speculative capital", 3),
        (3, "In ATEG, rent payments create:",
         "Long-term liabilities", "Ownership debt", "Hidden obligations", "No liabilities", 4),
        (4, "Rent in ATEG is most similar to paying for:",
         "A mortgage", "Electricity and utilities", "Equity shares", "Bonds", 2),
        (5, "ATEG ensures rent does NOT represent:",
         "Usage payment", "Service access", "Loan financing", "Operational support", 3),
        (6, "In conventional systems, rent often disappears into:",
         "Long-term reinvestment", "Community growth", "Private consumption", "Token mechanisms", 3),
        (7, "In ATEG, rent remains inside:",
         "External markets", "The economic loop", "Speculative pools", "Debt markets", 2),
        (8, "Which is NOT supported by rent in ATEG?",
         "Property maintenance", "Operational continuity", "Asset liquidation", "System reinvestment", 3),
        (9, "ATEG replaces linear extraction with:",
         "Instant liquidity", "Circular economic flow", "Fixed-term speculation", "Short-term profit", 2),
        (10, "A circular model emphasizes:",
         "Pay and forget", "Reuse and resilience", "Fast exits", "Asset flipping", 2),
        # Questions 11-20
        (11, "In ATEG, real estate is treated as:",
         "A trading asset", "A liquidity tool", "Value preservation infrastructure", "A speculative instrument", 3),
        (12, "ATEG buildings are intentionally:",
         "Highly liquid", "Volatile", "Illiquid and stable", "Short-term focused", 3),
        (13, "Liquidity in ATEG comes primarily from:",
         "Asset sales", "Market speculation", "Real-world usage", "Token minting", 3),
        (14, "Which contributes to liquidity generation in ATEG?",
         "Building liquidation", "Housing occupancy", "Asset flipping", "Market manipulation", 2),
        (15, "ATEG avoids which of the following?",
         "Predictable value flow", "Sustainable housing", "Debt-driven pressure", "Long-term stability", 3),
        (16, "ATEG supports balance-sheet stability through:",
         "Artificial liquidity", "Forced sales", "Usage-based flow", "Speculation", 3),
        (17, "The core principle of ATEG separates:",
         "Rent and ownership", "Value preservation and liquidity", "Housing and energy", "Tokens and blockchain", 2),
        (18, "In ATEG, buildings primarily:",
         "Generate fast liquidity", "Hold long-term value", "Enable speculation", "Fund traders", 2),
        (19, "Rent in ATEG mainly:",
         "Disappears", "Accumulates interest", "Circulates capital", "Creates debt", 3),
        (20, "Usage in ATEG:",
         "Drains the system", "Sustains the system", "Causes instability", "Freezes value", 2),
        # Questions 21-30
        (21, "HST aligns two different economic clocks:",
         "Annual and weekly", "Fast trading and slow living", "Global and local", "Debt and equity", 2),
        (22, "The Monthly Index Price is taken:",
         "Every hour", "Daily", "Weekly", "Monthly", 4),
        (23, "Tokens are removed from circulation through:",
         "Minting and staking", "Burn and freeze", "Trading fees", "Inflation", 2),
        (24, "Supply reduction in HST is based on:",
         "Market hype", "Trading volume", "Real usage", "Speculation", 3),
        (25, "HST allows trading and housing to:",
         "Compete", "Collapse", "Coexist", "Replace each other", 3),
        (26, "Traditional homeownership often fails because:",
         "Payments are too flexible", "Interest consumes most payments", "Ownership is immediate", "Risk is low", 2),
        (27, "In ATEG, residents:",
         "Wait years to live", "Live in the home immediately", "Rent without progress", "Pay interest upfront", 2),
        (28, "Each ATEG payment:",
         "Is wasted", "Builds debt", "Increases stake", "Creates penalties", 3),
        (29, "ATEG housing aims to be:",
         "Exclusive", "Speculative", "Accessible and fair", "Short-term", 3),
        (30, "FlexCo focuses on:",
         "Hype-driven growth", "Noise and speculation", "Long-term stability", "Rapid flipping", 3),
        # Questions 31-40
        (31, "ATEG prioritizes value growth from:",
         "Market excitement", "Tangible projects", "High volatility", "Arbitrage", 2),
        (32, "One goal of ATEG is stabilizing:",
         "Token prices only", "Housing costs", "Trading fees", "Gas prices", 2),
        (33, "ATEG reduces inflation impact by:",
         "Increasing debt", "Anchoring to real assets", "Printing tokens", "Fast trading", 2),
        (34, "Transparency and compliance in ATEG are:",
         "Optional", "Delayed", "Built-in", "Ignored", 3),
        (35, "The missing layer in digital assets was:",
         "Technical scalability", "Security", "Monthly economic alignment", "Speed", 3),
        (36, "Humans primarily live economically on:",
         "Daily cycles", "Weekly cycles", "Monthly cycles", "Yearly cycles", 3),
        (37, "Crypto markets typically operate in:",
         "Months", "Days", "Seconds", "Years", 3),
        (38, "Stablecoins fail to provide:",
         "Price stability", "Monthly life stability", "Liquidity", "Speed", 2),
        (39, "The Monthly Economic Layer introduces:",
         "Constant repricing", "Monthly price reference", "Arbitrary valuation", "Unlimited inflation", 2),
        (40, "HST combines how many unique elements?",
         "Two", "Three", "Four", "Five", 3),
        # Questions 41-50
        (41, "Demand in HST is built from:",
         "Speculative traders", "Recurring real revenues", "Marketing hype", "Token unlocks", 2),
        (42, "Deflation in HST is:",
         "Random", "Daily", "Controlled and monthly", "Artificial", 3),
        (43, "A monthly-aligned asset helps with:",
         "Gambling", "Financial stress", "Price chaos", "Asset dumping", 2),
        (44, "ATEG complements Bitcoin by:",
         "Replacing it", "Competing directly", "Adding monthly alignment", "Increasing volatility", 3),
        (45, "ATEG is NOT described as:",
         "A meme coin", "Infrastructure", "A housing ecosystem", "A monthly model", 1),
        (46, "Traditional leases often force people to:",
         "Adapt housing to life", "Adapt life to contracts", "Gain equity fast", "Reduce costs", 2),
        (47, "ATEG removes:",
         "Flexibility", "Fixed-term rental traps", "Transparency", "Ownership paths", 2),
        (48, "Transitioning to ownership in ATEG includes:",
         "Penalties", "Resets", "Seamless continuity", "Interest", 3),
        (49, "ATEG FlexCo rent is typically:",
         "Above market", "Equal to market", "25–35% below market", "Unregulated", 3),
        (50, "Lower rent in ATEG is:",
         "A marketing trick", "A temporary discount", "A design choice", "A subsidy", 3),
        # Questions 51-60
        (51, "Security deposits in ATEG are reduced by up to:",
         "10%", "20%", "35%", "50%", 3),
        (52, "ATEG rent-to-own interest rate is:",
         "Variable", "Market-based", "0%", "Hidden", 3),
        (53, "ATEG is designed to remain stable across:",
         "Bull markets only", "Bear markets only", "All market cycles", "Short-term rallies", 3),
        (54, "ATEG prioritizes:",
         "Liquidity before people", "Profit before access", "Access before ownership", "Speculation before utility", 3),
        (55, "Blockchain in ATEG is used mainly for:",
         "Hype", "Fast trading", "Transparency and records", "Arbitrage", 3),
        (56, "ATEG converts usage into:",
         "Loss", "Debt", "Ownership progress", "Fees", 3),
        (57, "The future of finance belongs to systems that:",
         "Are the loudest", "Respect people and progress", "Move the fastest", "Create hype", 2),
        (58, "ATEG's economic model is anchored in:",
         "Synthetic value", "Real homes and people", "Price manipulation", "Token speculation", 2),
        (59, "Traditional rent usually builds:",
         "Equity", "Ownership", "No lasting value", "Transparency", 3),
        (60, "ATEG's rent model ensures progress:",
         "Is delayed", "Is lost", "Counts from day one", "Depends on approval", 3),
        # Questions 61-70
        (61, "The ATEG system avoids:",
         "Predictability", "Stability", "Forced asset sales", "Transparency", 3),
        (62, "Value in ATEG grows primarily from:",
         "Token price action", "Participation and usage", "Leverage", "Arbitrage", 2),
        (63, "ATEG treats housing as:",
         "A commodity", "A liability", "Infrastructure", "A short-term product", 3),
        (64, "Monthly alignment improves:",
         "Volatility", "Budgeting and planning", "Speculation", "Arbitrage", 2),
        (65, "ATEG's model reduces:",
         "Stability", "Dignity", "Financial strain", "Transparency", 3),
        (66, "Ownership in ATEG is:",
         "Punitive", "Interest-heavy", "Transparent and fair", "Delayed indefinitely", 3),
        (67, "Traditional housing systems are described as:",
         "Resident-centered", "Extractive", "Flexible", "Progressive", 2),
        (68, "ATEG prioritizes:",
         "Speed over logic", "Logic over noise", "Noise over structure", "Volatility over stability", 2),
        (69, "The ATEG ecosystem reinvests into:",
         "Speculation", "Short-term gains", "Growth and continuity", "Token dumping", 3),
        (70, "ATEG's design goal is:",
         "Market dominance", "Artificial growth", "Long-term resilience", "Fast exits", 3),
        # Questions 71-80
        (71, "Monthly deflation in HST is tied to:",
         "Trading volume", "Real economic activity", "Market cycles", "Token burns only", 2),
        (72, "ATEG aligns digital assets with:",
         "High-frequency trading", "Human economic life", "Arbitrage windows", "Speculative cycles", 2),
        (73, "The system avoids forcing:",
         "Stability", "Planning", "Clocks to match unnaturally", "Monthly alignment", 3),
        (74, "ATEG allows value to:",
         "Drain", "Reset", "Accumulate gradually", "Inflate rapidly", 3),
        (75, "Real income in ATEG comes from:",
         "Token sales", "Living and usage", "Market pumps", "Leverage", 2),
        (76, "ATEG is best described as:",
         "A speculative token", "A housing meme", "Economic infrastructure", "A trading bot", 3),
        (77, "Traditional rent systems mainly benefit:",
         "Residents", "Communities", "Extractive owners", "Long-term stability", 3),
        (78, "ATEG's rent model promotes:",
         "Dependency", "Uncertainty", "Predictable value flow", "Volatility", 3),
        (79, "The ATEG mission focuses on:",
         "Complexity", "Arbitrary rules", "Freedom and clarity", "Lock-in contracts", 3),
        (80, "ATEG was created to:",
         "Compete with all crypto", "Replace housing markets", "Bridge real life and blockchain", "Increase speculation", 3),
    ]
    
    for q in questions:
        c.execute('''INSERT INTO questions (id, question, option1, option2, option3, option4, correct_option)
                    VALUES (?,?,?,?,?,?,?)''', q)
    
    conn.commit()
    conn.close()
    logger.info(f"Added {len(questions)} ATEG questions")

# ==================== QUIZ BOT CLASS ====================
class QuizBot:
    def __init__(self):
        self.active_question = None
        self.answered_users = set()
        self.current_question_msg_id = None
        self.application = None
    
    def get_week_start(self):
        today = datetime.now().date()
        return today - timedelta(days=today.weekday())

quiz_bot = QuizBot()

# ==================== DATABASE FUNCTIONS ====================
def add_user(user_id, username, first_name):
    conn = sqlite3.connect('quiz_bot.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''INSERT OR IGNORE INTO users (user_id, username, first_name, joined_date)
                 VALUES (?, ?, ?, ?)''', (user_id, username, first_name, datetime.now().date()))
    conn.commit()
    conn.close()

def add_points(user_id, points, question_id):
    conn = sqlite3.connect('quiz_bot.db', check_same_thread=False)
    c = conn.cursor()
    week_start = quiz_bot.get_week_start()
    c.execute('''INSERT INTO points (user_id, points, week_start, question_id)
                 VALUES (?, ?, ?, ?)''', (user_id, points, week_start, question_id))
    conn.commit()
    conn.close()

def get_leaderboard(week_start):
    conn = sqlite3.connect('quiz_bot.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''SELECT u.user_id, u.username, u.first_name, SUM(p.points) as total_points
                 FROM points p
                 JOIN users u ON p.user_id = u.user_id
                 WHERE p.week_start = ?
                 GROUP BY p.user_id
                 ORDER BY total_points DESC
                 LIMIT 10''', (week_start,))
    results = c.fetchall()
    conn.close()
    return results

def get_user_points(user_id, week_start):
    conn = sqlite3.connect('quiz_bot.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''SELECT SUM(points) FROM points 
                 WHERE user_id = ? AND week_start = ?''', (user_id, week_start))
    total = c.fetchone()[0] or 0
    conn.close()
    return total

# ==================== BOT HANDLERS ====================
async def start_quiz(context: ContextTypes.DEFAULT_TYPE):
    """Send a new quiz question every 15 minutes"""
    try:
        conn = sqlite3.connect('quiz_bot.db', check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT * FROM questions ORDER BY RANDOM() LIMIT 1")
        question = c.fetchone()
        conn.close()
        
        if not question:
            return
        
        q_id, q_text, opt1, opt2, opt3, opt4, correct = question
        
        quiz_bot.active_question = {
            'id': q_id,
            'correct': correct,
            'answered': False,
            'winner': None
        }
        quiz_bot.answered_users = set()
        
        keyboard = [
            [
                InlineKeyboardButton(f"🟢 {opt1}", callback_data=f"ans_{q_id}_1"),
                InlineKeyboardButton(f"🔵 {opt2}", callback_data=f"ans_{q_id}_2")
            ],
            [
                InlineKeyboardButton(f"🟡 {opt3}", callback_data=f"ans_{q_id}_3"),
                InlineKeyboardButton(f"🔴 {opt4}", callback_data=f"ans_{q_id}_4")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = await context.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=f"🧠 *ATEG QUIZ TIME!* 🧠\n\n"
                 f"❓ {q_text}\n\n"
                 f"⏳ *You have 60 seconds!*\n"
                 f"🏆 *First correct answer wins 5 points!*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        quiz_bot.current_question_msg_id = message.message_id
        logger.info(f"Question sent: {q_text[:50]}...")
        
        # Schedule answer reveal after 60 seconds
        context.job_queue.run_once(reveal_answer, 60, data=question)
        
    except Exception as e:
        logger.error(f"Error in start_quiz: {e}")

async def reveal_answer(context: ContextTypes.DEFAULT_TYPE):
    """Reveal the correct answer after 1 minute"""
    try:
        question = context.job.data
        q_id, q_text, opt1, opt2, opt3, opt4, correct = question
        
        options = [opt1, opt2, opt3, opt4]
        correct_text = options[correct - 1]
        
        if quiz_bot.current_question_msg_id:
            winner_text = ""
            if quiz_bot.active_question and quiz_bot.active_question['answered']:
                winner_text = f"\n\n🏆 *Winner:* {quiz_bot.active_question['winner']} (+5 points)"
            else:
                winner_text = "\n\n❌ *No one answered correctly this time!*"
            
            await context.bot.edit_message_text(
                chat_id=GROUP_CHAT_ID,
                message_id=quiz_bot.current_question_msg_id,
                text=f"🧠 *QUIZ - TIME'S UP!* 🧠\n\n"
                     f"❓ {q_text}\n\n"
                     f"✅ *Correct Answer:* {correct_text}{winner_text}",
                parse_mode='Markdown'
            )
        
        quiz_bot.active_question = None
        
    except Exception as e:
        logger.error(f"Error in reveal_answer: {e}")

async def answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle answer button clicks"""
    query = update.callback_query
    await query.answer()
    
    if not quiz_bot.active_question:
        await query.edit_message_text(text="⏰ Time's up for this question!")
        return
    
    try:
        data = query.data.split('_')
        q_id = int(data[1])
        selected = int(data[2])
    except:
        await query.edit_message_text(text="❌ Invalid selection!")
        return
    
    user = query.from_user
    user_id = user.id
    username = user.username or user.first_name
    
    if (quiz_bot.active_question and 
        quiz_bot.active_question['id'] == q_id and 
        not quiz_bot.active_question['answered'] and
        user_id not in quiz_bot.answered_users):
        
        quiz_bot.answered_users.add(user_id)
        
        if selected == quiz_bot.active_question['correct']:
            quiz_bot.active_question['answered'] = True
            quiz_bot.active_question['winner'] = f"@{username}" if user.username else user.first_name
            
            add_user(user_id, user.username, user.first_name)
            add_points(user_id, 5, q_id)
            
            mention = f"@{username}" if user.username else user.first_name
            await context.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=f"🎉🎉 *CONGRATULATIONS!* 🎉🎉\n\n"
                     f"🏆 {mention} got the correct answer FIRST!\n\n"
                     f"✨ *+5 POINTS ADDED TO YOUR SCORE!* ✨",
                parse_mode='Markdown'
            )
            
            total_points = get_user_points(user_id, quiz_bot.get_week_start())
            await context.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=f"📊 {mention}, you now have *{total_points} points* this week!",
                parse_mode='Markdown'
            )
            
            await query.edit_message_text(text="✅ *CORRECT!* You won this round! 🏆", 
                                        parse_mode='Markdown')
        else:
            await query.edit_message_text(text="❌ Wrong answer! Try next time!")
    else:
        if user_id in quiz_bot.answered_users:
            await query.edit_message_text(text="⚠️ You already answered this question!")
        else:
            await query.edit_message_text(text="⏰ Someone else already answered correctly!")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show weekly leaderboard"""
    week_start = quiz_bot.get_week_start()
    leaders = get_leaderboard(week_start)
    
    if not leaders:
        await update.message.reply_text(
            "📊 *WEEKLY LEADERBOARD* 📊\n\n"
            "✨ No points yet this week!\n"
            "🎯 Be the first to answer correctly and win 5 points!",
            parse_mode='Markdown'
        )
        return
    
    message = "📊 *🏆 WEEKLY LEADERBOARD 🏆* 📊\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for i, (user_id, username, first_name, points) in enumerate(leaders):
        name = f"@{username}" if username else first_name
        medal = medals[i] if i < len(medals) else f"{i+1}."
        message += f"{medal} {name} — *{points} pts*\n"
    
    week_end = week_start + timedelta(days=6)
    message += f"\n📅 Week: {week_start.strftime('%b %d')} - {week_end.strftime('%b %d')}"
    message += f"\n🔄 Resets every Monday"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def mypoints(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check user's personal points"""
    user = update.effective_user
    week_start = quiz_bot.get_week_start()
    
    total = get_user_points(user.id, week_start)
    
    conn = sqlite3.connect('quiz_bot.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''SELECT user_id, SUM(points) as total_points
                 FROM points 
                 WHERE week_start = ?
                 GROUP BY user_id
                 ORDER BY total_points DESC''', (week_start,))
    rankings = c.fetchall()
    conn.close()
    
    rank = next((i+1 for i, (uid, _) in enumerate(rankings) if uid == user.id), 0)
    total_players = len(rankings)
    
    mention = f"@{user.username}" if user.username else user.first_name
    
    await update.message.reply_text(
        f"📊 *YOUR WEEKLY SCORE* 📊\n\n"
        f"👤 {mention}\n"
        f"⭐ Points: *{total}*\n"
        f"🏆 Rank: *{rank}* of {total_players}\n\n"
        f"💡 Answer first to earn 5 points!",
        parse_mode='Markdown'
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show quiz statistics"""
    conn = sqlite3.connect('quiz_bot.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM questions")
    total_questions = c.fetchone()[0]
    
    week_start = quiz_bot.get_week_start()
    c.execute('''SELECT COUNT(DISTINCT user_id) FROM points WHERE week_start = ?''', (week_start,))
    active_players = c.fetchone()[0] or 0
    conn.close()
    
    await update.message.reply_text(
        f"📈 *ATEG QUIZ STATISTICS* 📈\n\n"
        f"❓ Total Questions: *{total_questions}*\n"
        f"👥 Active Players: *{active_players}*\n"
        f"⏰ Quiz Frequency: *Every 15 minutes*\n"
        f"⏳ Answer Time: *60 seconds*\n"
        f"💰 Points per Win: *5*\n\n"
        f"📚 Topic: *ATEG Housing System*",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    await update.message.reply_text(
        f"🤖 *ATEG QUIZ BOT - HELP* 🤖\n\n"
        f"*🎮 HOW TO PLAY:*\n"
        f"• A question appears every 15 minutes\n"
        f"• You have 60 seconds to answer\n"
        f"• Click on your answer choice\n"
        f"• First correct answer wins 5 points!\n\n"
        f"*📋 COMMANDS:*\n"
        f"• /leaderboard - View top 10 players this week\n"
        f"• /mypoints - Check your personal score\n"
        f"• /stats - View quiz statistics\n"
        f"• /help - Show this message\n\n"
        f"*📚 TOPIC:* ATEG Housing Economic System\n"
        f"*🔄 Leaderboard resets every Monday*",
        parse_mode='Markdown'
    )

async def reset_weekly_leaderboard(context: ContextTypes.DEFAULT_TYPE):
    """Reset leaderboard every Monday"""
    try:
        await context.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text="🔄 *WEEKLY LEADERBOARD RESET* 🔄\n\n"
                 "✨ New week, new opportunities!\n"
                 "🎯 First correct answer gets 5 points!",
            parse_mode='Markdown'
        )
        logger.info("Weekly leaderboard reset")
    except Exception as e:
        logger.error(f"Error resetting leaderboard: {e}")

# ==================== MAIN FUNCTION ====================
async def main():
    """Start the bot"""
    # Initialize database
    init_db()
    add_questions()
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", help_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("mypoints", mypoints))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CallbackQueryHandler(answer_callback, pattern='^ans_'))
    
    # Schedule quiz every 15 minutes
    job_queue = application.job_queue
    job_queue.run_repeating(start_quiz, interval=900, first=10)
    
    # Schedule weekly reset every Monday at 00:00
    job_queue.run_daily(
        reset_weekly_leaderboard,
        time=datetime.strptime("00:00", "%H:%M").time(),
        days=(0,)
    )
    
    logger.info(f"Bot started! Group: {GROUP_CHAT_ID}")
    
    # Start bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    # Keep running
    while True:
        await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(main())
