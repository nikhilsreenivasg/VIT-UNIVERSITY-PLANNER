import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
from plyer import notification

# ================= THEME ================= #

COLORS = {
    "bg": "#0f172a",
    "sidebar": "#020617",
    "card": "#1e293b",
    "accent": "#38bdf8",
    "text": "#e5e7eb",
    "theory": "#22c55e",   # GREEN
    "lab": "#ef4444",      # RED
    "cell": "#020617",
    "cell_alt": "#020b2e",
    "header": "#1e40af",
    "danger": "#ef4444",
    "success": "#22c55e"
}

# ================= TIME STRUCTURE ================= #

THEORY_TIMES = [
    "08:00–08:50","09:00–09:50","10:00–10:50",
    "11:00–11:50","12:00–12:50",
    "LUNCH",
    "14:00–14:50","15:00–15:50","16:00–16:50",
    "17:00–17:50","18:00–18:50","19:00–19:50"
]

LAB_TIMES = [
    "08:00–08:50","08:51–09:40","09:51–10:40",
    "10:41–11:30","11:40–12:30","12:31–13:20",
    "LUNCH",
    "14:00–14:50","14:51–15:40","15:51–16:40",
    "16:41–17:30","17:40–18:30","18:31–19:20"
]

DAYS = ["MON","TUE","WED","THU","FRI"]

SLOT_COLUMN = {
    "A1":0,"B1":0,"C1":0,"D1":0,"E1":0,
    "F1":1,"G1":1,
    "TB1":3,"TG1":4,
    "A2":6,"B2":6,"C2":6,"D2":6,
    "F2":7,
    "TB2":9,"TG2":10,
    "V1":11,"V2":11,"V3":11,"V4":11,"V5":11,"V6":11,"V7":11
}

for i in range(1,61):
    SLOT_COLUMN[f"L{i}"] = (i-1) % 12

ALL_SLOTS = sorted(SLOT_COLUMN.keys())

# ================= DATABASE ================= #

