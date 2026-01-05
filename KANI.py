import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, simpledialog, filedialog
import datetime
import csv
import sqlite3

DB_PATH = "kitchet.db"
BORROW_DAYS_LIMIT = 7  # Overdue after 7 days

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        school_year TEXT NOT NULL,
        department TEXT NOT NULL
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 0
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS borrow (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        id_no TEXT,
        year_section TEXT,
        item TEXT NOT NULL,
        qty INTEGER NOT NULL DEFAULT 1,
        returned_qty INTEGER DEFAULT 0,
        date_borrow TEXT NOT NULL,
        date_return TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')
    # Migration: ensure columns exist
    c.execute("PRAGMA table_info(borrow)")
    cols = [row[1] for row in c.fetchall()]
    if "id_no" not in cols:
        c.execute("ALTER TABLE borrow ADD COLUMN id_no TEXT")
    if "year_section" not in cols:
        c.execute("ALTER TABLE borrow ADD COLUMN year_section TEXT")
    if "qty" not in cols:
        c.execute("ALTER TABLE borrow ADD COLUMN qty INTEGER NOT NULL DEFAULT 1")
    if "returned_qty" not in cols:
        c.execute("ALTER TABLE borrow ADD COLUMN returned_qty INTEGER DEFAULT 0")
    if "status" not in cols:
        c.execute("ALTER TABLE borrow ADD COLUMN status TEXT")
    conn.commit()
    conn.close()

def get_db_connection():
    return sqlite3.connect(DB_PATH)

class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Login")
        self.geometry("350x250")
        self.config(bg="#e5d6cc")
        self.resizable(False, False)
        tk.Label(self, text="LOGIN", bg="#e5d6cc", fg="#6b3f2c",
                 font=("Arial", 18, "bold")).pack(pady=20)
        frame = tk.Frame(self, bg="#e5d6cc")
        frame.pack(pady=10)
        tk.Label(frame, text="Username:", bg="#e5d6cc").grid(row=0, column=0, pady=5, sticky="w")
        tk.Label(frame, text="Password:", bg="#e5d6cc").grid(row=1, column=0, pady=5, sticky="w")
        self.user_entry = tk.Entry(frame)
        self.pass_entry = tk.Entry(frame, show="*")
        self.user_entry.grid(row=0, column=1, pady=5)
        self.pass_entry.grid(row=1, column=1, pady=5)
        tk.Button(self, text="Login", width=12, command=self.check_login).pack(pady=15)
        self.user_entry.focus()

    def check_login(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()
        if username == "admin" and password == "admin123":
            self.destroy()
            KitchenInventoryApp()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")

class KitchenInventoryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        init_db()
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
        self.inventory_items = []
        self.logs = []
        self.load_items_from_db()
        self.load_borrow_logs_from_db()
        self.create_sidebar()
        self.create_main()
        table_frame = tk.Frame(self.main_frame, bg="#e5d6cc")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        columns = (
            "Borrower Name", "ID No.", "Year & Section",
            "Item Borrowed", "Quantity", "Date Borrowed",
            "Date Returned", "Status"
        )
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        self.tree.pack(fill="both", expand=True)
        # Pagination setup
        self.logs_per_page = 15
        self.current_page = 0

        def display_page():
            self.tree.delete(*self.tree.get_children())
            start = self.current_page * self.logs_per_page
            end = start + self.logs_per_page
            for log in self.logs[start:end]:
                self.tree.insert('', tk.END, iid=str(log.get('db_id')), values=(
                    log.get('borrower'),
                    log.get('id_no'),
                    log.get('ys'),
                    log.get('item'),
                    log.get('qty'),
                    log.get('date_borrowed'),
                    log.get('date_returned') if log.get('date_returned') else "",
                    log.get('status'),
                ))

        btn_frame = tk.Frame(self.main_frame, bg="#e5d6cc")
        btn_frame.pack(pady=5)
        def next_page():
            if (self.current_page + 1) * self.logs_per_page < len(self.logs):
                self.current_page += 1
                display_page()
        def prev_page():
            if self.current_page > 0:
                self.current_page -= 1
                display_page()
        tk.Button(btn_frame, text="<< Prev", command=prev_page).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Next >>", command=next_page).pack(side="right", padx=10)
        display_page()
        self.display_page = display_page  # Make it accessible

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
        if not self.inventory_items:
            messagebox.showerror("Error", "Inventory is empty. Add items first.")
            return
        pop_up = tk.Toplevel(self)
        pop_up.title("Add Borrowed Item")
        pop_up.geometry("580x550")
        pop_up.config(bg="#e5d6cc")
        frame = tk.Frame(pop_up, bg="#e5d6cc")
        frame.pack(padx=40, pady=30, fill="both", expand=True)
        # Department Label
        tk.Label(frame, text="Department:", bg="#e5d6cc", font=("Arial", 12, "bold"), anchor="w").grid(row=0, column=0, sticky="w", pady=(20, 5))
        tk.Label(frame, text="BSHM", bg="#e5d6cc", fg="#6b3f2c", font=("Arial", 12, "bold")).grid(row=0, column=1, sticky="w", pady=(20, 5))
        # Borrower Type (below Department)
        tk.Label(frame, text="Borrower Type:", bg="#e5d6cc", font=("Arial", 12, "bold"), anchor="w").grid(row=1, column=0, sticky="w", pady=(5, 15))
        type_frame = tk.Frame(frame, bg="#e5d6cc")
        type_frame.grid(row=1, column=1, sticky="w", pady=(5, 15))
        borrower_type = tk.StringVar(value="Student")
        tk.Radiobutton(type_frame, text="Student", variable=borrower_type, value="Student", bg="#e5d6cc").pack(side="left", padx=10)
        tk.Radiobutton(type_frame, text="Instructor", variable=borrower_type, value="Instructor", bg="#e5d6cc").pack(side="left", padx=10)
        # Borrower Name
        tk.Label(frame, text="Borrower Name:", bg="#e5d6cc", anchor="w").grid(row=2, column=0, sticky="w", pady=10)
        name_entry = tk.Entry(frame, font=("Arial", 12), width=40)
        name_entry.grid(row=2, column=1, pady=10, sticky="ew")
        # ID No.
        tk.Label(frame, text="ID No.:", bg="#e5d6cc", anchor="w").grid(row=3, column=0, sticky="w", pady=10)
        id_entry = tk.Entry(frame, font=("Arial", 12), width=40)
        id_entry.grid(row=3, column=1, pady=10, sticky="ew")
        # Year & Section
        tk.Label(frame, text="Year & Section:", bg="#e5d6cc", anchor="w").grid(row=4, column=0, sticky="w", pady=10)
        ys_entry = tk.Entry(frame, font=("Arial", 12), width=40)
        ys_entry.grid(row=4, column=1, pady=10, sticky="ew")
        # Item Borrowed
        tk.Label(frame, text="Item Borrowed:", bg="#e5d6cc", anchor="w").grid(row=5, column=0, sticky="w", pady=10)
        item_var = tk.StringVar()
        combobox = ttk.Combobox(frame, textvariable=item_var, state="readonly")
        combobox['values'] = [inv['name'] for inv in self.inventory_items]
        combobox.grid(row=5, column=1, sticky="ew", pady=10)
        # Quantity
        tk.Label(frame, text="Quantity:", bg="#e5d6cc", anchor="w").grid(row=6, column=0, sticky="w", pady=10)
        qty_entry = tk.Entry(frame, font=("Arial", 12), width=40)
        qty_entry.grid(row=6, column=1, pady=10, sticky="ew")
        # Date Borrowed (optional)
        tk.Label(frame, text="Date Borrowed (optional):", bg="#e5d6cc", anchor="w").grid(row=7, column=0, sticky="w", pady=10)
        date_entry = tk.Entry(frame, font=("Arial", 12), width=40)
        date_entry.insert(0, datetime.date.today().isoformat())
        date_entry.grid(row=7, column=1, pady=10, sticky="ew")
        frame.columnconfigure(1, weight=1)
        # Toggle Year & Section based on borrower type
        def toggle_ys(*args):
            if borrower_type.get() == "Student":
                ys_entry.config(state="normal")
                ys_entry.delete(0, tk.END)
            else:
                ys_entry.config(state="disabled")
                ys_entry.delete(0, tk.END)
                ys_entry.insert(0, "BSHM")
        toggle_ys()
        borrower_type.trace("w", toggle_ys)
        def on_submit():
            name = name_entry.get().strip()
            id_no = id_entry.get().strip()
            section_input = ys_entry.get().strip()
            item_name = item_var.get()
            qty_str = qty_entry.get().strip()
            date_b = date_entry.get().strip()
            if not (name and id_no and item_name and qty_str):
                messagebox.showerror("Error", "Borrower Name, ID No., Item Borrowed, and Quantity are required.")
                return
            if borrower_type.get() == "Student":
                if not section_input:
                    messagebox.showerror("Error", "Year & Section is required for students.")
                    return
                year_section = f"BSHM {section_input}"
            else:
                year_section = "Instructor"
            if not date_b:
                date_b = datetime.date.today().isoformat()
            try:
                qty_int = int(qty_str)
                if qty_int <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Quantity must be a positive integer.")
                return
            for inv in self.inventory_items:
                if inv['name'] == item_name:
                    if inv['quantity'] >= qty_int:
                        inv['quantity'] -= qty_int
                        self.update_item_db(inv['id'], inv['name'], inv['quantity'])
                        conn = get_db_connection()
                        c = conn.cursor()
                        c.execute(
                            "INSERT INTO borrow (user_id, name, id_no, year_section, item, qty, returned_qty, date_borrow, date_return) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)",
                            (0, name, id_no, year_section, item_name, qty_int, date_b, "")
                        )
                        borrow_id = c.lastrowid
                        conn.commit()
                        conn.close()
                        self.load_borrow_logs_from_db()
                        self.display_page()
                        messagebox.showinfo("Success", f"{item_name} borrowed successfully!")
                        pop_up.destroy()
                        return
                    else:
                        messagebox.showerror("Error", f"Not enough {item_name} in inventory!")
                        return
            messagebox.showerror("Error", f"Item '{item_name}' not found in inventory!")
        tk.Button(pop_up, text="Submit", command=on_submit, width=20).pack(pady=30, anchor="e", padx=40)
        pop_up.grab_set()
        pop_up.wait_window()

    def open_return_items(self):
        self.load_borrow_logs_from_db()
        active_logs = [log for log in self.logs if log['status'] != "Returned"]
        if not active_logs:
            messagebox.showwarning("Warning", "No borrowed items to return!")
            return
        pop_up = tk.Toplevel(self)
        pop_up.title("Return Items")
        pop_up.geometry("600x500")
        pop_up.config(bg="#e5d6cc")
        tk.Label(pop_up, text="Select item to return:",
                 font=("Arial", 14, "bold"), bg="#e5d6cc").pack(pady=10)
        columns = ("Name", "Item", "Qty Outstanding")
        ret_tree = ttk.Treeview(pop_up, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            ret_tree.heading(col, text=col)
            ret_tree.column(col, anchor="center", width=180)
        ret_tree.pack(padx=20, pady=10, fill="both", expand=True)
        for log in active_logs:
            outstanding = log['qty'] - log.get('returned_qty', 0)
            if outstanding > 0:
                ret_tree.insert("", "end", iid=str(log['db_id']), values=(log['borrower'], log['item'], outstanding))

        def return_item():
            sel = ret_tree.selection()
            if not sel:
                messagebox.showerror("Error", "Please select an item to return.")
                return
            sel_iid = sel[0]
            db_id = int(sel_iid)
            log = next((l for l in self.logs if l['db_id'] == db_id), None)
            if not log:
                return
            item_name = log['item']
            outstanding = log['qty'] - log.get('returned_qty', 0)

            qty_str = simpledialog.askstring("Return Quantity", f"How many {item_name} to return?\n(Outstanding: {outstanding})", initialvalue=str(outstanding))
            if not qty_str or not qty_str.isdigit():
                return
            return_qty = int(qty_str)
            if return_qty < 1 or return_qty > outstanding:
                messagebox.showerror("Error", "Invalid quantity.")
                return

            # Update inventory
            for inv in self.inventory_items:
                if inv['name'] == item_name:
                    inv['quantity'] += return_qty
                    self.update_item_db(inv['id'], inv['name'], inv['quantity'])
                    break

            conn = get_db_connection()
            c = conn.cursor()
            new_returned = log.get('returned_qty', 0) + return_qty
            if new_returned == log['qty']:
                c.execute("UPDATE borrow SET returned_qty = ?, date_return = ? WHERE id = ?", (new_returned, datetime.date.today().isoformat(), db_id))
                log['status'] = "Returned"
                log['date_returned'] = datetime.date.today().isoformat()
                messagebox.showinfo("Returned", "All items returned successfully!")
            else:
                missing = log['qty'] - new_returned
                c.execute("UPDATE borrow SET returned_qty = ? WHERE id = ?", (new_returned, db_id))
                log['status'] = f"Missing {missing}"
                messagebox.showinfo("Partial Return", f"{return_qty} returned. {missing} still missing.")

            log['returned_qty'] = new_returned
            conn.commit()
            conn.close()

            self.load_borrow_logs_from_db()
            self.display_page()
            ret_tree.delete(sel_iid)
            if not ret_tree.get_children():
                pop_up.destroy()

        tk.Button(pop_up, text="Return Selected Item", command=return_item).pack(pady=10)
        pop_up.grab_set()
        pop_up.wait_window()

    def open_edit_item(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "No borrowed item selected to edit.")
            return
        iid = sel[0]
        db_id = int(iid)
        vals = list(self.tree.item(iid)["values"])
        cur_name, cur_id_no, cur_ys, cur_item, cur_qty_str, cur_date_b, cur_date_r, cur_status = vals
        cur_qty = int(cur_qty_str)

        pop = tk.Toplevel(self)
        pop.title("Edit Borrowed Item")
        pop.geometry("550x450")
        pop.config(bg="#e5d6cc")

        frame = tk.Frame(pop, bg="#e5d6cc")
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        labels = [
            "Borrower Name:", "ID No.:", "Year & Section:", "Item Borrowed:",
            "Quantity:", "Date Borrowed:", "Date Returned (optional):", "Status:"
        ]
        entries = []
        for i, lbl_text in enumerate(labels):
            tk.Label(frame, text=lbl_text, bg="#e5d6cc", anchor="w").grid(row=i, column=0, sticky="w", pady=8, padx=5)
            if lbl_text == "Item Borrowed:":
                item_var = tk.StringVar(value=cur_item)
                cb_item = ttk.Combobox(
                    frame, textvariable=item_var, state='readonly',
                    values=[inv['name'] for inv in self.inventory_items]
                )
                cb_item.grid(row=i, column=1, sticky="ew", pady=8)
                entries.append(cb_item)
            else:
                e = tk.Entry(frame, font=("Arial", 12))
                e.grid(row=i, column=1, sticky="ew", pady=8)
                if i == 0: e.insert(0, cur_name)
                elif i == 1: e.insert(0, cur_id_no)
                elif i == 2: e.insert(0, cur_ys)
                elif i == 4: e.insert(0, cur_qty_str)
                elif i == 5: e.insert(0, cur_date_b)
                elif i == 6: e.insert(0, cur_date_r or "")
                elif i == 7: e.insert(0, cur_status)
                entries.append(e)
        frame.columnconfigure(1, weight=1)

        btn_frame = tk.Frame(pop, bg="#e5d6cc")
        btn_frame.pack(pady=15)

        def on_update():
            new_vals = [e.get().strip() if isinstance(e, tk.Entry) else e.get().strip() for e in entries]
            new_name, new_id_no, new_ys, new_item, new_qty_str, new_date_b, new_date_r, new_status = new_vals
            new_date_r = new_date_r or ""

            try:
                new_qty = int(new_qty_str)
                if new_qty <= 0: raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Invalid quantity.")
                return

            qty_diff = new_qty - cur_qty
            updated = False
            for inv in self.inventory_items:
                if inv['name'] == new_item:
                    if inv['quantity'] >= qty_diff or qty_diff < 0:
                        inv['quantity'] -= qty_diff
                        self.update_item_db(inv['id'], inv['name'], inv['quantity'])
                        updated = True
                        break
            if not updated:
                messagebox.showerror("Error", "Not enough stock.")
                return

            conn = get_db_connection()
            c = conn.cursor()
            c.execute("""
                UPDATE borrow
                SET name=?, id_no=?, year_section=?, item=?, qty=?, date_borrow=?, date_return=?, status=?
                WHERE id=?
            """, (new_name, new_id_no, new_ys, new_item, new_qty, new_date_b, new_date_r, new_status, db_id))

            conn.commit()
            conn.close()

            self.load_borrow_logs_from_db()
            self.display_page()
            messagebox.showinfo("Success", "Record updated.")
            pop.destroy()

        def on_delete():
            if messagebox.askyesno("Delete", "Delete this record? Stock will be returned."):
                for inv in self.inventory_items:
                    if inv['name'] == cur_item:
                        inv['quantity'] += cur_qty
                        self.update_item_db(inv['id'], inv['name'], inv['quantity'])
                        break
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("DELETE FROM borrow WHERE id=?", (db_id,))
                conn.commit()
                conn.close()
                self.tree.delete(iid)
                self.load_borrow_logs_from_db()
                messagebox.showinfo("Deleted", "Record deleted.")
                pop.destroy()

        tk.Button(btn_frame, text="Update", command=on_update, bg="#6b3f2c", fg="white", width=12).pack(side="right", padx=5)
        tk.Button(btn_frame, text="Delete", command=on_delete, bg="red", fg="white", width=12).pack(side="right", padx=5)

        pop.grab_set()
        pop.wait_window()

    def open_invtry_items(self):
        inv = tk.Toplevel(self)
        inv.title("Inventory")
        inv.geometry("600x500")
        inv.config(bg="#e5d6cc")
        cols = ("name", "quantity")
        inv_tree = ttk.Treeview(inv, columns=cols, show="headings", selectmode="browse")
        inv_tree.heading("name", text="Item Name")
        inv_tree.heading("quantity", text="Quantity")
        inv_tree.column("name", anchor="w", width=350)
        inv_tree.column("quantity", anchor="center", width=150)
        inv_tree.pack(padx=20, pady=20, fill="both", expand=True)
        def refresh_inventory():
            inv_tree.delete(*inv_tree.get_children())
            for item in self.inventory_items:
                inv_tree.insert("", "end", iid=str(item['id']), values=(item['name'], item['quantity']))
        refresh_inventory()
        btnf = tk.Frame(inv, bg="#e5d6cc")
        btnf.pack(pady=10)
        def add_item():
            name = simpledialog.askstring("New Inventory Item", "Enter item name:", parent=inv)
            if not name or not name.strip():
                return
            name = name.strip()
            qty = simpledialog.askinteger("Quantity", f"Enter initial quantity for '{name}':", minvalue=0, initialvalue=0, parent=inv)
            if qty is None:
                return
            self.add_item_db(name, qty)
            refresh_inventory()
        def edit_item():
            sel = inv_tree.selection()
            if not sel:
                messagebox.showwarning("No Selection", "Please select an item to edit.")
                return
            item_iid = sel[0]
            item_values = inv_tree.item(item_iid, "values")
            current_name = item_values[0]
            current_qty = int(item_values[1])
            item_id = int(item_iid)
            current_item = next((it for it in self.inventory_items if it['id'] == item_id), None)
            if not current_item:
                messagebox.showerror("Error", "Item not found.")
                return
            new_name = simpledialog.askstring("Edit Item Name", "Enter new name:", initialvalue=current_name, parent=inv)
            if new_name is None:
                return
            new_name = new_name.strip()
            if not new_name:
                messagebox.showerror("Error", "Item name cannot be empty.")
                return
            new_qty = simpledialog.askinteger("Edit Quantity", f"Enter new quantity for '{new_name}':",
                                              initialvalue=current_qty, minvalue=0, parent=inv)
            if new_qty is None:
                return
            self.update_item_db(item_id, new_name, new_qty)
            refresh_inventory()
        def delete_item():
            sel = inv_tree.selection()
            if not sel:
                messagebox.showwarning("No Selection", "Please select an item to delete.")
                return
            item_iid = sel[0]
            item_name = inv_tree.item(item_iid, "values")[0]
            item_id = int(item_iid)
            confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{item_name}'?")
            if not confirm:
                return
            self.delete_item_db(item_id)
            refresh_inventory()
        tk.Button(btnf, text="Add Item", command=add_item, width=12).grid(row=0, column=0, padx=10)
        tk.Button(btnf, text="Edit Item", command=edit_item, width=12).grid(row=0, column=1, padx=10)
        tk.Button(btnf, text="Delete Item", command=delete_item, width=12, bg="red", fg="white").grid(row=0, column=2, padx=10)
        inv.grab_set()
        inv.wait_window()

    def open_logs_history(self):
        pop = tk.Toplevel(self)
        pop.title("Logs / History")
        pop.geometry("1300x600")
        pop.config(bg="#e5d6cc")
        cols = ("Borrower", "ID No.", "Year & Section", "Item", "Qty Borrowed", "Qty Returned", "Date Borrowed", "Date Returned", "Status")
        logs_tree = ttk.Treeview(pop, columns=cols, show="headings", selectmode="extended")
        for c in cols:
            logs_tree.heading(c, text=c)
            logs_tree.column(c, anchor="center", width=120)
        logs_tree.pack(fill="both", expand=True, padx=10, pady=10)
        def refresh_logs():
            logs_tree.delete(*logs_tree.get_children())
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT name, id_no, year_section, item, qty, returned_qty, date_borrow, date_return
                FROM borrow
                ORDER BY id DESC
            """)
            today = datetime.date.today()
            for row in cur.fetchall():
                name, id_no, year_section, item, qty_borrowed, returned_qty, db, dr = row
                returned_qty = returned_qty or 0
                missing = qty_borrowed - returned_qty
                if dr and dr.strip():
                    status = "Returned" if returned_qty == qty_borrowed else f"Missing {missing}"
                else:
                    days_out = (today - datetime.date.fromisoformat(db)).days
                    status = "Overdue" if days_out > BORROW_DAYS_LIMIT else ("Borrowed" if returned_qty == 0 else f"Missing {missing}")
                logs_tree.insert(
                    "", tk.END,
                    values=(
                        name,
                        id_no or "",
                        year_section or "",
                        item,
                        qty_borrowed,
                        returned_qty,
                        db,
                        dr if dr and dr.strip() else "",
                        status
                    )
                )
            conn.close()
        def export_csv():
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, user_id, name, id_no, year_section, item, qty, returned_qty, date_borrow, date_return FROM borrow ORDER BY id DESC")
            rows = cur.fetchall()
            conn.close()
            if not rows:
                messagebox.showinfo("Export", "No logs to export.")
                return
            filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")])
            if not filepath:
                return
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["id", "user_id", "name", "id_no", "year_section", "item", "qty", "returned_qty", "date_borrow", "date_return"])
                for r in rows:
                    writer.writerow(r)
            messagebox.showinfo("Export", f"Logs exported to {filepath}")
        btnf = tk.Frame(pop, bg="#e5d6cc")
        btnf.pack(pady=5)
        tk.Button(btnf, text="Refresh", command=refresh_logs).grid(row=0, column=0, padx=5)
        tk.Button(btnf, text="Export CSV", command=export_csv).grid(row=0, column=1, padx=5)
        tk.Button(btnf, text="Close", command=pop.destroy).grid(row=0, column=2, padx=5)
        refresh_logs()
        pop.grab_set()
        pop.wait_window()

    def logout(self):
        for child in self.winfo_children():
            if isinstance(child, tk.Toplevel):
                child.destroy()
        self.destroy()
        LoginWindow()

    def create_sidebar(self):
        self.label_dashboard = tk.Label(
            self.sidebar, text="DASHBOARD", bg="#6b3f2c",
            fg="white", font=("Arial", 14, "bold")
        )
        self.label_dashboard.place(x=20, y=20)
        menu_items = [
            ("Borrow Items", self.open_borrowed_items),
            ("Return Items", self.open_return_items),
            ("Edit Borrowed Item", self.open_edit_item),
            ("Inventory", self.open_invtry_items),
            ("Log / History", self.open_logs_history),
        ]
        self.sidebar_button = []
        y_offset = 70
        for text, command in menu_items:
            btn = tk.Button(
                self.sidebar, text=text, bg="#be8b76", fg="white",
                font=("Arial", 12, "bold"), relief="flat", width=15,
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

    def load_items_from_db(self):
        self.inventory_items.clear()
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT id, item_name, quantity FROM items")
        rows = c.fetchall()
        for r in rows:
            self.inventory_items.append({'id': r[0], 'name': r[1], 'quantity': r[2]})
        conn.close()

    def load_borrow_logs_from_db(self):
        self.logs.clear()
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
            SELECT id, user_id, name, id_no, year_section, item, qty, returned_qty, date_borrow, date_return, status
            FROM borrow
            ORDER BY id DESC
        """)
        today = datetime.date.today()
        for row in c.fetchall():
            db_id, user_id, name, id_no, ys, item, qty, returned_qty, date_borrow, date_return, db_status = row
            returned_qty = returned_qty or 0
            missing = qty - returned_qty
            borrow_date = datetime.date.fromisoformat(date_borrow)
            days_out = (today - borrow_date).days

            if returned_qty == qty and date_return:
                status = "Returned"
            elif returned_qty > 0 and returned_qty < qty:
                status = f"Missing {missing}"
            elif days_out > BORROW_DAYS_LIMIT:
                status = "Overdue"
            else:
                status = "Borrowed"
            

            self.logs.append({
                'db_id': db_id,
                'user_id': user_id,
                'borrower': name,
                'id_no': id_no or "",
                'ys': ys or "",
                'item': item,
                'qty': qty,
                'returned_qty': returned_qty,
                'date_borrowed': date_borrow,
                'date_returned': date_return,
                'status': status
            })
        conn.close()

    def add_item_db(self, name, qty):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT INTO items (item_name, quantity) VALUES (?, ?)", (name, qty))
        conn.commit()
        item_id = c.lastrowid
        conn.close()
        self.inventory_items.append({'id': item_id, 'name': name, 'quantity': qty})

    def update_item_db(self, item_id, new_name, new_qty):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("UPDATE items SET item_name=?, quantity=? WHERE id=?", (new_name, new_qty, item_id))
        conn.commit()
        conn.close()
        for it in self.inventory_items:
            if it['id'] == item_id:
                it['name'] = new_name
                it['quantity'] = new_qty
                break

    def delete_item_db(self, item_id):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("DELETE FROM items WHERE id=?", (item_id,))
        conn.commit()
        conn.close()
        self.inventory_items = [it for it in self.inventory_items if it['id'] != item_id]

if __name__ == "__main__":
    init_db()
    LoginWindow().mainloop()