import customtkinter as ctk
from tkinter import messagebox, simpledialog, filedialog, ttk
import sqlite3
import hashlib
import uuid
import platform
import os
import csv
import shutil
import calendar
import time
import subprocess
import urllib.request
import webbrowser
from datetime import datetime, timedelta

# =============================================================================
# CONFIGURATION GLOBALE
# =============================================================================
APP_NAME = "DRINK MANAGER PRO"
APP_VERSION = "v25.0" # Version actuelle du logiciel
DB_FILE = "enterprise_data.db"

# --- INFOS DÉVELOPPEUR ---
DEV_NAME = "ABDOUL FALL"
DEV_EMAIL = "abdoulfall1293@gmail.com"
DEV_PHONE = "074 00 84 50"

# --- CONFIGURATION MISE A JOUR (GITHUB) ---
# Ces liens pointent vers VOTRE espace GitHub
URL_VERSION = "https://raw.githubusercontent.com/AbdoulFall/LogicielBar/main/version.txt"
URL_CODE = "https://raw.githubusercontent.com/AbdoulFall/LogicielBar/main/main.py"

# --- COULEURS ---
C_PRIM = "#2980b9"   # Bleu
C_SEC = "#2c3e50"    # Sombre
C_ACC = "#1abc9c"    # Turquoise
C_OK = "#27ae60"     # Vert
C_ERR = "#c0392b"    # Rouge
C_WARN = "#e67e22"   # Orange
C_INFO = "#8e44ad"   # Violet
C_TXT = "#ecf0f1"    # Texte

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
class UpdateManager:
    """Gère la mise à jour via GitHub."""
    @staticmethod
    def check_update():
        try:
            # On lit le fichier version.txt sur GitHub
            with urllib.request.urlopen(URL_VERSION, timeout=3) as response:
                online_ver = response.read().decode('utf-8').strip()
            
            # Si la version en ligne est différente de la version locale
            if online_ver != APP_VERSION:
                msg = f"✨ MISE À JOUR DISPONIBLE !\n\nVersion actuelle : {APP_VERSION}\nNouvelle version : {online_ver}\n\nTélécharger maintenant ?"
                if messagebox.askyesno("UPDATE", msg):
                    UpdateManager.download(online_ver)
        except: 
            pass # Si pas d'internet, on ne fait rien silencieusement

    @staticmethod
    def download(ver):
        try:
            new_file = f"DrinkManager_{ver}.py"
            urllib.request.urlretrieve(URL_CODE, new_file)
            messagebox.showinfo("SUCCÈS", f"Mise à jour téléchargée !\n\nNom du fichier : {new_file}\n\nFermez ce programme et lancez le nouveau fichier.")
        except Exception as e:
            messagebox.showerror("ERREUR", f"Echec téléchargement : {e}")

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
        super().__init__(parent); self.cb = cb; self.title("DATE"); self.geometry("400x450"); self.attributes("-topmost", True)
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
    SALT = "MAURICETTE_V25"
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

