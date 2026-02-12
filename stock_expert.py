#%%
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
import socket  
from datetime import datetime, timedelta

# =============================================================================
# CONFIGURATION GLOBALE
# =============================================================================
APP_NAME = "DRINK MANAGER PRO"
APP_VERSION = "v34.0" 
DB_FILE = "enterprise_data.db"
PORT_LOCK = 65432 

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
# GESTION INSTANCE UNIQUE
# =============================================================================
def check_single_instance():
    """Empêche d'ouvrir le logiciel deux fois."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', PORT_LOCK))
        return s  # On retourne le socket pour le garder ouvert
    except socket.error:
        return None

# =============================================================================
# UPDATE MANAGER
# =============================================================================
class UpdateManager:
    @staticmethod
    def check_update():
        try:
            req = urllib.request.Request(URL_VERSION, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                online_ver = response.read().decode('utf-8').strip()
            
            if online_ver != APP_VERSION:
                msg = f"🚀 MISE À JOUR DISPO ({online_ver}) !\n\nLe logiciel va redémarrer pour l'installer.\nConfirmer ?"
                if messagebox.askyesno("UPDATE", msg):
                    UpdateManager.download_and_install(online_ver)
        except Exception as e:
            print(f"Update Check Error: {e}")

    @staticmethod
    def download_and_install(ver):
        try:
            if getattr(sys, 'frozen', False):
                current_exe = os.path.basename(sys.executable)
                current_dir = os.path.dirname(sys.executable)
            else:
                current_exe = os.path.basename(sys.argv[0])
                current_dir = os.path.dirname(os.path.abspath(__file__))

            new_exe_name = "update_temp.exe"
            new_exe_path = os.path.join(current_dir, new_exe_name)
            dynamic_url = f"https://github.com/doufall/LogicielBar/releases/download/{ver}/stock_expert_1.exe"
            
            messagebox.showinfo("TÉLÉCHARGEMENT", "Téléchargement en cours...\nNe touchez à rien.")
            urllib.request.urlretrieve(dynamic_url, new_exe_path)
            
            # Exécution directe pour éviter le bug EOF
            cmd = f'cmd /c timeout /t 2 /nobreak > NUL & del "{current_exe}" & ren "{new_exe_name}" "{current_exe}" & start "" "{current_exe}"'
            subprocess.Popen(cmd, shell=True)
            sys.exit(0)
        except Exception as e:
            messagebox.showerror("ERREUR", f"Echec update auto :\n{e}")

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
        
        # --- REND LA FENÊTRE MODALE (Empêche de cliquer ailleurs) ---
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
    SALT = "MAURICETTE_V31"
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
#%%
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
        
        self.after(2000, UpdateManager.check_update)
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
        
        # --- MODIF: TAILLE POLICE PAR DEFAUT A 18 COMME DANS TA V31 ---
        defaults = [('store_name', 'MA BOUTIQUE'), ('license_key', ''), ('install_date', datetime.now().strftime("%Y-%m-%d")), ('theme', 'System'), ('font_family', 'Arial'), ('font_size', '18'), ('printer', ''), ('stock_alert', '5')]
        self.cur.executemany("INSERT OR IGNORE INTO settings VALUES (?,?)", defaults)
        self.cur.executemany("INSERT OR IGNORE INTO categories VALUES (?)", [('BOISSONS',), ('SNACKS',), ('DIVERS',)])
        
        self.cur.execute("SELECT count(*) FROM staff WHERE role='admin'")
        if self.cur.fetchone()[0] == 0:
            self.cur.execute("INSERT INTO staff VALUES ('admin','admin','admin')")
        
        self.conn.commit()

    def load_cfg(self):
        self.cur.execute("SELECT cle, valeur FROM settings")
        d = dict(self.cur.fetchall())
        self.store_name = d.get('store_name', 'MA BOUTIQUE')
        self.font_fam = d.get('font_family', 'Arial')
        self.font_sz = int(d.get('font_size', 18)) # Default bigger
        self.alert_thr = int(d.get('stock_alert', 5))
        self.sel_print = d.get('printer', '')
        ctk.set_appearance_mode(d.get('theme', 'System'))

    def apply_style(self):
        # --- POLICES PLUS GRANDES ---
        self.f_title = (self.font_fam, int(self.font_sz * 2.0), "bold") # Titres
        self.f_norm = (self.font_fam, int(self.font_sz * 1.2), "bold")  # Textes normaux
        self.f_small = (self.font_fam, int(self.font_sz), "bold")       # Petits textes
        self.f_btn = (self.font_fam, int(self.font_sz * 1.1), "bold")   # Boutons
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
        f = ctk.CTkFrame(self, width=500, height=650); f.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(f, text=self.store_name, font=self.f_title).pack(pady=(50, 30))
        if self.trial: ctk.CTkLabel(f, text="MODE ESSAI", text_color=C_WARN, font=self.f_small).pack()
        
        self.eu = ctk.CTkEntry(f, placeholder_text="Utilisateur", width=350, height=50, font=self.f_norm)
        self.eu.pack(pady=15)
        
        self.ep = ctk.CTkEntry(f, placeholder_text="Mot de passe", show="*", width=350, height=50, font=self.f_norm)
        self.ep.pack(pady=15)
        
        def toggle_login_pass():
            if self.ep.cget('show') == '*': self.ep.configure(show='')
            else: self.ep.configure(show='*')
        
        ctk.CTkCheckBox(f, text="👁️ Voir le mot de passe", font=self.f_small, command=toggle_login_pass).pack(pady=10)
        ctk.CTkButton(f, text="SE CONNECTER", width=350, height=60, font=self.f_norm, command=self.do_log).pack(pady=30)
        ctk.CTkLabel(f, text=f"Besoin d'aide ? {DEV_PHONE}", text_color=C_INFO, font=("Arial", 12)).pack(side="bottom", pady=20)

    def do_log(self):
        u, p = self.eu.get().lower(), self.ep.get()
        self.cur.execute("SELECT role FROM staff WHERE username=? AND password=?", (u, p)); r = self.cur.fetchone()
        if r: self.user = {"name": u, "role": r[0]}; self.dash()
        else: messagebox.showerror("ERREUR", "Nom d'utilisateur ou mot de passe incorrect.")

   # =============================================================================
    # TABLEAU DE BORD PRINCIPAL
    # =============================================================================
    def dash(self):
        # 1. Nettoyage de l'écran précédent (Login)
        self.clear()
        
        # 2. Zoom et Style
        ctk.set_widget_scaling(1.1) 
        
        # 3. Création du conteneur d'onglets (Tabview)
        # On l'assigne à self.main_tabs pour être sûr de sa référence
        self.main_tabs = ctk.CTkTabview(self, height=800)
        self.main_tabs.pack(fill="both", expand=True, padx=10, pady=10)
        self.main_tabs._segmented_button.configure(font=self.f_norm, height=50) 

        # 4. AJOUT DES ONGLETS (L'ordre est important)
        self.t_pos = self.main_tabs.add("CAISSE")
        self.t_inv = self.main_tabs.add("STOCK")
        
        # 5. ONGLETS ADMINISTRATEUR
        if self.user["role"] == "admin":
            self.t_stf = self.main_tabs.add("EQUIPE")
            self.t_stat = self.main_tabs.add("RAPPORTS")
            self.t_cfg = self.main_tabs.add("CONFIG")
            self.t_logs = self.main_tabs.add("JOURNAL")
            
            # Initialisation des contenus Admin
            # On utilise try/except pour qu'une erreur dans un onglet ne bloque pas les autres
            try: self.init_staff()
            except Exception as e: print(f"Erreur Staff: {e}")
            
            try: self.init_stats()
            except Exception as e: print(f"Erreur Stats: {e}")
            
            try: self.init_cfg()
            except Exception as e: print(f"Erreur Config: {e}")
            
            try: self.init_logs()
            except Exception as e: print(f"Erreur Logs: {e}")
            
        # 6. INITIALISATION DES CONTENUS STANDARDS
        # Ces deux fonctions DOIVENT être appelées en dernier
        self.init_pos()   # Remplit la Caisse
        self.init_stock() # Remplit le Stock (C'est ici que tes éléments apparaîtront)
        
        # Forcer la mise à jour visuelle
        self.update_idletasks()

    # --- POS (CAISSE) ---
    def init_pos(self):
        self.t_pos.grid_columnconfigure(0, weight=3); self.t_pos.grid_columnconfigure(1, weight=1); self.t_pos.grid_rowconfigure(0, weight=1)
        
        lf = ctk.CTkFrame(self.t_pos); lf.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        sf = ctk.CTkFrame(lf, height=60); sf.pack(fill="x", pady=5)
        
        self.eps = ctk.CTkEntry(sf, placeholder_text="🔍 Chercher un produit...", height=50, font=self.f_norm)
        self.eps.pack(side="left", fill="x", expand=True, padx=5)
        self.eps.bind("<KeyRelease>", lambda e: self.ref_pos())
        
        self.ecf = ctk.CTkComboBox(sf, values=["TOUT"] + [r[0] for r in self.cur.execute("SELECT name FROM categories")], height=50, font=self.f_norm, command=lambda x: self.ref_pos())
        self.ecf.pack(side="left", padx=5)
        
        self.gp = ctk.CTkScrollableFrame(lf, fg_color="transparent"); self.gp.pack(fill="both", expand=True)
        
        rf = ctk.CTkFrame(self.t_pos, fg_color=C_SEC); rf.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(rf, text="PANIER", font=self.f_title).pack(pady=10)
        
        self.cv = ctk.CTkScrollableFrame(rf); self.cv.pack(fill="both", expand=True)
        
        self.lt = ctk.CTkLabel(rf, text="TOTAL: 0 FCFA", font=("Arial", 30, "bold"), text_color=C_OK); self.lt.pack(pady=20)
        
        ctk.CTkButton(rf, text="ENCAISSER (PAYER)", fg_color=C_OK, height=80, font=("Arial", 20, "bold"), command=self.pay).pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(rf, text="VIDER PANIER", fg_color=C_ERR, height=50, font=self.f_norm, command=lambda: (self.cart.clear(), self.upd_cart())).pack(fill="x", padx=10, pady=5)
        
        self.cat = "TOUT"; self.ref_pos()
    # --- POS (FONCTIONS DE MISE À JOUR) ---
      # --- POS (FONCTIONS DE MISE À JOUR) ---
    def ref_pos(self):
        for w in self.gp.winfo_children(): w.destroy()
        q = "SELECT name, sell_price, stock_qty FROM products WHERE name LIKE ?"
        p = [f"%{self.eps.get()}%"]
        if self.ecf.get() != "TOUT": 
            q += " AND category=?"
            p.append(self.ecf.get())
        
        for n, pr, qt in self.cur.execute(q, p):
            c = C_PRIM if qt > self.alert_thr else (C_WARN if qt > 0 else "gray")
            ctk.CTkButton(self.gp, text=f"{n}\n{pr} F\n({qt})", fg_color=c, width=160, height=120, font=("Arial", 14, "bold"), command=lambda x=n, y=pr, z=qt: self.add_c(x, y, z)).pack(side="left", padx=5, pady=5)

    # --- STOCK ET TRAÇABILITÉ (BLOC RÉPARÉ) ---


def get_prods(self):
    """Retourne la liste des produits"""
    self.cur.execute("SELECT name FROM products ORDER BY name")
    return [r[0] for r in self.cur.fetchall()]

def init_stock(self):

    # ===============================
    # ZONE FORMULAIRES
    # ===============================
    form_frame = ctk.CTkFrame(self.t_inv)
    form_frame.pack(fill="x", padx=10, pady=10)

    # --------- CREATION PRODUIT ----------
    create_frame = ctk.CTkFrame(form_frame)
    create_frame.pack(side="left", expand=True, fill="both", padx=5)

    ctk.CTkLabel(create_frame, text="CRÉER PRODUIT", font=self.f_small).pack(pady=5)

    self.stock_name = ctk.CTkEntry(create_frame, placeholder_text="Nom produit")
    self.stock_name.pack(fill="x", pady=3)

    self.stock_cat = ctk.CTkComboBox(
        create_frame,
        values=[r[0] for r in self.cur.execute("SELECT name FROM categories")]
    )
    self.stock_cat.pack(fill="x", pady=3)

    self.stock_buy = ctk.CTkEntry(create_frame, placeholder_text="Prix Achat")
    self.stock_buy.pack(fill="x", pady=3)

    self.stock_sell = ctk.CTkEntry(create_frame, placeholder_text="Prix Vente")
    self.stock_sell.pack(fill="x", pady=3)

    def create_product():
        if not self.ask_admin():
            return

        name = self.stock_name.get().strip().upper()
        if not name:
            return

        try:
            self.cur.execute("""
                INSERT INTO products (name, category, buy_price, sell_price, stock_qty)
                VALUES (?,?,?,?,0)
            """, (
                name,
                self.stock_cat.get(),
                self.safe_int(self.stock_buy.get()),
                self.safe_int(self.stock_sell.get())
            ))

            self.conn.commit()
            self.ref_stock()
            self.stock_name.delete(0, "end")
            messagebox.showinfo("OK", "Produit créé")

        except sqlite3.IntegrityError:
            messagebox.showerror("Erreur", "Produit déjà existant")

    ctk.CTkButton(create_frame, text="CRÉER", command=create_product).pack(pady=5, fill="x")

    # --------- ENTREE STOCK ----------
    entry_frame = ctk.CTkFrame(form_frame, border_color="green", border_width=2)
    entry_frame.pack(side="left", expand=True, fill="both", padx=5)

    ctk.CTkLabel(entry_frame, text="ENTRÉE STOCK").pack(pady=5)

    self.entry_product = ctk.CTkComboBox(entry_frame, values=[])
    self.entry_product.pack(fill="x", pady=3)

    self.entry_qty = ctk.CTkEntry(entry_frame, placeholder_text="Quantité")
    self.entry_qty.pack(fill="x", pady=3)

    def add_stock():
        if not self.ask_admin():
            return

        qty = self.safe_int(self.entry_qty.get())
        prod = self.entry_product.get()

        if qty <= 0 or not prod:
            return

        self.cur.execute(
            "UPDATE products SET stock_qty = stock_qty + ? WHERE name=?",
            (qty, prod)
        )

        self.cur.execute("""
            INSERT INTO stock_movements (date, prod_name, qty, type, user)
            VALUES (?,?,?,?,?)
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            prod,
            qty,
            "ENTREE",
            self.user["name"]
        ))

        self.conn.commit()
        self.ref_stock()
        self.entry_qty.delete(0, "end")

    ctk.CTkButton(entry_frame, text="VALIDER", command=add_stock).pack(pady=5, fill="x")

    # --------- PERTE ----------
    loss_frame = ctk.CTkFrame(form_frame, border_color="red", border_width=2)
    loss_frame.pack(side="left", expand=True, fill="both", padx=5)

    ctk.CTkLabel(loss_frame, text="PERTE").pack(pady=5)

    self.loss_product = ctk.CTkComboBox(loss_frame, values=[])
    self.loss_product.pack(fill="x", pady=3)

    self.loss_qty = ctk.CTkEntry(loss_frame, placeholder_text="Quantité")
    self.loss_qty.pack(fill="x", pady=3)

    self.loss_reason = ctk.CTkEntry(loss_frame, placeholder_text="Motif")
    self.loss_reason.pack(fill="x", pady=3)

    def remove_stock():
        if not self.ask_admin():
            return

        qty = self.safe_int(self.loss_qty.get())
        prod = self.loss_product.get()

        if qty <= 0 or not prod:
            return

        self.cur.execute(
            "UPDATE products SET stock_qty = stock_qty - ? WHERE name=?",
            (qty, prod)
        )

        self.cur.execute("""
            INSERT INTO stock_movements
            (date, prod_name, qty, type, reason_or_ref, user)
            VALUES (?,?,?,?,?,?)
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            prod,
            qty,
            "PERTE",
            self.loss_reason.get(),
            self.user["name"]
        ))

        self.conn.commit()
        self.ref_stock()
        self.loss_qty.delete(0, "end")

    ctk.CTkButton(loss_frame, text="VALIDER PERTE", command=remove_stock).pack(pady=5, fill="x")

    # ===============================
    # TABLEAU TRAÇABILITÉ
    # ===============================
    table_frame = ctk.CTkFrame(self.t_inv)
    table_frame.pack(fill="both", expand=True, padx=10, pady=10)

    cols = ("ID", "Date", "Utilisateur", "Type", "Produit", "Qté", "Motif")

    self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")

    for col in cols:
        self.tree.heading(col, text=col)
        self.tree.column(col, anchor="center", width=120)

    self.tree.pack(fill="both", expand=True)

    # Boutons
    bottom_frame = ctk.CTkFrame(self.t_inv)
    bottom_frame.pack(pady=5)

    ctk.CTkButton(bottom_frame, text="ACTUALISER", command=self.ref_stock).pack(side="left", padx=10)
    ctk.CTkButton(bottom_frame, text="EXPORT CSV", command=self.stock_export_csv).pack(side="left", padx=10)

    self.ref_stock()


def ref_stock(self):

    products = self.get_prods()

    if hasattr(self, "entry_product"):
        self.entry_product.configure(values=products)

    if hasattr(self, "loss_product"):
        self.loss_product.configure(values=products)

    if hasattr(self, "tree"):
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.cur.execute("""
            SELECT id, date, user, type, prod_name, qty, reason_or_ref
            FROM stock_movements
            ORDER BY id DESC
            LIMIT 200
        """)

        for row in self.cur.fetchall():
            self.tree.insert("", "end", values=row)



def stock_export_csv(self):
    path = filedialog.asksaveasfilename(defaultextension=".csv")
    if not path:
        return

    ExportManager.to_csv(self.cur, "products", path)
    messagebox.showinfo("OK", "Export terminé")


    def sales_export_csv(self):
        p = filedialog.asksaveasfilename(defaultextension=".csv")
        if p: 
            ExportManager.to_csv(self.cur, "sales_header", p)
            messagebox.showinfo("OK", "Ventes exportées en CSV avec succès.")
    # =============================================================================
    # GESTION ÉQUIPE (STAFF)
    # =============================================================================
    def init_staff(self):
        f = ctk.CTkFrame(self.t_stf)
        f.pack(fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(f, text="GESTION DU PERSONNEL", font=self.f_title).pack(pady=10)

        # Tableau du Staff
        self.staff_tree = ttk.Treeview(f, columns=("Username", "Role"), show="headings")
        self.staff_tree.heading("Username", text="Utilisateur")
        self.staff_tree.heading("Role", text="Rôle")
        self.staff_tree.pack(fill="both", expand=True, pady=10)

        bf = ctk.CTkFrame(f)
        bf.pack(pady=10)

        ctk.CTkButton(bf, text="AJOUTER MEMBRE", height=45, command=self.add_staff).pack(side="left", padx=5)
        ctk.CTkButton(bf, text="SUPPRIMER", height=45, fg_color=C_ERR, command=self.del_staff).pack(side="left", padx=5)
        
        self.refresh_staff()

    def refresh_staff(self):
        for i in self.staff_tree.get_children(): self.staff_tree.delete(i)
        self.cur.execute("SELECT username, role FROM staff")
        for row in self.cur.fetchall(): self.staff_tree.insert("", "end", values=row)

    def add_staff(self):
        u = simpledialog.askstring("USER", "Nom d'utilisateur :")
        p = simpledialog.askstring("PASS", "Mot de passe :", show='*')
        r = simpledialog.askstring("ROLE", "Rôle (admin/caissier) :")
        if u and p and r:
            try:
                self.cur.execute("INSERT INTO staff VALUES (?,?,?)", (u.lower(), p, r.lower()))
                self.conn.commit(); self.refresh_staff()
                messagebox.showinfo("OK", "Utilisateur créé !")
            except: messagebox.showerror("ERREUR", "L'utilisateur existe déjà.")

    def del_staff(self):
        sel = self.staff_tree.focus()
        if not sel: return
        user = self.staff_tree.item(sel)["values"][0]
        if user == "admin": 
            messagebox.showwarning("NON", "Impossible de supprimer l'admin principal."); return
        if messagebox.askyesno("CONFIRMER", f"Supprimer {user} ?"):
            self.cur.execute("DELETE FROM staff WHERE username=?", (user,))
            self.conn.commit(); self.refresh_staff()

    # =============================================================================
    # RAPPORTS ET STATISTIQUES (DESIGN V31 FINAL)
    # =============================================================================
    def init_stats(self):
        f = ctk.CTkFrame(self.t_stat); f.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ZONE 1: BOUTONS DE CALCUL RAPIDE
        qf = ctk.CTkFrame(f); qf.pack(fill="x", pady=5)
        ctk.CTkLabel(qf, text="📊 PERFORMANCE ET DIAGNOSTIC", font=self.f_norm, text_color=C_INFO).pack(pady=10)
        
        # LIGNE 1 : Argent et Alertes
        r1 = ctk.CTkFrame(qf, fg_color="transparent"); r1.pack(fill="x", pady=2)
        
        def low_stk():
            self.cur.execute("SELECT name, stock_qty FROM products WHERE stock_qty <= ?", (self.alert_thr,))
            res = self.cur.fetchall()
            msg = "✅ Stock OK" if not res else "⚠️ ALERTE RUPTURE :\n\n" + "\n".join([f"- {r[0]} ({r[1]})" for r in res])
            messagebox.showwarning("STOCK", msg)
        ctk.CTkButton(r1, text="📉 STOCK BAS", height=55, fg_color=C_ERR, command=low_stk).pack(side="left", fill="x", expand=True, padx=2)
        
        def ca_month():
            m = datetime.now().strftime("%Y-%m")
            self.cur.execute("SELECT SUM(total_price) FROM sales_header WHERE date_time LIKE ?", (m+"%",))
            r = self.cur.fetchone()[0] or 0
            messagebox.showinfo("CA MOIS", f"💰 Chiffre d'Affaire ({m}) :\n\n{r} FCFA")
        ctk.CTkButton(r1, text="💰 CA DU MOIS", height=55, fg_color=C_OK, command=ca_month).pack(side="left", fill="x", expand=True, padx=2)

        def profit_calc():
            self.cur.execute("SELECT SUM((p.sell_price - p.buy_price) * sl.qty) FROM sales_lines sl JOIN products p ON sl.prod_name = p.name")
            res = self.cur.fetchone()[0] or 0
            messagebox.showinfo("BÉNÉFICE", f"💎 Bénéfice total estimé :\n\n+{res} FCFA")
        ctk.CTkButton(r1, text="💎 BÉNÉFICE", height=55, fg_color="#8e44ad", command=profit_calc).pack(side="left", fill="x", expand=True, padx=2)

        # LIGNE 2 : Valeurs et Tops (AJOUT V31.0)
        r2 = ctk.CTkFrame(qf, fg_color="transparent"); r2.pack(fill="x", pady=2)

        def val_stock():
            self.cur.execute("SELECT SUM(stock_qty * buy_price) FROM products")
            res = self.cur.fetchone()[0] or 0
            messagebox.showinfo("VALEUR STOCK", f"🏦 Valeur marchande en stock :\n\n{res} FCFA")
        ctk.CTkButton(r2, text="🏦 VALEUR STOCK", height=55, fg_color="#2980b9", command=val_stock).pack(side="left", fill="x", expand=True, padx=2)

        def top_prod_msg():
            self.cur.execute("SELECT prod_name, SUM(qty) as s FROM sales_lines GROUP BY prod_name ORDER BY s DESC LIMIT 1")
            r = self.cur.fetchone()
            msg = f"🏆 Produit Champion :\n\n{r[0]} ({r[1]} ventes)" if r else "Aucune vente"
            messagebox.showinfo("TOP PRODUIT", msg)
        ctk.CTkButton(r2, text="🏆 TOP PRODUIT", height=55, fg_color=C_WARN, command=top_prod_msg).pack(side="left", fill="x", expand=True, padx=2)

        def top_vendeur():
            self.cur.execute("SELECT user_name, SUM(total_price) as tot FROM sales_header GROUP BY user_name ORDER BY tot DESC LIMIT 1")
            r = self.cur.fetchone()
            msg = f"🥇 Meilleur Vendeur :\n\n{str(r[0]).upper()} ({r[1]} FCFA)" if r else "Pas de données"
            messagebox.showinfo("STAFF", msg)
        ctk.CTkButton(r2, text="🥇 TOP VENDEUR", height=55, fg_color="#f39c12", command=top_vendeur).pack(side="left", fill="x", expand=True, padx=2)

        # ZONE 2: IMPRESSION ET ÉTATS PHYSIQUES
        rf = ctk.CTkFrame(f); rf.pack(fill="x", pady=10)
        ctk.CTkLabel(rf, text="🖨️ IMPRESSIONS", font=("Arial", 14, "bold")).pack(side="left", padx=10)
        d1 = ctk.CTkEntry(rf, width=120, height=40); d1.pack(side="left", padx=2)
        ctk.CTkButton(rf, text="📅", width=40, command=lambda: MauricetteCalendar(self, lambda d: (d1.delete(0, 'end'), d1.insert(0, d)))).pack(side="left")
        d2 = ctk.CTkEntry(rf, width=120, height=40); d2.pack(side="left", padx=2)
        ctk.CTkButton(rf, text="📅", width=40, command=lambda: MauricetteCalendar(self, lambda d: (d2.delete(0, 'end'), d2.insert(0, d)))).pack(side="left")
        
        def rep_per():
            if not d1.get() or not d2.get(): return
            q = "SELECT prod_name, SUM(qty), SUM(qty*unit_price) FROM sales_lines JOIN sales_header ON sales_lines.sale_id = sales_header.id WHERE date_time BETWEEN ? AND ? GROUP BY prod_name"
            self.cur.execute(q, (d1.get()+" 00:00:00", d2.get()+" 23:59:59"))
            rows = self.cur.fetchall()
            t = f"RECAP DU {d1.get()} AU {d2.get()}\n" + "="*30 + "\n"
            for r in rows: t += f"{r[0]}: {r[1]} | {r[2]}F\n"
            messagebox.showinfo("RAPPORT", t)
        ctk.CTkButton(rf, text="RÉCAP PÉRIODE", height=40, command=rep_per).pack(side="left", padx=10)
        
        def ticket_z():
            today = datetime.now().strftime("%Y-%m-%d")
            self.cur.execute("SELECT prod_name, SUM(qty), SUM(qty*unit_price) FROM sales_lines JOIN sales_header ON sales_lines.sale_id = sales_header.id WHERE date_time LIKE ? GROUP BY prod_name", (today+"%",))
            rows = self.cur.fetchall()
            t = f"--- TICKET Z ({today}) ---\n"
            gt = 0
            for r in rows: t += f"{r[0]} x{r[1]} = {r[2]}F\n"; gt += r[2]
            t += f"\nTOTAL JOUR : {gt} FCFA"
            if self.sel_print: PrinterManager.print_ticket(self.sel_print, t)
            messagebox.showinfo("Z", t)
        ctk.CTkButton(rf, text="TICKET Z", height=40, fg_color=C_WARN, command=ticket_z).pack(side="left", padx=5)

        def etat_stock():
            self.cur.execute("SELECT name, stock_qty FROM products ORDER BY name ASC")
            rows = self.cur.fetchall()
            t = "📦 ÉTAT DU STOCK PHYSIQUE\n" + "="*30 + "\n"
            for r in rows: t += f"{r[0]:<20} : {r[1]:>5}\n"
            if self.sel_print: PrinterManager.print_ticket(self.sel_print, t)
            messagebox.showinfo("STOCK", t)
        ctk.CTkButton(rf, text="📦 ÉTAT STOCK", height=40, fg_color=C_INFO, command=etat_stock).pack(side="left", padx=5)

        # ZONE 3: GRAPHIQUES
        self.stats_container = ctk.CTkFrame(f); self.stats_container.pack(fill="both", expand=True, pady=10)
        self.draw_stats()

    def draw_stats(self):
        if not HAS_PLOT: return
        for w in self.stats_container.winfo_children(): w.destroy()
        fig, ax = plt.subplots(figsize=(6, 4)); fig.patch.set_facecolor('#2b2b2b'); plt.style.use('dark_background')
        self.cur.execute("SELECT prod_name, SUM(qty) as s FROM sales_lines GROUP BY prod_name ORDER BY s DESC LIMIT 5")
        data = self.cur.fetchall()
        if data:
            ax.bar([x[0][:10] for x in data], [x[1] for x in data], color=C_ACC)
            ax.set_title("TOP 5 PRODUITS VENDUS")
            FigureCanvasTkAgg(fig, master=self.stats_container).get_tk_widget().pack(fill="both", expand=True)
# =============================================================================
    # CONFIGURATION ET PARAMÈTRES (RESTAURATION DES 5 SOUS-ONGLETS V31)
    # =============================================================================
    def init_cfg(self):
        # Création du conteneur de sous-onglets
        tab_cfg = ctk.CTkTabview(self.t_cfg)
        tab_cfg.pack(fill="both", expand=True, padx=10, pady=10)
        tab_cfg._segmented_button.configure(font=self.f_norm, height=50)
        
        # Ajout des 5 onglets officiels
        t_app = tab_cfg.add("APPARENCE")
        t_sys = tab_cfg.add("SYSTÈME")
        t_prn = tab_cfg.add("IMPRIMANTE")
        t_tl  = tab_cfg.add("OUTILS")
        t_ct  = tab_cfg.add("CONTACT")
        
        # --- 1. SOUS-ONGLET : APPARENCE ---
        ctk.CTkLabel(t_app, text="PERSONNALISATION VISUELLE", font=self.f_title).pack(pady=20)
        ctk.CTkLabel(t_app, text="Taille de police globale (Recommandé: 18)", font=self.f_small).pack(pady=5)
        self.cb_font = ctk.CTkComboBox(t_app, values=["14", "16", "18", "20", "22", "24"], height=45, font=self.f_norm)
        self.cb_font.set(str(self.font_sz))
        self.cb_font.pack(pady=10)
        
        ctk.CTkLabel(t_app, text="Thème de l'interface", font=self.f_small).pack(pady=5)
        self.cb_theme = ctk.CTkComboBox(t_app, values=["System", "Dark", "Light"], height=45, font=self.f_norm)
        # On récupère le thème actuel en BDD
        try:
            curr_theme = self.cur.execute("SELECT valeur FROM settings WHERE cle='theme'").fetchone()[0]
            self.cb_theme.set(curr_theme)
        except: self.cb_theme.set("System")
        self.cb_theme.pack(pady=10)

        def save_app_settings():
            self.cur.execute("UPDATE settings SET valeur=? WHERE cle='font_size'", (self.cb_font.get(),))
            self.cur.execute("UPDATE settings SET valeur=? WHERE cle='theme'", (self.cb_theme.get(),))
            self.conn.commit()
            messagebox.showinfo("APPARENCE", "Modifications enregistrées !\nVeuillez redémarrer pour appliquer.")
        ctk.CTkButton(t_app, text="💾 SAUVEGARDER LE STYLE", height=50, fg_color=C_INFO, command=save_app_settings).pack(pady=30)

        # --- 2. SOUS-ONGLET : SYSTÈME ---
        ctk.CTkLabel(t_sys, text="PARAMÈTRES DE L'ÉTABLISSEMENT", font=self.f_title).pack(pady=20)
        ctk.CTkLabel(t_sys, text="Nom du Commerce (En-tête ticket)", font=self.f_small).pack(pady=5)
        self.en_store = ctk.CTkEntry(t_sys, width=400, height=50, font=self.f_norm, justify="center")
        self.en_store.insert(0, self.store_name)
        self.en_store.pack(pady=10)
        
        ctk.CTkLabel(t_sys, text="Seuil d'alerte Stock Bas", font=self.f_small).pack(pady=5)
        self.en_alert = ctk.CTkEntry(t_sys, width=150, height=50, font=self.f_norm, justify="center")
        self.en_alert.insert(0, str(self.alert_thr))
        self.en_alert.pack(pady=10)

        def save_sys_settings():
            self.cur.execute("UPDATE settings SET valeur=? WHERE cle='store_name'", (self.en_store.get().upper(),))
            self.cur.execute("UPDATE settings SET valeur=? WHERE cle='stock_alert'", (self.en_alert.get(),))
            self.conn.commit()
            messagebox.showinfo("SYSTÈME", "Paramètres système mis à jour.")
        ctk.CTkButton(t_sys, text="💾 ENREGISTRER SYSTÈME", height=50, fg_color=C_OK, command=save_sys_settings).pack(pady=30)

        # --- 3. SOUS-ONGLET : IMPRIMANTE ---
        ctk.CTkLabel(t_prn, text="CONFIGURATION IMPRESSION", font=self.f_title).pack(pady=20)
        printers = PrinterManager.get_printers()
        self.cb_prn = ctk.CTkComboBox(t_prn, values=printers, width=400, height=50, font=self.f_norm)
        self.cb_prn.set(self.sel_print)
        self.cb_prn.pack(pady=10)
        
        def save_printer_choice():
            self.cur.execute("UPDATE settings SET valeur=? WHERE cle='printer'", (self.cb_prn.get(),))
            self.conn.commit()
            messagebox.showinfo("IMPRIMANTE", f"Par défaut : {self.cb_prn.get()}")
        ctk.CTkButton(t_prn, text="✅ DÉFINIR PAR DÉFAUT", height=50, command=save_printer_choice).pack(pady=30)

        # --- 4. SOUS-ONGLET : OUTILS ---
        ctk.CTkLabel(t_tl, text="MAINTENANCE ET SÉCURITÉ", font=self.f_title).pack(pady=20)
        ctk.CTkButton(t_tl, text="📂 DOSSIER SOURCE", height=55, command=lambda: os.startfile(os.getcwd())).pack(pady=10, fill="x", padx=100)
        ctk.CTkButton(t_tl, text="💾 BACKUP BASE DE DONNÉES", height=55, fg_color=C_OK, command=self.db_backup).pack(pady=10, fill="x", padx=100)
        ctk.CTkButton(t_tl, text="🔄 VÉRIFIER MISE À JOUR", height=55, fg_color=C_INFO, command=UpdateManager.check_update).pack(pady=10, fill="x", padx=100)
        
        # --- 5. SOUS-ONGLET : CONTACT ---
        ctk.CTkLabel(t_ct, text="SUPPORT TECHNIQUE", font=self.f_title).pack(pady=20)
        ctk.CTkLabel(t_ct, text=f"👤 DÉVELOPPEUR : {DEV_NAME}", font=self.f_norm).pack(pady=5)
        ctk.CTkLabel(t_ct, text=f"📧 EMAIL : {DEV_EMAIL}", font=self.f_norm).pack(pady=5)
        ctk.CTkLabel(t_ct, text=f"📞 TÉL : {DEV_PHONE}", font=self.f_norm).pack(pady=5)
        ctk.CTkButton(t_ct, text="🌐 VOIR GITHUB", fg_color=C_SEC, command=lambda: webbrowser.open("https://github.com/doufall")).pack(pady=20)
        
        info_frame = ctk.CTkFrame(t_ct, fg_color="transparent")
        info_frame.pack(pady=10)
        
        ctk.CTkLabel(info_frame, text=f"👤 DÉVELOPPEUR : {DEV_NAME}", font=self.f_norm).pack(pady=5)
        ctk.CTkLabel(info_frame, text=f"📧 EMAIL : {DEV_EMAIL}", font=self.f_norm).pack(pady=5)
        ctk.CTkLabel(info_frame, text=f"📞 TÉL : {DEV_PHONE}", font=self.f_norm).pack(pady=5)
        ctk.CTkLabel(info_frame, text="📍 LIBREVILLE, GABON", font=self.f_norm).pack(pady=5)
        
        ctk.CTkButton(t_ct, text="🌐 VOIR LE SITE WEB", fg_color=C_SEC, command=lambda: webbrowser.open("https://github.com/doufall")).pack(pady=20)

    def init_logs(self):
        f = ctk.CTkFrame(self.t_logs); f.pack(fill="both", expand=True, padx=10, pady=10)
        self.log_tree = ttk.Treeview(f, columns=("Date", "User", "Action", "Détail"), show="headings")
        for c in ("Date", "User", "Action", "Détail"): self.log_tree.heading(c, text=c)
        self.log_tree.pack(fill="both", expand=True)
        self.cur.execute("SELECT timestamp, user, action, detail FROM audit_logs ORDER BY id DESC LIMIT 100")
        for r in self.cur.fetchall(): self.log_tree.insert("", "end", values=r)

    def db_backup(self):
        p = filedialog.asksaveasfilename(defaultextension=".db")
        if p: shutil.copy2(DB_FILE, p); messagebox.showinfo("OK", "Sauvegardé.")

    def close(self):
        if messagebox.askyesno("QUITTER", "Fermer le logiciel ?"):
            self.conn.commit(); self.conn.close(); self.destroy()

# =============================================================================
# LANCEMENT FINAL
# =============================================================================
if __name__ == "__main__":
    if platform.system() == "Windows":
        try: from ctypes import windll; windll.shcore.SetProcessDpiAwareness(1)
        except: pass
    
    lock = check_single_instance()
    if not lock:
        root = ctk.CTk(); root.withdraw()
        messagebox.showerror("ERREUR", "DRINK MANAGER PRO est déjà ouvert !")
        sys.exit(0)
        
    app = DrinkManagerEnterprise()
    app.mainloop()
# %%
