import json
import time
import tkinter as tk
from tkinter import scrolledtext, filedialog
import sys
from io import StringIO
import os
import requests
from tqdm import tqdm

global_url_list = []
global_video_info_list_of_dicts = []
global_save_directory = os.getcwd() # idk what to default this to... Downloads/TikTok folder ?

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

class Utilities:
    def save(video_info_list: list, save_directory: str):
            # Loop through the list of dict objects
            # Each dict contains the information of one video, so download it in chunks of 8 MB to disk
        num_videos = len(video_info_list)
        vid_count = 0
        total_byte_size = 0
        for video_info in tqdm(video_info_list, desc="Downloading Videos to Disk "):
            vid_count += 1
            print(f"\nSaving video {vid_count} out of {num_videos} to disk.")

            url = video_info['HD_video_url']
            author_username = video_info['author_username']
            video_byte_size = video_info['HD_size']
            total_byte_size += video_byte_size
            save_path = os.path.join(save_directory, f"{author_username}.mp4")

            response = requests.get(url, stream=True)
            response.raise_for_status()

            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=(8192)): # 8 KB chunks
                    if chunk:
                        f.write(chunk)
                f.close()
        
        print("\n")
        print(f"-->Download to Disk complete. Total Bytes written to Disk: {total_byte_size}")
        print("-" * 50)
                    
    def request_content(target_url_list: list) -> dict:
        tiktok_download_website = "https://www.tikwm.com/api/"
        session = requests.Session()
        session.headers.update({
            'Cookie': 'current_language=en'
        })
        # This will become a list of dictionary objects, each dict is info of one tiktok (incl. download link)
        video_info_list = []
        num_vids = len(target_url_list)
        vid_count = 0

            # Loop through list of TikTok URL's
            # Make a request (using same HTTP session for speed and efficiency)
            # Download JSON, create dict of HD-Video-URL, HD-Video-Byte-Size, Author-Username (for file naming)
        for target_url in tqdm(target_url_list, desc="Initiated Session, making Session requests "):
            vid_count += 1
            print(f"\nMaking Request for video {vid_count} out of {num_vids}...")
            payload = {'url': target_url,
            'hd': '1'}
        
            failed_response = True
            fail_count = 0
            while failed_response and fail_count < 100:
                response = session.request("POST", tiktok_download_website, data=payload)
                time.sleep(1) # Free API is limited to 1 request per second, must delay between requests
                response.raise_for_status()
                json_dict = json.loads(response.text)

                if json_dict['msg'] == 'success':
                    failed_response = False
                    break
                
                fail_count += 1
                print(f"Failed try {fail_count}, retrying... Website Message:\n\t{json_dict['msg']}")
            
            if failed_response:
                print(f'Failed to download video: {target_url}')
                return
        
            # else, video json data successfully grabbed:
            HD_video_url = json_dict['data']['hdplay']
            HD_size_mb = json_dict['data']['hd_size']
            author_username = json_dict['data']['author']['nickname']

            video_to_download = {
                "HD_video_url": HD_video_url,
                "HD_size": HD_size_mb,
                "author_username":  author_username
            }

            video_info_list.append(video_to_download)
        
        session.close()
        print("\n")
        print(">>Videos Grabbed, Closing HTTP Session<<")
        print("-" * 50)
        return video_info_list

    def load_tiktok_links(filepath: str) -> list:
        with open(filepath, "r") as file:
            url_list = file.readlines()
            file.close()
        
        for index, url in enumerate(url_list):
            fixed_url = url.replace('\n', '')
            url_list[index] = fixed_url
        
        return url_list


class TikTokDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("TikTok Downloader")
        self.root.geometry("800x400")  # Initial size
        
        # Configure grid to be resizable
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        
        # Create buttons
        self.button1 = tk.Button(root, text="Open File", command=self.select_file)
        self.button1.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.button2 = tk.Button(root, text="Select Folder to Save Videos Into", command=self.select_directory)
        self.button2.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.button3 = tk.Button(root, text="Run", command=self.run_function)
        self.button3.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        # Create scrolled text widget for terminal output
        self.terminal = scrolledtext.ScrolledText(root, wrap=tk.WORD, bg="black", fg="green")
        self.terminal.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        self.terminal.config(font=('Courier', 10))
        
        self.utilities = Utilities()
        # Redirect standard output to the terminal widget
        self.redirect = RedirectText(self.terminal)
        sys.stdout = self.redirect

        
        # Print welcome message
        print("TikTok Downloader\n")
        print("Use 'Open File' to browse and open a text file.")
        print("Use 'Select Directory' to choose the folder to save TikTok videos to on disk.")
        print("Click 'Run' to download selected videos.")
        
    def select_file(self):
        print('\nYou have chosen select a file.\n')
        file_path = filedialog.askopenfilename(
            title="Open Text File",
            filetypes=[("Text files", "*.txt")]
        )
        
        if os.path.isfile(file_path):
            try:
                url_list = Utilities.load_tiktok_links(filepath=file_path)
                    # IDK HOW ELSE TO CHANGE 😭😭 I tried making it a class var, but could not get it to work
                    # I can only blame my own incompetence and lack of knowledge
                global global_url_list
                global_url_list = url_list

                # Clear terminal and show file content... maybe use? Kind of nice to see everything, can scroll anyways
                # self.terminal.delete(1.0, tk.END)
                print(f"Opened file: {os.path.basename(file_path)}")
                print("-" * 50)
                print(*url_list, sep="\n")
                print("-" * 50)
                print(f"File loaded successfully: {file_path}\n")
            except Exception as e:
                print(f"Error opening file: {e}")
        else:
            print("No file selected")
    
    def select_directory(self):
        directory_path = filedialog.askdirectory(
            title="Select Folder"
        )
        
        if os.path.isdir(directory_path):
            print(f"\nSelected directory: {directory_path}")
                # I am sorry for what sin I must commit here...
            global global_save_directory
            global_save_directory = directory_path
            
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
                        if size < 1024: # size less than 1 KB?
                            size_str = f"{size} bytes"
                        elif size < 1024*1024: # size less than 1 MB?
                            size_str = f"{size/1024:.1f} KB"
                        elif size < 1024*1024*1024: # size less than 1 GB?
                            size_str = f"{size/(1024*1024):.1f} MB"
                        else:
                            size_str = f"{size/(1024*1024*1024):.1f} GB"
                        print(f"{i}. 📄 {item} ({size_str})")
                
                # Store the directory path for possible later use
                self.current_directory = directory_path
                return directory_path
            except Exception as e:
                print(f"Error reading directory: {e}")

        else:
            print("No Folder/Directory selected")
    
    def run_function(self):
        """
        This function will be called when the Run button is clicked.
        """
            # This will hurt many people to look at, but I know no other way...
        global global_url_list
        global global_save_directory
        print(f"\nRunning....Downloading TikToks to {global_save_directory}\n")
            # assigning to other vars so I do not accidentally change the global
        url_list = global_url_list 
        save_directory = global_save_directory
        
        video_info_list_of_dicts = Utilities.request_content(target_url_list=url_list)
        Utilities.save(video_info_list=video_info_list_of_dicts, save_directory=save_directory)
        print("\nFINISHED RUNNING FUNCTION. THERE ARE NO MORE COMMANDS BELOW THIS LINE OF CODE.\n")
        # video_info_list_of_dicts = util.request_content(target_url_list=TikTokDownloader.get_url_list())
        # util.save(video_info_list=video_info_list_of_dicts)
            

if __name__ == "__main__":
    sys.stdout = sys.__stdout__
    root = tk.Tk()
    app = TikTokDownloader(root)
    
    # Add a menu (top of screen) for additional file operations
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