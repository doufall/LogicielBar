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
import json 
from datetime import datetime, timedelta

# --- IMPORT SÉCURISÉ DU CALENDRIER ---
try:
    from tkcalendar import DateEntry
    HAS_CALENDAR = True
except ImportError:
    HAS_CALENDAR = False
    print("Avertissement : tkcalendar non trouvé. Passage en mode texte.")
# =============================================================================
# CONFIGURATION GLOBALE
# =============================================================================
APP_NAME = "DRINK MANAGER PRO"
APP_VERSION = "v41.0" 
DB_FILE = "enterprise_data.db"
PORT_LOCK = 65432 

# INFOS DÉVELOPPEUR
DEV_NAME = "ABDOUL FALL"
DEV_EMAIL = "abdoulfall1293@gmail.com"
DEV_PHONE = "074 00 84 50"

# CONFIGURATION MISE À JOUR
URL_VERSION = "https://raw.githubusercontent.com/doufall/LogicielBar/main/version.txt"

# COULEURS (THÈME EXPERT)
C_PRIM = "#2980b9" # Bleu pro
C_SEC = "#2c3e50"  # Gris foncé
C_ACC = "#1abc9c"  # Turquoise
C_OK = "#27ae60"   # Vert succès
C_ERR = "#c0392b"  # Rouge erreur
C_WARN = "#e67e22" # Orange alerte
C_INFO = "#8e44ad" # Violet info
C_TXT = "#ecf0f1"  # Blanc cassé

