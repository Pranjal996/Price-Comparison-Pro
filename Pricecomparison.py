import tkinter as tk
from tkinter import ttk, messagebox
import threading
import requests
from bs4 import BeautifulSoup
import webbrowser
import difflib
import sqlite3
import json
import re # New: For advanced text cleaning

# ================= DATABASE & SETTINGS =================

# Colors
COLOR_BG = "#0F172A"       # Dark Navy
COLOR_SIDEBAR = "#1E293B"  # Slightly Lighter Navy
COLOR_ACCENT = "#38BDF8"   # Light Blue
COLOR_SUCCESS = "#22C55E"  # Green
COLOR_TEXT = "#E5E7EB"     # White/Grey
COLOR_BEST_DEAL = "#FFD700" # Gold

def init_db():
    conn = sqlite3.connect("app_data.db")
    cursor = conn.cursor()
    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    """)
    # History Table (New)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            query TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://www.google.com/"
}

OFFICIAL_BRANDS = {
    "cello": "https://celloworld.com/search?q={}",
    "samsung": "https://www.samsung.com/in/search/?searchtext={}",
    "boat": "https://www.boat-lifestyle.com/pages/search?q={}",
    "apple": "https://www.apple.com/in/search/{}",
    "realme": "https://www.realme.com/in/search?q={}",
    "sony": "https://www.sony.co.in/search?q={}",
    "nike": "https://www.nike.com/in/w?q={}",
    "adidas": "https://www.adidas.co.in/search?q={}",
    "philips": "https://www.philips.co.in/c-m-so/search#q={}",
    "hp": "https://www.hp.com/in-en/search.html#qt={}",
    "dell": "https://www.dell.com/en-in/search/{}",
    "lenovo": "https://www.lenovo.com/in/en/search?text={}",
    "puma": "https://in.puma.com/in/en/search?q={}",
    "oneplus": "https://www.oneplus.in/search?q={}",
    "xiaomi": "https://www.mi.com/in/search?keyword={}"
}

# Global Data Stores
url_map = {} 
current_user = None

# ================= HELPER FUNCTIONS =================

def clean_price(price_str):
    """Converts '₹1,999' to 1999.0 for math comparisons"""
    if not price_str or price_str in ["-", "N/A", "Check Site"]:
        return float('inf') # Infinite price for unavailable items
    
    # Remove non-numeric chars except dot
    clean = re.sub(r'[^\d.]', '', price_str)
    try:
        return float(clean)
    except ValueError:
        return float('inf')

def save_history(query):
    if current_user:
        conn = sqlite3.connect("app_data.db")
        cursor = conn.cursor()
        # Delete duplicate recent searches to keep list clean
        cursor.execute("DELETE FROM history WHERE username=? AND query=?", (current_user, query))
        # Insert new
        cursor.execute("INSERT INTO history (username, query) VALUES (?, ?)", (current_user, query))
        conn.commit()
        conn.close()

# ================= SCRAPING LOGIC =================

def search_amazon(query):
    search_url = f"https://www.amazon.in/s?k={query.replace(' ', '+')}"
    try:
        response = requests.get(search_url, headers=HEADERS)
        soup = BeautifulSoup(response.content, "html.parser")
        
        no_results = soup.find("span", string=lambda text: "No results for" in text if text else False)
        if no_results: return ("Amazon", "Not Available", "-", "Search", search_url)

        result = soup.find("div", {"data-component-type": "s-search-result"})
        if result:
            price_elm = result.find("span", class_="a-price-whole")
            title_elm = result.find("h2")
            link_elm = result.find("a", class_="a-link-normal")

            if price_elm and title_elm:
                price = f"₹{price_elm.text}"
                name = title_elm.text.strip()[:40] + "..."
                link = "https://www.amazon.in" + link_elm['href'] if link_elm else search_url
                return ("Amazon", name, price, "Open", link)
        return ("Amazon", "Not Available", "-", "Search", search_url)
    except:
        return ("Amazon", "Not Available", "-", "Retry", search_url)

def search_flipkart(query):
    search_url = f"https://www.flipkart.com/search?q={query.replace(' ', '%20')}"
    try:
        response = requests.get(search_url, headers=HEADERS)
        soup = BeautifulSoup(response.content, "html.parser")
        
        if "Sorry, no results found" in soup.text:
             return ("Flipkart", "Not Available", "-", "Search", search_url)

        container = soup.find("div", class_="_1AtVbE")
        if not container: container = soup.find("div", class_="_4ddWZP")
        
        price_div = soup.find("div", class_="_30jeq3")
        name_div = soup.find("div", class_="_4rR01T")
        if not name_div: name_div = soup.find("a", class_="s1Q9rs")

        if price_div and name_div:
            price = price_div.text
            name = name_div.text.strip()[:40] + "..."
            link_tag = price_div.find_parent("a")
            if not link_tag: link_tag = name_div.find_parent("a")
            link = "https://www.flipkart.com" + link_tag['href'] if link_tag else search_url
            return ("Flipkart", name, price, "Open", link)
        return ("Flipkart", "Not Available", "-", "Search", search_url)
    except:
        return ("Flipkart", "Not Available", "-", "Search", search_url)

def search_ajio(query):
    try:
        api_url = f"https://www.ajio.com/api/search/searchResults?text={query.replace(' ', '%20')}"
        response = requests.get(api_url, headers=HEADERS)
        data = response.json()
        if "products" in data and len(data["products"]) > 0:
            item = data["products"][0]
            name = item.get("name", "Unknown")[:40] + "..."
            price = f"₹{item.get('price', {}).get('value', 'N/A')}"
            link = "https://www.ajio.com" + item.get("url", "")
            return ("Ajio", name, price, "Open", link)
        return ("Ajio", "Not Available", "-", "Check Site", f"https://www.ajio.com/search/?text={query}")
    except:
        return ("Ajio", "Not Available", "-", "Check Site", f"https://www.ajio.com/search/?text={query}")

def search_meesho(query):
    search_url = f"https://www.meesho.com/search?q={query.replace(' ', '%20')}"
    try:
        response = requests.get(search_url, headers=HEADERS)
        soup = BeautifulSoup(response.content, "html.parser")
        price_tag = soup.find("h5", string=lambda text: "₹" in text if text else False)
        if price_tag:
            price = price_tag.text
            container = price_tag.find_parent("div")
            if container:
                name_tag = container.find("p")
                if name_tag:
                    name = name_tag.text.strip()[:40] + "..."
                    return ("Meesho", name, price, "Open", search_url)
        return ("Meesho", "Not Available", "-", "Search", search_url)
    except:
        return ("Meesho", "Not Available", "-", "Search", search_url)

def search_official(query):
    query_lower = query.lower()
    words = query_lower.split()
    found_brand = None
    for brand in OFFICIAL_BRANDS:
        if brand in query_lower:
            found_brand = brand
            break
    if not found_brand:
        for word in words:
            matches = difflib.get_close_matches(word, OFFICIAL_BRANDS.keys(), n=1, cutoff=0.7)
            if matches:
                found_brand = matches[0]
                break
    if found_brand:
        url_template = OFFICIAL_BRANDS[found_brand]
        search_link = url_template.format(query.replace(' ', '%20'))
        return (f"{found_brand.title()} Official", "Visit Store", "Check Site", "Open", search_link)
    return None

# ================= UI CLASSES =================

class PriceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Universal Price Comparison Pro")
        self.geometry("1280x720")
        self.configure(bg=COLOR_BG)
        
        # UI Components
        self.current_frame = None
        self.show_login()

    def show_login(self):
        if self.current_frame: self.current_frame.destroy()
        self.current_frame = LoginFrame(self)
        self.current_frame.pack(fill="both", expand=True)

    def show_register(self):
        if self.current_frame: self.current_frame.destroy()
        self.current_frame = RegisterFrame(self)
        self.current_frame.pack(fill="both", expand=True)

    def show_main(self):
        if self.current_frame: self.current_frame.destroy()
        self.current_frame = MainFrame(self)
        self.current_frame.pack(fill="both", expand=True)

class LoginFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=COLOR_BG)
        self.master = master
        
        tk.Label(self, text="LOGIN", font=("Segoe UI", 24, "bold"), fg=COLOR_TEXT, bg=COLOR_BG).pack(pady=80)
        
        tk.Label(self, text="Username", font=("Segoe UI", 12), fg=COLOR_TEXT, bg=COLOR_BG).pack()
        self.user_entry = ttk.Entry(self, font=("Segoe UI", 12), width=30)
        self.user_entry.pack(pady=5)
        
        tk.Label(self, text="Password", font=("Segoe UI", 12), fg=COLOR_TEXT, bg=COLOR_BG).pack()
        self.pass_entry = ttk.Entry(self, font=("Segoe UI", 12), width=30, show="*")
        self.pass_entry.pack(pady=5)
        
        ttk.Button(self, text="Login", command=self.do_login).pack(pady=20)
        ttk.Button(self, text="Create Account", command=master.show_register).pack()

    def do_login(self):
        user = self.user_entry.get()
        pwd = self.pass_entry.get()
        
        conn = sqlite3.connect("app_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pwd))
        if cursor.fetchone():
            global current_user
            current_user = user
            self.master.show_main()
        else:
            messagebox.showerror("Error", "Invalid Credentials")
        conn.close()

class RegisterFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=COLOR_BG)
        self.master = master
        
        tk.Label(self, text="REGISTER", font=("Segoe UI", 24, "bold"), fg=COLOR_TEXT, bg=COLOR_BG).pack(pady=80)
        
        tk.Label(self, text="Username", font=("Segoe UI", 12), fg=COLOR_TEXT, bg=COLOR_BG).pack()
        self.user_entry = ttk.Entry(self, font=("Segoe UI", 12), width=30)
        self.user_entry.pack(pady=5)
        
        tk.Label(self, text="Password", font=("Segoe UI", 12), fg=COLOR_TEXT, bg=COLOR_BG).pack()
        self.pass_entry = ttk.Entry(self, font=("Segoe UI", 12), width=30, show="*")
        self.pass_entry.pack(pady=5)
        
        ttk.Button(self, text="Register", command=self.do_register).pack(pady=20)
        ttk.Button(self, text="Back", command=master.show_login).pack()

    def do_register(self):
        user = self.user_entry.get()
        pwd = self.pass_entry.get()
        if not user or not pwd: return
        
        try:
            conn = sqlite3.connect("app_data.db")
            conn.execute("INSERT INTO users VALUES (?, ?)", (user, pwd))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Account Created")
            self.master.show_login()
        except:
            messagebox.showerror("Error", "User exists")

class MainFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=COLOR_BG)
        
        # --- SIDEBAR (History) ---
        self.sidebar = tk.Frame(self, bg=COLOR_SIDEBAR, width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        tk.Label(self.sidebar, text="HISTORY", font=("Segoe UI", 12, "bold"), fg=COLOR_ACCENT, bg=COLOR_SIDEBAR).pack(pady=20)
        self.history_list = tk.Listbox(self.sidebar, bg=COLOR_SIDEBAR, fg=COLOR_TEXT, borderwidth=0, font=("Segoe UI", 10))
        self.history_list.pack(fill="both", expand=True, padx=10)
        self.history_list.bind("<<ListboxSelect>>", self.load_history)
        
        # --- CONTENT AREA ---
        self.content = tk.Frame(self, bg=COLOR_BG)
        self.content.pack(side="right", fill="both", expand=True)
        
        # Header
        header = tk.Frame(self.content, bg=COLOR_BG)
        header.pack(fill="x", pady=20, padx=20)
        tk.Label(header, text="Price Comparison Pro", font=("Segoe UI", 20, "bold"), fg=COLOR_TEXT, bg=COLOR_BG).pack(side="left")
        ttk.Button(header, text="Logout", command=master.show_login).pack(side="right")
        
        # Search Bar
        search_frame = tk.Frame(self.content, bg=COLOR_BG)
        search_frame.pack(pady=10)
        
        self.search_entry = ttk.Entry(search_frame, width=50, font=("Segoe UI", 12))
        self.search_entry.grid(row=0, column=0, padx=10)
        self.search_entry.bind("<Return>", self.start_search)
        
        btn = ttk.Button(search_frame, text="Search", command=self.start_search)
        btn.grid(row=0, column=1)
        
        # Recommendation Banner
        self.rec_label = tk.Label(self.content, text="", font=("Segoe UI", 12, "bold"), bg=COLOR_BG, fg=COLOR_SUCCESS)
        self.rec_label.pack(pady=10)
        
        # Results Table
        cols = ("Site", "Product Name", "Price", "Link")
        self.tree = ttk.Treeview(self.content, columns=cols, show="headings", height=10)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")
        
        # Adjust Column Widths
        self.tree.column("Site", width=100)
        self.tree.column("Product Name", width=400)
        self.tree.column("Price", width=100)
        self.tree.column("Link", width=100)
        
        # Tag configuration for highlighting
        self.tree.tag_configure('best_deal', background='#14532d', foreground='white') # Dark Green
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        self.tree.bind("<Double-1>", self.on_item_click)
        
        self.status = tk.Label(self.content, text="Ready", font=("Segoe UI", 10), bg=COLOR_BG, fg="grey")
        self.status.pack(pady=5)
        
        self.refresh_history()

    def refresh_history(self):
        self.history_list.delete(0, tk.END)
        conn = sqlite3.connect("app_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT query FROM history WHERE username=? ORDER BY timestamp DESC LIMIT 15", (current_user,))
        for row in cursor.fetchall():
            self.history_list.insert(tk.END, row[0])
        conn.close()

    def load_history(self, event):
        selection = self.history_list.curselection()
        if selection:
            query = self.history_list.get(selection[0])
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, query)
            self.start_search()

    def start_search(self, event=None):
        query = self.search_entry.get()
        if not query: return
        
        # Save to DB
        save_history(query)
        self.refresh_history()
        
        self.tree.delete(*self.tree.get_children())
        url_map.clear()
        self.rec_label.config(text="Searching... analyzing prices...", fg=COLOR_ACCENT)
        self.status.config(text="Scraping active...")
        
        thread = threading.Thread(target=self.run_scrape, args=(query,))
        thread.daemon = True
        thread.start()

    def run_scrape(self, query):
        results = []
        results.append(search_amazon(query))
        results.append(search_flipkart(query))
        results.append(search_ajio(query))
        results.append(search_meesho(query))
        
        official = search_official(query)
        if official: results.insert(0, official)
        
        self.after(0, lambda: self.update_results(results))

    def update_results(self, results):
        lowest_price = float('inf')
        best_site = None
        
        # First pass: Find lowest price
        for row in results:
            site, name, price_str, _, _ = row
            price_val = clean_price(price_str)
            if price_val < lowest_price:
                lowest_price = price_val
                best_site = site

        # Second pass: Insert data
        for row in results:
            site, name, price_str, action, link = row
            price_val = clean_price(price_str)
            
            # Apply 'best_deal' tag if it matches lowest price
            tags = ('best_deal',) if (price_val == lowest_price and price_val != float('inf')) else ()
            
            item_id = self.tree.insert("", "end", values=(site, name, price_str, action), tags=tags)
            url_map[item_id] = link

        self.status.config(text="Search Complete")
        if best_site:
            self.rec_label.config(text=f"🏆 Recommendation: Best price on {best_site} (₹{lowest_price})", fg=COLOR_SUCCESS)
        else:
            self.rec_label.config(text="No valid prices found.", fg="red")

    def on_item_click(self, event):
        selected = self.tree.selection()
        if selected:
            webbrowser.open(url_map.get(selected[0], ""))

# ================= RUN =================
if __name__ == "__main__":
    app = PriceApp()
    app.mainloop()