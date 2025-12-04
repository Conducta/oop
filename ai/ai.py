import tkinter as tk
from tkinter import ttk

class InventoryApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Kitchen Utensils Inventory & Monitoring System")
        self.geometry("1000x600")
        self.config(bg="#e5d6cc")

        # Sidebar properties
        self.sidebar_width = 0
        self.sidebar_expanded = False

        # Create sidebar frame
        self.sidebar = tk.Frame(self, bg="#6b3f2c", width=self.sidebar_width, height=600)
        self.sidebar.place(x=0, y=0)

        # Toggle button
        self.toggle_btn = tk.Button(self, text="☰", font=("Arial", 16), command=self.toggle_sidebar)
        self.toggle_btn.place(x=5, y=5)

        # Add content *inside* sidebar
        self.create_sidebar_content()

        # Main content (header + table)
        self.create_main_content()

    # ============================================================
    # SIDEBAR CONTENT (Inside the sliding panel)
    # ============================================================
    def create_sidebar_content(self):
        # DASHBOARD label
        self.lbl_dashboard = tk.Label(
            self.sidebar,
            text="DASHBOARD",
            bg="#6b3f2c",
            fg="white",
            font=("Arial", 14, "bold")
        )
        self.lbl_dashboard.place(x=20, y=20)

        # Sidebar menu buttons
        self.menu_buttons = []
        menu_items = [
            "Borrowed Items",
            "Returned Items",
            "Borrowers List",
            "Logs / History"
        ]

        y = 70
        for item in menu_items:
            btn = tk.Button(
                self.sidebar,
                text=item,
                bg="#8a543f",
                fg="white",
                relief="flat",
                font=("Arial", 12),
                width=18,
                height=2
            )
            btn.place(x=10, y=y)
            self.menu_buttons.append(btn)
            y += 60

        # Bottom user box
        self.user_frame = tk.Frame(self.sidebar, bg="#8a543f", width=200, height=70)
        self.user_frame.place(x=0, y=500)

        self.user_label = tk.Label(
            self.user_frame,
            text="Ihnee Cyrille A.\nInstructor",
            bg="#8a543f",
            fg="white",
            font=("Arial", 11)
        )
        self.user_label.place(x=15, y=10)

    # ============================================================
    # MAIN CONTENT (Header + Table)
    # ============================================================
    def create_main_content(self):
        self.main_frame = tk.Frame(self, bg="#e5d6cc")
        self.main_frame.pack(side="right", fill="both", expand=True)

        header = tk.Label(
            self.main_frame,
            text="KITCHEN UTENSILS INVENTORY & MONITORING SYSTEM",
            bg="#e5d6cc",
            fg="#6b3f2c",
            font=("Arial", 16, "bold")
        )
        header.pack(pady=15)

        # Table frame
        table_frame = tk.Frame(self.main_frame, bg="#e5d6cc")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("Borrower Name", "Year & Section", "Item Borrowed",
                   "Quantity", "Date Borrowed", "Date Returned")

        tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=15
        )

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor="center")

        tree.pack(fill="both", expand=True)

    # ============================================================
    # SLIDING SIDEBAR ANIMATION
    # ============================================================
    def toggle_sidebar(self):
        target_width = 220 if not self.sidebar_expanded else 0
        step = 10 if not self.sidebar_expanded else -10

        def animate():
            new_width = self.sidebar.winfo_width() + step

            # Stop at target width
            if (step > 0 and new_width >= target_width) or (step < 0 and new_width <= target_width):
                new_width = target_width

            self.sidebar.config(width=new_width)
            self.toggle_btn.place(x=new_width + 5, y=5)

            # Continue animation
            if new_width != target_width:
                self.after(10, animate)
            else:
                self.sidebar_expanded = not self.sidebar_expanded

        animate()


# RUN APP
if __name__ == "__main__":
    app = InventoryApp()
    app.mainloop()
