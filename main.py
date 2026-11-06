import asyncio
import random
import re
import sys
import discord
from config import (
    TOKEN, CHANNEL_ID, OWO_BOT_ID,
    MIN_DELAY, MAX_DELAY, COMMAND_PREFIXES, CAPTCHA_KEYWORDS
)
from tracker import SessionTracker

# Windows PC par loud beep alarm ke liye
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


class OwoAutoBot(discord.Client):
    def __init__(self):
        super().__init__()
        self.tracker = SessionTracker()
        self.is_running = False
        self.waiting_for_cash = False
        self.round_event = asyncio.Event()
        self.loop_task = None

    def trigger_alarm(self):
        """Captcha aane par PC mein loud beep bajata hai."""
        if HAS_WINSOUND:
            for _ in range(6):
                winsound.Beep(1200, 400)
        else:
            print("\a" * 5)

    def check_captcha(self, content: str) -> bool:
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in CAPTCHA_KEYWORDS)

    async def emergency_captcha_stop(self, channel):
        self.is_running = False
        self.waiting_for_cash = False
        self.round_event.set()
        if self.loop_task and not self.loop_task.done():
            self.loop_task.cancel()

        print("\n[CRITICAL ALERT] CAPTCHA DETECTED! Script stopped immediately.")
        self.trigger_alarm()

        stats = self.tracker.get_stats_message(stop_reason="CAPTCHA / VERIFICATION TRIGGERED")
        await channel.send(f"🚨 **CAPTCHA ALERT!** <@{self.user.id}> Verification aaya hai, turant solve karo!\n{stats}")

    async def betting_loop(self, channel):
        print("[INFO] Coinflip loop started.")
        while self.is_running:
            prefix = random.choice(COMMAND_PREFIXES)
            bet_amount = self.tracker.current_bet
            cmd = f"{prefix} {bet_amount}"

            self.round_event.clear()
            await channel.send(cmd)
            print(f"[SENT] {cmd} | Waiting for OwO edit result...")

            # OwO ke message edit ka wait (Max 20s timeout agar OwO lag kare)
            try:
                await asyncio.wait_for(self.round_event.wait(), timeout=20.0)
            except asyncio.TimeoutError:
                print("[WARNING] OwO response timeout. Retrying after delay...")

            if not self.is_running:
                break

            delay = round(random.uniform(MIN_DELAY, MAX_DELAY), 2)
            print(f"[SLEEP] Waiting {delay}s before next command...")
            await asyncio.sleep(delay)

    async def on_ready(self):
        print(f"Logged in as: {self.user} (ID: {self.user.id})")
        print(f"Target Channel ID: {CHANNEL_ID}")
        print("Commands: '!start' (auto balance fetch), '!start 500000' (manual balance), '!stop'")

    async def on_message(self, message: discord.Message):
        # 1. OwO DM ya Channel mein Captcha check
        if message.author.id == OWO_BOT_ID:
            if message.guild is None or message.channel.id == CHANNEL_ID:
                if self.check_captcha(message.content):
                    target_channel = self.get_channel(CHANNEL_ID) or message.channel
                    await self.emergency_captcha_stop(target_channel)
                    return

            # Auto Balance Parser ('owo cash' ka response padhne ke liye)
            if self.waiting_for_cash and message.channel.id == CHANNEL_ID:
                # OwO format: currently have **__123,456__** cowoncy
                cleaned = message.content.replace(",", "").replace("_", "").replace("*", "")
                match = re.search(r"currently have (\d+) cowoncy", cleaned, re.IGNORECASE)
                if match:
                    balance = int(match.group(1))
                    self.waiting_for_cash = False
                    self.tracker.reset(start_balance=balance)
                    self.is_running = True
                    await message.channel.send(
                        f"✅ **Bot Started!** Starting Balance: `{balance:,}` cowoncy | Base Bet: `{self.tracker.base_bet:,}`"
                    )
                    self.loop_task = asyncio.create_task(self.betting_loop(message.channel))
                    return

        # 2. User Commands (!start aur !stop)
        if message.author.id != self.user.id or message.channel.id != CHANNEL_ID:
            return

        content = message.content.strip()

        if content.lower().startswith("!start"):
            if self.is_running:
                await message.channel.send("⚠️ Script pehle se chal rahi hai.")
                return

            parts = content.split()
            if len(parts) > 1 and parts[1].isdigit():
                # Manual balance input: e.g. !start 500000
                start_bal = int(parts[1])
                self.tracker.reset(start_balance=start_bal)
                self.is_running = True
                await message.channel.send(
                    f"✅ **Bot Started!** Starting Balance: `{start_bal:,}` cowoncy | Base Bet: `{self.tracker.base_bet:,}`"
                )
                self.loop_task = asyncio.create_task(self.betting_loop(message.channel))
            else:
                # Automatic balance fetch via 'owo cash'
                self.waiting_for_cash = True
                await message.channel.send("🔍 Fetching starting balance...")
                await asyncio.sleep(1.5)
                await message.channel.send("owo cash")

        elif content.lower() == "!stop":
            if not self.is_running and not self.waiting_for_cash:
                await message.channel.send("⚠️ Script abhi band hai.")
                return

            self.is_running = False
            self.waiting_for_cash = False
            self.round_event.set()
            if self.loop_task and not self.loop_task.done():
                self.loop_task.cancel()

            stats = self.tracker.get_stats_message(stop_reason="Manual Command (!stop)")
            await message.channel.send(f"🛑 **Bot Stopped.**\n{stats}")
            print("[INFO] Bot stopped by user.")

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """OwO coinflip result message edit hone par aata hai."""
        if not self.is_running:
            return

        if after.author.id != OWO_BOT_ID or after.channel.id != CHANNEL_ID:
            return

        if self.check_captcha(after.content):
            await self.emergency_captcha_stop(after.channel)
            return

        content_lower = after.content.lower()

        # Result check
        if "and you won" in content_lower:
            self.tracker.register_win()
            print(f"[RESULT: WIN] Balance: {self.tracker.current_balance:,} | Next Bet: {self.tracker.current_bet:,}")
            self.round_event.set()

        elif "and you lost it all" in content_lower:
            self.tracker.register_loss()
            print(f"[RESULT: LOSS] Balance: {self.tracker.current_balance:,} | Next Bet: {self.tracker.current_bet:,}")
            self.round_event.set()


if __name__ == "__main__":
    if not TOKEN or CHANNEL_ID == 0:
        print("[ERROR] .env file mein DISCORD_TOKEN aur CHANNEL_ID sahi se set karo.")
        sys.exit(1)
    
    client = OwoAutoBot()
    client.run(TOKEN)