import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
import speech_recognition as sr
import pyttsx3
import sqlite3

class PrioritizeMeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Prioritize Me")
        self.root.geometry("500x730")
        
        # Updated themes with a more subtle palette
        self.themes = {
            "light": {
                "bg": "#f7f9fa",    # very light gray
                "fg": "#333333",    # dark gray text
                "card": "#ffffff",  # white cards
                "header": "#95a5a6" # soft gray-blue header
            },
            "dark": {
                "bg": "#2c3e50",    # dark blue-gray
                "fg": "#ecf0f1",    # soft light text
                "card": "#34495e",  # medium dark card background
                "header": "#7f8c8d" # muted gray header
            }
        }
        self.current_theme = "light"
        self.apply_theme()

        self.tasks = []
        self.engine = pyttsx3.init()

        self.db_connection()
        self.setup_styles()
        self.check_reminders()
        self.show_welcome_screen()

    def db_connection(self):
        self.conn = sqlite3.connect("tasks")
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                name TEXT, category TEXT, priority TEXT,
                date TEXT, start TEXT, end TEXT,
                desc TEXT, completed INTEGER, reminded INTEGER
            )
        ''')
        self.conn.commit()
        self.load_tasks()

    def load_tasks(self):
        self.tasks.clear()
        rows = self.cursor.execute("SELECT * FROM tasks").fetchall()
        for row in rows:
            task = {
                "id": row[0], "name": row[1], "category": row[2],
                "priority": row[3], "date": row[4], "start": row[5],
                "end": row[6], "desc": row[7],
                "completed": bool(row[8]), "reminded": bool(row[9])
            }
            self.tasks.append(task)

    def save_task_to_db(self, task):
        self.cursor.execute('''
            INSERT INTO tasks (name, category, priority, date, start, end, desc, completed, reminded)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (task['name'], task['category'], task['priority'], task['date'],
              task['start'], task['end'], task['desc'], int(task['completed']), int(task['reminded'])))
        self.conn.commit()
        task["id"] = self.cursor.lastrowid

    def delete_task_from_db(self, task_id):
        self.cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self.conn.commit()

    def update_task_in_db(self, task):
        self.cursor.execute('''
            UPDATE tasks SET completed=?, reminded=? WHERE id=?
        ''', (int(task['completed']), int(task['reminded']), task['id']))
        self.conn.commit()

    def apply_theme(self):
        theme = self.themes[self.current_theme]
        self.root.configure(bg=theme["bg"])

    def toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.apply_theme()
        self.show_homepage()

    def setup_styles(self):
        style = ttk.Style(self.root)
        style.theme_use('clam')
        # Use the header color from the active theme for buttons for a subtle look.
        style.configure("TButton", font=("Segoe UI", 10, "bold"), foreground="white", background=self.themes[self.current_theme]["header"])
        style.map("TButton", background=[("active", self.themes[self.current_theme]["header"])])
        style.configure("TCombobox", font=("Segoe UI", 10))

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_welcome_screen(self):
        self.clear_window()
        theme = self.themes[self.current_theme]
        frame = tk.Frame(self.root, bg=theme["bg"])
        frame.pack(expand=True, fill="both")
        
        header = tk.Frame(frame, bg=theme["header"], height=150)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="Welcome to Prioritize Me", font=("Segoe UI", 22, "bold"),
                 bg=theme["header"], fg="white").pack(expand=True)
        
        content = tk.Frame(frame, bg=theme["bg"])
        content.pack(expand=True)
        tk.Label(content, text="A workspace to boost your productivity.",
                 font=("Segoe UI", 12), bg=theme["bg"], fg=theme["fg"]).pack(pady=10)
        ttk.Button(content, text="Let's Start", command=self.show_homepage).pack(pady=20, ipadx=15, ipady=5)

    def show_homepage(self):
        self.clear_window()
        theme = self.themes[self.current_theme]
        
        header = tk.Frame(self.root, bg=theme["header"], height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="Today's Tasks", font=("Segoe UI", 18, "bold"),
                 bg=theme["header"], fg="white").pack(side="left", padx=10)
        ttk.Button(header, text="➕", command=self.show_create_task).pack(side="right", padx=5)
        ttk.Button(header, text="☀️🌙", command=self.toggle_theme).pack(side="right", padx=5)
        
        options = ["No Priority", "Low", "Medium", "High"]
        self.sort_var = tk.StringVar(value="Sort By")
        sort_box = ttk.Combobox(header, textvariable=self.sort_var, values=options, state="readonly", width=10)
        sort_box.pack(side="right", padx=10)
        sort_box.bind("<<ComboboxSelected>>", self.sort_tasks)
        
        self.task_frame = tk.Frame(self.root, bg=theme["bg"])
        self.task_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        self.update_task_list()

    def sort_tasks(self, event=None):
        priority_order = {"High": 1, "Medium": 2, "Low": 3, "No Priority": 4}
        selected = self.sort_var.get()
        if selected in priority_order:
            self.tasks.sort(key=lambda t: priority_order.get(t['priority'], 5))
        self.update_task_list()

    def show_create_task(self):
        self.clear_window()
        theme = self.themes[self.current_theme]
        header = tk.Frame(self.root, bg=theme["header"], height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="Create New Task", font=("Segoe UI", 18, "bold"),
                 bg=theme["header"], fg="white").pack(side="left", padx=10)
        ttk.Button(header, text="←", command=self.show_homepage).pack(side="right", padx=10)

        form = tk.Frame(self.root, bg=theme["bg"])
        form.pack(padx=20, pady=10, fill=tk.X)

        # Task Name
        tk.Label(form, text="Task Name:", font=("Segoe UI", 10),
                 bg=theme["bg"], fg=theme["fg"]).pack(anchor="w")
        self.task_name_entry = ttk.Entry(form)
        self.task_name_entry.pack(fill=tk.X, pady=5)

        ttk.Button(form, text="🎤 Speak Task", command=self.voice_input).pack(pady=5)

        # Category
        tk.Label(form, text="Category:", font=("Segoe UI", 10),
                 bg=theme["bg"], fg=theme["fg"]).pack(anchor="w", pady=(10, 0))
        self.category_var = tk.StringVar()
        cat_frame = tk.Frame(form, bg=theme["bg"])
        cat_frame.pack()
        for cat in ["Tech", "Development", "Completion"]:
            ttk.Radiobutton(cat_frame, text=cat, variable=self.category_var, value=cat).pack(side=tk.LEFT, padx=5)

        # Priority
        tk.Label(form, text="Priority:", font=("Segoe UI", 10),
                 bg=theme["bg"], fg=theme["fg"]).pack(anchor="w", pady=(10, 0))
        self.priority_var = tk.StringVar(value="No Priority")
        priority_menu = ttk.Combobox(form, textvariable=self.priority_var, state="readonly")
        priority_menu['values'] = ["No Priority", "Low", "Medium", "High"]
        priority_menu.pack(pady=5)

        # Date
        tk.Label(form, text="Date:", font=("Segoe UI", 10),
                 bg=theme["bg"], fg=theme["fg"]).pack(anchor="w")
        self.date_entry = DateEntry(form, width=18, date_pattern="yyyy-mm-dd")
        self.date_entry.pack(pady=5)

        # Start Time Picker
        tk.Label(form, text="Start Time (HH:MM):", font=("Segoe UI", 10),
                 bg=theme["bg"], fg=theme["fg"]).pack(anchor="w")
        time_frame_start = tk.Frame(form, bg=theme["bg"])
        time_frame_start.pack(pady=5, anchor="w")
        self.start_time_hour = tk.Spinbox(time_frame_start, from_=0, to=23, width=3, format="%02.0f")
        self.start_time_hour.pack(side=tk.LEFT)
        tk.Label(time_frame_start, text=":", font=("Segoe UI", 10),
                 bg=theme["bg"], fg=theme["fg"]).pack(side=tk.LEFT)
        self.start_time_min = tk.Spinbox(time_frame_start, from_=0, to=59, width=3, format="%02.0f")
        self.start_time_min.pack(side=tk.LEFT)

        # End Time Picker
        tk.Label(form, text="End Time (HH:MM):", font=("Segoe UI", 10),
                 bg=theme["bg"], fg=theme["fg"]).pack(anchor="w")
        time_frame_end = tk.Frame(form, bg=theme["bg"])
        time_frame_end.pack(pady=5, anchor="w")
        self.end_time_hour = tk.Spinbox(time_frame_end, from_=0, to=23, width=3, format="%02.0f")
        self.end_time_hour.pack(side=tk.LEFT)
        tk.Label(time_frame_end, text=":", font=("Segoe UI", 10),
                 bg=theme["bg"], fg=theme["fg"]).pack(side=tk.LEFT)
        self.end_time_min = tk.Spinbox(time_frame_end, from_=0, to=59, width=3, format="%02.0f")
        self.end_time_min.pack(side=tk.LEFT)

        # Description
        tk.Label(form, text="Description:", font=("Segoe UI", 10),
                 bg=theme["bg"], fg=theme["fg"]).pack(anchor="w", pady=(10, 0))
        self.desc_entry = tk.Text(form, height=4, wrap=tk.WORD)
        self.desc_entry.pack(fill=tk.X, pady=5)

        ttk.Button(self.root, text="Create Task", command=self.save_task).pack(pady=15, ipadx=15, ipady=5)

    def voice_input(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            messagebox.showinfo("Voice Input", "Listening... Please say your task name.")
            try:
                audio = recognizer.listen(source, timeout=5)
                text = recognizer.recognize_google(audio)
                self.task_name_entry.delete(0, tk.END)
                self.task_name_entry.insert(0, text)
            except:
                messagebox.showerror("Error", "Could not process voice input.")

    def save_task(self):
        # Combine hour and minute spinbox values into HH:MM strings.
        start_time = f"{int(self.start_time_hour.get()):02d}:{int(self.start_time_min.get()):02d}"
        end_time   = f"{int(self.end_time_hour.get()):02d}:{int(self.end_time_min.get()):02d}"
        
        task = {
            "name": self.task_name_entry.get().strip(),
            "category": self.category_var.get(),
            "priority": self.priority_var.get(),
            "date": self.date_entry.get(),
            "start": start_time,
            "end": end_time,
            "desc": self.desc_entry.get("1.0", tk.END).strip(),
            "completed": False,
            "reminded": False
        }
        if not task["name"] or not task["category"]:
            messagebox.showwarning("Missing Info", "Please fill out all required fields.")
            return

        self.save_task_to_db(task)
        self.tasks.append(task)
        self.speak("Task created successfully.")
        messagebox.showinfo("Task Created", "Your task has been added.")
        self.show_homepage()

    def update_task_list(self):
        theme = self.themes[self.current_theme]
        for widget in self.task_frame.winfo_children():
            widget.destroy()
        if not self.tasks:
            tk.Label(self.task_frame, text="No tasks today.", bg=theme["bg"], fg=theme["fg"]).pack()
            return

        for task in self.tasks:
            card = tk.Frame(self.task_frame, bg=theme["card"], bd=1, relief=tk.SOLID, padx=10, pady=8)
            card.pack(fill=tk.X, pady=5)
            title = f"{task['name']} ({task['start']} - {task['end']}) [{task['priority']}]"
            if task['completed']:
                title = f"✔️ {title}"
            tk.Label(card, text=title, font=("Segoe UI", 12, "bold"), bg=theme["card"], fg=theme["fg"]).pack(anchor="w")
            tk.Label(card, text=f"Category: {task['category']} | Date: {task['date']}", font=("Segoe UI", 9), bg=theme["card"], fg="gray").pack(anchor="w")
            tk.Label(card, text=task['desc'], font=("Segoe UI", 9), bg=theme["card"], fg=theme["fg"],   
                     wraplength=400, justify="left").pack(anchor="w")

            btn_frame = tk.Frame(card, bg=theme["card"])
            btn_frame.pack(anchor="w", pady=5)
            if not task['completed']:
                ttk.Button(btn_frame, text="Complete", command=lambda t=task: self.mark_as_complete(t)).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Delete", command=lambda t=task: self.delete_task(t)).pack(side=tk.LEFT, padx=5)

    def mark_as_complete(self, task):
        task["completed"] = True
        self.update_task_in_db(task)
        self.speak(f"Task '{task['name']}' marked as completed.")
        self.update_task_list()

    def delete_task(self, task):
        self.delete_task_from_db(task["id"])
        self.tasks.remove(task)
        self.speak(f"Task '{task['name']}' has been deleted.")
        self.update_task_list()

    def check_reminders(self):
        now = datetime.now()
        for task in self.tasks:
            if not task["completed"] and not task.get("reminded", False):
                try:
                    task_dt_str = f"{task['date']} {task['end']}"
                    task_dt = datetime.strptime(task_dt_str, "%Y-%m-%d %H:%M")
                    if now > task_dt:
                        self.speak(f"Time out for the task {task['name']}")
                        task["reminded"] = True
                        self.update_task_in_db(task)
                except Exception as e:
                    print(f"Error parsing time for '{task['name']}': {e}")
        self.root.after(60000, self.check_reminders)

if __name__ == "__main__":
    root = tk.Tk()
    app = PrioritizeMeApp(root)
    root.mainloop()
