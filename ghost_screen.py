import tkinter as tk
import time

root = tk.Tk()
root.attributes("-fullscreen", True)
root.configure(bg="black")
root.attributes("-topmost", True)
root.config(cursor="none")

# Block inputs
def block(e):
    return "break"

root.bind("<Any-KeyPress>", block)
root.bind("<Any-Button>", block)
root.bind("<Motion>", block)

def keep_on_top():
    root.attributes("-topmost", True)
    root.after(100, keep_on_top)

keep_on_top()
root.mainloop()
