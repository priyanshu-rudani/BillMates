import sys
from pathlib import Path

if getattr(sys, 'frozen', False):  # Running as a PyInstaller EXE
    root_path = Path(sys.executable).parent
else:  # Running as a Python script
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))
 
from utilities.path_utils import *
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, filedialog
from utilities.backup import BackupSystem
from datetime import datetime


class Backup_ui(tk.Toplevel):
    def __init__(self, parent=None):
        super().__init__(master=parent)

        self.iconbitmap(generate_path("UI", "assets", "BillMates.ico"))
        self.title("Generate Backups")
        self.configure(bg = "#E7EBFF")
        center_window(self, 580, 500)
        self.grab_set() 
        self.focus()

        self.canvas = Canvas(
            self,
            bg = "#E7EBFF",
            height = 500,
            width = 580,
            bd = 0,
            highlightthickness = 0,
            relief = "ridge"
        )
        self.canvas.place(x = 0, y = 0)

        self.Folder_Path = Entry(
            self,
            bd=0,
            bg="#F5F5F5",
            fg="#000716",
            font=("VarelaRound Regular", 10),
            state="readonly",
            highlightthickness=0
        )
        self.Folder_Path.place(
            x=72.0,
            y=85.0,
            width=390.0,
            height=25.0
        )

        entry_image_1 = PhotoImage(
            file=self.relative_to_assets("entry_1.png"))
        entry_bg_1 = self.canvas.create_image(
            267.0,
            98.0,
            image=entry_image_1
        )

        button_image_1 = PhotoImage(
            file=self.relative_to_assets("button_1.png"))
        self.PathSelecter = Button(
            self,
            image=button_image_1,
            borderwidth=0,
            highlightthickness=0,
            cursor="hand2",
            command= self.browse_folder,
            relief="flat"
        )
        self.PathSelecter.place(
            x=477.0,
            y=80.0,
            width=35.0,
            height=35.0
        )

        button_image_2 = PhotoImage(
            file=self.relative_to_assets("button_2.png"))
        button_2 = Button(
            self,
            image=button_image_2,
            borderwidth=0,
            highlightthickness=0,
            cursor="hand2",
            command=self.generateBackup,
            relief="flat"
        )
        button_2.place(
            x=67.0,
            y=152.0,
            width=200.0,
            height=40.0
        )

        path = read_ini("BACKUP", "FolderPath")
        if path:
            self.Folder_Path.config(state="normal")
            self.Folder_Path.insert(0, path)
            self.Folder_Path.config(state="readonly")

        self.canvas.create_text(
            67.0,
            56.0,
            anchor="nw",
            text="Backup Location",
            fill="#000000",
            font=("VarelaRound Regular", 16 * -1)
        )

        self.LastBackup = self.canvas.create_text(
            68.0,
            205.0,
            anchor="nw",
            text="",
            fill="#5F5F5F",
            font=("VarelaRound Regular", 14 * -1)
        )

        Timestemp = read_ini("BACKUP", "lastbackup")
        if Timestemp != "None":
            self.canvas.itemconfig(self.LastBackup, text=f"Last backup at {Timestemp}")
        else:
            self.canvas.itemconfig(self.LastBackup, text="No last Backup Found")


        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.resizable(False, False)
        self.mainloop()


    def on_close(self):
        Folder = self.Folder_Path.get().strip()
        write_ini("BACKUP", "FolderPath", Folder)
        self.destroy()


    def browse_folder(self):
        """Open folder dialog and save the selected path to INI file."""
        folder_selected = filedialog.askdirectory(title="Browse Folder", parent=self)
        if folder_selected:
            self.Folder_Path.config(state="normal")
            self.Folder_Path.delete(0, 'end')
            self.Folder_Path.insert(0, folder_selected)
            self.Folder_Path.config(state="readonly")

            write_ini("BACKUP", "FolderPath", folder_selected)


    def relative_to_assets(self, path: str) -> Path:
        ASSETS_PATH = Path(generate_path(root_path, "UI", "assets", "frame11"))
        return ASSETS_PATH / Path(path)
    
    def generateBackup(self):
        self.update_idletasks()
        self.config(cursor="watch")
        source_folder = database_path()
        if not source_folder or not os.path.exists(source_folder):
            messagebox.showerror("Error", "Database folder not found!", parent=self)
            return
        
        backup_dest = read_ini("BACKUP", "FolderPath")

        password = "#67^8J}rUL"

        if password:
            try:
                encryptor = BackupSystem(source_folder, backup_dest)
                encrypted_file_path = encryptor.perform_backup_and_encrypt(password)
                if encrypted_file_path:
                    encryptor.cleanup_temp_zip()

                    backup = datetime.now().strftime("%d/%m/%Y : %H:%M:%S")
                    write_ini("BACKUP", "lastbackup", backup)
                    self.canvas.itemconfig(self.LastBackup, text=f"Last backup at {backup}")
                    
                    messagebox.showinfo("Backup Success", f"Backup Generated Successfully at {backup_dest}", parent=self)

                else:   
                    messagebox.showwarning("Backup Error", "Backup Generation process failed.", parent=self)
            except Exception as e:
                messagebox.showwarning("Backup Exception Error", f"Backup Generation failed. \n Error: {e}", parent=self)
        self.config(cursor="")


if __name__ == "__main__":
    Backup_ui(parent=None)