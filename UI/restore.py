import sys
from pathlib import Path

if getattr(sys, 'frozen', False):  # Running as a PyInstaller EXE
    root_path = Path(sys.executable).parent
else:  # Running as a Python script
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from tkinter import Tk
from utilities.path_utils import *
from tkinter import ttk
from tkinter import Tk, Button, PhotoImage, filedialog, messagebox
from utilities.backup import BackupSystem



class Restore_ui(tk.Toplevel):
    def __init__(self, parent=None):
        super().__init__(master=parent)

        self.title("Restore Backups")
        self.iconbitmap(generate_path("UI", "assets", "BillMates.ico"))
        center_window(self, 780, 480)
        self.configure(bg="#E7EBFF")
        self.focus()
        self.grab_set() 


        self.style = ttk.Style()
        self.style.configure("TLabel", font=("VarelaRound Regular", 18*-1), background="#E7EBFF")
        self.style.configure("TEntry", font=("Segoe UI", 14))

        self.backup_path = tk.StringVar()

        self.heading = ttk.Label(self, text="Backup File")
        self.heading.place(x=65.0, y=48.0, width=140.0, height=22.0)

        self.backup_path_entry = ttk.Entry(self, textvariable=self.backup_path, state="readonly")
        self.backup_path_entry.place(x=65, y=78, width=600, height=30)

        button_image_1 = PhotoImage(
            file=self.relative_to_assets("button_1.png")
            )
        PathSelecter = Button(
            self,
            image=button_image_1,
            borderwidth=0,
            highlightthickness=0,
            cursor="hand2",
            command= self.browse_folder,
            relief="flat"
        )
        PathSelecter.place(
            x=675.0,
            y=76.0,
            width=35.0,
            height=35.0
        )

        self.heading2 = ttk.Label(self, text="Restore Management")
        self.heading2.place(x=65.0, y=133.0, width=500.0, height=30.0)

        self.button_image_2 = PhotoImage(
            file=self.relative_to_assets("button_3.png"))
        restore_button = Button(
            self,
            image=self.button_image_2,
            borderwidth=0,
            highlightthickness=0,
            cursor="hand2",
            command= self.restore_Backup,
            relief="flat"
        )
        restore_button.place(
            x=65.0,
            y=165.0,
            width=175.0,
            height=40.0
        )


        self.resizable(False, False)
        self.bind("<Escape>", lambda key: self.destroy())
        self.mainloop()
    
    def browse_folder(self) -> Path:
        """Open folder dialog and save the selected path to INI file."""
        file_selected = filedialog.askopenfilename(parent=self, initialfile=".enc", filetypes=[("Backup File", "*.enc")], title="Select Backup File")
        if file_selected:
            self.backup_path_entry.config(state="normal")
            self.backup_path_entry.delete(0, 'end')
            self.backup_path_entry.insert(0, file_selected)
            self.backup_path_entry.config(state="readonly")
        return file_selected

    def relative_to_assets(self, path: str) -> Path:
        ASSETS_PATH = Path(generate_path(root_path, "UI", "assets", "frame11"))
        return ASSETS_PATH / Path(path)
    
    def restore_Backup(self):
        source_folder = database_path()
        encrypted_file_path = self.backup_path_entry.get().strip()
        if not encrypted_file_path:
            messagebox.showerror("value Error", f"Please select a backup file First", parent=self)
            return
        
        backup_dest = Path(encrypted_file_path).parent

        encryptor = BackupSystem(source_folder, backup_dest)
        success_decrypt = encryptor.perform_decrypt_and_restore(encrypted_file_path, "#67^8J}rUL")
        if success_decrypt:
            messagebox.showinfo("Restore Success", f"Backup Restored Successfully. \nRestart the Software", parent=self)
            sys.exit()         
        else:
            messagebox.showerror("Restore Failed", f"Backup Restored Failed", parent=self)


if __name__ == "__main__":
    Restore_ui()
