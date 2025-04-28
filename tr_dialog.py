import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

class EditTransactionDialog(tk.Toplevel):
    def __init__(self, master, tx):
        super().__init__(master)
        self.title("Edit transaction")
        self.grab_set()                       # modal
        self.resizable(False, False)

        # current values
        self.var_amount = tk.StringVar(value=f"{tx['amount']:.2f}")
        self.var_type   = tk.StringVar(value=tx['type'])
        self.var_desc   = tk.StringVar(value=tx.get("description", ""))

        frm = ttk.Frame(self, padding=10)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Amount").grid(row=0, column=0, sticky="e")
        ttk.Entry(frm, textvariable=self.var_amount, width=12).grid(row=0, column=1, pady=3)

        ttk.Label(frm, text="Type").grid(row=1, column=0, sticky="e")
        ttk.Combobox(frm, textvariable=self.var_type, values=("income", "expense"),
                     state="readonly", width=10).grid(row=1, column=1, pady=3)

        ttk.Label(frm, text="Description").grid(row=2, column=0, sticky="e")
        ttk.Entry(frm, textvariable=self.var_desc, width=25).grid(row=2, column=1, pady=3)

        btns = ttk.Frame(frm)
        btns.grid(row=3, column=0, columnspan=2, pady=(8,0))
        ttk.Button(btns, text="Save", command=self._ok).pack(side="left", padx=5)
        ttk.Button(btns, text="Cancel", command=self._cancel).pack(side="left", padx=5)

        self.result = None
        self.bind("<Return>", lambda *_: self._ok())
        self.bind("<Escape>", lambda *_: self._cancel())

    def _ok(self):
        try:
            amt = float(self.var_amount.get())
            assert amt > 0
            self.result = {
                "amount": amt,
                "type": self.var_type.get(),
                "desc": self.var_desc.get().strip()
            }
            self.destroy()
        except Exception:
            messagebox.showerror("Error", "Enter a positive number")

    def _cancel(self):
        self.destroy()