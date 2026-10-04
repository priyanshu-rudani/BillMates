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
from tkinter import ttk, messagebox

class TermsPopup(tk.Toplevel):
    """
    A scalable popup window (Toplevel) to input and save text with character
    and line limits. Ideal for terms and conditions or short notes.
    """
    MAX_CHARS = 355
    MAX_LINES = 5
    MAX_CHARS_PER_LINE = 71  # 355 / 5 = 71, using 71 for display

    def __init__(self, parent):
        """
        Initializes the popup window.

        Args:
            parent: The parent window (must be a tkinter root or another Toplevel).
        """
        super().__init__(parent)
        self.parent = parent
        self.result = None  # This will store the saved text

        # --- Window Configuration ---
        self.title("Enter Terms & Conditions")
        try:
            self.iconbitmap(generate_path("UI", "assets", "BillMates.ico"))
        except Exception:
            pass  # Skip icon if not found
        
        center_window(self, 450, 250)
        self.resizable(False, False)  # Prevent resizing

        # Make the window modal: it blocks interaction with the parent window
        self.transient(parent)
        self.grab_set()
        self.focus()

        self.bind("<Escape>", lambda key: self.destroy())

        # --- Widget Creation ---
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Label for the text area
        ttk.Label(
            main_frame, 
            text=f"Enter terms (max {self.MAX_LINES} lines, {self.MAX_CHARS} characters):"
        ).pack(anchor="w")

        # Text widget for multi-line input
        self.text_entry = tk.Text(
            main_frame, height=8, wrap="word", relief="solid", borderwidth=1
        )
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

        # Fill existing terms in the Text widget
        self._populate_terms()

        # --- Event Binding ---
        # Bind the key release event to our validation function
        self.text_entry.bind("<KeyRelease>", self._validate_text)

        # Run the validation once at the start to set the initial counter
        self._validate_text()

    def _validate_text(self, event=None):
        """
        Performs real-time validation on the text entry widget.
        Updates status label with line count based on 71 char per line limit.
        Does NOT modify text during typing.
        """
        try:
            final_widget_content = self.text_entry.get("1.0", "end-1c")
            current_chars = len(final_widget_content)
            
            # Calculate lines based on 71 chars per line wrapping
            projected_lines = self._calculate_projected_lines(final_widget_content)

            # Determine status color/warning
            status_text = f"Lines: {projected_lines}/{self.MAX_LINES} | Chars: {current_chars}/{self.MAX_CHARS}"
            
            # Add warning if exceeding limits
            if projected_lines > self.MAX_LINES:
                status_text += " ⚠ Line limit exceeded"
            if current_chars > self.MAX_CHARS:
                status_text += " ⚠ Char limit exceeded"

            self.status_label.config(text=status_text)

        except Exception as e:
            print(f"Validation error: {e}")
            self.status_label.config(text="Error in validation. Please check input.")

    def _calculate_projected_lines(self, text):
        """
        Calculate how many lines the text will wrap to based on MAX_CHARS_PER_LINE.
        """
        if not text.strip():
            return 0
        
        projected_lines = 0
        paragraphs = text.split('\n')
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
            
            words = paragraph.split()
            current_line_len = 0
            
            for word in words:
                word_len = len(word)
                space_len = 1 if current_line_len > 0 else 0
                
                if current_line_len + space_len + word_len > self.MAX_CHARS_PER_LINE:
                    # Word exceeds line, move to next line
                    if current_line_len > 0:
                        projected_lines += 1
                    current_line_len = word_len
                else:
                    current_line_len += space_len + word_len
            
            # Add remaining line
            if current_line_len > 0:
                projected_lines += 1
        
        return projected_lines

    def _on_save(self):
        """
        Saves the current text to the result variable and closes the popup.
        Validates and wraps text ONLY on save.
        """
        try:
            raw_content = self.text_entry.get("1.0", "end-1c").strip()
            
            # Enforce character limit
            if len(raw_content) > self.MAX_CHARS:
                raw_content = raw_content[:self.MAX_CHARS]

            # Ensure result is not empty
            if not raw_content:
                messagebox.showwarning("Empty Terms", "Please enter some terms and conditions.", parent=self)
                return

            # Check projected lines
            projected_lines = self._calculate_projected_lines(raw_content)
            
            if projected_lines > self.MAX_LINES:
                messagebox.showwarning(
                    "Line Limit Exceeded",
                    f"Your text will wrap to {projected_lines} lines, but maximum is {self.MAX_LINES} lines.\n\nPlease reduce your text or make it more concise.",
                    parent=self
                )
                return

            self.result = raw_content
            terms_conditions_lines = self._wrap_text(self.result, self.MAX_CHARS_PER_LINE, self.MAX_LINES)

            # Save to INI file
            for i, line in enumerate(terms_conditions_lines, start=1):
                if i > self.MAX_LINES:
                    break
                try:
                    write_ini("POLICY", f"line{i}", line)
                except Exception as e:
                    print(f"Error writing line {i} to INI: {e}")

            self.destroy()  # Close the Toplevel window

        except Exception as e:
            print(f"Save error: {e}")
            messagebox.showerror("Save Error", f"Failed to save terms: {e}", parent=self)

    def _wrap_text(self, para, max_line_length, max_lines):
        """
        Wraps the text into lines with a maximum length of max_line_length 
        and limits total lines to max_lines.
        """
        try:
            lines = []
            current_line = ""

            # Handle % escaping
            text = para.replace("%", "%%")
            paragraphs = text.splitlines()
            is_first_line = True

            for paragraph in paragraphs:
                words = paragraph.split()
                
                for word in words:
                    # Ensure word fits within line length
                    word = word[:int(max_line_length)]
                    
                    test_line = current_line + (" " if current_line else "") + word
                    
                    if len(test_line) <= max_line_length:
                        current_line = test_line
                    else:
                        # Save current line if it's not empty
                        if current_line:
                            if len(lines) >= max_lines:
                                return lines
                            
                            if is_first_line:
                                lines.append(current_line.rstrip())
                                is_first_line = False
                            else:
                                lines.append("   " + current_line.rstrip())
                        
                        # Start new line with current word
                        current_line = word

                # End of paragraph: save current line
                if current_line:
                    if len(lines) >= max_lines:
                        return lines
                    
                    if is_first_line:
                        lines.append(current_line.rstrip())
                        is_first_line = False
                    else:
                        lines.append("   " + current_line.rstrip())
                    
                    current_line = ""

            return lines

        except Exception as e:
            print(f"Text wrapping error: {e}")
            return [para[:int(max_line_length)] for _ in range(min(1, max_lines))]

    def _populate_terms(self):
        """
        Populate the text widget with existing terms from INI file.
        Fetches all lines, joins them, and breaks at . or ! delimiters.
        """
        try:
            self.text_entry.delete("1.0", tk.END)
            all_lines = []
            
            # Fetch all lines from INI
            for i in range(1, self.MAX_LINES + 1):
                try:
                    line = read_ini("POLICY", f"line{i}")
                    if line:
                        all_lines.append(line.lstrip())
                except Exception:
                    pass
            
            # Join all lines into single text
            full_text = ' '.join(all_lines)
            
            # Replace multiple spaces with single space
            full_text = ' '.join(full_text.split())
            
            # Break at . or ! and add newlines
            import re
            full_text = re.sub(r'([.!?])\s+', r'\1\n', full_text)
            
            self.text_entry.insert("1.0", full_text)
            self._validate_text()
            
        except Exception as e:
            print(f"Populate terms error: {e}")

    @staticmethod
    def ask_terms(parent):
        """
        Class method to easily create and show the dialog.
        This makes the calling code cleaner.

        Args:
            parent: The parent window.

        Returns:
            str or None: The text entered by the user, or None if the window is closed
                         without saving.
        """
        try:
            dialog = TermsPopup(parent)
            parent.wait_window(dialog)  # Wait until the dialog is closed

            if dialog.result is not None:
                # If the user clicked "Save"
                messagebox.showinfo(
                    "Success",
                    "Your Terms & Conditions have been successfully updated. \nThese new terms will be applied to all future documents and transactions.",
                    parent=parent
                )
                return dialog.result
            
            return None

        except Exception as e:
            print(f"Ask terms error: {e}")
            messagebox.showerror("Error", f"Failed to open Terms dialog: {e}", parent=parent)
            return None


# --- Example of how to use the scalable popup class ---
if __name__ == "__main__":
    app = tk.Tk()
    app.title("Main Application")
    try:
        app.iconbitmap(generate_path("UI", "assets", "BillMates.ico"))
    except Exception:
        pass

    app.grab_set()
    app.focus()
    center_window(app, 400, 200)

    TermsPopup.ask_terms(app)

    app.bind("<Escape>", lambda key: app.destroy())
    app.mainloop()