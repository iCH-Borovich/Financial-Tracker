import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import datetime
from calendar import monthrange
from logic import FinancialTracker
from tr_dialog import EditTransactionDialog
import os
import sys # Import sys module

class FinancialTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pocket Financial Tracker")
        self.root.geometry("650x650") # Increased size further for new settings

        # Determine base path (executable dir or script dir)
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Running as packaged app
            base_path = os.path.dirname(sys.executable)
        else:
            # Running as script
            base_path = os.path.dirname(os.path.abspath(__file__))

        data_file_path = os.path.join(base_path, "data.json")
        print(f"Data file path: {data_file_path}") # Add print for debugging
        self.tracker = FinancialTracker(data_file=data_file_path)

        self.selected_date = datetime.date.today()
        self.current_display_month = self.selected_date.month
        self.current_display_year = self.selected_date.year

        # UI Variables
        self.calendar_display_mode = tk.StringVar(value="date_only") # date_only, show_remaining, show_spent
        self.surplus_enabled_var = tk.BooleanVar(value=self.tracker.data["settings"].get("surplus_enabled", False))
        self.surplus_days_var = tk.StringVar(value=str(self.tracker.data["settings"].get("surplus_distribution_days", 4)))

        self.create_widgets()
        self.update_calendar()
        self.update_details_for_date(self.selected_date)

        # Save data on closing the window
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left frame (Calendar)
        left_frame = ttk.Frame(main_frame, padding="5")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # Right frame (Details, Inputs, Settings)
        right_frame = ttk.Frame(main_frame, padding="5")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        main_frame.columnconfigure(1, weight=1)

        # --- Calendar Widgets (Left Frame) ---
        calendar_nav_frame = ttk.Frame(left_frame)
        calendar_nav_frame.pack(pady=(0, 5))

        ttk.Button(calendar_nav_frame, text="<", command=self.prev_month).pack(side=tk.LEFT)
        self.month_year_label = ttk.Label(calendar_nav_frame, text="", width=15, anchor="center")
        self.month_year_label.pack(side=tk.LEFT, padx=5)
        ttk.Button(calendar_nav_frame, text=">", command=self.next_month).pack(side=tk.LEFT)

        self.calendar_frame = ttk.Frame(left_frame)
        self.calendar_frame.pack(fill=tk.BOTH, expand=True)

        # --- Details Widgets (Right Frame) ---
        details_frame = ttk.LabelFrame(right_frame, text="Details for Selected Date", padding="10")
        details_frame.pack(fill=tk.X, pady=(0, 10))

        self.selected_date_label = ttk.Label(details_frame, text="Date: YYYY-MM-DD")
        self.selected_date_label.pack()
        self.daily_limit_label = ttk.Label(details_frame, text="Daily Limit: $0.00")
        self.daily_limit_label.pack()
        self.daily_spent_label = ttk.Label(details_frame, text="Spent Today: $0.00")
        self.daily_spent_label.pack()
        self.daily_remaining_label = ttk.Label(details_frame, text="Remaining Today: $0.00")
        self.daily_remaining_label.pack()
        self.total_balance_label = ttk.Label(details_frame, text="Balance: $0.00")
        self.total_balance_label.pack()

        # --- Transaction List (Right Frame) ---
        transactions_frame = ttk.LabelFrame(right_frame, text="Transactions", padding="10")
        transactions_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.transactions_list = tk.Listbox(transactions_frame, height=6)
        self.transactions_list.pack(fill=tk.BOTH, expand=True)
        self.transactions_list.bind("<Button-3>", self._tx_context)

        # --- Input Widgets (Right Frame) ---
        input_frame = ttk.LabelFrame(right_frame, text="Add Transaction", padding="10")
        input_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(input_frame, text="Amount:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.amount_entry = ttk.Entry(input_frame, width=10)
        self.amount_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Desc:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.desc_entry = ttk.Entry(input_frame, width=15)
        self.desc_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

        ttk.Button(input_frame, text="Add Income", command=self.add_income).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(input_frame, text="Add Expense", command=self.add_expense).grid(row=0, column=3, padx=5, pady=5)

        # --- Savings/Limit Settings Widgets (Right Frame) ---
        savings_settings_frame = ttk.LabelFrame(right_frame, text="Savings/Limit Settings", padding="10")
        savings_settings_frame.pack(fill=tk.X, pady=(0, 10))

        self.settings_var = tk.StringVar(value="percentage") # Default to percentage
        ttk.Radiobutton(savings_settings_frame, text="Save %", variable=self.settings_var, value="percentage", command=self.update_settings_input).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Radiobutton(savings_settings_frame, text="Fixed Limit $", variable=self.settings_var, value="fixed", command=self.update_settings_input).grid(row=1, column=0, padx=5, pady=5, sticky="w")

        self.settings_value_entry = ttk.Entry(savings_settings_frame, width=10)
        self.settings_value_entry.grid(row=0, column=1, rowspan=2, padx=5, pady=5)
        ttk.Button(savings_settings_frame, text="Save Settings", command=self.save_savings_settings).grid(row=0, column=2, rowspan=2, padx=5, pady=5)

        # Load initial savings settings values
        if self.tracker.data["settings"]["fixed_daily_limit"] is not None:
            self.settings_var.set("fixed")
            self.settings_value_entry.insert(0, str(self.tracker.data["settings"]["fixed_daily_limit"]))
        else:
            self.settings_var.set("percentage")
            self.settings_value_entry.insert(0, str(self.tracker.data["settings"]["savings_percentage"]))
        self.update_settings_input() # Ensure correct state initially

        # --- Surplus Settings Widgets (Right Frame) ---
        surplus_settings_frame = ttk.LabelFrame(right_frame, text="Surplus Distribution Settings", padding="10")
        surplus_settings_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(surplus_settings_frame, text="Enable Surplus Distribution", variable=self.surplus_enabled_var).grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        ttk.Label(surplus_settings_frame, text="Distribute over (days):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.surplus_days_entry = ttk.Entry(surplus_settings_frame, textvariable=self.surplus_days_var, width=5)
        self.surplus_days_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        ttk.Button(surplus_settings_frame, text="Save Surplus Settings", command=self.save_surplus_settings).grid(row=0, column=2, rowspan=2, padx=5, pady=5)

        # --- Display Settings Widgets (Right Frame) ---
        display_settings_frame = ttk.LabelFrame(right_frame, text="Calendar Display Settings", padding="10")
        display_settings_frame.pack(fill=tk.X)

        ttk.Radiobutton(display_settings_frame, text="Date Only", variable=self.calendar_display_mode, value="date_only", command=self.update_calendar).pack(anchor=tk.W)
        ttk.Radiobutton(display_settings_frame, text="Show Remaining", variable=self.calendar_display_mode, value="show_remaining", command=self.update_calendar).pack(anchor=tk.W)
        ttk.Radiobutton(display_settings_frame, text="Show Spent", variable=self.calendar_display_mode, value="show_spent", command=self.update_calendar).pack(anchor=tk.W)

    def update_settings_input(self):
        # Optional: Could add validation or change labels based on selection
        pass

    def save_savings_settings(self):
        try:
            value = float(self.settings_value_entry.get())
            if self.settings_var.get() == "percentage":
                if 0 <= value <= 100:
                    self.tracker.set_savings_percentage(value)
                    messagebox.showinfo("Settings Saved", f"Savings percentage set to {value}%")
                else:
                    messagebox.showerror("Error", "Percentage must be between 0 and 100.")
                    return
            else: # fixed limit
                if value >= 0:
                    self.tracker.set_fixed_daily_limit(value)
                    messagebox.showinfo("Settings Saved", f"Fixed daily limit set to ${value:.2f}")
                else:
                    messagebox.showerror("Error", "Fixed limit must be non-negative.")
                    return
            # Recalculate and update display for the currently selected date
            self.update_details_for_date(self.selected_date)
            self.update_calendar() # Update calendar as limits might change
        except ValueError:
            messagebox.showerror("Error", "Invalid input for settings value. Please enter a number.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

    def save_surplus_settings(self):
        try:
            enabled = self.surplus_enabled_var.get()
            days = int(self.surplus_days_var.get())
            if days < 1:
                messagebox.showerror("Error", "Distribution days must be at least 1.")
                return

            self.tracker.set_surplus_settings(enabled, days)
            messagebox.showinfo("Settings Saved", f"Surplus distribution settings saved (Enabled: {enabled}, Days: {days})")
            # Recalculate and update display
            self.update_details_for_date(self.selected_date)
            self.update_calendar()
        except ValueError:
            messagebox.showerror("Error", "Invalid input for distribution days. Please enter a whole number.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save surplus settings: {e}")

    def update_calendar(self):
        # Clear previous calendar
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        self.month_year_label.config(text=datetime.date(self.current_display_year, self.current_display_month, 1).strftime("%B %Y"))

        # Add day headers
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(days):
            ttk.Label(self.calendar_frame, text=day, width=3, anchor="center").grid(row=0, column=i, padx=1, pady=1)

        # Get calendar data
        month_cal = monthrange(self.current_display_year, self.current_display_month)
        first_day_weekday = month_cal[0] # 0 = Monday, 6 = Sunday
        days_in_month = month_cal[1]

        current_day = 1
        for week in range(6): # Max 6 weeks needed
            for day_of_week in range(7):
                if week == 0 and day_of_week < first_day_weekday:
                    # Empty cell before the 1st day
                    ttk.Label(self.calendar_frame, text="").grid(row=week + 1, column=day_of_week, padx=1, pady=1)
                elif current_day <= days_in_month:
                    # Create button for the day
                    date_obj = datetime.date(self.current_display_year, self.current_display_month, current_day)
                    date_str = date_obj.strftime("%Y-%m-%d")
                    limit = self.tracker.get_daily_limit(date_str)
                    expenses = self.tracker.get_daily_expenses(date_str)
                    remaining = limit - expenses

                    # Determine button text based on display mode
                    display_text = str(current_day)
                    if self.calendar_display_mode.get() == "show_remaining":
                        display_text = f"{remaining:.0f}"
                    elif self.calendar_display_mode.get() == "show_spent":
                        display_text = f"{expenses:.0f}"

                    # Determine button style
                    style = "TButton"
                    if date_obj == self.selected_date:
                        style = "Selected.TButton"
                    elif expenses > limit and limit > 0: # Exceeded limit (and limit was positive)
                        style = "Exceeded.TButton"
                    elif limit > 0:
                        style = "HasLimit.TButton"

                    # Make button smaller (width=3)
                    btn = ttk.Button(self.calendar_frame, text=display_text, width=3,
                                     command=lambda d=date_obj: self.select_date(d), style=style)
                    btn.grid(row=week + 1, column=day_of_week, padx=1, pady=1, sticky="nsew")
                    current_day += 1
                else:
                    # Empty cell after the last day
                    ttk.Label(self.calendar_frame, text="").grid(row=week + 1, column=day_of_week, padx=1, pady=1)
            if current_day > days_in_month:
                break # Stop creating rows if month is finished

        # Configure styles
        style = ttk.Style()
        style.configure("Selected.TButton", background="lightblue")
        style.configure("HasLimit.TButton", foreground="blue") # Indicate days with calculated limits
        style.configure("Exceeded.TButton", foreground="red") # Indicate days where limit was exceeded

    def select_date(self, date_obj):
        self.selected_date = date_obj
        self.update_calendar() # Redraw to show selection
        self.update_details_for_date(date_obj)

    def prev_month(self):
        if self.current_display_month == 1:
            self.current_display_month = 12
            self.current_display_year -= 1
        else:
            self.current_display_month -= 1
        self.update_calendar()

    def next_month(self):
        if self.current_display_month == 12:
            self.current_display_month = 1
            self.current_display_year += 1
        else:
            self.current_display_month += 1
        self.update_calendar()

    def add_income(self):
        self._add_transaction("income")

    def add_expense(self):
        self._add_transaction("expense")

    def _add_transaction(self, transaction_type):
        try:
            amount = float(self.amount_entry.get())
            if amount <= 0:
                messagebox.showerror("Error", "Amount must be positive.")
                return
            description = self.desc_entry.get()
            date_str = self.selected_date.strftime("%Y-%m-%d")

            self.tracker.add_transaction(date_str, amount, transaction_type, description)

            # Clear input fields
            self.amount_entry.delete(0, tk.END)
            self.desc_entry.delete(0, tk.END)

            # Update display
            self.update_details_for_date(self.selected_date)
            # Recalculate limits might affect future days, update calendar potentially
            self.update_calendar()

        except ValueError:
            messagebox.showerror("Error", "Invalid amount. Please enter a number.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add transaction: {e}")

    def _tx_context(self, event):
        sel = self.transactions_list.curselection()
        if not sel: return
        idx = sel[0]
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Edit…", command=lambda: self._edit_tx(idx))
        menu.add_command(label="Delete", command=lambda: self._del_tx(idx))
        menu.post(event.x_root, event.y_root)

    def _del_tx(self, idx):
        try:
            self.tracker.remove_transaction(self.selected_date.strftime("%Y-%m-%d"), idx)
            self.update_details_for_date(self.selected_date)
            self.update_calendar()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _edit_tx(self, idx):
        date_str = self.selected_date.strftime("%Y-%m-%d")
        tx = self.tracker.get_transactions_for_date(date_str)[idx]

        dlg = EditTransactionDialog(self.root, tx)
        self.root.wait_window(dlg)

        if not dlg.result:    # cancelled
            return

        self.tracker.edit_transaction(
            date_str,
            idx,
            amount=dlg.result["amount"],
            transaction_type=dlg.result["type"],
            description=dlg.result["desc"]
        )
        self.update_details_for_date(self.selected_date)
        self.update_calendar()

    def update_details_for_date(self, date_obj: datetime.date):
            date_str = date_obj.strftime("%Y-%m-%d")
            self.selected_date_label.config(text=f"Date: {date_str}")

            limit     = self.tracker.get_daily_limit(date_str)
            spent     = self.tracker.get_daily_expenses(date_str)
            remaining = limit - spent
            balance   = self.tracker.get_balance_summary()["remaining_balance"]

            self.daily_limit_label.config(text=f"Daily Limit: ${limit:.2f}")
            self.daily_spent_label.config(text=f"Spent Today: ${spent:.2f}")
            self.daily_remaining_label.config(text=f"Remaining Today: ${remaining:.2f}")
            self.total_balance_label.config(text=f"Balance: ${balance:.2f}")

            # refresh transaction list
            self.transactions_list.delete(0, tk.END)
            for idx, t in enumerate(self.tracker.get_transactions_for_date(date_str)):
                sign = "-" if t["type"] == "expense" else "+"
                desc = f": {t['description']}" if t.get("description") else ""
                self.transactions_list.insert(idx, f"{sign}${t['amount']:.2f} ({t['type']}){desc}")
            if self.transactions_list.size() == 0:
                self.transactions_list.insert(0, "No transactions for this date.")

    def on_closing(self):
        """Handle window closing event."""
        try:
            print("Attempting to save data...") # Add print for debugging
            self.tracker.save_data()
            print("Data saved successfully.") # Add print for debugging
        except Exception as e:
            print(f"Error saving data: {e}") # Add print for debugging
            messagebox.showwarning("Save Error", f"Could not save data: {e}")
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = FinancialTrackerApp(root)
    root.mainloop()