# =============================================================================
# APPLICATION PRINCIPALE
# =============================================================================
class DrinkManagerEnterprise(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} | {APP_VERSION}")
        self.geometry("1600x950")
        self.protocol("WM_DELETE_WINDOW", self.close)
        
        # Base de données
        self.conn = sqlite3.connect(DB_FILE)
        self.cur = self.conn.cursor()
        self.init_db()
        self.load_cfg()
        self.apply_style()
        
        # Variables Session
        self.hwid = SecurityEngine.get_hwid()
        self.user = None; self.cart = {}; self.trial = False
        
        # Vérification MAJ au démarrage
        self.after(2000, UpdateManager.check_update) # Vérifie après 2 sec
        
        self.check_lic()

    def safe_int(self, v): 
        try: return int(str(v).strip()) if v else 0
        except: return 0
    def clear(self): 
        for w in self.winfo_children(): w.destroy()
    def ask_admin(self):
        p = simpledialog.askstring("SÉCURITÉ", "Mot de passe ADMIN :", show="*")
        if not p: return False
        self.cur.execute("SELECT password FROM staff WHERE username='admin'")
        r = self.cur.fetchone()
        if r and r[0] == p: return True
        messagebox.showerror("REFUSÉ", "Mot de passe incorrect."); return False

    # --- BDD & CONFIG ---
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

    # --- LICENSE ---
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

    # --- LOGIN ---
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

    # --- DASHBOARD ---
    def dash(self):
        self.clear()
        tabs = ctk.CTkTabview(self); tabs.pack(fill="both", expand=True)
        self.t_pos = tabs.add("CAISSE"); self.t_inv = tabs.add("STOCK")
        if self.user["role"] == "admin":
            self.t_stf = tabs.add("EQUIPE"); self.t_stat = tabs.add("RAPPORTS")
            self.t_cfg = tabs.add("CONFIG")
            self.init_staff(); self.init_stats(); self.init_cfg()
        self.init_pos(); self.init_stock()

    # --- POS ---
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
        self.cat = "TOUT"; self.ref_pos()

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
        
        ctk.CTkLabel(w, text="A PAYER", font=self.f_norm).pack(pady=10)
        ctk.CTkLabel(w, text=f"{tot} FCFA", font=self.f_title, text_color=C_OK).pack(pady=10)
        ec = ctk.CTkEntry(w, justify="center", font=self.f_title); ec.pack(pady=10); ec.focus()
        
        def val():
            r = self.safe_int(ec.get())
            if r < tot: messagebox.showerror("ERREUR", "Montant insuffisant"); return
            dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cur.execute("INSERT INTO sales_header (date_time, total_price, user_name) VALUES (?,?,?)", (dt, tot, self.user['name']))
            sid = self.cur.lastrowid
            
            # --- STRUCTURE TICKET (Identique) ---
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
            
            tick_c = f"{self.store_name.center(42)}\n" + "TICKET CLIENT".center(42) + "\n" + "="*42 + "\n" + body
            tick_b = f"{self.store_name.center(42)}\n" + "TICKET CAISSE".center(42) + "\n" + "="*42 + "\n" + body

            if self.sel_print:
                PrinterManager.print_ticket(self.sel_print, tick_c)
                time.sleep(1.5)
                PrinterManager.print_ticket(self.sel_print, tick_b)

            messagebox.showinfo("OK", f"Rendre: {r-tot}")
            self.cart = {}; self.upd_cart(); self.ref_pos(); w.destroy()
            
        ctk.CTkButton(w, text="VALIDER", height=50, fg_color=C_OK, command=val).pack(pady=20)

    # --- STOCK ---
    def init_stock(self):
        tf = ctk.CTkFrame(self.t_inv); tf.pack(fill="x", padx=5, pady=5)
        # Création
        c1 = ctk.CTkFrame(tf); c1.pack(side="left", expand=True, fill="both", padx=2)
        ctk.CTkLabel(c1, text="GESTION PRODUITS").pack()
        en = ctk.CTkEntry(c1, placeholder_text="Nom"); en.pack(pady=2)
        ec = ctk.CTkComboBox(c1, values=["CAT..."] + [r[0] for r in self.cur.execute("SELECT name FROM categories")]); ec.pack(pady=2)
        epa = ctk.CTkEntry(c1, placeholder_text="P.Achat"); epa.pack(pady=2)
        epv = ctk.CTkEntry(c1, placeholder_text="P.Vente"); epv.pack(pady=2)
        def create():
            if not self.ask_admin(): return
            try: 
                self.cur.execute("INSERT INTO products (name, category, buy_price, sell_price, stock_qty) VALUES (?,?,?,?,0)", (en.get().upper(), ec.get(), int(epa.get()), int(epv.get())))
                self.conn.commit(); self.ref_stock(); messagebox.showinfo("OK", "Fait")
            except: messagebox.showerror("Err", "Erreur")
        ctk.CTkButton(c1, text="CRÉER", fg_color=C_INFO, command=create).pack(pady=2)
        
        def mod_win():
            if not self.ask_admin(): return
            w = ctk.CTkToplevel(self); w.geometry("300x400")
            c = ctk.CTkComboBox(w, values=self.get_prods()); c.pack(pady=10)
            e1 = ctk.CTkEntry(w, placeholder_text="New Nom"); e1.pack(pady=5)
            e2 = ctk.CTkEntry(w, placeholder_text="New PV"); e2.pack(pady=5)
            def save(): self.cur.execute("UPDATE products SET name=?, sell_price=? WHERE name=?", (e1.get().upper(), int(e2.get()), c.get())); self.conn.commit(); self.ref_stock(); w.destroy()
            ctk.CTkButton(w, text="SAUVEGARDER", command=save).pack(pady=10)
            def dele():
                if messagebox.askyesno("SUR?", "Supprimer ?"): self.cur.execute("DELETE FROM products WHERE name=?", (c.get(),)); self.conn.commit(); self.ref_stock(); w.destroy()
            ctk.CTkButton(w, text="SUPPRIMER", fg_color=C_ERR, command=dele).pack()
        ctk.CTkButton(c1, text="MODIFIER", command=mod_win).pack(pady=2)
        ctk.CTkButton(c1, text="+ CATÉGORIE", width=80, command=lambda: (self.cur.execute("INSERT OR IGNORE INTO categories VALUES (?)", (simpledialog.askstring("C", "Nom"),)), self.conn.commit())).pack()

        # Entrée
        c2 = ctk.CTkFrame(tf, border_color=C_OK, border_width=2); c2.pack(side="left", expand=True, fill="both", padx=2)
        ctk.CTkLabel(c2, text="ENTRÉE STOCK", text_color=C_OK).pack()
        cb = ctk.CTkComboBox(c2, values=[]); cb.pack(pady=5)
        eq = ctk.CTkEntry(c2, placeholder_text="Qté"); eq.pack(pady=5)
        def add_stk():
            if not self.ask_admin(): return
            q = self.safe_int(eq.get()); p = cb.get()
            self.cur.execute("UPDATE products SET stock_qty=stock_qty+? WHERE name=?", (q, p))
            self.cur.execute("INSERT INTO stock_movements (date,prod_name,qty,type,user) VALUES (?,?,?,?,?)", (datetime.now(), p, q, "ENTREE", self.user['name']))
            self.conn.commit(); self.ref_stock(); messagebox.showinfo("OK", "Ajouté")
        ctk.CTkButton(c2, text="VALIDER", fg_color=C_OK, command=add_stk).pack(pady=20)

        # Perte
        c3 = ctk.CTkFrame(tf, border_color=C_ERR, border_width=2); c3.pack(side="left", expand=True, fill="both", padx=2)
        ctk.CTkLabel(c3, text="PERTE", text_color=C_ERR).pack()
        cp = ctk.CTkComboBox(c3, values=[]); cp.pack(pady=5)
        eqp = ctk.CTkEntry(c3, placeholder_text="Qté"); eqp.pack(pady=5)
        erp = ctk.CTkEntry(c3, placeholder_text="Motif"); erp.pack(pady=5)
        def loss():
            if not self.ask_admin(): return
            q = self.safe_int(eqp.get()); p = cp.get()
            self.cur.execute("UPDATE products SET stock_qty=stock_qty-? WHERE name=?", (q, p))
            self.cur.execute("INSERT INTO stock_movements (date,prod_name,qty,type,reason_or_ref,user) VALUES (?,?,?,?,?,?)", (datetime.now(), p, q, "PERTE", erp.get(), self.user['name']))
            self.conn.commit(); self.ref_stock(); messagebox.showinfo("OK", "Perte notée")
        ctk.CTkButton(c3, text="VALIDER", fg_color=C_ERR, command=loss).pack(pady=10)

        # Offre
        c4 = ctk.CTkFrame(tf, border_color=C_INFO, border_width=2); c4.pack(side="left", expand=True, fill="both", padx=2)
        ctk.CTkLabel(c4, text="OFFRE/CADEAU", text_color=C_INFO).pack()
        co = ctk.CTkComboBox(c4, values=[]); co.pack(pady=5)
        eqo = ctk.CTkEntry(c4, placeholder_text="Qté"); eqo.pack(pady=5)
        ero = ctk.CTkEntry(c4, placeholder_text="Bénéficiaire"); ero.pack(pady=5)
        def offer():
            if not self.ask_admin(): return
            q = self.safe_int(eqo.get()); p = co.get()
            self.cur.execute("UPDATE products SET stock_qty=stock_qty-? WHERE name=?", (q, p))
            self.cur.execute("INSERT INTO stock_movements (date,prod_name,qty,type,reason_or_ref,user) VALUES (?,?,?,?,?,?)", (datetime.now(), p, q, "OFFERT", ero.get(), self.user['name']))
            self.conn.commit(); self.ref_stock(); messagebox.showinfo("OK", "Offre notée")
        ctk.CTkButton(c4, text="VALIDER", fg_color=C_INFO, command=offer).pack(pady=10)

        self.cbs = [cb, cp, co]; self.hist = ctk.CTkTextbox(self.t_inv, height=150); self.hist.pack(fill="x", padx=10, pady=5)
        bb = ctk.CTkFrame(self.t_inv); bb.pack(pady=5)
        ctk.CTkButton(bb, text="ACTUALISER", command=self.ref_stock).pack(side="left", padx=10)
        ctk.CTkButton(bb, text="EXPORT STOCK CSV", fg_color=C_PRIM, command=self.stock_export_csv).pack(side="left", padx=10)
        ctk.CTkButton(bb, text="EXPORT VENTES CSV", fg_color=C_INFO, command=self.sales_export_csv).pack(side="left", padx=10)
        self.ref_stock()

    def get_prods(self): return [r[0] for r in self.cur.execute("SELECT name FROM products")]
    def ref_stock(self):
        l = self.get_prods(); 
        for c in self.cbs: c.configure(values=l)
        self.hist.delete("1.0", "end")
        self.cur.execute("SELECT * FROM stock_movements ORDER BY id DESC LIMIT 50")
        for r in self.cur.fetchall(): self.hist.insert("end", f"{r[1]} | {r[4]} | {r[2]} | Qté: {r[3]} | {r[5]} | {r[6]}\n")
        self.ref_pos()
    def stock_export_csv(self):
        p = filedialog.asksaveasfilename(defaultextension=".csv"); 
        if p: ExportManager.to_csv(self.cur, "products", p); messagebox.showinfo("OK", "Exporté")
    def sales_export_csv(self):
        p = filedialog.asksaveasfilename(defaultextension=".csv"); 
        if p: ExportManager.to_csv(self.cur, "sales_header", p); messagebox.showinfo("OK", "Exporté")

    # --- ADMINISTRATION (STAFF FIX) ---
    def init_staff(self):
        tf = ctk.CTkFrame(self.t_stf, height=60); tf.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(tf, text="GESTION ÉQUIPE", font=self.f_title).pack(side="left", padx=20)
        
        # Ajout
        fa = ctk.CTkFrame(self.t_stf); fa.pack(fill="x", padx=20)
        eu = ctk.CTkEntry(fa, placeholder_text="Identifiant"); eu.pack(side="left", padx=5)
        ep = ctk.CTkEntry(fa, placeholder_text="Mot de passe"); ep.pack(side="left", padx=5)
        er = ctk.CTkComboBox(fa, values=["caissier", "admin"]); er.pack(side="left", padx=5)
        
        def add():
            if self.ask_admin(): 
                try: 
                    self.cur.execute("INSERT INTO staff VALUES (?,?,?)", (eu.get().lower(), ep.get(), er.get())); 
                    self.conn.commit(); self.ref_staff(); messagebox.showinfo("OK", "Ajouté")
                except: messagebox.showerror("ERR", "Existe déjà")
        ctk.CTkButton(fa, text="AJOUTER", command=add).pack(side="left", padx=5)
        
        # Config Admin Principal
        def mod_admin():
            if not self.ask_admin(): return
            w = ctk.CTkToplevel(self); w.geometry("400x400"); w.title("CONFIG ADMIN SUPRÊME")
            ctk.CTkLabel(w, text="MODIFIER ADMIN PRINCIPAL", font=("Arial", 14, "bold"), text_color="red").pack(pady=20)
            ctk.CTkLabel(w, text="Nouveau Nom (Vide = inchangé)").pack(); nu = ctk.CTkEntry(w); nu.pack(pady=5)
            ctk.CTkLabel(w, text="Nouveau MDP (Vide = inchangé)").pack(); np = ctk.CTkEntry(w, show="*"); np.pack(pady=5)
            def save():
                if nu.get() and np.get(): self.cur.execute("UPDATE staff SET username=?, password=? WHERE role='admin'", (nu.get(), np.get())); self.conn.commit(); messagebox.showinfo("OK", "Modifié. Redémarrage requis."); self.close()
            ctk.CTkButton(w, text="SAUVEGARDER", fg_color="red", command=save).pack(pady=20)
        ctk.CTkButton(tf, text="CONFIG ADMIN", fg_color="red", command=mod_admin).pack(side="right", padx=10)

        # LISTE AVEC BOUTONS
        self.stf_scroll = ctk.CTkScrollableFrame(self.t_stf)
        self.stf_scroll.pack(fill="both", expand=True, padx=20, pady=10)
        self.ref_staff()

    def ref_staff(self):
        for w in self.stf_scroll.winfo_children(): w.destroy()
        self.cur.execute("SELECT username, role FROM staff")
        for u, r in self.cur.fetchall():
            row = ctk.CTkFrame(self.stf_scroll)
            row.pack(fill="x", pady=5)
            ctk.CTkLabel(row, text=f"{u.upper()} ({r})", width=200, anchor="w", font=("Arial", 12, "bold")).pack(side="left", padx=20)
            def edit_user(user=u):
                if not self.ask_admin(): return
                w = ctk.CTkToplevel(self); w.title("MODIF USER")
                ctk.CTkLabel(w, text=f"MODIFIER {user.upper()}").pack(pady=10)
                np = ctk.CTkEntry(w, placeholder_text="Nouveau MDP"); np.pack(pady=5)
                nr = ctk.CTkComboBox(w, values=["caissier", "admin"]); nr.pack(pady=5)
                def save_edit():
                    if np.get(): self.cur.execute("UPDATE staff SET password=?, role=? WHERE username=?", (np.get(), nr.get(), user))
                    else: self.cur.execute("UPDATE staff SET role=? WHERE username=?", (nr.get(), user))
                    self.conn.commit(); self.ref_staff(); w.destroy()
                ctk.CTkButton(w, text="SAUVEGARDER", command=save_edit).pack(pady=10)
            ctk.CTkButton(row, text="✏️", width=40, command=edit_user).pack(side="right", padx=5)
            if u != "admin":
                ctk.CTkButton(row, text="🗑️", width=40, fg_color=C_ERR, command=lambda x=u: self.del_staff(x)).pack(side="right", padx=5)

    def del_staff(self, u):
        if not self.ask_admin(): return
        if messagebox.askyesno("SURE?", f"Supprimer {u}?"):
            self.cur.execute("DELETE FROM staff WHERE username=?", (u,)); self.conn.commit(); self.ref_staff()

    # --- RAPPORTS DETAILLÉS ---
    def init_stats(self):
        f = ctk.CTkFrame(self.t_stat); f.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ZONE 1: REQUÊTES RAPIDES
        qf = ctk.CTkFrame(f); qf.pack(fill="x", pady=5)
        ctk.CTkLabel(qf, text="⚡ TABLEAU DE BORD DÉCISIONNEL", font=self.f_small, text_color=C_INFO).pack(pady=5)
        
        row1 = ctk.CTkFrame(qf, fg_color="transparent"); row1.pack(fill="x", pady=2)
        def low_stk():
            self.cur.execute("SELECT name, stock_qty FROM products WHERE stock_qty <= ?", (self.alert_thr,))
            rows = self.cur.fetchall()
            msg = "✅ STOCK SAIN" if not rows else "⚠️ URGENT COMMANDER :\n\n" + "\n".join([f"- {r[0]} ({r[1]})" for r in rows])
            messagebox.showinfo("ALERTE STOCK", msg)
        ctk.CTkButton(row1, text="📉 STOCK BAS", fg_color=C_ERR, command=low_stk).pack(side="left", fill="x", expand=True, padx=2)
        
        def ca_month():
            m = datetime.now().strftime("%Y-%m")
            self.cur.execute("SELECT SUM(total_price) FROM sales_header WHERE date_time LIKE ?", (f"{m}%",))
            r = self.cur.fetchone()
            messagebox.showinfo("CA MOIS", f"📅 CA {m} :\n\n💰 {r[0] or 0} FCFA")
        ctk.CTkButton(row1, text="💰 CA MOIS", fg_color=C_OK, command=ca_month).pack(side="left", fill="x", expand=True, padx=2)
        
        def best_sell():
            try:
                self.cur.execute("SELECT prod_name, SUM(qty) as s FROM sales_lines GROUP BY prod_name ORDER BY s DESC LIMIT 1")
                r = self.cur.fetchone()
                msg = f"🏆 CHAMPION :\n\n{r[0]}\n({r[1]} ventes)" if r else "Aucune vente"
                messagebox.showinfo("TOP VENTE", msg)
            except: pass
        ctk.CTkButton(row1, text="🏆 TOP PRODUIT", fg_color=C_WARN, command=best_sell).pack(side="left", fill="x", expand=True, padx=2)

        row2 = ctk.CTkFrame(qf, fg_color="transparent"); row2.pack(fill="x", pady=2)
        def calc_profit():
            self.cur.execute("SELECT SUM((p.sell_price - p.buy_price) * sl.qty) FROM sales_lines sl JOIN products p ON sl.prod_name = p.name")
            res = self.cur.fetchone()[0] or 0
            messagebox.showinfo("RENTABILITÉ", f"💎 BÉNÉFICE ESTIMÉ :\n\n+{res} FCFA")
        ctk.CTkButton(row2, text="💎 BÉNÉFICE", fg_color="#8e44ad", command=calc_profit).pack(side="left", fill="x", expand=True, padx=2)
        
        def stock_value():
            self.cur.execute("SELECT SUM(buy_price * stock_qty) FROM products")
            res = self.cur.fetchone()[0] or 0
            messagebox.showinfo("TRESORERIE", f"🏦 ARGENT EN STOCK :\n\n{res} FCFA")
        ctk.CTkButton(row2, text="🏦 VALEUR STOCK", fg_color="#2980b9", command=stock_value).pack(side="left", fill="x", expand=True, padx=2)
        
        def show_losses():
            self.cur.execute("SELECT type, COUNT(*), SUM(qty) FROM stock_movements WHERE type IN ('PERTE', 'OFFERT') GROUP BY type")
            rows = self.cur.fetchall()
            msg = "🗑️ BILAN DES PERTES :\n\n" + "\n".join([f"- {r[0]} : {r[2]} produits ({r[1]} fois)" for r in rows]) if rows else "Aucune perte."
            messagebox.showwarning("PERTES", msg)
        ctk.CTkButton(row2, text="🗑️ PERTES/DONS", fg_color="#c0392b", command=show_losses).pack(side="left", fill="x", expand=True, padx=2)
        
        def top_staff():
            self.cur.execute("SELECT user_name, SUM(total_price) as tot FROM sales_header GROUP BY user_name ORDER BY tot DESC LIMIT 1")
            r = self.cur.fetchone()
            msg = f"🥇 MEILLEUR VENDEUR :\n\n{r[0].upper()}\n(A vendu pour {r[1]} FCFA)" if r else "Rien"
            messagebox.showinfo("STAFF", msg)
        ctk.CTkButton(row2, text="🥇 TOP VENDEUR", fg_color="#f39c12", command=top_staff).pack(side="left", fill="x", expand=True, padx=2)

        # ZONE 3: IMPRESSION RAPPORTS
        rf = ctk.CTkFrame(f); rf.pack(fill="x", pady=10)
        ctk.CTkLabel(rf, text="🖨️ ZONE D'IMPRESSION", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        d1 = ctk.CTkEntry(rf, width=100); d1.pack(side="left", padx=2)
        ctk.CTkButton(rf, text="📅", width=30, command=lambda: MauricetteCalendar(self, lambda d: (d1.delete(0, 'end'), d1.insert(0, d)))).pack(side="left")
        d2 = ctk.CTkEntry(rf, width=100); d2.pack(side="left", padx=2)
        ctk.CTkButton(rf, text="📅", width=30, command=lambda: MauricetteCalendar(self, lambda d: (d2.delete(0, 'end'), d2.insert(0, d)))).pack(side="left")
        
        def rep():
            if not d1.get() or not d2.get(): return
            q = """SELECT prod_name, SUM(qty), SUM(qty*unit_price) FROM sales_lines 
                   JOIN sales_header ON sales_lines.sale_id = sales_header.id 
                   WHERE date_time BETWEEN ? AND ? GROUP BY prod_name"""
            self.cur.execute(q, (d1.get()+" 00:00:00", d2.get()+" 23:59:59"))
            rows = self.cur.fetchall()
            t = f"{self.store_name.center(42)}\nRAPPORT PERIODE\n{d1.get()} AU {d2.get()}\n"
            t += "="*42 + "\n" + f"{'PRODUIT':<20} {'QTE':<5} {'TOTAL':>15}\n" + "-"*42 + "\n"
            gt = 0
            for r in rows:
                t += f"{r[0]:<20} {r[1]:<5} {r[2]:>15}\n"; gt += r[2]
            t += "="*42 + "\n" + f"CA TOTAL : {gt} FCFA".center(42) + "\n\n"
            if self.sel_print: PrinterManager.print_ticket(self.sel_print, t)
            messagebox.showinfo("RAPPORT", t)
        ctk.CTkButton(rf, text="RECAP PÉRIODE", command=rep).pack(side="left", padx=10)
        
        def z():
            d = datetime.now().strftime("%Y-%m-%d")
            q = """SELECT prod_name, SUM(qty), SUM(qty*unit_price) FROM sales_lines 
                   JOIN sales_header ON sales_lines.sale_id = sales_header.id 
                   WHERE date_time LIKE ? GROUP BY prod_name"""
            self.cur.execute(q, (f"{d}%",)); rows = self.cur.fetchall()
            t = f"{self.store_name.center(42)}\nZ DE CAISSE DETAIL\nDATE: {d}\n"
            t += "="*42 + "\n" + f"{'PRODUIT':<20} {'QTE':<5} {'TOTAL':>15}\n" + "-"*42 + "\n"
            gt = 0
            for r in rows:
                t += f"{r[0]:<20} {r[1]:<5} {r[2]:>15}\n"; gt += r[2]
            t += "="*42 + "\n" + f"TOTAL JOUR : {gt} FCFA".center(42) + "\n\n"
            if self.sel_print: PrinterManager.print_ticket(self.sel_print, t)
            messagebox.showinfo("Z", t)
        ctk.CTkButton(rf, text="TICKET Z", fg_color=C_WARN, command=z).pack(side="left", padx=5)
        
        def stk_val():
            self.cur.execute("SELECT name, stock_qty FROM products"); rows = self.cur.fetchall()
            t = f"{self.store_name.center(42)}\nETAT DU STOCK\n{datetime.now().strftime('%d/%m/%Y')}\n"
            t += "="*42 + "\n" + f"{'PRODUIT':<30} {'STOCK':>10}\n" + "-"*42 + "\n"
            for r in rows: t += f"{r[0]:<30} {r[1]:>10}\n"
            if self.sel_print: PrinterManager.print_ticket(self.sel_print, t)
            messagebox.showinfo("STOCK", t)
        ctk.CTkButton(rf, text="ETAT STOCK", fg_color=C_INFO, command=stk_val).pack(side="left", padx=5)

        self.stats_container = ctk.CTkFrame(f); self.stats_container.pack(fill="both", expand=True, pady=10); self.draw_stats()

    def draw_stats(self):
        if not HAS_PLOT: return
        for w in self.stats_container.winfo_children(): w.destroy()
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4)); fig.patch.set_facecolor('#2b2b2b'); plt.style.use('dark_background')
        self.cur.execute("SELECT prod_name, SUM(qty) FROM sales_lines GROUP BY prod_name ORDER BY SUM(qty) DESC LIMIT 5"); d1 = self.cur.fetchall()
        if d1: ax1.bar([x[0] for x in d1], [x[1] for x in d1], color=C_ACC); ax1.set_title("TOP 5 VENTES")
        self.cur.execute("SELECT user_name, SUM(total_price) FROM sales_header GROUP BY user_name"); d2 = self.cur.fetchall()
        if d2: ax2.pie([x[1] for x in d2], labels=[x[0] for x in d2], autopct='%1.1f%%'); ax2.set_title("PAR VENDEUR")
        FigureCanvasTkAgg(fig, master=self.stats_container).get_tk_widget().pack(fill="both", expand=True)

    # --- CONFIG ---
    def init_cfg(self):
        t = ctk.CTkTabview(self.t_cfg); t.pack(fill="both", expand=True, padx=10, pady=10)
        ta = t.add("APPARENCE"); ts = t.add("SYSTÈME"); to = t.add("OUTILS"); tl = t.add("LICENCE"); tc = t.add("CONTACT")
        
        # CONTACT (NEW)
        ctk.CTkLabel(tc, text="LOGICIEL DÉVELOPPÉ PAR", font=("Arial", 14, "bold")).pack(pady=20)
        ctk.CTkLabel(tc, text=DEV_NAME, font=("Arial", 20, "bold"), text_color=C_PRIM).pack()
        f_contact = ctk.CTkFrame(tc); f_contact.pack(pady=20, padx=20)
        ctk.CTkLabel(f_contact, text="📧 EMAIL :", font=("Arial", 12, "bold")).pack()
        ctk.CTkLabel(f_contact, text=DEV_EMAIL, text_color=C_INFO).pack(pady=(0, 10))
        ctk.CTkLabel(f_contact, text="📞 TÉLÉPHONE :", font=("Arial", 12, "bold")).pack()
        ctk.CTkLabel(f_contact, text=DEV_PHONE, text_color=C_INFO).pack()
        
        # APPARENCE
        ctk.CTkLabel(ta, text="Police d'écriture").pack(); cbf = ctk.CTkComboBox(ta, values=["Arial", "Segoe UI", "Roboto", "Courier New", "Verdana"]); cbf.set(self.font_fam); cbf.pack(pady=5)
        ctk.CTkLabel(ta, text="Taille du texte").pack(); cbs = ctk.CTkComboBox(ta, values=["10", "12", "14", "16", "18", "20", "24"]); cbs.set(str(self.font_sz)); cbs.pack(pady=5)
        def save_f():
            self.cur.execute("UPDATE settings SET valeur=? WHERE cle='font_family'", (cbf.get(),)); self.cur.execute("UPDATE settings SET valeur=? WHERE cle='font_size'", (cbs.get(),)); self.conn.commit(); messagebox.showinfo("OK", "Redémarrage requis")
        ctk.CTkButton(ta, text="SAUVEGARDER", command=save_f).pack(pady=20)

        # SYSTÈME
        ctk.CTkLabel(ts, text="NOM DE VOTRE MAGASIN (APPARAÎT SUR TICKET)", font=self.f_norm, text_color=C_WARN).pack(pady=20)
        en = ctk.CTkEntry(ts, font=("Arial", 16), justify="center", width=300); en.insert(0, self.store_name); en.pack(pady=10)
        ctk.CTkButton(ts, text="VALIDER LE NOUVEAU NOM", height=40, fg_color=C_OK, command=lambda: (self.cur.execute("UPDATE settings SET valeur=? WHERE cle='store_name'", (en.get(),)), self.conn.commit(), messagebox.showinfo("OK", "Nom changé. Redémarrez."))).pack()
        ctk.CTkLabel(ts, text="IMPRIMANTE TICKET", font=self.f_norm).pack(pady=(30, 10))
        cp = ctk.CTkComboBox(ts, values=PrinterManager.get_printers()); cp.set(self.sel_print); cp.pack()
        ctk.CTkButton(ts, text="SAUVEGARDER IMPRIMANTE", command=lambda: (self.cur.execute("UPDATE settings SET valeur=? WHERE cle='printer'", (cp.get(),)), self.conn.commit())).pack(pady=10)
        
        # OUTILS
        ctk.CTkLabel(to, text="BOÎTE À OUTILS", font=self.f_title).pack(pady=20)
        def open_folder(): os.startfile(os.getcwd()) if platform.system() == "Windows" else None
        ctk.CTkButton(to, text="📂 OUVRIR DOSSIER DONNÉES", command=open_folder).pack(pady=10)
        def quick_calc(): subprocess.Popen('calc.exe')
        ctk.CTkButton(to, text="🧮 CALCULATRICE", command=quick_calc).pack(pady=10)
        ctk.CTkButton(to, text="💾 SAUVEGARDER BDD", command=self.db_backup).pack(pady=10)

        # LICENCE
        ek = ctk.CTkEntry(tl, placeholder_text="CLÉ MASTER", show="*"); ek.pack(pady=5)
        def act():
            k = ek.get().strip(); v, m = SecurityEngine.check(k)
            if v: self.cur.execute("INSERT OR REPLACE INTO settings (cle,valeur) VALUES ('license_key',?)", (k,)); self.conn.commit(); messagebox.showinfo("OK", "Activé !")
            else: messagebox.showerror("NON", "Invalide")
        ctk.CTkButton(tl, text="ACTIVER (SUPER ADMIN)", fg_color=C_ERR, command=act).pack(pady=10)

    # --- JOURNAUX ---
    def init_logs(self):
        s = ctk.CTkScrollableFrame(self.t_logs); s.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkButton(self.t_logs, text="VIDER LES LOGS", fg_color=C_ERR, command=lambda: (self.cur.execute("DELETE FROM audit_logs"), self.conn.commit(), self.ref_logs(s)) if self.ask_admin() else None).pack(pady=10)
        self.ref_logs(s)
    def ref_logs(self, scroll):
        for w in scroll.winfo_children(): w.destroy()
        for r in self.cur.execute("SELECT timestamp, user, action, detail FROM audit_logs ORDER BY id DESC LIMIT 100"): ctk.CTkLabel(scroll, text=f"[{r[0]}] {r[1].upper()} : {r[2]} -> {r[3]}", anchor="w", font=("Consolas", 12)).pack(fill="x", pady=2)

    def db_backup(self):
        p = filedialog.asksaveasfilename(defaultextension=".db")
        if p: self.conn.commit(); shutil.copy2(self.db_path, p); messagebox.showinfo("OK", "Saved")

    def close(self):
        if messagebox.askyesno("QUITTER", "Fermer l'application ?"): self.conn.close(); self.destroy()

if __name__ == "__main__":
    if platform.system() == "Windows":
        try: from ctypes import windll; windll.shcore.SetProcessDpiAwareness(1)
        except: pass
    app = DrinkManagerEnterprise()
    app.mainloop()
