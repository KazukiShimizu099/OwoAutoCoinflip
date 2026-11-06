import time
from config import BASE_BET, MAX_BET

class SessionTracker:
    def __init__(self):
        self.reset(0)

    def reset(self, start_balance: int = 0):
        self.start_balance = start_balance
        self.current_balance = start_balance
        self.base_bet = BASE_BET
        self.current_bet = BASE_BET
        self.max_bet = MAX_BET
        
        self.total_rounds = 0
        self.wins = 0
        self.losses = 0
        self.current_loss_streak = 0
        self.max_loss_streak = 0
        self.start_time = time.time()

    def register_win(self):
        self.total_rounds += 1
        self.wins += 1
        self.current_balance += self.current_bet
        self.current_loss_streak = 0
        # Win hone par wapas 10000 par reset
        self.current_bet = self.base_bet

    def register_loss(self):
        self.total_rounds += 1
        self.losses += 1
        self.current_balance -= self.current_bet
        self.current_loss_streak += 1
        
        if self.current_loss_streak > self.max_loss_streak:
            self.max_loss_streak = self.current_loss_streak

        # Loss hone par double (Capped at 250,000 OwO limit)
        doubled = self.current_bet * 2
        self.current_bet = min(doubled, self.max_bet)

    def get_stats_message(self, stop_reason: str = "Manual Stop (!stop)") -> str:
        elapsed_sec = int(time.time() - self.start_time)
        mins, secs = divmod(elapsed_sec, 60)
        hours, mins = divmod(mins, 60)
        
        net_profit = self.current_balance - self.start_balance
        profit_sign = "+" if net_profit >= 0 else ""
        win_rate = (self.wins / self.total_rounds * 100) if self.total_rounds > 0 else 0.0

        return (
            f"```ini\n"
            f"[ OwO Coinflip Session Stats ]\n"
            f"Stop Reason     = {stop_reason}\n"
            f"Runtime         = {hours}h {mins}m {secs}s\n"
            f"----------------------------------------\n"
            f"Start Balance   = {self.start_balance:,}\n"
            f"End Balance     = {self.current_balance:,}\n"
            f"Net Profit/Loss = {profit_sign}{net_profit:,} cowoncy\n"
            f"----------------------------------------\n"
            f"Total Coinflips = {self.total_rounds}\n"
            f"Total Wins      = {self.wins}\n"
            f"Total Losses    = {self.losses}\n"
            f"Win Rate        = {win_rate:.2f}%\n"
            f"Max Loss Streak = {self.max_loss_streak}\n"
            f"Next Bet Was    = {self.current_bet:,}\n"
            f"```"
        )