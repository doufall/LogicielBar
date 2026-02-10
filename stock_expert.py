import customtkinter as ctk
from tkinter import messagebox, simpledialog, filedialog, ttk
import sqlite3
import hashlib
import uuid
import platform
import os
import sys
import csv
import shutil
import calendar
import time
import subprocess
import urllib.request
import webbrowser
import socket  # <--- AJOUT POUR L'INSTANCE UNIQUE
from datetime import datetime, timedelta

# =============================================================================
# CONFIGURATION GLOBALE
# =============================================================================
APP_NAME = "DRINK MANAGER PRO"
APP_VERSION = "v28.0" 
DB_FILE = "enterprise_data.db"
PORT_LOCK = 65432 # Port interne pour vérifier l'instance unique

# INFOS DÉVELOPPEUR
DEV_NAME = "ABDOUL FALL"
DEV_EMAIL = "abdoulfall1293@gmail.com"
DEV_PHONE = "074 00 84 50"

# CONFIGURATION MISE À JOUR
URL_VERSION = "https://raw.githubusercontent.com/doufall/LogicielBar/main/version.txt"

# COULEURS
C_PRIM = "#2980b9"
C_SEC = "#2c3e50"
C_ACC = "#1abc9c"
C_OK = "#27ae60"
C_ERR = "#c0392b"
C_WARN = "#e67e22"
C_INFO = "#8e44ad"
C_TXT = "#ecf0f1"

# =============================================================================
# MODULES EXTERNES
# =============================================================================
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_PLOT = True
except: HAS_PLOT = False

try:
    import win32print, win32ui, win32con
    HAS_WIN32 = True
except: HAS_WIN32 = False

# =============================================================================
# CLASSES UTILITAIRES
# =============================================================================
class PrinterManager:
    CUT_COMMAND = b'\x1d\x56\x42\x00'
    @staticmethod
    def get_printers():
        if not HAS_WIN32: return ["Erreur Module Win32"]
        try: return [p[2] for p in win32print.EnumPrinters(2)]
        except: return ["Aucune imprimante"]
    @classmethod
    def print_ticket(cls, p_name, content):
        if not HAS_WIN32 or not p_name: return False
        try:
            h = win32print.OpenPrinter(p_name)
            try:
                win32print.StartDocPrinter(h, 1, ("Ticket", None, "RAW"))
                win32print.StartPagePrinter(h)
                win32print.WritePrinter(h, (content + "\n\n\n\n").encode("utf-8"))
                win32print.WritePrinter(h, cls.CUT_COMMAND)
                win32print.EndPagePrinter(h)
                win32print.EndDocPrinter(h)
            finally: win32print.ClosePrinter(h)
            return True
        except: return False

class ExportManager:
    @staticmethod
    def to_csv(cursor, table, path):
        try:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            cols = [d[0] for d in cursor.description]
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                w = csv.writer(f, delimiter=';'); w.writerow(cols); w.writerows(rows)
            return True, "Succès"
        except Exception as e: return False, str(e)

class MauricetteCalendar(ctk.CTkToplevel):
    def __init__(self, parent, cb):
        super().__init__(parent)
        self.cb = cb
        self.title("DATE")
        self.geometry("400x450")
        self.attributes("-topmost", True)
        self.grab_set()
        self.focus_force()
        self.cur = datetime.now()
        hf = ctk.CTkFrame(self); hf.pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(hf, text="<", width=40, command=self.prev).pack(side="left")
        self.lbl = ctk.CTkLabel(hf, text="", font=("Arial", 16, "bold")); self.lbl.pack(side="left", expand=True)
        ctk.CTkButton(hf, text=">", width=40, command=self.next).pack(side="right")
        self.gf = ctk.CTkFrame(self); self.gf.pack(fill="both", expand=True, padx=10)
        self.upd()
    def upd(self):
        self.lbl.configure(text=f"{calendar.month_name[self.cur.month]} {self.cur.year}")
        for w in self.gf.winfo_children(): w.destroy()
        cal = calendar.monthcalendar(self.cur.year, self.cur.month)
        for i, d in enumerate(["L","M","M","J","V","S","D"]): ctk.CTkLabel(self.gf, text=d, text_color=C_WARN).grid(row=0, column=i, padx=5)
        for r, w in enumerate(cal):
            for c, d in enumerate(w):
                if d != 0: ctk.CTkButton(self.gf, text=str(d), width=40, fg_color=C_SEC, command=lambda x=d: self.sel(x)).grid(row=r+1, column=c, padx=3, pady=3)
    def prev(self): self.cur = self.cur.replace(day=1) - timedelta(days=1); self.upd()
    def next(self): self.cur = self.cur.replace(day=28) + timedelta(days=4); self.cur = self.cur.replace(day=1); self.upd()
    def sel(self, d): self.cb(f"{self.cur.year}-{self.cur.month:02d}-{d:02d}"); self.destroy()