# =============================================================================
# MODULES EXTERNES (GESTION DES ERREURS D'IMPORT)
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
def check_single_instance():
    """Empêche le logiciel de s'ouvrir deux fois"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', PORT_LOCK))
        return s 
    except socket.error:
        return None

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
            
            cmd = f'cmd /c timeout /t 2 /nobreak > NUL & del "{current_exe}" & ren "{new_exe_name}" "{current_exe}" & start "" "{current_exe}"'
            subprocess.Popen(cmd, shell=True)
            sys.exit(0)
        except Exception as e:
            messagebox.showerror("ERREUR", f"Echec update auto :\n{e}")

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
        
        # --- MODIFICATION ICI ---
        self.user = None
        self.cart = {}
        self.current_note_name = None  # <--- MÉMOIRE DU NOM DU CLIENT
        self.trial = False
        # ------------------------
        
        self.after(2000, UpdateManager.check_update)
        self.check_lic()

    def safe_int(self, v): 
        try: return int(str(v).strip()) if v else 0
        except: return 0
        
    def clear(self): 
        for w in self.winfo_children(): w.destroy()

    def clear_cart_full(self): 
        """ Vide le panier ET oublie le nom de la note en cours """
        self.cart.clear()
        self.current_note_name = None  # On remet la mémoire à zéro
        self.upd_cart()               # On rafraîchit l'affichage
        print("Panier et mémoire client réinitialisés.")

    def ask_admin(self):
        p = simpledialog.askstring("SÉCURITÉ", "Mot de passe ADMIN :", show="*")
        if not p: return False
        self.cur.execute("SELECT password FROM staff WHERE role='admin' LIMIT 1")
        r = self.cur.fetchone()
        if r and r[0] == p: return True
        messagebox.showerror("REFUSÉ", "Mot de passe incorrect."); return False
    
    

    def init_journal(self):
        for w in self.t_logs.winfo_children(): w.destroy()

        f_filter = ctk.CTkFrame(self.t_logs)
        f_filter.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(f_filter, text="📅 Historique du :", font=("Arial", 14, "bold")).pack(side="left", padx=10)

        # --- UTILISATION DU SYSTÈME SÉCURISÉ ---
        if HAS_CALENDAR:
            self.cal_journal = DateEntry(f_filter, width=12, background='darkblue', 
                                         foreground='white', borderwidth=2, date_pattern='y-mm-dd')
            self.cal_journal.pack(side="left", padx=10)
        else:
            # Si le calendrier a échoué, on met un champ de texte normal
            self.cal_journal = ctk.CTkEntry(f_filter, placeholder_text="AAAA-MM-DD", width=150)
            self.cal_journal.pack(side="left", padx=10)
            self.cal_journal.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ctk.CTkButton(f_filter, text="🔍 FILTRER", width=100, command=self.ref_journal).pack(side="left", padx=5)
        ctk.CTkButton(f_filter, text="TOUT", width=60, fg_color="gray", command=self.ref_journal_all).pack(side="left", padx=5)

        # --- LE TABLEAU (Treeview) ---
        # On utilise encore self.t_logs
        f_tree = ctk.CTkFrame(self.t_logs)
        f_tree.pack(fill="both", expand=True, padx=10, pady=10)

        from tkinter import ttk
        columns = ("date", "user", "action", "detail")
        self.tree_j = ttk.Treeview(f_tree, columns=columns, show="headings")
    
        self.tree_j.heading("date", text="Date & Heure")
        self.tree_j.heading("user", text="Utilisateur")
        self.tree_j.heading("action", text="Action")
        self.tree_j.heading("detail", text="Détails")
    
        self.tree_j.column("date", width=150)
        self.tree_j.column("user", width=100)
        self.tree_j.column("action", width=120)
        self.tree_j.column("detail", width=400)

        self.tree_j.pack(side="left", fill="both", expand=True)
    
        scv = ttk.Scrollbar(f_tree, orient="vertical", command=self.tree_j.yview)
        self.tree_j.configure(yscrollcommand=scv.set)
        scv.pack(side="right", fill="y")

        # Charger les données au démarrage
        self.ref_journal()

    # --- GARDER L'ALIGNEMENT CI-DESSOUS ---

    def ref_journal(self):
        """ Filtre le journal par la date du calendrier """
        try:
            # Gestion de la date selon si c'est DateEntry ou un Entry simple
            if hasattr(self.cal_journal, 'get_date'):
                date_sel = self.cal_journal.get_date().strftime("%Y-%m-%d")
            else:
                date_sel = self.cal_journal.get()
                
            for i in self.tree_j.get_children(): self.tree_j.delete(i)
    
            self.cur.execute("SELECT timestamp, user, action, detail FROM audit_logs WHERE timestamp LIKE ? ORDER BY id DESC", (f"{date_sel}%",))
            for row in self.cur.fetchall():
                self.tree_j.insert("", "end", values=row)
        except Exception as e: 
            print(f"Erreur SQL Journal: {e}")

    def ref_journal_all(self):
        """ Affiche tout sans filtre """
        for i in self.tree_j.get_children(): self.tree_j.delete(i)
        self.cur.execute("SELECT timestamp, user, action, detail FROM audit_logs ORDER BY id DESC LIMIT 500")
        for row in self.cur.fetchall():
            self.tree_j.insert("", "end", values=row)

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
            "CREATE TABLE IF NOT EXISTS settings (cle TEXT PRIMARY KEY, valeur TEXT)",
            # --- LA NOUVELLE TABLE POUR TES CONSOMMATIONS SUIVIES ---
            "CREATE TABLE IF NOT EXISTS notes_ouvertes (id INTEGER PRIMARY KEY, nom_client TEXT, panier_data TEXT, total_provisoire INT)"
        ]
        
        for q in tables: 
            self.cur.execute(q)
        
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
        self.font_sz = int(d.get('font_size', 18))
        self.alert_thr = int(d.get('stock_alert', 5))
        self.sel_print = d.get('printer', '')
        ctk.set_appearance_mode(d.get('theme', 'System'))

    def apply_style(self):
        self.f_title = (self.font_fam, int(self.font_sz * 2.0), "bold")
        self.f_norm = (self.font_fam, int(self.font_sz * 1.2), "bold")
        self.f_small = (self.font_fam, int(self.font_sz), "bold")
        self.f_btn = (self.font_fam, int(self.font_sz * 1.1), "bold")

    # --- SÉCURITÉ ---
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
        # On cherche l'utilisateur dans la table staff
        self.cur.execute("SELECT role FROM staff WHERE username=? AND password=?", (u, p))
        r = self.cur.fetchone()
        
        if r: 
            # 1. On définit l'utilisateur actuel
            self.user = {"name": u, "role": r[0]}
            
            # 2. --- AJOUT TRACABILITÉ ICI ---
            self.tracer("CONNEXION", f"L'utilisateur {u} s'est connecté avec succès.")
            # --------------------------------
            
            self.dash() # On ouvre le tableau de bord
        else: 
            # Optionnel : Tu peux même tracer les tentatives d'échec !
            # self.tracer("ALERTE", f"Tentative de connexion échouée pour : {u}")
            messagebox.showerror("ERREUR", "Nom d'utilisateur ou mot de passe incorrect.")

    # --- CETTE FONCTION DOIT EXISTER ICI ---
    def tracer(self, action, detail):
        try:
            # On utilise les noms exacts de tes colonnes : timestamp, user, action, detail
            dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            u = self.user['name'] if hasattr(self, 'user') else "Système"
            
            self.cur.execute("INSERT INTO audit_logs (timestamp, user, action, detail) VALUES (?,?,?,?)", 
                             (dt, u, action, detail))
            self.conn.commit()
            print(f"DEBUG LOG: {action} enregistré") 
        except Exception as e:
            print(f"Erreur traceur: {e}")
    

    # =============================================================================
    # DASHBOARD
    # =============================================================================
    def dash(self):
        self.clear()
        ctk.set_widget_scaling(1.1)

        self.main_tabs = ctk.CTkTabview(self, height=800, command=self.on_tab_change)
        self.main_tabs.pack(fill="both", expand=True, padx=10, pady=10)
        self.main_tabs._segmented_button.configure(font=self.f_norm, height=50)

        # Création des onglets
        self.t_pos = self.main_tabs.add("CAISSE")
        self.t_inv = self.main_tabs.add("STOCK")

        if self.user["role"] == "admin":
            self.t_stf = self.main_tabs.add("EQUIPE")
            self.t_stat = self.main_tabs.add("RAPPORTS")
            self.t_cfg = self.main_tabs.add("CONFIG")
            self.t_logs = self.main_tabs.add("JOURNAL") # C'est ton onglet t_logs
            
            try: self.init_staff()
            except: pass
            try: self.init_stats()
            except: pass
            try: self.init_cfg()
            except: pass
            try: self.init_logs()
            except: pass

            # --- CORRECTION ICI ---
            try: 
                self.init_journal() # On appelle le nom exact de la fonction
            except Exception as e: 
                print(f"Erreur init journal: {e}")

        self.init_pos()
        self.init_stock()
        self.update_idletasks()

    def on_tab_change(self):
        # Cette fonction se lance automatiquement au clic sur un onglet
        choix = self.main_tabs.get() # Récupère le nom de l'onglet actif
        
        if choix == "CAISSE":
            # Si on clique sur CAISSE, on vide et on recharge les produits
            self.ref_pos()
            
        elif choix == "STOCK":
            self.ref_stock() # Actualise le stock
            
        # --- AJOUTEZ CECI POUR LE JOURNAL ---
        elif choix == "JOURNAL":
            # On vérifie que la fonction existe avant de l'appeler pour éviter les erreurs
            try:
                self.ref_logs() 
            except AttributeError:
                pass # Si la fonction n'est pas encore créée, on ne fait rien
        
    # Exemple de fonction ref_stock (à adapter à votre code)
    def ref_stock(self):
      # Cette fonction sert juste de raccourci vers votre vraie fonction
        self.ref_stock_ui()

    # =============================================================================
    # MODULE CAISSE (POS)
    # =============================================================================
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

        # --- NOUVEAU : CADRE POUR LES NOTES EN ATTENTE ---
        f_notes = ctk.CTkFrame(rf, fg_color="transparent")
        f_notes.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(f_notes, text="📥 EN ATTENTE", fg_color="#f39c12", height=50, 
                      font=("Arial", 14, "bold"), command=self.save_note).pack(side="left", fill="x", expand=True, padx=(0,2))
        
        ctk.CTkButton(f_notes, text="📂 RAPPELER", fg_color="#3498db", height=50, 
                      font=("Arial", 14, "bold"), command=self.list_notes).pack(side="left", fill="x", expand=True, padx=(2,0))
        # ------------------------------------------------
        
        ctk.CTkButton(rf, text="ENCAISSER (PAYER)", fg_color=C_OK, height=80, font=("Arial", 20, "bold"), command=self.pay).pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(rf, text="VIDER PANIER", fg_color=C_ERR, height=50, font=self.f_norm,command=self.clear_cart_full).pack(fill="x", padx=10, pady=5)
        self.ref_pos()
    
    
    
    
    def ref_pos(self):
        for w in self.gp.winfo_children():
            w.destroy()

        q = "SELECT name, sell_price, stock_qty FROM products WHERE name LIKE ?"
        p = [f"%{self.eps.get()}%"]

        if self.ecf.get() != "TOUT":
            q += " AND category=?"
            p.append(self.ecf.get())

        produits = list(self.cur.execute(q, p))

        colonnes = 7   # Nombre de colonnes
        row = 0
        col = 0

        for n, pr, qt in produits:
            c = C_PRIM if qt > self.alert_thr else (C_WARN if qt > 0 else "gray")

            btn = ctk.CTkButton(
                self.gp,
                text=f"{n}\n{pr} F\n(Stock: {qt})",
                fg_color=c,
                width=130,
                height=120,
                font=("Arial", 14, "bold"),
                command=lambda x=n, y=pr, z=qt: self.add_c(x, y, z)
            )
            
            # --- CORRECTION ICI : Tout ceci doit être ALIGNÉ (indenté) dans le for ---
            btn.grid(row=row, column=col, padx=5, pady=5)

            col += 1
            if col >= colonnes:
                col = 0
                row += 1
    





    def add_c(self, n, p, mq):
        if mq <= 0: return
        cur = self.cart.get(n, {'q': 0, 'p': p})
        if cur['q'] < mq: cur['q'] += 1; self.cart[n] = cur; self.upd_cart()

    def upd_cart(self):
        for w in self.cv.winfo_children(): w.destroy()
        t = 0
        for n, d in self.cart.items():
            s = d['q'] * d['p']; t += s
            r = ctk.CTkFrame(self.cv, height=50); r.pack(fill="x", pady=2)
            ctk.CTkLabel(r, text=f"{n}", font=self.f_small, width=150, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(r, text=f"x{d['q']}", font=self.f_norm, text_color=C_WARN).pack(side="left", padx=5)
            ctk.CTkButton(r, text="X", width=40, fg_color=C_ERR, command=lambda x=n: (self.cart.pop(x), self.upd_cart())).pack(side="right")
            ctk.CTkLabel(r, text=f"{s} F", font=self.f_norm).pack(side="right", padx=10)
            # --- MODIFICATION ICI : Affichage du nom de la note ---
        if self.current_note_name:
            self.lt.configure(text=f"[{self.current_note_name}] TOTAL: {t} FCFA", text_color="#f39c12")
        else:
            self.lt.configure(text=f"TOTAL: {t} FCFA", text_color=C_OK)

        self.lt.configure(text=f"TOTAL: {t} FCFA")

    def pay(self):
        # 1. Sécurité : Panier vide ?
        if not self.cart: return
        
        # 2. Calcul du Total
        tot = sum(d['q'] * d['p'] for d in self.cart.values())
        
        # 3. Création de la belle fenêtre
        w = ctk.CTkToplevel(self)
        w.geometry("500x700") # Plus haute pour les boutons
        w.title("ENCAISSEMENT")
        w.grab_set()   # Bloque les autres fenêtres
        w.focus_force()
        
        # --- Cadre Principal ---
        main_f = ctk.CTkFrame(w, fg_color="transparent")
        main_f.pack(fill="both", expand=True, padx=20, pady=20)

        # A. Affichage du TOTAL (Gros et Vert)
        ctk.CTkLabel(main_f, text="TOTAL À PAYER", font=("Arial", 16, "bold")).pack(pady=(10, 0))
        lbl_tot = ctk.CTkLabel(main_f, text=f"{tot} FCFA", font=("Arial", 50, "bold"), text_color=C_OK)
        lbl_tot.pack(pady=10)
        
        ctk.CTkLabel(main_f, text="REÇU (ESPÈCES)", font=("Arial", 16)).pack(pady=(20, 0))
        
        # B. Champ de saisie (Connecté au calcul automatique)
        ec = ctk.CTkEntry(main_f, justify="center", font=("Arial", 30), height=60, placeholder_text="0")
        ec.pack(fill="x", pady=10)
        ec.focus() # Le curseur se met direct dedans

        # C. Zone d'affichage du RENDU en temps réel
        lbl_rendu = ctk.CTkLabel(main_f, text="RENDU : 0 FCFA", font=("Arial", 25, "bold"), text_color="gray")
        lbl_rendu.pack(pady=10)

        # --- FONCTION INTERNE : Calcul en direct ---
        def calcul_rendu(event=None):
            try:
                # On essaie de lire le montant reçu
                valeur_recu = ec.get()
                if not valeur_recu: recu = 0
                else: recu = int(valeur_recu)

                rendu = recu - tot
                
                # Changement de couleur selon si c'est assez ou pas
                if rendu < 0:
                    lbl_rendu.configure(text=f"MANQUE : {abs(rendu)} FCFA", text_color="#e74c3c") # Rouge
                else:
                    lbl_rendu.configure(text=f"RENDU : {rendu} FCFA", text_color=C_OK) # Vert
            except:
                lbl_rendu.configure(text="...", text_color="gray")

        # On attache le calcul à chaque touche du clavier
        ec.bind("<KeyRelease>", calcul_rendu)

        # --- D. BOUTONS RAPIDES (Billets) ---
        frame_billets = ctk.CTkFrame(main_f, fg_color="transparent")
        frame_billets.pack(fill="x", pady=10)
        
        def set_cash(amount):
            ec.delete(0, "end")
            ec.insert(0, str(amount))
            calcul_rendu() # On force le calcul
            
        # Liste des boutons
        billets = [2000, 5000, 10000]
        for b in billets:
            ctk.CTkButton(frame_billets, text=f"{b}", width=80, height=45, fg_color="#34495e", 
                          font=("Arial", 14, "bold"),
                          command=lambda x=b: set_cash(x)).pack(side="left", padx=5, expand=True)
            
        # Bouton "Compte Rond" (Montant exact)
        ctk.CTkButton(frame_billets, text="EXACT", width=80, height=45, fg_color="#2980b9", 
                      font=("Arial", 14, "bold"),
                      command=lambda: set_cash(tot)).pack(side="left", padx=5, expand=True)
            # --- E. LA FONCTION DE VALIDATION (C'est elle qui manquait !) ---
        # --- E. FONCTION DE VALIDATION AVEC DOUBLE IMPRESSION ET COUPE ---
        def val(event=None):
            try:
                # 1. Vérification de la saisie
                res_saisie = ec.get().strip()
                r = int(res_saisie) if res_saisie else 0
                if r < tot: 
                    messagebox.showerror("ERREUR", "Montant insuffisant !"); return
                
                # 2. Enregistrement Base de données
                dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.cur.execute("INSERT INTO sales_header (date_time, total_price, user_name) VALUES (?,?,?)", 
                                 (dt, tot, self.user['name']))
                sid = self.cur.lastrowid
                
                # --- CONSTRUCTION DU STYLE DU TICKET ---
                sep = "-" * 42 + "\n"
                double_sep = "=" * 42 + "\n"
                cut_command = "\x1d\x56\x42\x00" # Code ESC/POS pour la découpe automatique
                
                # En-tête
                header = f"{self.store_name.center(42)}\n"
                header += f"Ticket #{sid}\n"
                header += f"Date: {dt}\n"
                header += f"Caissier: {self.user['name'].upper()}\n"
                header += sep
                header += f"{'PRODUIT':<20} {'QTE':<5} {'TOTAL':>15}\n"
                header += sep
                
                # Corps (Produits)
                body = ""
                for n, d in self.cart.items():
                    self.cur.execute("INSERT INTO sales_lines (sale_id, prod_name, qty, unit_price) VALUES (?,?,?,?)", 
                                     (sid, n, d['q'], d['p']))
                    self.cur.execute("UPDATE products SET stock_qty=stock_qty-? WHERE name=?", (d['q'], n))
                    self.cur.execute("INSERT INTO stock_movements (date,prod_name,qty,type,user) VALUES (?,?,?,?,?)", 
                                     (dt, n, d['q'], "VENTE", self.user['name']))
                    
                    line_total = d['q'] * d['p']
                    body += f"{n[:19]:<20} x{d['q']:<4} {line_total:>15}F\n"
                
                # Pied de ticket
                rendu = r - tot
                footer = sep
                footer += f"TOTAL A PAYER : {tot:>20} F\n"
                footer += f"MONTANT RECU  : {r:>20} F\n"
                footer += f"RENDU         : {rendu:>20} F\n"
                footer += double_sep
                footer += "MERCI DE VOTRE VISITE !\n".center(42)
                footer += "\n\n\n\n\n" # Espaces pour que le texte dépasse la lame
                footer += cut_command
                
                # 3. DOUBLE IMPRESSION SUCCESSIVE
                if self.sel_print:
                    try:
                        # --- PREMIER TICKET : CLIENT ---
                        ticket_client = f"{'*** COPIE CLIENT ***'.center(42)}\n" + header + body + footer
                        PrinterManager.print_ticket(self.sel_print, ticket_client)
                        
                        # --- DEUXIÈME TICKET : CAISSE (après 1.5 seconde) ---
                        def second_print():
                            ticket_caisse = f"{'*** COPIE CAISSE ***'.center(42)}\n" + header + body + footer
                            PrinterManager.print_ticket(self.sel_print, ticket_caisse)
                        
                        self.after(1500, second_print)
                        
                    except Exception as e:
                        print(f"Erreur imprimante : {e}")

                # 4. Journal et Finalisation
                self.tracer("VENTE", f"Ticket #{sid} encaissé - Total: {tot} F")
                self.conn.commit()

                messagebox.showinfo("SUCCÈS", f"✅ Paiement validé !\n\n➡️ RENDRE : {rendu} FCFA")
                
                # 5. Nettoyage Interface
                self.cart = {}
                self.upd_cart()
                self.ref_pos()   
                self.gp.update() 
                w.destroy()

            except Exception as e:
                messagebox.showerror("ERREUR", f"Erreur lors de la vente : {e}")

        # --- F. CRÉATION DU BOUTON PHYSIQUE ---
        btn_val = ctk.CTkButton(main_f, text="VALIDER LE PAIEMENT", height=70, fg_color=C_OK, 
                                font=("Arial", 20, "bold"), command=val)
        btn_val.pack(side="bottom", fill="x", pady=10)
        
        # Raccourci touche Entrée
        w.bind('<Return>', val)

    def save_note(self):
        if not self.cart: return
        
        # 1. Déterminer le nom (demander si nouveau, sinon utiliser la mémoire)
        if not self.current_note_name:
            nom = ctk.CTkInputDialog(text="Nom du client / Table :", title="Mise en attente").get_input()
            if not nom or not nom.strip(): return
            self.current_note_name = nom.strip().upper()

        try:
            panier_json = json.dumps(self.cart)
            total = sum(d['q'] * d['p'] for d in self.cart.values())
            
            # 2. Vérifier si cette note existe déjà dans la BDD pour ce nom
            self.cur.execute("SELECT id FROM notes_ouvertes WHERE nom_client=?", (self.current_note_name,))
            existe = self.cur.fetchone()
            
            if existe:
                # Mise à jour de la note existante
                self.cur.execute("UPDATE notes_ouvertes SET panier_data=?, total_provisoire=? WHERE nom_client=?",
                                 (panier_json, total, self.current_note_name))
            else:
                # Création d'une nouvelle note
                self.cur.execute("INSERT INTO notes_ouvertes (nom_client, panier_data, total_provisoire) VALUES (?,?,?)",
                                 (self.current_note_name, panier_json, total))
            
            self.conn.commit()
            self.tracer("NOTE", f"Note '{self.current_note_name}' mise en attente.")
            
            # 3. Réinitialisation complète pour le client suivant
            self.clear_cart_full() 
            messagebox.showinfo("OK", "Commande mise en attente !")
            
        except Exception as e:
            messagebox.showerror("ERREUR", f"Erreur note : {e}")

    def list_notes(self):
        """ Affiche la liste des notes à reprendre """
        self.cur.execute("SELECT id, nom_client, total_provisoire FROM notes_ouvertes")
        notes = self.cur.fetchall()
        
        if not notes:
            messagebox.showinfo("INFO", "Aucune note en attente.")
            return

        w = ctk.CTkToplevel(self)
        w.title("NOTES EN ATTENTE")
        w.geometry("450x550")
        w.grab_set()

        ctk.CTkLabel(w, text="CHOISIR UNE NOTE À REPRENDRE", font=("Arial", 16, "bold")).pack(pady=15)
        
        container = ctk.CTkScrollableFrame(w)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        for id_n, nom, tot in notes:
            f = ctk.CTkFrame(container)
            f.pack(fill="x", pady=5)
            
            ctk.CTkLabel(f, text=f"👤 {nom}", font=("Arial", 14, "bold")).pack(side="left", padx=10, pady=10)
            ctk.CTkLabel(f, text=f"{tot} F", text_color=C_OK).pack(side="left", padx=10)
            
            def reprendre(idx=id_n, n_client=nom): # On ajoute le nom en argument
                self.cur.execute("SELECT panier_data FROM notes_ouvertes WHERE id=?", (idx,))
                data = self.cur.fetchone()[0]
                
                self.cart = json.loads(data)
                self.current_note_name = n_client # <--- ON GARDE LE NOM EN MÉMOIRE
                
                # On ne supprime plus forcément la note tout de suite, 
                # ou on la supprime mais self.current_note_name s'en souvient.
                self.cur.execute("DELETE FROM notes_ouvertes WHERE id=?", (idx,))
                self.conn.commit()
                
                self.upd_cart()
                w.destroy()

            ctk.CTkButton(f, text="REPRENDRE", width=100, command=reprendre).pack(side="right", padx=10)    

    # =============================================================================
    # MODULE STOCK EXPERT (V31.0)
    # =============================================================================
    def init_stock(self):
        # 1. En-tête et Actions Rapides
        tf = ctk.CTkFrame(self.t_inv); tf.pack(fill="x", padx=10, pady=10)
        
        # Bouton Création
        c1 = ctk.CTkFrame(tf)
        c1.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkLabel(c1, text="NOUVEAU PRODUIT", font=self.f_small, text_color=C_INFO).pack(pady=5)
        btn_new = ctk.CTkButton(c1, text="+ CRÉER FICHE", height=40, fg_color=C_INFO, command=self.open_new_prod_window)
        btn_new.pack(pady=10, padx=10, fill="x")

        # Bouton Entrée Rapide
        c2 = ctk.CTkFrame(tf)
        c2.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkLabel(c2, text="ENTRÉE STOCK", font=self.f_small, text_color=C_OK).pack(pady=5)
        self.cb_quick_in = ctk.CTkComboBox(c2, values=[], height=35)
        self.cb_quick_in.pack(pady=2, padx=10, fill="x")
        self.en_quick_in = ctk.CTkEntry(c2, placeholder_text="Quantité", height=35)
        self.en_quick_in.pack(pady=2, padx=10, fill="x")
        ctk.CTkButton(c2, text="VALIDER", height=35, fg_color=C_OK, command=self.quick_add_stock).pack(pady=5, padx=10)

        # 2. Tableau de Bord avec Couleurs
        table_frame = ctk.CTkFrame(self.t_inv)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        leg = ctk.CTkFrame(table_frame, height=30, fg_color="transparent"); leg.pack(fill="x", pady=5)
        ctk.CTkLabel(leg, text="LÉGENDE : ", font=("Arial", 12, "bold")).pack(side="left")
        ctk.CTkLabel(leg, text=" ■ RUPTURE (0) ", text_color="#e74c3c", font=("Arial", 12, "bold")).pack(side="left")
        ctk.CTkLabel(leg, text=" ■ ALERTE (≤5) ", text_color="#e67e22", font=("Arial", 12, "bold")).pack(side="left")
        ctk.CTkLabel(leg, text=" ■ NORMAL ", text_color="#2ecc71", font=("Arial", 12, "bold")).pack(side="left")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2c3e50", foreground="white", fieldbackground="#2c3e50", rowheight=35, font=("Arial", 12))
        style.configure("Treeview.Heading", font=("Arial", 13, "bold"), background="#2980b9", foreground="white")
        style.map("Treeview", background=[("selected", "#3498db")])
        
        self.tree_stock = ttk.Treeview(table_frame, columns=("Nom", "Cat", "PA", "PV", "Stock"), show="headings")
        self.tree_stock.heading("Nom", text="PRODUIT"); self.tree_stock.heading("Cat", text="CATÉGORIE")
        self.tree_stock.heading("PA", text="P. ACHAT"); self.tree_stock.heading("PV", text="P. VENTE")
        self.tree_stock.heading("Stock", text="STOCK ACTUEL")
        
        self.tree_stock.column("Nom", width=250); self.tree_stock.column("Cat", width=150, anchor="center")
        self.tree_stock.column("PA", width=100, anchor="center"); self.tree_stock.column("PV", width=100, anchor="center")
        self.tree_stock.column("Stock", width=100, anchor="center")
        
        self.tree_stock.tag_configure("rupture", foreground="#e74c3c", background="#4a2323")
        self.tree_stock.tag_configure("alerte", foreground="#e67e22", background="#4a3b23")
        self.tree_stock.tag_configure("normal", foreground="white")

        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree_stock.yview)
        self.tree_stock.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree_stock.pack(fill="both", expand=True)
        self.tree_stock.bind("<Double-1>", self.on_stock_double_click)

        bf = ctk.CTkFrame(self.t_inv, fg_color="transparent"); bf.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(bf, text="ACTUALISER LISTE", command=self.ref_stock_ui).pack(side="left")
        ctk.CTkLabel(bf, text="Double-cliquez sur un produit pour le gérer", text_color="gray").pack(side="right")

        self.ref_stock_ui()

    def ref_stock_ui(self):
        try:
            prods = [r[0] for r in self.cur.execute("SELECT name FROM products ORDER BY name ASC")]
            self.cb_quick_in.configure(values=prods)
        except: pass

        for i in self.tree_stock.get_children(): self.tree_stock.delete(i)
        
        self.cur.execute("SELECT name, category, buy_price, sell_price, stock_qty FROM products ORDER BY name ASC")
        for row in self.cur.fetchall():
            nom, cat, pa, pv, qty = row
            tag = "normal"
            if qty == 0: tag = "rupture"
            elif qty <= self.alert_thr: tag = "alerte"
            self.tree_stock.insert("", "end", values=(nom, cat, f"{pa} F", f"{pv} F", qty), tags=(tag,))

    def open_new_prod_window(self):
        if not self.ask_admin(): return
        w = ctk.CTkToplevel(self); w.geometry("400x500"); w.title("NOUVEAU PRODUIT")
        w.grab_set(); w.focus_force()
        ctk.CTkLabel(w, text="CRÉATION FICHE", font=self.f_title).pack(pady=20)
        en = ctk.CTkEntry(w, placeholder_text="Nom du produit (ex: COCA)", width=300); en.pack(pady=10)
        ec = ctk.CTkComboBox(w, values=[r[0] for r in self.cur.execute("SELECT name FROM categories")], width=300); ec.pack(pady=10)
        epa = ctk.CTkEntry(w, placeholder_text="Prix Achat (ex: 500)", width=300); epa.pack(pady=10)
        epv = ctk.CTkEntry(w, placeholder_text="Prix Vente (ex: 1000)", width=300); epv.pack(pady=10)
        def save():
            n = en.get().strip().upper()
            if not n: return
            try:
                pa = self.safe_int(epa.get())
                pv = self.safe_int(epv.get())
                self.cur.execute("INSERT INTO products (name, category, buy_price, sell_price, stock_qty) VALUES (?,?,?,?,0)", 
                                 (n, ec.get(), pa, pv))
                self.conn.commit()
                
                # --- TRACABILITÉ ---
                self.tracer("CRÉATION", f"Nouveau produit créé : {n} (Achat: {pa}F, Vente: {pv}F)")
                
                self.ref_stock_ui(); self.ref_pos()
                messagebox.showinfo("OK", f"{n} a été créé avec succès !"); w.destroy()
            except Exception as e: messagebox.showerror("ERREUR", f"Impossible de créer :\n{e}")
            
        ctk.CTkButton(w, text="ENREGISTRER", width=300, height=50, fg_color=C_OK, command=save).pack(pady=30)

    def on_stock_double_click(self, event):
        item = self.tree_stock.selection()
        if not item: return
        self.open_manage_window(self.tree_stock.item(item)["values"][0])

    def open_manage_window(self, nom_prod):
        if not self.ask_admin(): return
        self.cur.execute("SELECT * FROM products WHERE name=?", (nom_prod,))
        data = self.cur.fetchone()
        if not data: return
        pid, name, cat, pv, pa, qty, alert = data
        w = ctk.CTkToplevel(self); w.geometry("500x700"); w.title(f"GESTION : {name}"); w.grab_set(); w.focus_force()
        
        ctk.CTkLabel(w, text=f"{name}", font=("Arial", 24, "bold"), text_color=C_PRIM).pack(pady=(20,5))
        ctk.CTkLabel(w, text=f"Catégorie : {cat}", text_color="gray").pack()
        
        stk_color = C_ERR if qty == 0 else (C_WARN if qty <= self.alert_thr else C_OK)
        f_stk = ctk.CTkFrame(w, fg_color=stk_color, corner_radius=20)
        f_stk.pack(pady=20, padx=50, fill="x")
        ctk.CTkLabel(f_stk, text=f"{qty}", font=("Arial", 60, "bold"), text_color="white").pack(pady=10)
        ctk.CTkLabel(f_stk, text="EN STOCK", text_color="white", font=("Arial", 12, "bold")).pack(pady=(0,10))

        tab = ctk.CTkTabview(w, height=300); tab.pack(fill="both", padx=20, pady=10)
        t_mouv = tab.add("MOUVEMENTS"); t_prix = tab.add("MODIFIER PRIX"); t_danger = tab.add("ZONE DANGER")
        
        ctk.CTkLabel(t_mouv, text="Sélectionnez une action :").pack(pady=5)
        act_var = ctk.StringVar(value="ENTREE")
        ctk.CTkSegmentedButton(t_mouv, values=["ENTREE", "PERTE", "OFFRE"], variable=act_var).pack(pady=5)
        e_qty = ctk.CTkEntry(t_mouv, placeholder_text="Quantité", width=200, font=("Arial", 18), justify="center"); e_qty.pack(pady=10)
        e_motif = ctk.CTkEntry(t_mouv, placeholder_text="Motif (si perte/offre)", width=200); e_motif.pack(pady=5)
        
        def valider_mouv():
            q = self.safe_int(e_qty.get())
            if q <= 0: return
            action = act_var.get()
            motif = e_motif.get()
            new_qty = qty + q if action == "ENTREE" else qty - q
            
            self.cur.execute("UPDATE products SET stock_qty=? WHERE name=?", (new_qty, name))
            self.cur.execute("INSERT INTO stock_movements (date,prod_name,qty,type,reason_or_ref,user) VALUES (?,?,?,?,?,?)", 
                             (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), name, q, action, motif, self.user['name']))
            self.conn.commit()
            
            # --- TRACABILITÉ ---
            # Enregistre l'action précise dans le journal (PERTE, OFFRE ou ENTREE)
            self.tracer(action, f"Produit: {name} | Qté: {q} | Motif: {motif}")
            
            self.ref_stock_ui(); w.destroy(); messagebox.showinfo("OK", f"Stock mis à jour : {new_qty}")

        ctk.CTkButton(t_mouv, text="VALIDER LE MOUVEMENT", fg_color=C_PRIM, height=40, command=valider_mouv).pack(pady=20)

        ctk.CTkLabel(t_prix, text="Prix Achat :").pack()
        epa_new = ctk.CTkEntry(t_prix, justify="center"); epa_new.insert(0, str(pa)); epa_new.pack(pady=5)
        ctk.CTkLabel(t_prix, text="Prix Vente :").pack()
        epv_new = ctk.CTkEntry(t_prix, justify="center"); epv_new.insert(0, str(pv)); epv_new.pack(pady=5)


        def update_prices():
            new_pa = self.safe_int(epa_new.get())
            new_pv = self.safe_int(epv_new.get())
            self.cur.execute("UPDATE products SET buy_price=?, sell_price=? WHERE name=?", (new_pa, new_pv, name))
            self.conn.commit()
            
            # --- TRACABILITÉ ---
            self.tracer("PRIX", f"Changement prix {name} -> Achat: {new_pa}F, Vente: {new_pv}F")
            
            self.ref_stock_ui(); self.ref_pos(); messagebox.showinfo("OK", "Prix modifiés"); w.destroy()

        ctk.CTkButton(t_prix, text="SAUVEGARDER PRIX", fg_color=C_INFO, command=update_prices).pack(pady=20)

        ctk.CTkLabel(t_danger, text="Actions irréversibles", text_color=C_ERR).pack(pady=20)
     
        # --- ONGLET ZONE DANGER (CORRECTION & SUPPRESSION) ---
        ctk.CTkLabel(t_danger, text="--- RECTIFICATION DE STOCK ---", text_color=C_WARN, font=("Arial", 12, "bold")).pack(pady=(10, 5))
        ctk.CTkLabel(t_danger, text="Utilisez ceci uniquement pour corriger une erreur de saisie.", font=("Arial", 10), text_color="gray").pack()
        
        e_rectif = ctk.CTkEntry(t_danger, placeholder_text=f"Nouvelle quantité exacte", width=200, justify="center")
        e_rectif.pack(pady=10)

        def rectifier_stock():
            val_saisie = e_rectif.get().strip()
            if not val_saisie: return
            nouvelle_q = self.safe_int(val_saisie)
            
            if messagebox.askyesno("CONFIRMATION", f"Forcer le stock de {name} à {nouvelle_q} ?\n(Ancien: {qty} -> Nouveau: {nouvelle_q})"):
                self.cur.execute("UPDATE products SET stock_qty=? WHERE name=?", (nouvelle_q, name))
                self.tracer("RECTIFICATION", f"Stock {name} forcé de {qty} vers {nouvelle_q}")
                self.conn.commit(); self.ref_stock_ui(); messagebox.showinfo("OK", "Stock rectifié !"); w.destroy()

        ctk.CTkButton(t_danger, text="RECTIFIER MANUELLEMENT", fg_color="#d35400", command=rectifier_stock).pack(pady=5)

        ctk.CTkLabel(t_danger, text="--------------------------------", text_color="gray").pack(pady=10)

        def delete_prod():
            if messagebox.askyesno("DANGER", f"Voulez-vous vraiment supprimer {name} ?"):
                self.cur.execute("DELETE FROM products WHERE name=?", (name,))
                self.conn.commit()
                
                # --- TRACABILITÉ ---
                self.tracer("SUPPRESSION", f"Le produit {name} a été supprimé définitivement.")
                
                self.ref_stock_ui(); self.ref_pos(); w.destroy()


        ctk.CTkButton(t_danger, text="SUPPRIMER LE PRODUIT", fg_color=C_ERR, command=delete_prod).pack()

    def quick_add_stock(self):
        if not self.ask_admin(): return
        p = self.cb_quick_in.get()
        q = self.safe_int(self.en_quick_in.get())
        
        if p and q > 0:
            # 1. Mise à jour du stock
            self.cur.execute("UPDATE products SET stock_qty=stock_qty+? WHERE name=?", (q, p))
            
            # 2. Historique des mouvements (Table stock_movements)
            self.cur.execute("INSERT INTO stock_movements (date,prod_name,qty,type,user) VALUES (?,?,?,?,?)", 
                             (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), p, q, "ENTREE", self.user['name']))
            
            self.conn.commit()
            
            # --- AJOUT TRACABILITÉ POUR LE JOURNAL ---
            self.tracer("STOCK_ENTREE", f"L'utilisateur {self.user['name']} a ajouté +{q} unités de {p}")
            # ------------------------------------------

            # 3. Rafraîchissement interface
            self.ref_stock_ui()
            self.en_quick_in.delete(0, 'end')
            messagebox.showinfo("OK", f"Ajouté +{q} à {p}")

    # =============================================================================
    # GESTION ÉQUIPE (STAFF)
    # =============================================================================
    def init_staff(self):
        f = ctk.CTkFrame(self.t_stf); f.pack(fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(f, text="GESTION DU PERSONNEL", font=self.f_title).pack(pady=10)
        self.staff_tree = ttk.Treeview(f, columns=("Username", "Role"), show="headings")
        self.staff_tree.heading("Username", text="Utilisateur"); self.staff_tree.heading("Role", text="Rôle")
        self.staff_tree.pack(fill="both", expand=True, pady=10)
        bf = ctk.CTkFrame(f); bf.pack(pady=10)
        ctk.CTkButton(bf, text="AJOUTER MEMBRE", height=45, command=self.add_staff).pack(side="left", padx=5)
        ctk.CTkButton(bf, text="SUPPRIMER", height=45, fg_color=C_ERR, command=self.del_staff).pack(side="left", padx=5)
        self.refresh_staff()

    def refresh_staff(self):
        for i in self.staff_tree.get_children(): self.staff_tree.delete(i)
        self.cur.execute("SELECT username, role FROM staff")
        for row in self.cur.fetchall(): self.staff_tree.insert("", "end", values=row)

    def add_staff(self):
        u = simpledialog.askstring("USER", "Nom d'utilisateur :"); p = simpledialog.askstring("PASS", "Mot de passe :", show='*'); r = simpledialog.askstring("ROLE", "Rôle (admin/caissier) :")
        if u and p and r:
            try: self.cur.execute("INSERT INTO staff VALUES (?,?,?)", (u.lower(), p, r.lower())); self.conn.commit(); self.refresh_staff(); messagebox.showinfo("OK", "Utilisateur créé !")
            except: messagebox.showerror("ERREUR", "L'utilisateur existe déjà.")

    def del_staff(self):
        sel = self.staff_tree.focus()
        if not sel: return
        user = self.staff_tree.item(sel)["values"][0]
        if user == "admin": messagebox.showwarning("NON", "Impossible de supprimer l'admin principal."); return
        if messagebox.askyesno("CONFIRMER", f"Supprimer {user} ?"): self.cur.execute("DELETE FROM staff WHERE username=?", (user,)); self.conn.commit(); self.refresh_staff()

    # =============================================================================
    # RAPPORTS ET STATISTIQUES (VERSION V31)
    # =============================================================================
    def init_stats(self):
        f = ctk.CTkFrame(self.t_stat); f.pack(fill="both", expand=True, padx=10, pady=10)
        qf = ctk.CTkFrame(f); qf.pack(fill="x", pady=5)
        ctk.CTkLabel(qf, text="📊 TABLEAU DE BORD FINANCIER & STOCK", font=self.f_norm, text_color=C_INFO).pack(pady=10)
        
        # KPI ROW 1
        r1 = ctk.CTkFrame(qf, fg_color="transparent"); r1.pack(fill="x", pady=2)
        def low_stk():
            self.cur.execute("SELECT name, stock_qty FROM products WHERE stock_qty <= ?", (self.alert_thr,))
            res = self.cur.fetchall()
            msg = "✅ Stock OK" if not res else "⚠️ RUPTURE :\n\n" + "\n".join([f"- {r[0]} ({r[1]})" for r in res])
            messagebox.showwarning("ALERTES", msg)
        ctk.CTkButton(r1, text="📉 STOCK BAS", height=50, fg_color=C_ERR, command=low_stk).pack(side="left", fill="x", expand=True, padx=2)
        def ca_month():
            m = datetime.now().strftime("%Y-%m")
            self.cur.execute("SELECT SUM(total_price) FROM sales_header WHERE date_time LIKE ?", (m+"%",))
            r = self.cur.fetchone()[0] or 0
            messagebox.showinfo("CA MOIS", f"💰 CA du mois : {r} FCFA")
        ctk.CTkButton(r1, text="💰 CA MOIS", height=50, fg_color=C_OK, command=ca_month).pack(side="left", fill="x", expand=True, padx=2)
        def profit_calc():
            self.cur.execute("SELECT SUM((p.sell_price - p.buy_price) * sl.qty) FROM sales_lines sl JOIN products p ON sl.prod_name = p.name")
            res = self.cur.fetchone()[0] or 0
            messagebox.showinfo("BÉNÉFICE", f"💎 Marge estimée : {res} FCFA")
        ctk.CTkButton(r1, text="💎 BÉNÉFICE", height=50, fg_color="#8e44ad", command=profit_calc).pack(side="left", fill="x", expand=True, padx=2)

        # KPI ROW 2
        r2 = ctk.CTkFrame(qf, fg_color="transparent"); r2.pack(fill="x", pady=2)
        def val_stock():
            self.cur.execute("SELECT SUM(stock_qty * buy_price) FROM products")
            res = self.cur.fetchone()[0] or 0
            messagebox.showinfo("VALEUR STOCK", f"🏦 Valeur Marchande : {res} FCFA")
        ctk.CTkButton(r2, text="🏦 VALEUR STOCK", height=50, fg_color="#2980b9", command=val_stock).pack(side="left", fill="x", expand=True, padx=2)
        def top_prod():
            self.cur.execute("SELECT prod_name, SUM(qty) as s FROM sales_lines GROUP BY prod_name ORDER BY s DESC LIMIT 1")
            r = self.cur.fetchone()
            msg = f"🏆 Top Produit : {r[0]} ({r[1]} ventes)" if r else "Aucune vente"
            messagebox.showinfo("TOP VENTES", msg)
        ctk.CTkButton(r2, text="🏆 TOP PRODUIT", height=50, fg_color=C_WARN, command=top_prod).pack(side="left", fill="x", expand=True, padx=2)
        def top_vendeur():
            self.cur.execute("SELECT user_name, SUM(total_price) FROM sales_header GROUP BY user_name ORDER BY 2 DESC LIMIT 1")
            r = self.cur.fetchone()
            msg = f"🥇 Meilleur Vendeur : {str(r[0]).upper()} ({r[1]} F)" if r else "Néant"
            messagebox.showinfo("STAFF", msg)
        ctk.CTkButton(r2, text="🥇 TOP VENDEUR", height=50, fg_color="#f39c12", command=top_vendeur).pack(side="left", fill="x", expand=True, padx=2)

        # Date & Print
        rf = ctk.CTkFrame(f); rf.pack(fill="x", pady=10)
        ctk.CTkLabel(rf, text="🖨️ IMPRESSIONS", font=("Arial", 14, "bold")).pack(side="left", padx=10)
        self.d1 = ctk.CTkEntry(rf, width=120, height=40); self.d1.pack(side="left", padx=2)
        ctk.CTkButton(rf, text="📅", width=40, command=lambda: MauricetteCalendar(self, lambda d: (self.d1.delete(0, 'end'), self.d1.insert(0, d)))).pack(side="left")
        self.d2 = ctk.CTkEntry(rf, width=120, height=40); self.d2.pack(side="left", padx=2)
        ctk.CTkButton(rf, text="📅", width=40, command=lambda: MauricetteCalendar(self, lambda d: (self.d2.delete(0, 'end'), self.d2.insert(0, d)))).pack(side="left")
        
        def rep_per():
            d_start = self.d1.get()
            d_end = self.d2.get()
            
            if not d_start or not d_end:
                messagebox.showwarning("ERREUR", "Veuillez choisir deux dates.")
                return
            
            # 1. Requête SQL pour les ventes
            q = """SELECT prod_name, SUM(qty), SUM(qty*unit_price) 
                   FROM sales_lines 
                   JOIN sales_header ON sales_lines.sale_id = sales_header.id 
                   WHERE date_time BETWEEN ? AND ? 
                   GROUP BY prod_name 
                   ORDER BY SUM(qty*unit_price) DESC"""
            
            self.cur.execute(q, (d_start + " 00:00:00", d_end + " 23:59:59"))
            rows = self.cur.fetchall()
            
            if not rows:
                messagebox.showinfo("INFO", "Aucune vente sur cette période.")
                return

            # 2. Construction du Ticket (Formaté pour 42 caractères)
            sep = "-" * 42 + "\n"
            t = f"{self.store_name.center(42)}\n"
            t += f"RAPPORT DE PERIODE\n".center(42)
            t += f"Du {d_start} au {d_end}\n".center(42)
            t += sep
            t += f"{'PRODUIT':<20} {'QTÉ':<5} {'TOTAL':>15}\n"
            t += sep
            
            grand_total = 0
            for r in rows:
                nom = r[0][:19] 
                qte = r[1]
                total_ligne = r[2]
                grand_total += total_ligne
                t += f"{nom:<20} x{qte:<4} {total_ligne:>15}F\n"
            
            t += sep
            t += f"TOTAL GENERAL : {grand_total} FCFA\n".rjust(42)
            t += sep
            t += f"Imprimé le : {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
            t += f"Utilisateur : {self.user['name'].upper()}\n"
            t += "\n\n\n" 

            # 3. Impression et ENREGISTREMENT DANS LE JOURNAL
            if self.sel_print:
                try:
                    PrinterManager.print_ticket(self.sel_print, t)
                    
                    # --- LA LIGNE CRUCIALE POUR LE JOURNAL ---
                    # On appelle tracer qui va écrire dans 'audit_logs'
                    self.tracer("RAPPORT", f"Récap période {d_start} au {d_end}")
                    
                    messagebox.showinfo("SUCCÈS", "Le rapport a été envoyé à l'imprimante.")
                except Exception as e:
                    messagebox.showerror("ERREUR", f"Erreur imprimante : {e}")
            else:
                # Si pas d'imprimante, on enregistre quand même l'action de consultation
                self.tracer("CONSULTATION", f"Consultation Récap {d_start} au {d_end}")
                messagebox.showinfo("RECAP (Aperçu)", t)

            # 2. Construction du Ticket (Formaté pour 42 caractères)
            sep = "-" * 42 + "\n"
            t = f"{self.store_name.center(42)}\n"
            t += f"RAPPORT DE PERIODE\n".center(42)
            t += f"Du {d_start} au {d_end}\n".center(42)
            t += sep
            t += f"{'PRODUIT':<20} {'QTÉ':<5} {'TOTAL':>15}\n"
            t += sep
            
            grand_total = 0
            for r in rows:
                nom = r[0][:19] # Tronquer le nom si trop long
                qte = r[1]
                total_ligne = r[2]
                grand_total += total_ligne
                t += f"{nom:<20} x{qte:<4} {total_ligne:>15}F\n"
            
            t += sep
            t += f"TOTAL GENERAL : {grand_total} FCFA\n".rjust(42)
            t += sep
            t += f"Imprimé le : {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
            t += f"Utilisateur : {self.user['name'].upper()}\n"
            t += "\n\n\n" # Espace pour la découpe

            # 3. Action : Imprimer et Tracer
            if self.sel_print:
                try:
                    PrinterManager.print_ticket(self.sel_print, t)
                    # On ajoute une trace dans le journal
                    self.tracer("RAPPORT", f"Impression Récap période {d_start}/{d_end}")
                    messagebox.showinfo("SUCCÈS", "Le rapport a été envoyé à l'imprimante.")
                except Exception as e:
                    messagebox.showerror("ERREUR", f"Erreur imprimante : {e}")
            else:
                # Si pas d'imprimante, on affiche au moins à l'écran
                messagebox.showinfo("RECAP (Aperçu)", t)

                # --- C'EST CETTE LIGNE QU'IL TE MANQUAIT : ---
        ctk.CTkButton(rf, text="RÉCAP PÉRIODE", height=40, fg_color="#2980b9", command=rep_per).pack(side="left", padx=10)
        
        def ticket_z():
            today = datetime.now().strftime("%Y-%m-%d")
            self.cur.execute("SELECT prod_name, SUM(qty), SUM(qty*unit_price) FROM sales_lines JOIN sales_header ON sales_lines.sale_id = sales_header.id WHERE date_time LIKE ? GROUP BY prod_name", (today+"%",))
            rows = self.cur.fetchall()
            t = f"--- TICKET Z ({today}) ---\n"; gt = 0
            for r in rows: t += f"{r[0]} x{r[1]} = {r[2]}F\n"; gt += r[2]
            t += f"\nTOTAL JOUR : {gt} FCFA"
            if self.sel_print: PrinterManager.print_ticket(self.sel_print, t)
            messagebox.showinfo("Z", t)
        ctk.CTkButton(rf, text="TICKET Z", height=40, fg_color=C_WARN, command=ticket_z).pack(side="left", padx=5)

        self.stats_container = ctk.CTkFrame(f); self.stats_container.pack(fill="both", expand=True, pady=10)
        self.draw_stats()

    def draw_stats(self):
        if not HAS_PLOT: return
        for w in self.stats_container.winfo_children(): w.destroy()
        fig, ax = plt.subplots(figsize=(6, 4)); fig.patch.set_facecolor('#2b2b2b'); plt.style.use('dark_background')
        self.cur.execute("SELECT prod_name, SUM(qty) as s FROM sales_lines GROUP BY prod_name ORDER BY s DESC LIMIT 5")
        data = self.cur.fetchall()
        if data:
            ax.bar([x[0][:10] for x in data], [x[1] for x in data], color=C_ACC); ax.set_title("TOP 5 PRODUITS VENDUS")
            FigureCanvasTkAgg(fig, master=self.stats_container).get_tk_widget().pack(fill="both", expand=True)

    # =============================================================================
    # CONFIGURATION (AVEC LES 5 ONGLETS)
    # =============================================================================
    def init_cfg(self):
        tab_cfg = ctk.CTkTabview(self.t_cfg); tab_cfg.pack(fill="both", expand=True, padx=10, pady=10)
        tab_cfg._segmented_button.configure(font=self.f_norm, height=50)
        t_app = tab_cfg.add("APPARENCE"); t_sys = tab_cfg.add("SYSTÈME"); t_prn = tab_cfg.add("IMPRIMANTE"); t_tl = tab_cfg.add("OUTILS"); t_ct = tab_cfg.add("CONTACT")
        
        # 1. APPARENCE
        ctk.CTkLabel(t_app, text="PERSONNALISATION VISUELLE", font=self.f_title).pack(pady=20)
        self.cb_font = ctk.CTkComboBox(t_app, values=["14", "16", "18", "20", "22"], height=45, font=self.f_norm)
        self.cb_font.set(str(self.font_sz)); self.cb_font.pack(pady=10)
        self.cb_theme = ctk.CTkComboBox(t_app, values=["System", "Dark", "Light"], height=45, font=self.f_norm)
        try: self.cb_theme.set(self.cur.execute("SELECT valeur FROM settings WHERE cle='theme'").fetchone()[0])
        except: self.cb_theme.set("System")
        self.cb_theme.pack(pady=10)
        def save_app():
            self.cur.execute("UPDATE settings SET valeur=? WHERE cle='font_size'", (self.cb_font.get(),))
            self.cur.execute("UPDATE settings SET valeur=? WHERE cle='theme'", (self.cb_theme.get(),))
            self.conn.commit(); messagebox.showinfo("OK", "Redémarrer pour appliquer.")
        ctk.CTkButton(t_app, text="💾 SAUVEGARDER", height=50, fg_color=C_INFO, command=save_app).pack(pady=30)

        # 2. SYSTÈME
        ctk.CTkLabel(t_sys, text="PARAMÈTRES ÉTABLISSEMENT", font=self.f_title).pack(pady=20)
        self.en_store = ctk.CTkEntry(t_sys, width=400, height=50, font=self.f_norm, justify="center"); self.en_store.insert(0, self.store_name); self.en_store.pack(pady=10)
        self.en_alert = ctk.CTkEntry(t_sys, width=150, height=50, font=self.f_norm, justify="center"); self.en_alert.insert(0, str(self.alert_thr)); self.en_alert.pack(pady=10)
        def save_sys():
            self.cur.execute("UPDATE settings SET valeur=? WHERE cle='store_name'", (self.en_store.get().upper(),))
            self.cur.execute("UPDATE settings SET valeur=? WHERE cle='stock_alert'", (self.en_alert.get(),))
            self.conn.commit(); messagebox.showinfo("OK", "Enregistré.")
        ctk.CTkButton(t_sys, text="💾 ENREGISTRER", height=50, fg_color=C_OK, command=save_sys).pack(pady=30)

        # 3. IMPRIMANTE
        ctk.CTkLabel(t_prn, text="IMPRIMANTE THERMIQUE", font=self.f_title).pack(pady=20)
        self.cb_prn = ctk.CTkComboBox(t_prn, values=PrinterManager.get_printers(), width=400, height=50, font=self.f_norm)
        self.cb_prn.set(self.sel_print); self.cb_prn.pack(pady=10)
        def save_prn():
            self.cur.execute("UPDATE settings SET valeur=? WHERE cle='printer'", (self.cb_prn.get(),)); self.conn.commit(); messagebox.showinfo("OK", "Imprimante par défaut définie.")
        ctk.CTkButton(t_prn, text="✅ DÉFINIR", height=50, command=save_prn).pack(pady=30)

        # 4. OUTILS
        ctk.CTkLabel(t_tl, text="MAINTENANCE", font=self.f_title).pack(pady=20)
        ctk.CTkButton(t_tl, text="📂 DOSSIER SOURCE", height=55, command=lambda: os.startfile(os.getcwd())).pack(pady=10, fill="x", padx=100)
        ctk.CTkButton(t_tl, text="💾 BACKUP BDD", height=55, fg_color=C_OK, command=self.db_backup).pack(pady=10, fill="x", padx=100)
        ctk.CTkButton(t_tl, text="🔄 MISE À JOUR", height=55, fg_color=C_INFO, command=UpdateManager.check_update).pack(pady=10, fill="x", padx=100)

        # 5. CONTACT
        ctk.CTkLabel(t_ct, text="SUPPORT TECHNIQUE", font=self.f_title).pack(pady=20)
        ctk.CTkLabel(t_ct, text=f"DÉVELOPPEUR : {DEV_NAME}\n{DEV_EMAIL}\n{DEV_PHONE}", font=self.f_norm).pack(pady=20)
        ctk.CTkButton(t_ct, text="GITHUB", command=lambda: webbrowser.open("https://github.com/doufall")).pack()

    # =============================================================================
    # LOGS ET FERMETURE (CORRIGÉ)
    # =============================================================================
    def init_logs(self):
        # 1. Création de l'interface
        f = ctk.CTkFrame(self.t_logs)
        f.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Ajout d'une barre de défilement (Scrollbar)
        sb = ttk.Scrollbar(f, orient="vertical")
        
        # Création du tableau
        cols = ("Date", "User", "Action", "Détail")
        self.log_tree = ttk.Treeview(f, columns=cols, show="headings", yscrollcommand=sb.set)
        
        # Configuration des colonnes
        self.log_tree.heading("Date", text="DATE / HEURE")
        self.log_tree.heading("User", text="UTILISATEUR")
        self.log_tree.heading("Action", text="ACTION")
        self.log_tree.heading("Détail", text="DÉTAILS")
        
        self.log_tree.column("Date", width=140, anchor="center")
        self.log_tree.column("User", width=100, anchor="center")
        self.log_tree.column("Action", width=120, anchor="center")
        self.log_tree.column("Détail", width=400, anchor="w") # Plus large
        
        # Liaison de la scrollbar
        sb.config(command=self.log_tree.yview)
        sb.pack(side="right", fill="y")
        self.log_tree.pack(fill="both", expand=True)

        # Bouton d'actualisation manuelle
        ctk.CTkButton(self.t_logs, text="RAFRAÎCHIR", command=self.ref_logs).pack(pady=10)

        # Chargement initial
        self.ref_logs()

    def ref_logs(self):
        # On vide le tableau (Treeview)
        # Assure-toi que ton treeview s'appelle bien self.log_tree ou self.tree_logs
        for i in self.log_tree.get_children():
            self.log_tree.delete(i)
            
        try:
            # On lit la table audit_logs
            self.cur.execute("SELECT timestamp, user, action, detail FROM audit_logs ORDER BY id DESC LIMIT 100")
            for r in self.cur.fetchall():
                self.log_tree.insert("", "end", values=r)
        except Exception as e:
            print(f"Erreur affichage logs: {e}")

    def db_backup(self):
        p = filedialog.asksaveasfilename(defaultextension=".db")
        if p: shutil.copy2(DB_FILE, p); messagebox.showinfo("OK", "Sauvegardé.")

    def close(self):
        if messagebox.askyesno("QUITTER", "Voulez-vous vraiment fermer l'application ?"):
            try:
                # 1. On ferme proprement la connexion SQLite
                if hasattr(self, 'conn'):
                    self.conn.close()
                    print("Base de données fermée.")
                
                # 2. On arrête Tkinter
                self.quit()     # Arrête la boucle mainloop
                self.destroy()  # Détruit les fenêtres
                
                # 3. Sécurité ultime : On force l'arrêt du processus Python
                import os
                os._exit(0) 
                
            except Exception as e:
                print(f"Erreur lors de la fermeture : {e}")
                import os
                os._exit(0)

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
        messagebox.showerror("ERREUR", "LOGICIEL DÉJÀ OUVERT !")
        sys.exit(0)
        
    app = DrinkManagerEnterprise()
    app.mainloop()
#%%
