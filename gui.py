import tkinter as tk
from tkinter import scrolledtext, filedialog
import sys
from io import StringIO
import os
import utilities as util

class RedirectText:
    def __init__(self, text_widget):
        """Constructor that sets the text widget"""
        self.text_space = text_widget
        self.buffer = StringIO()

    def write(self, string):
        """Write text to the buffer and text widget"""
        self.buffer.write(string)
        self.text_space.insert(tk.END, string)
        self.text_space.see(tk.END)  # Auto-scroll to the end
    
    def flush(self):
        """Required for file-like objects"""
        pass

class TikTokDownloader:
    url_list = []
    video_info_list_of_dicts = []
    current_directory = os.getcwd()

    def __init__(self, root):
        self.root = root
        self.root.title("Terminal Output App")
        self.root.geometry("600x400")  # Initial size
        
        # Configure grid to be resizable
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_rowconfigure(2, weight=0)  # Run button row doesn't need to resize
        
        # Create buttons
        self.button1 = tk.Button(root, text="Open File", command=self.select_file)
        self.button1.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.button2 = tk.Button(root, text="Select Directory", command=self.select_directory)
        self.button2.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.button3 = tk.Button(root, text="Run", command=self.run_function)
        self.button3.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        # Create scrolled text widget for terminal output
        self.terminal = scrolledtext.ScrolledText(root, wrap=tk.WORD, bg="black", fg="green")
        self.terminal.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        self.terminal.config(font=('Courier', 10))
        
        # Redirect standard output to the terminal widget
        self.redirect = RedirectText(self.terminal)
        sys.stdout = self.redirect
        
        # Print welcome message
        print("TikTok Downloader\n")
        print("Use 'Open File' to browse and open a text file.")
        print("Use 'Select Directory' to choose the folder to save TikTok videos to on disk.")
        print("Click 'Run' to download selected videos.")

    @classmethod
    def get_url_list(cls):
        return cls.url_list
    @classmethod
    def set_url_list(cls, url_links_list: list):
        cls.url_list = url_links_list
        return cls # Not necessary
        
    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Open File",
            filetypes=[("Text files", "*.txt")]
        )
        
        if os.path.isfile(file_path):
            try:
                url_list = util.load_tiktok_links(filepath=file_path)
                self.set_url_list(url_links_list=url_list)

                # Clear terminal and show file content
                self.terminal.delete(1.0, tk.END)
                print(*url_list, sep='\n')
            except Exception as e:
                print(f"Error opening file: {e}")
        else:
            print("No file selected")
   
    
    def select_directory(self):
        directory_path = filedialog.askdirectory(
            title="Select Directory"
        )
        
        if os.path.isdir(directory_path):
            print(f"\nSelected directory: {directory_path}")
            
            # Display directory contents
            try:
                files = os.listdir(directory_path)
                print(f"Directory contains {len(files)} items:")
                for i, item in enumerate(files, 1):
                    item_path = os.path.join(directory_path, item)
                    if os.path.isdir(item_path):
                        print(f"{i}. 📁 {item} (Directory)")
                    else:
                        size = os.path.getsize(item_path)
                        if size < 1024:
                            size_str = f"{size} bytes"
                        elif size < 1024*1024:
                            size_str = f"{size/1024:.1f} KB"
                        else:
                            size_str = f"{size/(1024*1024):.1f} MB"
                        print(f"{i}. 📄 {item} ({size_str})")
                
                # Store the directory path for possible later use
                self.current_directory = directory_path
                return directory_path
            except Exception as e:
                print(f"Error reading directory: {e}")

        else:
            print("No directory selected")
    
    def run_function(self):
        """
        This function will be called when the Run button is clicked.
        Replace the code inside this function with your own predefined function.
        """
        print("RUNNING FUNCTION")
        urls = self.get_url_list()
        print(*urls, sep='\n')
        # video_info_list_of_dicts = util.request_content(target_url_list=TikTokDownloader.get_url_list())
        # util.save(video_info_list=video_info_list_of_dicts)
            

if __name__ == "__main__":
    root = tk.Tk()
    app = TikTokDownloader(root)
    
    # Add a menu for additional file operations
    menubar = tk.Menu(root)
    filemenu = tk.Menu(menubar, tearoff=0)
    filemenu.add_command(label="Open", command=app.select_file)
    filemenu.add_command(label="Select Directory", command=app.select_directory)
    filemenu.add_command(label="Run", command=app.run_function)
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=root.quit)
    menubar.add_cascade(label="File", menu=filemenu)
    root.config(menu=menubar)
    
    root.mainloop()
    
    # Restore standard output when application closes
    sys.stdout = sys.__stdout__