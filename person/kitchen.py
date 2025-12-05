import tkinter as tk 
from tkinter import ttk
from tkinter import messagebox, simpledialog, filedialog
import datetime
import csv

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

        self.inventory_items = []
        self.logs = []  # <- store borrow/return history here

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
            ("Edit Borrowed Item", self.open_edit_item),
            ("Inventory", self.open_invtry_items),
            ("Log / History", self.open_logs_history),
            ("Generate / Scan QR", self.Qr_user)
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

    # MAIN
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
            "Date Borrowed",
            "Date Returned",
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

    # Borrow
    def open_borrowed_items(self):
        if not self.inventory_items:
            messagebox.showerror("Error", "Inventory is empty. Add items first.")
            return
        pop_up = tk.Toplevel(self)
        pop_up.title("Add Borrowed Item")
        pop_up.geometry("500x500")
        pop_up.config(bg="#e5d6cc")

        labels = ["Borrower Name:","ID No.", "Year & Section:", "Item Borrowed:", "Quantity:", "Date Borrowed (YYYY-MM-DD):"]
        entries = []
        for lbl in labels:
            tk.Label(pop_up, text=lbl, bg="#e5d6cc", anchor="w").pack(pady=5, fill="x", padx=20)
            if lbl == "Item Borrowed:":
                item_var = tk.StringVar()
                combobox = ttk.Combobox(
                    pop_up,
                    textvariable=item_var,
                    state="readonly"
                )
                combobox['values'] = [inv['name'] for inv in self.inventory_items]
                combobox.pack(pady=5, fill="x", padx=20)
                entries.append(combobox)
            else:
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
            
            for inv in self.inventory_items:
                if inv['name'] == item_name:
                    if inv['quantity'] >= qty_int:
                        inv['quantity'] -= qty_int
                        # insert into active borrowed tree (Date Returned empty)
                        self.tree.insert('', tk.END, values=(name, id_no, ys, item_name, qty_int, date_b, "", "Borrowed"))
                        # add to logs history
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
                        messagebox.showinfo("Success", f"{item_name} borrowed successfully!")
                        pop_up.destroy()
                        return
                    else:
                        messagebox.showerror("Error", f"Not enough {item_name} in inventory!")
                        return
            
            messagebox.showerror("Error", f"Not enough {item_name} in inventory!")
        tk.Button(pop_up, text="Submit", command=on_submit).pack(pady=20, anchor="se", padx=10)

        pop_up.grab_set()
        pop_up.wait_window()

    # Return item       
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
            # vals: [name, id_no, ys, item_name, qty, date_b, date_r, status]
            borrower = vals[0]
            id_no = vals[1]
            ys = vals[2]
            returned_item = vals[3]
            returned_qty = int(vals[4])
            date_borrowed = vals[5]

            date_returned = datetime.date.today().isoformat()
            status = "Returned"

            # update inventory: find item and increase quantity
            for inv in self.inventory_items:
                if inv['name'].lower() == returned_item.lower():
                    inv['quantity'] += returned_qty
                    break
            else:
                # if item not found in inventory, add it back
                self.inventory_items.append({'name': returned_item, 'quantity': returned_qty})

            # append to logs (update the existing log entry if possible - match by all fields except date_returned)
            matched = False
            for log in self.logs:
                if (log['borrower'] == borrower and log['id_no'] == id_no and
                    log['item'] == returned_item and log['qty'] == returned_qty and
                    log['date_borrowed'] == date_borrowed and log['status'] == 'Borrowed' and
                    log['date_returned'] is None):
                    log['date_returned'] = date_returned
                    log['status'] = status
                    matched = True
                    break
            if not matched:
                # fallback - create a log anyway
                self.logs.append({
                    'borrower': borrower,
                    'id_no': id_no,
                    'ys': ys,
                    'item': returned_item,
                    'qty': returned_qty,
                    'date_borrowed': date_borrowed,
                    'date_returned': date_returned,
                    'status': status
                })

            # remove from active borrowed tree (we keep logs separate)
            self.tree.delete(sel_iid)
            messagebox.showinfo("Returned", "Item returned successfully!")
            pop_up.destroy()

        tk.Button(pop_up, text="Return Selected Item", command=return_item).pack(pady=10)

        pop_up.grab_set()
        pop_up.wait_window()

    # EDIT_BORROW ITEm
    def open_edit_item(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "No borrowed item selected to edit.")
            return
        
        iid = sel[0]
        vals = list(self.tree.item(iid)["values"])
        cur_name, cur_id, cur_ys, cur_item, cur_qty, cur_date_b, cur_date_r, cur_status = vals

        pop = tk.Toplevel(self)
        pop.title("Edit Borrowed Item")
        pop.geometry("500x600")
        pop.config(bg="#e5d6cc")


        tk.Label(pop, text="Borrower Name:", bg="#e5d6cc").pack(pady=5, padx=20, fill="x")
        e_name = tk.Entry(pop); e_name.pack(pady=5, padx=20, fill="x"); e_name.insert(0, cur_name)

        tk.Label(pop, text="ID No.:", bg="#e5d6cc").pack(pady=5, padx=20, fill="x")
        e_id = tk.Entry(pop); e_id.pack(pady=5, padx=20, fill="x"); e_id.insert(0, cur_id)

        tk.Label(pop, text="Year & Section:", bg="#e5d6cc").pack(pady=5, padx=20, fill="x")
        e_ys = tk.Entry(pop); e_ys.pack(pady=5, padx=20, fill="x"); e_ys.insert(0, cur_ys)

        tk.Label(pop, text="Item Borrowed:", bg="#e5d6cc").pack(pady=5, padx=20, fill="x")
        item_var = tk.StringVar(value=cur_item)
        cb_item = ttk.Combobox(pop, textvariable=item_var, state='readonly',
                            values=[inv['name'] for inv in self.inventory_items])
        cb_item.pack(pady=5, padx=20, fill="x")

        tk.Label(pop, text="Quantity:", bg="#e5d6cc").pack(pady=5, padx=20, fill="x")
        e_qty = tk.Entry(pop); e_qty.pack(pady=5, padx=20, fill="x"); e_qty.insert(0, str(cur_qty))

        tk.Label(pop, text="Date Borrowed (YYYY-MM-DD):", bg="#e5d6cc").pack(pady=5, padx=20, fill="x")
        e_date_b = tk.Entry(pop); e_date_b.pack(pady=5, padx=20, fill="x"); e_date_b.insert(0, cur_date_b)

        tk.Label(pop, text="Date Returned (optional):", bg="#e5d6cc").pack(pady=5, padx=20, fill="x")
        e_date_r = tk.Entry(pop); e_date_r.pack(pady=5, padx=20, fill="x"); e_date_r.insert(0, cur_date_r if cur_date_r else "")

        tk.Label(pop, text="Status:", bg="#e5d6cc").pack(pady=5, padx=20, fill="x")
        e_status = tk.Entry(pop); e_status.pack(pady=5, padx=20, fill="x"); e_status.insert(0, cur_status)

        def on_update():
            new_name = e_name.get().strip()
            new_id = e_id.get().strip()
            new_ys = e_ys.get().strip()
            new_item = cb_item.get().strip()
            new_qty_s = e_qty.get().strip()
            new_date_b = e_date_b.get().strip()
            new_date_r = e_date_r.get().strip()
            new_status = e_status.get().strip()

            if not (new_name and new_id and new_ys and new_item and new_qty_s and new_date_b and new_status):
                messagebox.showerror("Error", "All fields (except return date) are required.")
                return
            try:
                new_qty = int(new_qty_s)
            except ValueError:
                messagebox.showerror("Error", "Quantity must be integer.")
                return

            # return previous reserved quantity back to inventory
            for inv in self.inventory_items:
                if inv['name'] == cur_item:
                    try:
                        inv['quantity'] += int(cur_qty)
                    except:
                        inv['quantity'] += 0
                    break

            # deduct new reservation
            for inv in self.inventory_items:
                if inv['name'] == new_item:
                    if inv['quantity'] >= new_qty:
                        inv['quantity'] -= new_qty
                    else:
                        messagebox.showerror("Error", f"Not enough {new_item} in inventory.")
                        # revert earlier change (optional, but keep consistent)
                        for inv2 in self.inventory_items:
                            if inv2['name'] == cur_item:
                                inv2['quantity'] -= int(cur_qty)
                                break
                        return
                    break
            else:
                messagebox.showerror("Error", f"Item {new_item} not found in inventory.")
                return

            new_vals = [new_name, new_id, new_ys, new_item, new_qty, new_date_b, new_date_r, new_status]
            self.tree.item(iid, values=new_vals)

            # update logs if there's a matching log entry (best-effort matching)
            for log in self.logs:
                if (log['borrower'] == cur_name and log['id_no'] == cur_id and
                    log['item'] == cur_item and log['qty'] == cur_qty and
                    log['date_borrowed'] == cur_date_b):
                    log['borrower'] = new_name
                    log['id_no'] = new_id
                    log['ys'] = new_ys
                    log['item'] = new_item
                    log['qty'] = new_qty
                    log['date_borrowed'] = new_date_b
                    log['date_returned'] = new_date_r if new_date_r else log.get('date_returned')
                    log['status'] = new_status
                    break

            messagebox.showinfo("Success", "Borrowed item updated.")
            pop.destroy()

        def on_delete():
            confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this borrowed item?")
            if not confirm:
                return

            # return quantity back to inventory
            for inv in self.inventory_items:
                if inv['name'] == cur_item:
                    inv['quantity'] += int(cur_qty)
                    break
            else:
                self.inventory_items.append({'name': cur_item, 'quantity': int(cur_qty)})

            # remove from treeview
            self.tree.delete(iid)

            # remove from logs (match by all fields except date_returned)
            self.logs = [
                log for log in self.logs
                if not (
                    log['borrower'] == cur_name and
                    log['id_no'] == cur_id and
                    log['item'] == cur_item and
                    log['qty'] == cur_qty and
                    log['date_borrowed'] == cur_date_b
                )
            ]

            messagebox.showinfo("Deleted", "Borrowed item deleted successfully.")
            pop.destroy()


        tk.Button(pop, text="Update", command=on_update).pack(pady=10)
        tk.Button(pop, text="Delete", command=on_delete, bg="red", fg="white").pack(pady=5)

        pop.grab_set()
        pop.wait_window()

    # inventory      
    def open_invtry_items(self):
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

        def refresh_inventory():
            inv_tree.delete(*inv_tree.get_children())
            for item in self.inventory_items:
                inv_tree.insert("", tk.END, values=(item['name'], item['quantity']))

        refresh_inventory()

        btnf = tk.Frame(inv, bg="#e5d6cc")
        btnf.pack(pady=5)

        def add_item():
            name = simpledialog.askstring("New Inventory Item", "Enter item name:", parent=self)
            if not name:
                return
            qty = simpledialog.askinteger("Quantity", f"Enter quantity for {name}:", minvalue=0, parent=self)
            if qty is None:
                return
            self.inventory_items.append({'name': name, 'quantity': qty})
            refresh_inventory()

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

        def delete_item():
            sel = inv_tree.selection()
            if not sel:
                messagebox.showwarning("Warning", "No item selected to delete.")
                return
            iid = sel[0]
            item_name = inv_tree.item(iid, "values")[0]
                
            confirm = messagebox.askyesno(
                    "Confirm Delete",
                    f"Are you sure you want to delete '{item_name}'?"
                )
            if not confirm:
                    return
            self.inventory_items = [item for item in self.inventory_items if item['name'] != item_name]
            refresh_inventory()

        btn_add = tk.Button(btnf, text="Add", command=add_item)
        btn_add.grid(row=0, column=0, padx=5)
        btn_edit = tk.Button(btnf, text="Edit", command=edit_item)
        btn_edit.grid(row=0, column=1, padx=5)
        btn_del = tk.Button(btnf, text="Delete", command=delete_item)
        btn_del.grid(row=0, column=2, padx=5)

        inv.grab_set()
        inv.wait_window()

    def open_logs_history(self):
        pop = tk.Toplevel(self)
        pop.title("Logs / History")
        pop.geometry("900x500")
        pop.config(bg="#e5d6cc")

        cols = ("Borrower", "ID No.", "Year & Section", "Item", "Qty", "Date Borrowed", "Date Returned", "Status")
        logs_tree = ttk.Treeview(pop, columns=cols, show="headings")
        for c in cols:
            logs_tree.heading(c, text=c)
            logs_tree.column(c, anchor="center", width=110)
        logs_tree.pack(fill="both", expand=True, padx=10, pady=10)

        def refresh_logs():
            logs_tree.delete(*logs_tree.get_children())
            for log in reversed(self.logs):
                logs_tree.insert("", tk.END, values=(
                    log.get('borrower'),
                    log.get('id_no'),
                    log.get('ys'),
                    log.get('item'),
                    log.get('qty'),
                    log.get('date_borrowed'),
                    log.get('date_returned') if log.get('date_returned') else "",
                    log.get('status'),
                ))

        def export_csv():
            if not self.logs:
                messagebox.showinfo("Export", "No logs to export.")
                return
            filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")])
            if not filepath:
                return
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(cols)
                for log in self.logs:
                    writer.writerow([
                        log.get('borrower'),
                        log.get('id_no'),
                        log.get('ys'),
                        log.get('item'),
                        log.get('qty'),
                        log.get('date_borrowed'),
                        log.get('date_returned') if log.get('date_returned') else "",
                        log.get('status'),
                    ])
            messagebox.showinfo("Export", f"Logs exported to {filepath}")

        btnf = tk.Frame(pop, bg="#e5d6cc")
        btnf.pack(pady=5)
        tk.Button(btnf, text="Refresh", command=refresh_logs).grid(row=0, column=0, padx=5)
        tk.Button(btnf, text="Export CSV", command=export_csv).grid(row=0, column=1, padx=5)
        tk.Button(btnf, text="Close", command=pop.destroy).grid(row=0, column=2, padx=5)

        refresh_logs()
        pop.grab_set()
        pop.wait_window()

    def Qr_user(self):
        self.create_popup("QR")
            
    def  logout(self):
        self.destroy()

    # keep a simple generic popup helper used earlier in your code
    def create_popup(self, title):
        pop = tk.Toplevel(self)
        pop.title(title)
        pop.geometry("400x200")
        pop.config(bg="#e5d6cc")
        tk.Label(pop, text=title, bg="#e5d6cc", font=("Arial", 14, "bold")).pack(pady=20)
        tk.Button(pop, text="Close", command=pop.destroy).pack(pady=10)
        pop.grab_set()
        pop.wait_window()


if __name__ == "__main__":
    app = KitchenInventoryApp()
    app.mainloop()
