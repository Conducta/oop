import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import datetime

class KitchenInventoryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.state('zoomed')
        self.title("Kitchen Utensil and Monitoring System")
        self.config(bg="#e5d6cc")

        self.resizable(True, True)
        self.sidebar_width = 0
        self.sidebar = tk.Frame(self, width=self.sidebar_width, bg="#6B3F2C", height=600)
        self.sidebar.place(x=0, y=0, relheight=1.0)

        self.toggle_btn = tk.Button(self, text="☰", font=("Arial", 16), command=self.toggle_sidebar)
        self.toggle_btn.place(x=5, y=5)

        self.sidebar_shown = False

        # CENTRAL INVENTORY
        self.inventory_items = []  # {'name': str, 'quantity': int}

        self.create_sidebar()
        self.create_main()

    # ---------- SIDEBAR ----------
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
            ("Log / History", self.open_logs_history),
            ("Generate / Scan QR", self.Qr_user)
        ]

        y_offset = 70
        for text, command in menu_items:
            btn = tk.Button(
                self.sidebar,
                text=text,
                bg="#be8b76",
                fg="white",
                font=("Arial", 12, "bold"),
                relief="flat",
                width=15,
                command=command
            )
            btn.place(x=20, y=y_offset)
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

    # ---------- MAIN TABLE ----------
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

        columns = (
            "Borrower Name",
            "ID No.",
            "Year & Section",
            "Item Borrowed",
            "Quantity",
            "Date Borrowed",
            "Status"
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

    # ---------- SIDEBAR TOGGLE ----------
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

    # ---------- BORROW ITEMS ----------
    def open_borrowed_items(self):
        if not self.inventory_items:
            messagebox.showerror("Error", "Inventory is empty. Add items first.")
            return

        pop_up = tk.Toplevel(self)
        pop_up.title("Add Borrowed Item")
        pop_up.geometry("500x500")
        pop_up.config(bg="#e5d6cc")

        labels = ["Borrower Name:", "ID No.", "Year & Section:", "Item Borrowed:", "Quantity:", "Date Borrowed (YYYY-MM-DD):"]
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
            item_name = entries[3].get().strip()
            qty = entries[4].get().strip()
            date_b = entries[5].get().strip()

            if not (name and id_no and ys and item_name and qty and date_b):
                messagebox.showerror("Error", "All fields are required.")
                return

            try:
                qty_int = int(qty)
            except ValueError:
                messagebox.showerror("Error", "Quantity must be an integer.")
                return

            # CHECK INVENTORY
            for inv in self.inventory_items:
                if inv['name'].lower() == item_name.lower():
                    if inv['quantity'] >= qty_int:
                        inv['quantity'] -= qty_int
                        self.tree.insert('', tk.END, values=(name, id_no, ys, item_name, qty_int, date_b, "Borrowed"))
                        messagebox.showinfo("Success", f"{item_name} borrowed successfully!")
                        pop_up.destroy()
                        return
                    else:
                        messagebox.showerror("Error", f"Not enough {item_name} in inventory!")
                        return
            else:
                messagebox.showerror("Error", f"{item_name} does not exist in inventory!")

        tk.Button(pop_up, text="Submit", command=on_submit).pack(pady=20)
        pop_up.grab_set()
        pop_up.wait_window()

    # ---------- RETURN ITEMS ----------
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
            vals = self.tree.item(sel_iid)["values"]
            returned_item = vals[3]
            returned_qty = vals[4]

            # UPDATE INVENTORY
            for inv in self.inventory_items:
                if inv['name'].lower() == returned_item.lower():
                    inv['quantity'] += returned_qty
                    break

            self.tree.delete(sel_iid)
            messagebox.showinfo("Returned", "Item returned successfully!")
            pop_up.destroy()

        tk.Button(pop_up, text="Return Selected Item", command=return_item).pack(pady=10)
        pop_up.grab_set()
        pop_up.wait_window()

    # ---------- INVENTORY ----------
    def open_ivtry_items(self):
        inv = tk.Toplevel(self)
        inv.title("Inventory")
        inv.geometry("400x350")
        inv.config(bg="#e5d6cc")

        cols = ("name", "quantity")
        inv_tree = ttk.Treeview(inv, columns=cols, show="headings", selectmode="browse")
        inv_tree.heading("name", text="Item Name")
        inv_tree.heading("quantity", text="Quantity")
        inv_tree.column("name", anchor="w", width=200)
        inv_tree.column("quantity", anchor="center", width=100)
        inv_tree.pack(padx=10, pady=10, fill="both", expand=True)

        # REFRESH TREEVIEW
        def refresh_inventory():
            inv_tree.delete(*inv_tree.get_children())
            for item in self.inventory_items:
                inv_tree.insert("", tk.END, values=(item['name'], item['quantity']))

        refresh_inventory()

        btnf = tk.Frame(inv, bg="#e5d6cc")
        btnf.pack(pady=5)

        # ADD
        def add_item():
            name = simpledialog.askstring("New Inventory Item", "Enter item name:", parent=self)
            if not name:
                return
            qty = simpledialog.askinteger("Quantity", f"Enter quantity for {name}:", minvalue=0, parent=self)
            if qty is None:
                return
            self.inventory_items.append({'name': name, 'quantity': qty})
            refresh_inventory()

        # EDIT
        def edit_item():
            sel = inv_tree.selection()
            if not sel:
                messagebox.showwarning("Warning", "No item selected to edit.")
                return
            iid = sel[0]
            current_name, current_qty = inv_tree.item(iid, "values")
            current_qty = int(current_qty)

            new_name = simpledialog.askstring("Edit Item", "Enter new name:", initialvalue=current_name, parent=self)
            if not new_name:
                return
            new_qty = simpledialog.askinteger("Quantity", f"Enter new quantity for {new_name}:", initialvalue=current_qty, minvalue=0, parent=self)
            if new_qty is None:
                return

            for inv_item in self.inventory_items:
                if inv_item['name'] == current_name:
                    inv_item['name'] = new_name
                    inv_item['quantity'] = new_qty
                    break
            refresh_inventory()

        # DELETE
        def delete_item():
            sel = inv_tree.selection()
            if not sel:
                messagebox.showwarning("Warning", "No item selected to delete.")
                return
            iid = sel[0]
            item_name = inv_tree.item(iid, "values")[0]
            self.inventory_items = [item for item in self.inventory_items if item['name'] != item_name]
            refresh_inventory()

        # BUTTONS
        btn_add = tk.Button(btnf, text="Add", command=add_item)
        btn_add.grid(row=0, column=0, padx=5)
        btn_edit = tk.Button(btnf, text="Edit", command=edit_item)
        btn_edit.grid(row=0, column=1, padx=5)
        btn_del = tk.Button(btnf, text="Delete", command=delete_item)
        btn_del.grid(row=0, column=2, padx=5)

        inv.grab_set()
        inv.wait_window()

    # ---------- PLACEHOLDERS ----------
    def open_logs_history(self):
        messagebox.showinfo("Logs / History", "This is a placeholder for logs/history.")

    def Qr_user(self):
        messagebox.showinfo("QR", "This is a placeholder for QR functionality.")

    def logout(self):
        self.destroy()

# ---------- RUN ----------
if __name__ == "__main__":
    app = KitchenInventoryApp()
    app.mainloop()
