import sys
import os
from pathlib import Path

if getattr(sys, 'frozen', False):  # Running as a PyInstaller EXE
    root_path = Path(sys.executable).parent
else:  # Running as a Python script
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from utilities.path_utils import *
import tkinter as tk
from tkinter import ttk

class TermsPopup(tk.Toplevel):
    """
    A scalable popup window (Toplevel) to input and save text with character
    and line limits. Ideal for terms and conditions or short notes.
    """
    MAX_CHARS = 325
    MAX_LINES = 5

    def __init__(self, parent):
        """
        Initializes the popup window.

        Args:
            parent: The parent window (must be a tkinter root or another Toplevel).
            initial_text (str, optional): Text to pre-populate the entry box with.
                                          Defaults to "".
        """
        super().__init__(parent)
        self.parent = parent
        self.result = None  # This will store the saved text

        # --- Window Configuration ---
        self.title("Enter Terms & Conditions")
        self.iconbitmap(generate_path("UI", "assets", "BillMates.ico"))
        center_window(self, 450, 250)
        self.resizable(False, False) # Prevent resizing

        # Make the window modal: it blocks interaction with the parent window
        self.transient(parent)
        self.grab_set() 
        self.focus()

        self.bind("<Escape>", lambda key: self.destroy())

        # --- Widget Creation ---
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Label for the text area, using class constants for dynamic text
        ttk.Label(main_frame, text=f"Enter terms (max {self.MAX_LINES} lines, {self.MAX_CHARS} characters):").pack(anchor="w")

        # Text widget for multi-line input
        self.text_entry = tk.Text(main_frame, height=8, wrap="word", relief="solid", borderwidth=1)
        self.text_entry.pack(fill="both", expand=True, pady=5)

        # Frame for counter and button to keep them on the same line
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill="x", side="bottom")

        # Status label for character and line count
        self.status_label = ttk.Label(bottom_frame, text="")
        self.status_label.pack(side="left", anchor="w")

        # Save button
        save_button = ttk.Button(bottom_frame, text="Save", command=self._on_save)
        save_button.pack(side="right", anchor="e")

        # fill existing terms in the Text widget
        self._populate_terms()

        # --- Event Binding ---
        # Bind the key release event to our validation function
        self.text_entry.bind("<KeyRelease>", self._validate_text)

        # Run the validation once at the start to set the initial counter
        self._validate_text()

    def _validate_text(self, event=None):
        """
        Performs real-time validation on the text entry widget.
        Enforces character and line limits, auto-wraps long lines, and updates the status label.
        """
        # Get the current cursor position to restore it later
        cursor_pos = self.text_entry.index(tk.INSERT)
        original_content = self.text_entry.get("1.0", "end-1c")

        # --- Auto-wrap long lines ---
        max_line_len = self.MAX_CHARS / self.MAX_LINES
        reformatted_lines = []
        # Split by user-entered newlines to respect paragraphs
        for paragraph in original_content.split('\n'):
            line = paragraph
            while len(line) > max_line_len:
                # Find the last space to break the line at to avoid splitting words
                wrap_at = line.rfind(' ', 0, max_line_len)
                
                # If no space is found in the wrap-zone, we must do a hard break
                if wrap_at == -1:
                    wrap_at = max_line_len
                
                # Add the wrapped part to our list of lines
                reformatted_lines.append(line[:wrap_at])
                # The rest of the line becomes the new line to process
                line = line[wrap_at:].lstrip() # lstrip() removes leading space from the new line
            reformatted_lines.append(line) # Add the remainder of the paragraph

        # --- Enforce Total Line Limit ---
        if len(reformatted_lines) > self.MAX_LINES:
            reformatted_lines = reformatted_lines[:self.MAX_LINES]

        # Rejoin the lines into a single string
        content = '\n'.join(reformatted_lines)

        # --- Enforce Total Character Limit ---
        if len(content) > self.MAX_CHARS:
            content = content[:self.MAX_CHARS]

        # --- Update the text widget only if content has changed ---
        # This is crucial to prevent the cursor from jumping on every key press
        if content != original_content:
            self.text_entry.delete("1.0", "end")
            self.text_entry.insert("1.0", content)
            # Try to restore the cursor to its previous position
            try:
                self.text_entry.mark_set(tk.INSERT, cursor_pos)
            except tk.TclError:
                # If the cursor position is now invalid, place it at the end.
                self.text_entry.mark_set(tk.INSERT, tk.END)

        # --- Update Status Label ---
        # Always read the final content from the widget for the status update
        final_widget_content = self.text_entry.get("1.0", "end-1c")
        current_chars = len(final_widget_content)
        current_lines = len(final_widget_content.split('\n')) if final_widget_content else 0

        self.status_label.config(
            text=f"Lines: {current_lines}/{self.MAX_LINES} | Chars: {current_chars}/{self.MAX_CHARS}"
        )

    def _on_save(self):
        """
        Saves the current text to the result variable and closes the popup.
        """
        self.result = self.text_entry.get("1.0", "end-1c").strip()
        terms_conditions_lines = self._wrap_text(self.result, (self.MAX_CHARS/self.MAX_LINES), self.MAX_LINES)

        i = 1
        for line in terms_conditions_lines:
            write_ini("POLICY", f"line{i}", line)
            i += 1
            if i == 6:
                break

        self.destroy() # Close the Toplevel window

    def _wrap_text(self, pera, max_line_length, max_lines):
        """Wraps the text into lines with a maximum length of max_line_length and limits total lines to max_lines."""
        lines = []
        current_line = ""
        numbered = True  # Flag to track the first line of each paragraph

        text = pera.replace("%", "%%")
        paragraphs = text.splitlines()

        for paragraph in paragraphs:
            words = paragraph.split()
            for word in words:
                if len(current_line + " " + word) <= max_line_length:
                    if current_line:
                        current_line += " " + word
                    else:
                        current_line = word
                else:
                    if len(lines) >= max_lines:  # Stop adding lines if max_lines reached
                        return lines

                    if numbered:
                        lines.append(current_line.rstrip())  # First line without indentation
                        numbered = False
                    else:
                        lines.append("   " + current_line.rstrip())  # Indented subsequent lines

                    current_line = word  

            if current_line:
                if len(lines) >= max_lines:  # Stop adding lines if max_lines reached
                    return lines

                if numbered:
                    lines.append(current_line.rstrip())  
                else:
                    lines.append("   " + current_line.rstrip())  

            if len(lines) >= max_lines:  # Stop adding lines if max_lines reached
                return lines

            current_line = ""
            numbered = True  

        return lines

    def _populate_terms(self):
        self.text_entry.delete(1.0, tk.END)
        self.text_entry.insert(tk.END, read_ini("POLICY", "line1") + "\n")
        self.text_entry.insert(tk.END, read_ini("POLICY", "line2") + "\n")
        self.text_entry.insert(tk.END, read_ini("POLICY", "line3") + "\n")
        self.text_entry.insert(tk.END, read_ini("POLICY", "line4") + "\n")
        self.text_entry.insert(tk.END, read_ini("POLICY", "line5"))

    @staticmethod
    def ask_terms(parent):
        """
        Class method to easily create and show the dialog.
        This makes the calling code cleaner.

        Args:
            parent: The parent window.
            initial_text (str, optional): Initial text for the dialog.

        Returns:
            str or None: The text entered by the user, or None if the window is closed
                         without saving.
        """
        dialog = TermsPopup(parent)
        parent.wait_window(dialog) # Wait until the dialog is closed

        if dialog.result is not None:
            # If the user clicked "Save"
            messagebox.showinfo(
                "Success", 
                "Your Terms & Conditions have been successfully updated. \nThese new terms will be applied to all future documents and transactions.", 
                parent=parent
            )


# --- Example of how to use the scalable popup class ---
if __name__ == "__main__":
    app = tk.Tk()
    app.title("Main Application")
    app.iconbitmap(generate_path("UI", "assets", "BillMates.ico"))
    app.grab_set() 
    app.focus()
    center_window(app, 400, 200)

    TermsPopup.ask_terms(app)

    app.bind("<Escape>", lambda key: app.destroy())
    app.mainloop()

# terms_conditions
