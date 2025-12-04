import tkinter as tk 
from tkinter import ttk
from tkinter import messagebox
import datetime

class KitchenInventoryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.state('zoomed')
        self.title("Kitchen Utensin and Monitoring System")
        self.config(bg="#e5d6cc")
        
        self.resizable(True, True)
        self.sidebar_width = 0
        self.sidebar = tk.Frame(self, width=self.sidebar_width, bg="#6B3F2C", height=600)
        self.sidebar.place(x=0, y=0, relheight=1.0)

        self.toggle_btn = tk.Button(self, text= "☰", font=("Arial", 16), command=self.toggle_sidebar)
        self.toggle_btn.place(x=5, y=5)
        
        self.sidebar_shown = False

        self.create_sidebar()

        self.create_main()

    def create_sidebar(self):
        self.label_dashboard = tk.Label(
            self.sidebar,
            text="DASHBOARD",
            bg="#6b3f2c",
            fg="white",
            font=("Arial", 14, "bold")
        )
        self.label_dashboard.place(x=20, y=20)

        menu_items = [
            ("Borrow Items", self.open_borrowed_items),
            ("Return Items", self.open_return_items),
            ("Inventory", self.open_ivtry_items),
            ("Log / History", self.open_logs_history)
        ]


        self.sidebar_button = []
        y_offset = 70

        for text, command in menu_items:
            btn = tk.Button(
                self.sidebar,
                text=text,
                bg="#be8b76",
                fg="white",
                font=("Arial", 12 ,"bold"),
                relief="flat",
                width=15,
                command=command
            )
            btn.place(x=20, y=y_offset)
            self.sidebar_button.append(btn)
            y_offset += 50


        self.logout_btn = tk.Button(
            self.sidebar,
            text="Log Out",
            bg="#8a543f",
            fg="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            width=15,
            height=2,
            command=self.logout
        )  
        self.logout_btn.place(relx=0.05, rely=0.98, y=-20, anchor="sw")


    def create_main(self):
        self.main_frame = tk.Frame(self, bg="#e5d6cc")
        self.main_frame.place(x=0, y=60, relwidth=1, relheight=1)

        header = tk.Label(
            self.main_frame,
            text="KITCHEN UTENSIL AND MONITORING SYSTEM",
            bg="#e5d6cc",
            fg="#6b3f2c",
            font=("Arial", 16, "bold")
        )
        header.pack(pady=15)

        table_frame = tk.Frame(self.main_frame, bg="#e5d6cc")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns =(
            "Borrower Name",
            "ID No.",
            "year & section",
            "Item Borrowed",
            "Quantity",
            "Date Borrowed"
        )
        self.tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        height=15
        )

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")

        self.tree.pack(fill="both", expand=True)
        
    def toggle_sidebar(self):
        target_width = 200 if not self.sidebar_shown else 0
        step = 10 if not self.sidebar_shown else -10

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
                self.sidebar_shown = not self.sidebar_shown

        animate()
    def open_borrowed_items(self):
        pop_up = tk.Toplevel(self)
        pop_up.title("Add Borrowed Item")
        pop_up.geometry("500x500")
        pop_up.config(bg="#e5d6cc")

        labels = ["Borrower Name:","ID No.", "Year & Section:", "Item Borrowed:", "Quantity:", "Date Borrowed (YYYY-MM-DD):"]
        entries = []
        for lbl in labels:
            tk.Label(pop_up, text=lbl, bg="#e5d6cc", anchor="w").pack(pady=5, fill="x", padx=20)
            e = tk.Entry(pop_up)
            e.pack(pady=5, fill="x", padx=20)
            entries.append(e)

        entries[-1].insert(0, datetime.date.today().isoformat())

        def on_submit():
            name = entries[0].get().strip()
            id_no = entries[1].get().strip()
            ys = entries[2].get().strip()
            item = entries[3].get().strip()
            qty = entries[4].get().strip()
            date_b = entries[5].get().strip()

            if not (name and id_no and ys and item and qty and date_b):
                messagebox.showerror("Error", "All fields are required.")
                return
            try:
                qty_int = int(qty)
            except ValueError:
                messagebox.showerror("Error", "Quantity must be an integer.")
                return
            self.tree.insert('', tk.END, values=(name, id_no, ys, item, qty_int, date_b, ""))
            pop_up.destroy()

        tk.Button(pop_up, text="Submit", command=on_submit).pack(pady=20)

        pop_up.grab_set()
        pop_up.wait_window()
        
    def open_return_items(self):

        if not self.tree.get_children():
            messagebox.showwarning("Warning", "No borrowed items to return!")
            return

        pop_up = tk.Toplevel(self)
        pop_up.title("Return Items")
        pop_up.geometry("500x400")
        pop_up.config(bg="#e5d6cc")

        tk.Label(pop_up, text="Select item to return:", 
             font=("Arial", 14, "bold"), bg="#e5d6cc").pack(pady=10)
        
        columns = ("Name", "Item", "Quantity")
        ret_tree = ttk.Treeview(pop_up, columns=columns, show="headings", selectmode="browse")

        for col in columns:
            ret_tree.heading(col, text=col)
            ret_tree.column(col, anchor="center", width=100)

        ret_tree.pack(padx=20, pady=10, fill="both", expand=True)

        for iid in self.tree.get_children():
            vals = self.tree.item(iid)["values"]
            name = vals[0]
            item = vals[3]
            qty = vals[4]
            ret_tree.insert("", "end", iid=iid, values=(name, item, qty))

        def return_item():
            sel = ret_tree.selection()
            if not sel:
                messagebox.showerror("Error", "Please select an item to return.")
                return
            sel_iid = sel[0]
            self.tree.delete(sel_iid)
            messagebox.showinfo("Returned", "Item returned successfully!")
            pop_up.destroy()

        tk.Button(pop_up, text="Return Selected Item", command=return_item).pack(pady=10)

        pop_up.grab_set()
        pop_up.wait_window()

    def open_ivtry_items(self):
        self.create_popup("Add Items")

    def open_logs_history(self):
        self.create_popup("Logs / History")

            
    def  logout(self):
        self.destroy()

app = KitchenInventoryApp()
app.mainloop()