class SecurityEngine:
    MASTER_PASS = "GnawoulioGnyroundaMauricetteKhamy"
    SALT = "MAURICETTE_V28"
    @staticmethod
    def get_hwid():
        try: return hashlib.sha256(f"{platform.node()}-{uuid.getnode()}".encode()).hexdigest()[:16].upper()
        except: return "HWID-ERROR"
    @classmethod
    def gen_key(cls, hwid):
        return hashlib.sha256(f"{hwid}::{cls.SALT}".encode()).hexdigest().upper()[:16]
    @classmethod
    def check(cls, k):
        k = k.strip()
        if k == cls.MASTER_PASS: return True, "MODE MASTER"
        if k == cls.gen_key(cls.get_hwid()): return True, "MODE CLIENT"
        return False, "INVALID"

class DrinkManagerEnterprise(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} | {APP_VERSION}")
        self.geometry("1600x950")
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.conn = sqlite3.connect(DB_FILE)
        self.cur = self.conn.cursor()
        self.init_db()
        self.load_cfg()
        self.apply_style()
        self.hwid = SecurityEngine.get_hwid()
        self.user = None; self.cart = {}; self.trial = False
        self.check_lic()

    def safe_int(self, v): 
        try: return int(str(v).strip()) if v else 0
        except: return 0

    def clear(self): 
        for w in self.winfo_children(): w.destroy()

    def ask_admin(self):
        p = simpledialog.askstring("SÉCURITÉ", "Mot de passe ADMIN :", show="*")
        if not p: return False
        self.cur.execute("SELECT password FROM staff WHERE role='admin' LIMIT 1")
        r = self.cur.fetchone()
        if r and r[0] == p: return True
        messagebox.showerror("REFUSÉ", "Mot de passe incorrect."); return False

    def init_db(self):
        tables = [
            "CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT UNIQUE, category TEXT, sell_price INT, buy_price INT, stock_qty INT, min_alert INT DEFAULT 5)",
            "CREATE TABLE IF NOT EXISTS categories (name TEXT PRIMARY KEY)",
            "CREATE TABLE IF NOT EXISTS sales_header (id INTEGER PRIMARY KEY, date_time TEXT, total_price INT, user_name TEXT, payment_type TEXT)",
            "CREATE TABLE IF NOT EXISTS sales_lines (id INTEGER PRIMARY KEY, sale_id INT, prod_name TEXT, qty INT, unit_price INT)",
            "CREATE TABLE IF NOT EXISTS stock_movements (id INTEGER PRIMARY KEY, date TEXT, prod_name TEXT, qty INT, type TEXT, reason_or_ref TEXT, user TEXT)",
            "CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, timestamp TEXT, user TEXT, action TEXT, detail TEXT)",
            "CREATE TABLE IF NOT EXISTS staff (username TEXT PRIMARY KEY, password TEXT, role TEXT)",
            "CREATE TABLE IF NOT EXISTS settings (cle TEXT PRIMARY KEY, valeur TEXT)"
        ]
        for q in tables: self.cur.execute(q)
        defaults = [('store_name', 'MA BOUTIQUE'), ('license_key', ''), ('install_date', datetime.now().strftime("%Y-%m-%d")), ('theme', 'System'), ('font_family', 'Arial'), ('font_size', '14'), ('printer', ''), ('stock_alert', '5')]
        self.cur.executemany("INSERT OR IGNORE INTO settings VALUES (?,?)", defaults)
        self.cur.execute("INSERT OR IGNORE INTO staff VALUES ('admin','admin','admin')")
        self.cur.executemany("INSERT OR IGNORE INTO categories VALUES (?)", [('BOISSONS',), ('SNACKS',), ('DIVERS',)])
        self.conn.commit()

    def load_cfg(self):
        self.cur.execute("SELECT cle, valeur FROM settings")
        d = dict(self.cur.fetchall())
        self.store_name = d.get('store_name', 'MA BOUTIQUE')
        self.font_fam = d.get('font_family', 'Arial')
        self.font_sz = int(d.get('font_size', 14))
        self.alert_thr = int(d.get('stock_alert', 5))
        self.sel_print = d.get('printer', '')
        ctk.set_appearance_mode(d.get('theme', 'System'))

    def apply_style(self):
        self.f_title = (self.font_fam, int(self.font_sz * 2.0), "bold")
        self.f_norm = (self.font_fam, int(self.font_sz * 1.2), "bold")
        self.f_small = (self.font_fam, int(self.font_sz), "bold")

    def check_lic(self):
        self.cur.execute("SELECT valeur FROM settings WHERE cle='license_key'")
        k = self.cur.fetchone()
        if k and k[0] and SecurityEngine.check(k[0])[0]: self.login(); return
        self.cur.execute("SELECT valeur FROM settings WHERE cle='install_date'")
        d = self.cur.fetchone()
        if d:
            try:
                if (datetime.now() - datetime.strptime(d[0], "%Y-%m-%d")).days <= 7: self.trial = True; self.login()
                else: self.lock_screen()
            except: self.lock_screen()
        else: self.lock_screen()

    def lock_screen(self):
        self.clear()
        f = ctk.CTkFrame(self, width=600, height=500, border_color=C_ERR, border_width=4); f.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(f, text="LICENCE REQUISE", font=self.f_title, text_color=C_ERR).pack(pady=40)
        ctk.CTkLabel(f, text="VOTRE ID (HWID) :", font=self.f_small).pack()
        e = ctk.CTkEntry(f, width=400, justify="center"); e.insert(0, self.hwid); e.configure(state="readonly"); e.pack(pady=10)
        self.ek = ctk.CTkEntry(f, width=400, placeholder_text="ENTREZ VOTRE CLÉ ICI", justify="center"); self.ek.pack(pady=20)
        ctk.CTkButton(f, text="ACTIVER", command=self.do_act).pack()
        ctk.CTkLabel(f, text=f"Support Technique : {DEV_PHONE}", text_color="gray").pack(pady=20)

    def do_act(self):
        k = self.ek.get().strip(); v, m = SecurityEngine.check(k)
        if v:
            self.cur.execute("INSERT OR REPLACE INTO settings (cle,valeur) VALUES ('license_key',?)", (k,))
            self.conn.commit(); messagebox.showinfo("OK", f"Activé: {m}"); self.login()
        else: messagebox.showerror("NON", "Invalide")

    def login(self):
        self.clear()
        f = ctk.CTkFrame(self, width=400, height=550); f.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(f, text=self.store_name, font=self.f_title).pack(pady=30)
        if self.trial: ctk.CTkLabel(f, text="MODE ESSAI", text_color=C_WARN).pack()
        self.eu = ctk.CTkEntry(f, placeholder_text="Utilisateur"); self.eu.pack(pady=10)
        self.ep = ctk.CTkEntry(f, placeholder_text="Pass", show="*"); self.ep.pack(pady=10)
        ctk.CTkButton(f, text="GO", command=self.do_log).pack(pady=20)
        ctk.CTkLabel(f, text=f"Problème d'accès ?\nContactez le {DEV_PHONE}", text_color=C_INFO, font=("Arial", 10)).pack(side="bottom", pady=20)

    def do_log(self):
        u, p = self.eu.get().lower(), self.ep.get()
        self.cur.execute("SELECT role FROM staff WHERE username=? AND password=?", (u, p)); r = self.cur.fetchone()
        if r: self.user = {"name": u, "role": r[0]}; self.dash()
        else: messagebox.showerror("Err", "Non")

    def dash(self):
        self.clear()
        tabs = ctk.CTkTabview(self); tabs.pack(fill="both", expand=True)
        self.t_pos = tabs.add("CAISSE"); self.t_inv = tabs.add("STOCK")
        if self.user["role"] == "admin":
            self.t_stf = tabs.add("EQUIPE"); self.t_stat = tabs.add("RAPPORTS")
            self.t_cfg = tabs.add("CONFIG")
            self.init_staff(); self.init_stats(); self.init_cfg()
        self.init_pos(); self.init_stock()

    def init_pos(self):
        self.t_pos.grid_columnconfigure(0, weight=3); self.t_pos.grid_columnconfigure(1, weight=1); self.t_pos.grid_rowconfigure(0, weight=1)
        lf = ctk.CTkFrame(self.t_pos); lf.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        sf = ctk.CTkFrame(lf); sf.pack(fill="x")
        self.eps = ctk.CTkEntry(sf, placeholder_text="Chercher..."); self.eps.pack(side="left", fill="x", expand=True)
        self.eps.bind("<KeyRelease>", lambda e: self.ref_pos())
        self.ecf = ctk.CTkComboBox(sf, values=["TOUT"] + [r[0] for r in self.cur.execute("SELECT name FROM categories")], command=lambda x: self.ref_pos()); self.ecf.pack(side="left")
        self.gp = ctk.CTkScrollableFrame(lf, fg_color="transparent"); self.gp.pack(fill="both", expand=True)
        rf = ctk.CTkFrame(self.t_pos, fg_color=C_SEC); rf.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(rf, text="PANIER", font=self.f_norm).pack()
        self.cv = ctk.CTkScrollableFrame(rf); self.cv.pack(fill="both", expand=True)
        self.lt = ctk.CTkLabel(rf, text="TOTAL: 0", font=self.f_title, text_color=C_OK); self.lt.pack(pady=10)
        ctk.CTkButton(rf, text="ENCAISSER", fg_color=C_OK, height=50, command=self.pay).pack(fill="x", padx=10)
        ctk.CTkButton(rf, text="VIDER", fg_color=C_ERR, command=lambda: (self.cart.clear(), self.upd_cart())).pack(fill="x", padx=10, pady=5)
        self.ref_pos()

    def ref_pos(self):
        for w in self.gp.winfo_children(): w.destroy()
        q = "SELECT name, sell_price, stock_qty FROM products WHERE name LIKE ?"
        p = [f"%{self.eps.get()}%"]
        if self.ecf.get() != "TOUT": q += " AND category=?"; p.append(self.ecf.get())
        for n, pr, qt in self.cur.execute(q, p):
            c = C_PRIM if qt > self.alert_thr else (C_WARN if qt > 0 else "gray")
            ctk.CTkButton(self.gp, text=f"{n}\n{pr}F\n({qt})", fg_color=c, width=140, height=100, command=lambda x=n, y=pr, z=qt: self.add_c(x, y, z)).pack(side="left", padx=5, pady=5)

    def add_c(self, n, p, mq):
        if mq <= 0: return
        cur = self.cart.get(n, {'q': 0, 'p': p})
        if cur['q'] < mq: cur['q'] += 1; self.cart[n] = cur; self.upd_cart()

    def upd_cart(self):
        for w in self.cv.winfo_children(): w.destroy()
        t = 0
        for n, d in self.cart.items():
            s = d['q'] * d['p']; t += s
            r = ctk.CTkFrame(self.cv); r.pack(fill="x", pady=2)
            ctk.CTkLabel(r, text=f"{n} x{d['q']}", font=self.f_small).pack(side="left", padx=5)
            ctk.CTkButton(r, text="X", width=30, fg_color=C_ERR, command=lambda x=n: (self.cart.pop(x), self.upd_cart())).pack(side="right")
            ctk.CTkLabel(r, text=f"{s}", font=self.f_small).pack(side="right", padx=5)
        self.lt.configure(text=f"TOTAL: {t} FCFA")

    def pay(self):
        if not self.cart: return
        tot = sum(d['q'] * d['p'] for d in self.cart.values())
        w = ctk.CTkToplevel(self); w.geometry("400x550"); w.title("ENCAISSEMENT")
        w.grab_set(); w.focus_force()
        ctk.CTkLabel(w, text="A PAYER", font=self.f_norm).pack(pady=10)
        ctk.CTkLabel(w, text=f"{tot} FCFA", font=self.f_title, text_color=C_OK).pack(pady=10)
        ec = ctk.CTkEntry(w, justify="center", font=self.f_title); ec.pack(pady=10); ec.focus()
        def val():
            r = self.safe_int(ec.get())
            if r < tot: messagebox.showerror("ERREUR", "Montant insuffisant"); return
            dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cur.execute("INSERT INTO sales_header (date_time, total_price, user_name) VALUES (?,?,?)", (dt, tot, self.user['name']))
            sid = self.cur.lastrowid
            body = f"Date: {dt}\nTicket #{sid}\nCaissier: {self.user['name'].upper()}\n"
            body += "-"*42 + "\n" + f"{'PRODUIT':<20} {'QTE':<5} {'TOTAL':>15}\n" + "-"*42 + "\n"
            for n, d in self.cart.items():
                self.cur.execute("INSERT INTO sales_lines (sale_id, prod_name, qty, unit_price) VALUES (?,?,?,?)", (sid, n, d['q'], d['p']))
                self.cur.execute("UPDATE products SET stock_qty=stock_qty-? WHERE name=?", (d['q'], n))
                self.cur.execute("INSERT INTO stock_movements (date,prod_name,qty,type,user) VALUES (?,?,?,?,?)", (dt, n, d['q'], "VENTE", self.user['name']))
                line_total = d['q'] * d['p']
                body += f"{n:<20} x{d['q']:<4} {line_total:>15}\n"
            self.conn.commit()
            body += "="*42 + "\n" + f"TOTAL : {tot} FCFA\n".center(42) + f"ESPECES : {r} FCFA\nRENDU : {r-tot} FCFA\n" + "="*42
            if self.sel_print:
                PrinterManager.print_ticket(self.sel_print, body)
            messagebox.showinfo("OK", f"Rendre: {r-tot}")
            self.cart = {}; self.upd_cart(); self.ref_pos(); w.destroy()
        ctk.CTkButton(w, text="VALIDER", height=50, fg_color=C_OK, command=val).pack(pady=20)

    def init_stock(self):
        tf = ctk.CTkFrame(self.t_inv); tf.pack(fill="x", padx=5, pady=5)
        c1 = ctk.CTkFrame(tf); c1.pack(side="left", expand=True, fill="both", padx=2)
        ctk.CTkLabel(c1, text="GESTION PRODUITS").pack()
        en = ctk.CTkEntry(c1, placeholder_text="Nom"); en.pack(pady=2)
        ec = ctk.CTkComboBox(c1, values=["CAT..."] + [r[0] for r in self.cur.execute("SELECT name FROM categories")]); ec.pack(pady=2)
        epa = ctk.CTkEntry(c1, placeholder_text="P.Achat (Optionnel)"); epa.pack(pady=2)
        epv = ctk.CTkEntry(c1, placeholder_text="P.Vente"); epv.pack(pady=2)
        def create():
            if not self.ask_admin(): return
            nom = en.get().strip().upper()
            if not nom: messagebox.showwarning("ERREUR", "Nom obligatoire"); return
            pa, pv = self.safe_int(epa.get()), self.safe_int(epv.get())
            try: 
                self.cur.execute("INSERT INTO products (name, category, buy_price, sell_price, stock_qty) VALUES (?,?,?,?,0)", (nom, ec.get(), pa, pv))
                self.conn.commit(); self.ref_stock()
                en.delete(0, 'end'); epa.delete(0, 'end'); epv.delete(0, 'end'); ec.set("CAT...")
            except Exception as e: messagebox.showerror("Err", f"Erreur: {e}")
        ctk.CTkButton(c1, text="CRÉER", fg_color=C_INFO, command=create).pack(pady=2)
        
        c2 = ctk.CTkFrame(tf, border_color=C_OK, border_width=2); c2.pack(side="left", expand=True, fill="both", padx=2)
        ctk.CTkLabel(c2, text="ENTRÉE STOCK", text_color=C_OK).pack()
        self.cb_entry = ctk.CTkComboBox(c2, values=[]); self.cb_entry.pack(pady=5)
        eq = ctk.CTkEntry(c2, placeholder_text="Qté"); eq.pack(pady=5)
        def add_stk():
            if not self.ask_admin(): return
            q, p = self.safe_int(eq.get()), self.cb_entry.get()
            self.cur.execute("UPDATE products SET stock_qty=stock_qty+? WHERE name=?", (q, p))
            self.cur.execute("INSERT INTO stock_movements (date,prod_name,qty,type,user) VALUES (?,?,?,?,?)", (datetime.now(), p, q, "ENTREE", self.user['name']))
            self.conn.commit(); self.ref_stock(); eq.delete(0, 'end'); messagebox.showinfo("OK", "Ajouté")
        ctk.CTkButton(c2, text="VALIDER", fg_color=C_OK, command=add_stk).pack(pady=20)
        
        self.hist = ctk.CTkTextbox(self.t_inv, height=150); self.hist.pack(fill="x", padx=10, pady=5)
        self.ref_stock()

    def ref_stock(self):
        prods = [r[0] for r in self.cur.execute("SELECT name FROM products")]
        self.cb_entry.configure(values=prods)
        self.hist.delete("1.0", "end")
        self.cur.execute("SELECT * FROM stock_movements ORDER BY id DESC LIMIT 50")
        for r in self.cur.fetchall(): self.hist.insert("end", f"{r[1]} | {r[4]} | {r[2]} | Qté: {r[3]} | {r[5]} | {r[6]}\n")

    def init_staff(self):
        self.stf_scroll = ctk.CTkScrollableFrame(self.t_stf)
        self.stf_scroll.pack(fill="both", expand=True, padx=20, pady=10)
        self.ref_staff()

    def ref_staff(self):
        for w in self.stf_scroll.winfo_children(): w.destroy()
        self.cur.execute("SELECT username, role FROM staff")
        for u, r in self.cur.fetchall():
            row = ctk.CTkFrame(self.stf_scroll); row.pack(fill="x", pady=5)
            ctk.CTkLabel(row, text=f"{u.upper()} ({r})", width=200, anchor="w").pack(side="left", padx=20)

    def init_stats(self):
        f = ctk.CTkFrame(self.t_stat); f.pack(fill="both", expand=True, padx=10, pady=10)
        rf = ctk.CTkFrame(f); rf.pack(fill="x", pady=10)
        d1 = ctk.CTkEntry(rf, width=100); d1.pack(side="left", padx=2)
        ctk.CTkButton(rf, text="📅", width=30, command=lambda: MauricetteCalendar(self, lambda d: (d1.delete(0, 'end'), d1.insert(0, d)))).pack(side="left")
        d2 = ctk.CTkEntry(rf, width=100); d2.pack(side="left", padx=2)
        ctk.CTkButton(rf, text="📅", width=30, command=lambda: MauricetteCalendar(self, lambda d: (d2.delete(0, 'end'), d2.insert(0, d)))).pack(side="left")
        
        def rep():
            if not d1.get() or not d2.get(): return
            query = """SELECT prod_name, SUM(qty), SUM(qty*unit_price) 
                       FROM sales_lines 
                       JOIN sales_header ON sales_lines.sale_id = sales_header.id 
                       WHERE date_time BETWEEN ? AND ? 
                       GROUP BY prod_name"""
            self.cur.execute(query, (d1.get()+" 00:00:00", d2.get()+" 23:59:59"))
            rows = self.cur.fetchall()
            t = f"RAPPORT PERIODE {d1.get()} AU {d2.get()}\n" + "="*42 + "\n"
            for r in rows: t += f"{r[0]:<20} {r[1]:<5} {r[2]:>15}\n"
            messagebox.showinfo("RAPPORT", t)
        ctk.CTkButton(rf, text="RECAP PÉRIODE", command=rep).pack(side="left", padx=10)

    def init_cfg(self):
        tc = self.t_cfg
        ctk.CTkLabel(tc, text="PARAMÈTRES", font=self.f_title).pack(pady=20)
        ctk.CTkButton(tc, text="SAUVEGARDER BDD", command=self.db_backup).pack(pady=10)

    def db_backup(self):
        p = filedialog.asksaveasfilename(defaultextension=".db")
        if p: shutil.copy2(DB_FILE, p); messagebox.showinfo("OK", "Sauvegarde réussie")

    def close(self):
        if messagebox.askyesno("QUITTER", "Fermer l'application ?"): self.conn.close(); self.destroy()

if __name__ == "__main__":
    if platform.system() == "Windows":
        try: from ctypes import windll; windll.shcore.SetProcessDpiAwareness(1)
        except: pass
    app = DrinkManagerEnterprise()
    app.mainloop()
