import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import datetime

class KitchenInventoryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("1100x600")
        self.title("Kitchen Utensil and Monitoring System")
        self.config(bg="#e5d6cc")

        # Sidebar properties
        self.sidebar_width = 0
        self.sidebar_shown = False
        self.sidebar = tk.Frame(self, width=self.sidebar_width, bg="#6b3f2c", height=600)
        self.sidebar.place(x=0, y=0)

        # Sidebar widgets list
        self.sidebar_widgets = []

        # Toggle Button
        self.toggle_btn = tk.Button(self, text="☰", font=("Arial", 16), command=self.toggle_sidebar)
        self.toggle_btn.place(x=5, y=5)

        # Create Sidebar & Main Content
        self.create_sidebar()
        self.create_main_content()

    # -----------------------------
    # Sidebar Content
    # -----------------------------
    def create_sidebar(self):
        self.label_dashboard = tk.Label(
            self.sidebar,
            text="DASHBOARD",
            bg="#6b3f2c",
            fg="white",
            font=("Arial", 14, "bold")
        )
        self.label_dashboard.place(x=20, y=20)
        self.sidebar_widgets.append(self.label_dashboard)

        menu_items = [
            ("Borrowed Items", self.open_borrowed_items),
            ("Return Items", self.open_return_items),
            ("Borrowers List", self.open_borrowers_list),
            ("Log / History", self.open_logs_history)
        ]
        y_offset = 70
        for text, func in menu_items:
            btn = tk.Button(
                self.sidebar,
                text=text,
                bg="#8a543f",
                fg="white",
                font=("Arial", 12),
                width=18,
                height=2,
                relief="flat",
                command=func
            )
            btn.place(x=10, y=y_offset)
            self.sidebar_widgets.append(btn)
            y_offset += 60

        self.logout_btn = tk.Button(
            self.sidebar,
            text="Log Out",
            bg="#8a543f",
            fg="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            width=18,
            height=2,
            command=self.logout
        )
        self.logout_btn.place(x=10, y=500)
        self.sidebar_widgets.append(self.logout_btn)

    # -----------------------------
    # Main Content (NOW SCROLLABLE)
    # -----------------------------
    def create_main_content(self):

        # Main Frame that moves with sidebar
        self.main_frame = tk.Frame(self, bg="#e5d6cc")
        self.main_frame.place(x=0, y=60, relwidth=1, relheight=1)

        # Scrollable Canvas + Frame Setup
        self.canvas = tk.Canvas(self.main_frame, bg="#e5d6cc", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollable_frame = tk.Frame(self.canvas, bg="#e5d6cc")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Header
        header = tk.Label(
            self.scrollable_frame,
            text="KITCHEN UTENSILS INVENTORY & MONITORING SYSTEM",
            bg="#e5d6cc",
            fg="#6b3f2c",
            font=("Arial", 16, "bold")
        )
        header.pack(pady=15)

        # Table Frame
        table_frame = tk.Frame(self.scrollable_frame, bg="#e5d6cc")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("Borrower Name", "Year & Section", "Item Borrowed",
                   "Quantity", "Date Borrowed", "Date Returned")

        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")

        self.tree.pack(fill="both", expand=True)

    # -----------------------------
    # Toggle Sidebar (with animation)
    # -----------------------------
    def toggle_sidebar(self):
        target_width = 200 if not self.sidebar_shown else 0
        step = 10 if not self.sidebar_shown else -10

        for w in self.sidebar_widgets:
            w.place_forget()

        def animate():
            new_width = self.sidebar.winfo_width() + step

            if (step > 0 and new_width >= target_width) or (step < 0 and new_width <= target_width):
                new_width = target_width

            self.sidebar.config(width=new_width)
            self.toggle_btn.place(x=new_width + 5, y=5)
            self.main_frame.place(x=new_width, y=60, relwidth=1, relheight=1)

            if new_width != target_width:
                self.after(10, animate)
            else:
                if target_width == 200:
                    self.label_dashboard.place(x=20, y=20)
                    y_offset = 70
                    for w in self.sidebar_widgets[1:-1]:
                        w.place(x=10, y=y_offset)
                        y_offset += 60
                    self.logout_btn.place(x=10, y=500)

                self.sidebar_shown = not self.sidebar_shown

        animate()

    # -----------------------------
    # Sidebar Button Functions
    # -----------------------------
    def open_borrowed_items(self):
        popup = tk.Toplevel(self)
        popup.title("Add Borrowed Item")
        popup.geometry("400x400")
        popup.config(bg="#e5d6cc")

        labels = ["Borrower Name:", "Year & Section:", "Item Borrowed:",
                  "Quantity:", "Date Borrowed (YYYY-MM-DD):"]
        entries = []

        for lbl in labels:
            tk.Label(popup, text=lbl, bg="#e5d6cc").pack(pady=5)
            e = tk.Entry(popup)
            e.pack(pady=5, fill="x", padx=20)
            entries.append(e)

        entries[-1].insert(0, datetime.date.today().isoformat())

        def on_submit():
            name = entries[0].get().strip()
            ys = entries[1].get().strip()
            item = entries[2].get().strip()
            qty = entries[3].get().strip()
            date_b = entries[4].get().strip()

            if not (name and ys and item and qty and date_b):
                messagebox.showerror("Error", "All fields are required.")
                return

            try:
                qty_int = int(qty)
            except ValueError:
                messagebox.showerror("Error", "Quantity must be an integer.")
                return

            self.tree.insert('', tk.END, values=(name, ys, item, qty_int, date_b, ""))
            popup.destroy()

        submit_btn = tk.Button(popup, text="Submit", command=on_submit)
        submit_btn.pack(pady=20)

    def open_return_items(self):
        self.create_popup("Return Items")

    def open_borrowers_list(self):
        self.create_popup("Borrowers List")

    def open_logs_history(self):
        self.create_popup("Logs / History")

    def create_popup(self, title):
        popup = tk.Toplevel(self)
        popup.title(title)
        popup.geometry("500x400")
        popup.config(bg="#e5d6cc")
        label = tk.Label(popup, text=title, font=("Arial", 14, "bold"), bg="#e5d6cc", fg="#6b3f2c")
        label.pack(pady=20)
        info = tk.Label(popup, text=f"This is the {title} window.", bg="#e5d6cc", font=("Arial", 12))
        info.pack(pady=10)
        close_btn = tk.Button(popup, text="Close", command=popup.destroy)
        close_btn.pack(pady=20)

    def logout(self):
        self.destroy()


if __name__ == "__main__":
    app = KitchenInventoryApp()
    app.mainloop()
