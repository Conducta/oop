c.execute("UPDATE borrow SET returned_qty = ?, date_return = ? WHERE id = ?", (new_returned, datetime.date.today().isoformat(), db_id))
                log['status'] = "Returned"