import tkinter as tk

class CustomButton(tk.Button):
    """A custom button widget for slightly better looking buttons."""
    def __init__(self, parent, text="", command=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.config(
            text=text,
            command=command,
            bg="#333",  
            fg="#fff",  
            padx=10,
            pady=5,
            font=("Helvetica", 10, "bold"),
            borderwidth=0,  
            relief="flat"
        )
        
 
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        self.config(bg="#555")  

    def on_leave(self, e):
        self.config(bg="#333") 