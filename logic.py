import json
import datetime
from calendar import monthrange
import os

class FinancialTracker:
    def __init__(self, data_file="data.json"):
        self.data_file = data_file
        self.data = self._load_data()

    def _load_data(self):
        """Load data from JSON file or create default structure if file doesn't exist"""
        if os.path.exists(self.data_file) and os.path.getsize(self.data_file) > 0:
            try:
                with open(self.data_file, 'r') as f:
                    loaded_data = json.load(f)
                    # Ensure default settings exist if loading older data
                    if "settings" not in loaded_data:
                        loaded_data["settings"] = self._create_default_data()["settings"]
                    else:
                        # Add new settings if missing
                        if "surplus_enabled" not in loaded_data["settings"]:
                            loaded_data["settings"]["surplus_enabled"] = False
                        if "surplus_distribution_days" not in loaded_data["settings"]:
                            loaded_data["settings"]["surplus_distribution_days"] = 4
                    if "transactions" not in loaded_data:
                        loaded_data["transactions"] = {}
                    if "daily_limits" not in loaded_data:
                        loaded_data["daily_limits"] = {}
                    if "surplus_adjustments" not in loaded_data:
                        loaded_data["surplus_adjustments"] = {} # Store future deductions
                    return loaded_data
            except json.JSONDecodeError:
                # If file exists but is corrupted, create new data structure
                return self._create_default_data()
        else:
            return self._create_default_data()

    def _create_default_data(self):
        """Create default data structure"""
        return {
            "settings": {
                "savings_percentage": 0,  # Default 0% savings
                "fixed_daily_limit": None,  # No fixed daily limit by default
                "surplus_enabled": False, # Surplus distribution disabled by default
                "surplus_distribution_days": 4 # Default distribution over 4 days
            },
            "transactions": {},  # Will store transactions by date
            "daily_limits": {},   # Will store calculated daily limits
            "surplus_adjustments": {} # Stores date: adjustment_amount
        }

    def save_data(self):
        """Save data to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def add_transaction(
        self,
        date_str: str,
        amount: float,
        transaction_type: str = "expense",
        description: str = ""
    ):
        """Add income / expense.  Mid-period incomes are treated as top-ups."""
        self.data["transactions"].setdefault(date_str, [])
        amount = abs(float(amount))  # always positive

        self.data["transactions"][date_str].append({
            "type": transaction_type,
            "amount": amount,
            "description": description,
            "timestamp": datetime.datetime.now().isoformat()
        })

        # supplemental income logic
        if transaction_type == "income":
            income_dates = sorted(
                d for d, txs in self.data["transactions"].items()
                if any(t["type"] == "income" for t in txs)
            )
            # first income of period = “payday”, anything later = “top-up”
            if income_dates and date_str != income_dates[0]:
                days = max(1, self.data["settings"].get("surplus_distribution_days", 4))
                chunk = amount / days
                base  = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                for i in range(days):
                    key = (base + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
                    self.data["surplus_adjustments"][key] = self.data["surplus_adjustments"].get(key, 0) + chunk
                # no new payday created → just recalc from today onward
                self._recalculate_daily_limits(date_str)
                self.save_data()
                return

        # default path
        self._recalculate_daily_limits(date_str)
        self.save_data()

    def remove_transaction(self, date_str, idx):
        """Delete a transaction by list index, then recalc limits."""
        try:
            self.data["transactions"][date_str].pop(idx)
            if not self.data["transactions"][date_str]:
                del self.data["transactions"][date_str]
            self._recalculate_daily_limits(date_str)
            self.save_data()
        except (KeyError, IndexError):
            raise ValueError("Bad date or index")

    def edit_transaction(self, date_str, idx, *, amount=None,
                        transaction_type=None, description=None):
        """In-place edit, keep timestamp."""
        t = self.data["transactions"][date_str][idx]
        if amount is not None:          t["amount"] = abs(float(amount))
        if transaction_type is not None: t["type"]   = transaction_type
        if description is not None:      t["description"] = description
        self._recalculate_daily_limits(date_str)
        self.save_data()

    def set_savings_percentage(self, percentage):
        """Set savings percentage (0-100)"""
        percentage = max(0, min(100, float(percentage)))
        self.data["settings"]["savings_percentage"] = percentage
        self.data["settings"]["fixed_daily_limit"] = None  # Clear fixed daily limit when using percentage
        self._recalculate_all_daily_limits()
        self.save_data()

    def set_fixed_daily_limit(self, limit):
        """Set a fixed daily spending limit"""
        self.data["settings"]["fixed_daily_limit"] = float(limit)
        self.data["settings"]["savings_percentage"] = 0  # Clear savings percentage when using fixed limit
        self._recalculate_all_daily_limits()
        self.save_data()

    def set_surplus_settings(self, enabled, distribution_days):
        """Set surplus distribution settings"""
        self.data["settings"]["surplus_enabled"] = bool(enabled)
        self.data["settings"]["surplus_distribution_days"] = max(1, int(distribution_days)) # Ensure at least 1 day
        self._recalculate_all_daily_limits()
        self.save_data()

    def get_payday_income(self, date_str):
        """Get total income for a specific payday"""
        if date_str not in self.data["transactions"]:
            return 0

        return sum(t["amount"] for t in self.data["transactions"][date_str]
                  if t["type"] == "income")

    def get_daily_expenses(self, date_str):
        """Get total expenses for a specific day"""
        if date_str not in self.data["transactions"]:
            return 0

        return sum(t["amount"] for t in self.data["transactions"][date_str]
                  if t["type"] == "expense")

    def get_daily_limit(self, date_str):
        """Get calculated daily limit for a specific day"""
        if date_str in self.data["daily_limits"]:
            return self.data["daily_limits"][date_str]
        return 0

    def _get_days_in_period(self, start_date_str: str, end_date_str: str | None = None) -> int:
        """
        If a *fixed* daily limit is active → return how many whole days the
        incoming cash can cover. Otherwise fall back to “until next-month same-day”.
        """
        fixed = self.data["settings"]["fixed_daily_limit"]
        if fixed is not None and fixed > 0:
            available = self.get_payday_income(start_date_str)
            return int(available // fixed)  # whole days until balance would hit zero
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
        if end_date_str:
            end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
        else:
            next_month = 1 if start_date.month == 12 else start_date.month + 1
            next_year  = start_date.year + 1 if start_date.month == 12 else start_date.year
            days_next  = monthrange(next_year, next_month)[1]
            end_date   = datetime.date(next_year, next_month, min(start_date.day, days_next))
        return (end_date - start_date).days

    def _calculate_initial_daily_limit(self, payday_date_str, days_in_period):
        """Calculate initial daily limit based on income, period, and savings goal"""
        total_income = self.get_payday_income(payday_date_str)

        if self.data["settings"]["fixed_daily_limit"] is not None:
            # If fixed daily limit is set, use that
            return self.data["settings"]["fixed_daily_limit"]

        # Calculate savings amount
        savings_percentage = self.data["settings"]["savings_percentage"]
        savings_amount = total_income * (savings_percentage / 100)

        # Calculate available amount for the period
        available_amount = total_income - savings_amount

        # Calculate daily limit
        if days_in_period > 0:
            daily_limit = available_amount / days_in_period
        else:
            daily_limit = 0

        return daily_limit

    def _recalculate_daily_limits(self, start_date_str):
        """
        Recalculate daily limits starting from a specific date
        This handles the rollover/deficit logic and surplus distribution
        """
        # Find the most recent payday before or on start_date
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
        payday_date_str = None

        # Find all dates with income transactions
        income_dates = [date_str for date_str in self.data["transactions"]
                       if any(t["type"] == "income" for t in self.data["transactions"][date_str])]

        # Sort dates and find the most recent payday
        if income_dates:
            income_dates.sort()
            for date_str in income_dates:
                date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                if date <= start_date:
                    payday_date_str = date_str

        if not payday_date_str:
            # No payday found, nothing to calculate
            return

        # Find the next payday (if any)
        next_payday_date_str = None
        for date_str in income_dates:
            date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            if date > start_date:
                next_payday_date_str = date_str
                break

        # Calculate days in period
        days_in_period = self._get_days_in_period(payday_date_str, next_payday_date_str)

        # Calculate initial daily limit
        initial_daily_limit = self._calculate_initial_daily_limit(payday_date_str, days_in_period)

        # Clear old limits and surplus adjustments for the period being recalculated
        temp_date = datetime.datetime.strptime(payday_date_str, "%Y-%m-%d").date()
        end_recalc_date = temp_date + datetime.timedelta(days=days_in_period) if days_in_period else None
        keys_to_delete_limits = [k for k in self.data["daily_limits"] if k >= payday_date_str and (end_recalc_date is None or k < end_recalc_date.strftime("%Y-%m-%d"))]
        for k in keys_to_delete_limits:
            del self.data["daily_limits"][k]
        keys_to_delete_surplus = [k for k in self.data["surplus_adjustments"] if k >= payday_date_str and (end_recalc_date is None or k < end_recalc_date.strftime("%Y-%m-%d"))]
        for k in keys_to_delete_surplus:
            del self.data["surplus_adjustments"][k]

        # Generate all dates in the period
        current_date = (datetime.datetime.strptime(payday_date_str, "%Y-%m-%d").date()
                        + datetime.timedelta(days=1))
        end_date = current_date + datetime.timedelta(days=days_in_period) if days_in_period else None

        # Initialize with the initial daily limit
        running_limit = initial_daily_limit

        while end_date is None or current_date < end_date:
            current_date_str = current_date.strftime("%Y-%m-%d")

            # Apply any surplus adjustments for today
            today_adjustment = self.data["surplus_adjustments"].get(current_date_str, 0)
            adjusted_initial_limit = initial_daily_limit + today_adjustment

            # Get expenses for the current day
            daily_expenses = self.get_daily_expenses(current_date_str)

            # Store the daily limit for this day
            self.data["daily_limits"][current_date_str] = running_limit

            # Calculate rollover/deficit for the next day
            if daily_expenses <= running_limit:
                # If spent less than limit, add the savings to next day
                running_limit = adjusted_initial_limit + (running_limit - daily_expenses)
            else:
                # If spent more than limit
                deficit = daily_expenses - running_limit
                if self.data["settings"]["surplus_enabled"]:
                    # Distribute deficit over future days
                    distribution_days = self.data["settings"]["surplus_distribution_days"]
                    adjustment_per_day = deficit / distribution_days
                    for i in range(1, distribution_days + 1):
                        future_date = current_date + datetime.timedelta(days=i)
                        future_date_str = future_date.strftime("%Y-%m-%d")
                        # Stop distributing if we hit the next payday
                        if next_payday_date_str and future_date_str >= next_payday_date_str:
                            break
                        self.data["surplus_adjustments"][future_date_str] = self.data["surplus_adjustments"].get(future_date_str, 0) - adjustment_per_day
                    # Next day's limit starts from the adjusted initial limit (without deficit reduction)
                    running_limit = adjusted_initial_limit
                else:
                    # Reduce next day's limit by the full deficit
                    running_limit = adjusted_initial_limit - deficit
                    # Ensure limit doesn't go negative
                    running_limit = max(0, running_limit)

            # Move to next day
            current_date += datetime.timedelta(days=1)

            # Stop if we've reached the next payday
            if next_payday_date_str and current_date_str >= next_payday_date_str:
                break

    def _recalculate_all_daily_limits(self):
        """Recalculate all daily limits from the earliest payday"""
        # Find all dates with income transactions
        income_dates = [date_str for date_str in self.data["transactions"]
                       if any(t["type"] == "income" for t in self.data["transactions"][date_str])]

        if income_dates:
            # Sort dates and start recalculation from the earliest payday
            income_dates.sort()
            self._recalculate_daily_limits(income_dates[0])

    def get_transactions_for_date(self, date_str):
        """Get all transactions for a specific date"""
        if date_str in self.data["transactions"]:
            return self.data["transactions"][date_str]
        return []

    def get_balance_summary(self):
        """Get summary of current financial status"""
        total_income = sum(t["amount"] for date_str in self.data["transactions"]
                          for t in self.data["transactions"][date_str] if t["type"] == "income")

        total_expenses = sum(t["amount"] for date_str in self.data["transactions"]
                            for t in self.data["transactions"][date_str] if t["type"] == "expense")

        savings_percentage = self.data["settings"]["savings_percentage"]
        savings_amount = total_income * (savings_percentage / 100)

        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "savings_amount": savings_amount,
            "remaining_balance": total_income - total_expenses - savings_amount
        }

    def get_current_month_data(self):
        """Get data for the current month"""
        today = datetime.date.today()
        year_month = today.strftime("%Y-%m")

        month_transactions = {date_str: transactions for date_str, transactions in self.data["transactions"].items()
                             if date_str.startswith(year_month)}

        month_limits = {date_str: limit for date_str, limit in self.data["daily_limits"].items()
                       if date_str.startswith(year_month)}

        return {
            "transactions": month_transactions,
            "daily_limits": month_limits
        }