db = sqlite3.connect("planner.db")
cur = db.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS subjects(
    id INTEGER PRIMARY KEY,
    name TEXT, code TEXT, professor TEXT)""")

cur.execute("""CREATE TABLE IF NOT EXISTS timetable(
    subject_id INTEGER, day TEXT, slot TEXT)""")

cur.execute("""CREATE TABLE IF NOT EXISTS attendance(
    subject_id INTEGER, attended INTEGER, total INTEGER)""")

cur.execute("""CREATE TABLE IF NOT EXISTS assignments(
    id INTEGER PRIMARY KEY, subject_id INTEGER,
    title TEXT, deadline DATE)""")

db.commit()

# ================= APP ================= #

class Planner(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("University Planner")
        self.geometry("1700x950")
        self.configure(bg=COLORS["bg"])

        self.sidebar()
        self.main = tk.Frame(self, bg=COLORS["bg"])
        self.main.pack(side="right", fill="both", expand=True)

        self.show_dashboard()
        self.assignment_notifications()
        self.attendance_notifications()

    # ================= SIDEBAR ================= #

    def sidebar(self):
        sb = tk.Frame(self, bg=COLORS["sidebar"], width=240)
        sb.pack(side="left", fill="y")

        tk.Label(sb, text="🎓 University Planner",
                 bg=COLORS["sidebar"], fg=COLORS["accent"],
                 font=("Segoe UI",16,"bold")).pack(pady=25)

        for text, cmd in [
            ("Dashboard", self.show_dashboard),
            ("Add Subject", self.show_add_subject),
            ("Attendance", self.show_attendance),
            ("Assignments", self.show_assignments),
            ("Timetable", self.show_timetable)
        ]:
            tk.Button(sb, text=text, command=cmd,
                      bg=COLORS["sidebar"], fg=COLORS["text"],
                      relief="flat", height=2).pack(fill="x", padx=12, pady=6)

    def clear(self):
        for w in self.main.winfo_children():
            w.destroy()

    # ================= DASHBOARD ================= #

    def show_dashboard(self):
        self.clear()
        card = tk.Frame(self.main, bg=COLORS["card"], padx=30, pady=30)
        card.pack(padx=40, pady=40, fill="x")

        tk.Label(card, text="📅 Today's Classes",
                 bg=COLORS["card"], fg=COLORS["accent"],
                 font=("Segoe UI",15,"bold")).pack(anchor="w")

        today = DAYS[datetime.now().weekday()]
        rows = cur.execute("""
            SELECT s.code, t.slot FROM timetable t
            JOIN subjects s ON s.id=t.subject_id
            WHERE t.day=?""",(today,)).fetchall()

        if not rows:
            tk.Label(card, text="No classes today",
                     bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")
        else:
            for c,s in rows:
                tk.Label(card, text=f"• {s} – {c}",
                         bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")

    # ================= ADD SUBJECT ================= #

    def show_add_subject(self):
        self.clear()
        card = tk.Frame(self.main, bg=COLORS["card"], padx=40, pady=40)
        card.pack(padx=50, pady=50)

        tk.Label(card,
            text="For lab use:  L-<Subject Name>    |    For theory use:  T-<Subject Name>",
            bg=COLORS["card"], fg="#a5f3fc",
            font=("Segoe UI",10,"italic")).pack(pady=(0,15))

        fields = ["Subject Name","Subject Code","Professor","Day","Slot"]
        entries = {}

        for f in fields:
            row = tk.Frame(card, bg=COLORS["card"])
            row.pack(pady=6)
            tk.Label(row, text=f, bg=COLORS["card"],
                     fg=COLORS["text"], width=18, anchor="e").pack(side="left")
            if f=="Day":
                e = ttk.Combobox(row, values=DAYS, state="readonly", width=25)
            elif f=="Slot":
                e = ttk.Combobox(row, values=ALL_SLOTS, state="readonly", width=25)
            else:
                e = ttk.Entry(row, width=27)
            e.pack(side="left", padx=10)
            entries[f]=e

        def add():
            name = entries["Subject Name"].get()
            code = entries["Subject Code"].get()
            prof = entries["Professor"].get()
            day = entries["Day"].get()
            slot = entries["Slot"].get()
            if not all([name,code,prof,day,slot]):
                messagebox.showerror("Error","All fields required")
                return
            cur.execute("INSERT INTO subjects VALUES(NULL,?,?,?)",(name,code,prof))
            sid = cur.lastrowid
            cur.execute("INSERT INTO timetable VALUES(?,?,?)",(sid,day,slot))
            cur.execute("INSERT INTO attendance VALUES(?,?,?)",(sid,0,0))
            db.commit()
            messagebox.showinfo("Success","Subject added")
            self.show_timetable()

        ttk.Button(card,text="➕ Add Subject",command=add).pack(pady=20)

    # ================= ATTENDANCE (FIXED) ================= #

    def show_attendance(self):
        self.clear()
        card = tk.Frame(self.main, bg=COLORS["card"], padx=40, pady=40)
        card.pack(padx=50, pady=50)

        tk.Label(card,text="Attendance Manager",
                 bg=COLORS["card"], fg=COLORS["accent"],
                 font=("Segoe UI",16,"bold")).pack(pady=15)

        # ✅ DISTINCT subjects only
        subjects = [
            f"{sid} - {code}"
            for sid, code in cur.execute("""
                SELECT DISTINCT s.id, s.code
                FROM subjects s
                JOIN timetable t ON s.id=t.subject_id
            """)
        ]

        box = ttk.Combobox(card, values=subjects, state="readonly", width=30)
        box.pack(pady=10)

        result = tk.Label(card, bg=COLORS["card"], fg=COLORS["text"],
                          font=("Segoe UI",14))
        result.pack(pady=10)

        def mark(present):
            if not box.get():
                return

            sid = int(box.get().split(" - ")[0])
            today = DAYS[datetime.now().weekday()]

            # ✅ Count how many slots today
            slots_today = cur.execute("""
                SELECT COUNT(*) FROM timetable
                WHERE subject_id=? AND day=?
            """,(sid,today)).fetchone()[0]

            if slots_today == 0:
                messagebox.showinfo("Info","No classes today for this subject")
                return

            cur.execute("""
                UPDATE attendance
                SET attended = attended + ?,
                    total = total + ?
                WHERE subject_id=?
            """,(present*slots_today, slots_today, sid))
            db.commit()

            a,t = cur.execute("""
                SELECT attended,total FROM attendance WHERE subject_id=?
            """,(sid,)).fetchone()

            pct = (a/t)*100
            result.config(
                text=f"Attendance: {pct:.1f}%  ({slots_today} slots marked)",
                fg=COLORS["danger"] if pct<75 else COLORS["success"]
            )

        ttk.Button(card,text="✔ Present",command=lambda:mark(1)).pack(pady=5)
        ttk.Button(card,text="✖ Absent",command=lambda:mark(0)).pack(pady=5)

    # ================= ASSIGNMENTS ================= #

    def show_assignments(self):
        self.clear()
        card = tk.Frame(self.main, bg=COLORS["card"], padx=40, pady=40)
        card.pack(padx=40, pady=40)

        tk.Label(card,text="Assignments",
                 bg=COLORS["card"], fg=COLORS["accent"],
                 font=("Segoe UI",16,"bold")).grid(columnspan=2,pady=15)

        entries=[]
        for i,l in enumerate(["Subject ID","Title","Deadline (YYYY-MM-DD)"]):
            tk.Label(card,text=l,bg=COLORS["card"],fg=COLORS["text"]).grid(row=i+1,column=0,pady=8)
            e=ttk.Entry(card,width=25)
            e.grid(row=i+1,column=1)
            entries.append(e)

        def add():
            sid,title,date=[e.get() for e in entries]
            if not sid or not title or not date: return
            cur.execute("INSERT INTO assignments VALUES(NULL,?,?,?)",(sid,title,date))
            db.commit()
            self.show_assignments()

        ttk.Button(card,text="➕ Add Assignment",command=add).grid(row=4,column=1,pady=15)

    # ================= TIMETABLE ================= #

    def show_timetable(self):
        self.clear()
        wrapper = tk.Frame(self.main,bg=COLORS["card"])
        wrapper.pack(fill="both",expand=True,padx=20,pady=20)

        canvas=tk.Canvas(wrapper,bg=COLORS["card"],highlightthickness=0)
        h=tk.Scrollbar(wrapper,orient="horizontal",command=canvas.xview)
        canvas.configure(xscrollcommand=h.set)
        h.pack(side="bottom",fill="x")
        canvas.pack(side="left",fill="both",expand=True)

        table=tk.Frame(canvas,bg=COLORS["bg"])
        canvas.create_window((0,0),window=table,anchor="nw")

        tk.Label(table,text="THEORY HOURS",
                 bg=COLORS["header"],fg="white",width=14).grid(row=0,column=0,rowspan=2)
        for c,t in enumerate(THEORY_TIMES):
            tk.Label(table,text=t,bg=COLORS["header"],
                     fg="white",width=18).grid(row=0,column=c+1)

        tk.Label(table,text="LAB HOURS",
                 bg=COLORS["header"],fg="white",width=14).grid(row=2,column=0,rowspan=2)
        for c,t in enumerate(LAB_TIMES):
            tk.Label(table,text=t,bg=COLORS["header"],
                     fg="white",width=18).grid(row=2,column=c+1)

        start=4
        for r,d in enumerate(DAYS):
            tk.Label(table,text=d,bg=COLORS["header"],
                     fg="white",width=14).grid(row=start+r,column=0)
            for c in range(12):
                tk.Label(table,bg=COLORS["cell"],width=18,height=2,
                         relief="solid").grid(row=start+r,column=c+1)

        for code,day,slot in cur.execute("""
            SELECT s.code,t.day,t.slot FROM timetable t
            JOIN subjects s ON s.id=t.subject_id"""):
            r=DAYS.index(day)+start
            c=SLOT_COLUMN[slot]
            col=COLORS["lab"] if slot.startswith("L") else COLORS["theory"]
            tk.Label(table,text=code,bg=col,fg="white",
                     font=("Segoe UI",11,"bold"),
                     width=18,height=2,relief="solid").grid(row=r,column=c+1)

        table.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    # ================= NOTIFICATIONS ================= #

    def assignment_notifications(self):
        tomorrow=datetime.now().date()+timedelta(days=1)
        for t, in cur.execute("SELECT title FROM assignments WHERE deadline=?",(tomorrow,)):
            notification.notify("Assignment Due Tomorrow",t,timeout=5)

    def attendance_notifications(self):
        for c,a,t in cur.execute("""
            SELECT s.code,a.attended,a.total FROM attendance a
            JOIN subjects s ON s.id=a.subject_id WHERE a.total>0"""):
            if (a/t)*100<75:
                notification.notify("Attendance Alert",f"{c} below 75%",timeout=5)

# ================= RUN ================= #

if __name__=="__main__":
    Planner().mainloop()
