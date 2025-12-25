import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, simpledialog, filedialog
import datetime
import csv
import sqlite3

class Student:
    def __init__(self, name, quizzes):
        self.name = name
        self.quizzes = quizzes
    def compute_average(self):
        return sum(self.quizzes) / len(self.quizzes) if self.quizzes else 0

DB_PATH = "kitchet.db"

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
        year_section TEXT NOT NULL DEFAULT 'HM',  -- Fixed to HM
        item TEXT NOT NULL,
        qty INTEGER NOT NULL DEFAULT 1,
        date_borrow TEXT NOT NULL,
        date_return TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')
    # Migration: ensure columns exist and set default year_section to 'HM' if missing
    c.execute("PRAGMA table_info(borrow)")
    cols = [row[1] for row in c.fetchall()]
    if "id_no" not in cols:
        c.execute("ALTER TABLE borrow ADD COLUMN id_no TEXT")
    if "year_section" not in cols:
        c.execute("ALTER TABLE borrow ADD COLUMN year_section TEXT DEFAULT 'HM'")
    else:
        # If column exists but has no default, set default
        c.execute("ALTER TABLE borrow RENAME TO borrow_old")
        c.execute('''
        CREATE TABLE borrow (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            id_no TEXT,
            year_section TEXT NOT NULL DEFAULT 'HM',
            item TEXT NOT NULL,
            qty INTEGER NOT NULL DEFAULT 1,
            date_borrow TEXT NOT NULL,
            date_return TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        ''')
        c.execute("INSERT INTO borrow SELECT id, user_id, name, id_no, COALESCE(year_section, 'HM'), item, qty, date_borrow, date_return FROM borrow_old")
        c.execute("DROP TABLE borrow_old")
    if "qty" not in cols:
        c.execute("ALTER TABLE borrow ADD COLUMN qty INTEGER NOT NULL DEFAULT 1")
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
        self.title("Kitchen Utensil and Monitoring System - HM Department Only")
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
                self.tree.insert('', tk.END, values=(
                    log.get('borrower'),
                    log.get('id_no'),
                    log.get('ys'),
                    log.get('item'),
                    log.get('qty'),
                    log.get('date_borrowed'),
                    log.get('date_returned') if log.get('date_returned') else "",
                    log.get('status'),
                ))

        # Buttons for pagination
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
        pop_up.title("Add Borrowed Item (HM Department Only)")
        pop_up.geometry("500x300")
        pop_up.config(bg="#e5d6cc")
        labels = ["Borrower Name:", "ID No.", "Year & Section (HM Only):", "Item Borrowed:", "Quantity:", "Date Borrowed (YYYY-MM-DD):"]
        entries = []
        frame = tk.Frame(pop_up, bg="#e5d6cc")
        frame.pack(padx=20, pady=20, fill="both", expand=True)
        for i, lbl_text in enumerate(labels):
            tk.Label(frame, text=lbl_text, bg="#e5d6cc", anchor="w").grid(row=i, column=0, sticky="w", pady=5, padx=5)
            if lbl_text == "Item Borrowed:":
                item_var = tk.StringVar()
                combobox = ttk.Combobox(frame, textvariable=item_var, state="readonly")
                combobox['values'] = [inv['name'] for inv in self.inventory_items]
                combobox.grid(row=i, column=1, sticky="ew", pady=5, padx=5)
                entries.append(combobox)
            elif lbl_text == "Year & Section (HM Only):":
                e = tk.Entry(frame)
                e.insert(0, "HM")
                e.config(state="disabled")
                e.grid(row=i, column=1, sticky="ew", pady=5, padx=5)
                entries.append(e)
            else:
                e = tk.Entry(frame)
                e.grid(row=i, column=1, sticky="ew", pady=5, padx=5)
                e.config(font=("Arial", 12))
                entries.append(e)
        entries[-1].insert(0, datetime.date.today().isoformat())  # Date Borrowed
        frame.columnconfigure(1, weight=1)
        tk.Button(pop_up, text="Submit", command=lambda: on_submit(), width=20).pack(pady=20, anchor="e", padx=10)
        def on_submit():
            name = entries[0].get().strip()
            id_no = entries[1].get().strip()
            ys = entries[2].get().strip()  # Always "HM"
            item_name = entries[3].get().strip()
            qty = entries[4].get().strip()
            date_b = entries[5].get().strip()
            if not (name and id_no and item_name and qty and date_b):
                messagebox.showerror("Error", "All fields are required.")
                return
            if ys != "HM":
                messagebox.showerror("Error", "Only HM department can borrow items.")
                return
            try:
                qty_int = int(qty)
            except ValueError:
                messagebox.showerror("Error", "Quantity must be an integer.")
                return
            for inv in self.inventory_items:
                if inv['name'] == item_name:
                    if inv['quantity'] >= qty_int:
                        inv['quantity'] -= qty_int
                        self.update_item_db(inv['id'], inv['name'], inv['quantity'])
                        self.tree.insert('', tk.END, values=(name, id_no, ys, item_name, qty_int, date_b, "", "Borrowed"))
                        log_entry = {
                            'borrower': name,
                            'id_no': id_no,
                            'ys': ys,
                            'item': item_name,
                            'qty': qty_int,
                            'date_borrowed': date_b,
                            'date_returned': None,
                            'status': 'Borrowed'
                        }
                        self.logs.append(log_entry)
                        self.save_borrow_db(0, name, id_no, ys, item_name, qty_int, date_b, "")
                        messagebox.showinfo("Success", f"{item_name} borrowed successfully!")
                        pop_up.destroy()
                        return
                    else:
                        messagebox.showerror("Error", f"Not enough {item_name} in inventory!")
                        return
            messagebox.showerror("Error", f"Item '{item_name}' not found in inventory!")
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
            item_name = vals[3]
            qty = vals[4]
            ret_tree.insert("", "end", iid=iid, values=(name, item_name, qty))
        def return_item():
            sel = ret_tree.selection()
            if not sel:
                messagebox.showerror("Error", "Please select an item to return.")
                return
            sel_iid = sel[0]
            vals = self.tree.item(sel_iid)['values']
            borrower = vals[0]
            id_no = vals[1]
            ys = vals[2]
            returned_item = vals[3]
            returned_qty = int(vals[4])
            date_borrowed = vals[5]
            date_returned = datetime.date.today().isoformat()
            status = "Returned"
            if ys != "HM":
                messagebox.showerror("Error", "Only HM department records can be returned here.")
                return
            for inv in self.inventory_items:
                if inv['name'].lower() == returned_item.lower():
                    inv['quantity'] += returned_qty
                    self.update_item_db(inv['id'], inv['name'], inv['quantity'])
                    break
            else:
                self.add_item_db(returned_item, returned_qty)
            # Update borrow record
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("""
                UPDATE borrow
                SET date_return = ?
                WHERE name = ?
                AND item = ?
                AND qty = ?
                AND date_borrow = ?
            """, (date_returned, borrower, returned_item, returned_qty, date_borrowed))
            conn.commit()
            conn.close()
            # Update table row
            self.tree.item(
                sel_iid,
                values=(
                    borrower,
                    id_no,
                    ys,
                    returned_item,
                    returned_qty,
                    date_borrowed,
                    date_returned,
                    "Returned"
                )
            )
            messagebox.showinfo("Returned", "Item returned successfully!")
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
        vals = list(self.tree.item(iid)["values"])
        cur_name, cur_id_no, cur_ys, cur_item, cur_qty, cur_date_b, cur_date_r, cur_status = vals

        # Only allow editing if year_section is HM
        if cur_ys != "HM":
            messagebox.showerror("Error", "Only HM department records can be edited.")
            return

        # Find the corresponding log entry
        log_entry = next((log for log in self.logs if log.get('db_id') and
                          log['borrower'] == cur_name and
                          log['id_no'] == cur_id_no and
                          log['ys'] == cur_ys and
                          log['item'] == cur_item and
                          log['qty'] == int(cur_qty) and
                          log['date_borrowed'] == cur_date_b), None)

        if not log_entry or 'db_id' not in log_entry:
            messagebox.showerror("Error", "Could not find matching borrow record in database.")
            return

        db_id = log_entry['db_id']

        pop = tk.Toplevel(self)
        pop.title("Edit Borrowed Item (HM Only)")
        pop.geometry("500x350")
        pop.config(bg="#e5d6cc")
        frame = tk.Frame(pop, bg="#e5d6cc")
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        labels = [
            "Borrower Name:", "ID No.:", "Year & Section (HM Only):", "Item Borrowed:",
            "Quantity:", "Date Borrowed (YYYY-MM-DD):", "Date Returned (optional):", "Status:"
        ]
        entries = []
        for i, lbl_text in enumerate(labels):
            tk.Label(frame, text=lbl_text, bg="#e5d6cc", anchor="w").grid(row=i, column=0, sticky="w", pady=5, padx=5)
            if lbl_text == "Item Borrowed:":
                item_var = tk.StringVar(value=cur_item)
                cb_item = ttk.Combobox(
                    frame, textvariable=item_var, state='readonly',
                    values=[inv['name'] for inv in self.inventory_items]
                )
                cb_item.grid(row=i, column=1, sticky="ew", pady=5, padx=5)
                entries.append(cb_item)
            elif lbl_text == "Year & Section (HM Only):":
                e = tk.Entry(frame, state="disabled")
                e.insert(0, cur_ys)
                e.grid(row=i, column=1, sticky="ew", pady=5, padx=5)
                entries.append(e)
            else:
                e = tk.Entry(frame)
                e.grid(row=i, column=1, sticky="ew", pady=5, padx=5)
                e.config(font=("Arial", 12))
                if lbl_text == "Borrower Name:": e.insert(0, cur_name)
                elif lbl_text == "ID No.:": e.insert(0, cur_id_no)
                elif lbl_text == "Quantity:": e.insert(0, cur_qty)
                elif lbl_text == "Date Borrowed (YYYY-MM-DD):": e.insert(0, cur_date_b)
                elif lbl_text == "Date Returned (optional):": e.insert(0, cur_date_r if cur_date_r else "")
                elif lbl_text == "Status:": e.insert(0, cur_status)
                entries.append(e)

        frame.columnconfigure(1, weight=1)

        btn_frame = tk.Frame(pop, bg="#e5d6cc")
        btn_frame.pack(fill="x", padx=20, pady=10, anchor="e")

        def on_update():
            new_vals = [ent.get() if isinstance(ent, tk.Entry) else ent.get() for ent in entries]
            new_name = new_vals[0]
            new_id_no = new_vals[1]
            new_ys = "HM"  # Always HM
            new_item = new_vals[3]
            new_qty_str = new_vals[4]
            new_date_b = new_vals[5]
            new_date_r = new_vals[6] if new_vals[6].strip() else None
            new_status = new_vals[7]

            try:
                new_qty = int(new_qty_str)
            except ValueError:
                messagebox.showerror("Error", "Quantity must be an integer.")
                return

            # Update Treeview row
            self.tree.item(iid, values=(
                new_name, new_id_no, new_ys, new_item,
                new_qty, new_date_b, new_date_r or "", new_status
            ))

            # Update in-memory log
            log_entry['borrower'] = new_name
            log_entry['id_no'] = new_id_no
            log_entry['ys'] = new_ys
            log_entry['item'] = new_item
            log_entry['qty'] = new_qty
            log_entry['date_borrowed'] = new_date_b
            log_entry['date_returned'] = new_date_r
            log_entry['status'] = new_status

            # Update database
            self.update_borrow_db(
                db_id, new_name, new_id_no, new_ys, new_item,
                new_qty, new_date_b, new_date_r
            )

            messagebox.showinfo("Updated", "Borrowed item updated successfully.")
            pop.destroy()

        def on_delete():
            confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this borrowed item?")
            if not confirm:
                return

            # Return quantity to inventory
            for inv in self.inventory_items:
                if inv['name'] == cur_item:
                    inv['quantity'] += int(cur_qty)
                    self.update_item_db(inv['id'], inv['name'], inv['quantity'])
                    break
            else:
                self.add_item_db(cur_item, int(cur_qty))

            # Delete from database
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("DELETE FROM borrow WHERE id = ?", (db_id,))
            conn.commit()
            conn.close()

            # Remove from in-memory logs and Treeview
            self.logs = [log for log in self.logs if log.get('db_id') != db_id]
            self.tree.delete(iid)

            messagebox.showinfo("Deleted", "Borrowed item deleted successfully.")
            pop.destroy()

        tk.Button(btn_frame, text="Update", command=on_update, width=15).pack(side="right", padx=5)
        tk.Button(btn_frame, text="Delete", command=on_delete, bg="red", fg="white", width=15).pack(side="right", padx=5)
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
        pop.title("Logs / History (HM Department)")
        pop.geometry("900x500")
        pop.config(bg="#e5d6cc")
        cols = ("Borrower", "ID No.", "Year & Section", "Item", "Qty", "Date Borrowed", "Date Returned", "Status")
        logs_tree = ttk.Treeview(pop, columns=cols, show="headings", selectmode="extended")
        for c in cols:
            logs_tree.heading(c, text=c)
            logs_tree.column(c, anchor="center", width=110)
        logs_tree.pack(fill="both", expand=True, padx=10, pady=10)

        def refresh_logs():
            logs_tree.delete(*logs_tree.get_children())
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, name, id_no, year_section, item, qty, date_borrow, date_return
                FROM borrow
                ORDER BY id DESC
            """)
            for row in cur.fetchall():
                borrow_id, name, id_no, year_section, item, qty, db, dr = row
                status = "Returned" if dr and dr.strip() else "Borrowed"
                logs_tree.insert(
                    "", tk.END,
                    values=(
                        name,
                        id_no or "",
                        year_section or "",
                        item,
                        qty,
                        db,
                        dr if dr and dr.strip() else "",
                        status
                    ),
                    iid=str(borrow_id)
                )
            conn.close()

        def export_csv():
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, user_id, name, id_no, year_section, item, qty, date_borrow, date_return FROM borrow ORDER BY id DESC")
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
                writer.writerow(["id", "user_id", "name", "id_no", "year_section", "item", "qty", "date_borrow", "date_return"])
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
            text="KITCHEN UTENSIL AND MONITORING SYSTEM - HM DEPARTMENT ONLY",
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
            SELECT id, user_id, name, id_no, year_section, item, qty, date_borrow, date_return
            FROM borrow
            WHERE (date_return = '' OR date_return IS NULL OR date_return = 'None')
            AND year_section = 'HM'
            ORDER BY id DESC
        """)
        rows = c.fetchall()
        for row in rows:
            db_id, user_id, name, id_no, ys, item, qty, date_borrow, date_return = row
            self.logs.append({
                'db_id': db_id,
                'user_id': user_id,
                'borrower': name,
                'id_no': id_no or "",
                'ys': ys,
                'item': item,
                'qty': qty,
                'date_borrowed': date_borrow,
                'date_returned': date_return,
                'status': 'Borrowed'
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

    def save_borrow_db(self, user_id, name, id_no, year_section, item, qty, date_borrow, date_return):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(
            "INSERT INTO borrow (user_id, name, id_no, year_section, item, qty, date_borrow, date_return) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, name, id_no or "", year_section, item, qty, date_borrow, date_return)
        )
        conn.commit()
        conn.close()

    def update_borrow_db(self, borrow_id, name, id_no, year_section, item, qty, date_borrow, date_return):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
            UPDATE borrow
            SET name = ?, id_no = ?, year_section = ?, item = ?, qty = ?,
                date_borrow = ?, date_return = ?
            WHERE id = ?
        """, (name, id_no or "", year_section, item, qty, date_borrow, date_return, borrow_id))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    init_db()
    LoginWindow().mainloop()