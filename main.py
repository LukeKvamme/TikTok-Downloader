import json, time, sys, os, requests, queue, threading, time
import tkinter as tk
from tkinter import scrolledtext, filedialog
from io import StringIO
from tqdm import tqdm

global_url_list = []
global_video_info_list_of_dicts = []
global_save_directory = os.getcwd() # idk what to default this to... Downloads/TikTok folder ?
global_start = 0
global_end = 0

'''
This provides the functionality to redirect the console output to the GUI terminal
'''
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
    def __init__(self, root):
        self.root = root
        self.root.title("TikTok Downloader")
        self.root.geometry("900x600")  # Initial size

        # Create a Queue for safe thread communication
        self.queue = queue.Queue()
        
        # Configure grid to be resizable
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        
        # Create buttons
        self.file_button = tk.Button(root, text="Open File", command=self.select_file)
        self.file_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.directory_button = tk.Button(root, text="Select Folder to Save Videos Into", command=self.select_directory)
        self.directory_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.run_button = tk.Button(root, text="Run", command=self.run_function)
        self.run_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        # Create scrolled text widget for terminal output
        self.terminal = scrolledtext.ScrolledText(root, wrap=tk.WORD, bg="black", fg="green")
        self.terminal.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        self.terminal.config(font=('Courier', 10))
        
        # Redirect standard output to the terminal widget
        self.redirect = RedirectText(self.terminal)
        sys.stdout = self.redirect

        # Print welcome message
        print("Welcome to my TikTok Downloader!\n")
        print("This is mainly for the purpose of mass-downloading videos from a Collection on TikTok")
        print("\t(But it will download any TikTok video as long as the .txt file is properly formatted with the TikTik links)")
        print("")
        print("There are three steps to run this program:")
        print("\n1. Use 'Open File' to browse and open a text file.")
        print("\t-Text file MUST be formatted in the following way (newline-delimited):")
        print("\t\thttps://www.tiktok.com/@vital.aep/video/7469497077328809238?is_from_webapp=1&sender_device=pc&web_id=7460963924301841950")
        print("\t\thttps://www.tiktok.com/@slickzz23/video/7466598583459040558?is_from_webapp=1&sender_device=pc&web_id=7460963924301841950")
        print("\t-There are tools online (and browser extensions) to help you create this text file.")
        print("\n2. Use 'Select Folder to Save Video Into' to choose the folder on disk where you would like to save the videos into.")
        print("3. Click 'Run' to download selected videos.")

        # Start checking the queue
        self.check_queue()

    def check_queue(self):
        try:
            while True:
                message = self.queue.get_nowait()
                if message == "DONE":
                    global global_end
                    global_end = time.time()
                    global global_start
                    print(f"\n-------->DOWNLOAD COMPLETE! Total Runtime: {global_end-global_start:.1f} seconds<--------\n")
                    self.run_button.config(state=tk.NORMAL)
                    self.run_button.config(text="Run")
                else:
                    print(message)
                
                self.terminal.see(tk.END)
        except queue.Empty:
            # Queue empty, all good
            pass
        # Schedule to check queue again
        self.root.after(100, self.check_queue)
    
    def select_file(self):
        print("=" * 80)
        print('\nPlease Select a Text File.\n')
        file_path = filedialog.askopenfilename(
            title="Open Text File",
            filetypes=[("Text files", "*.txt")]
        )
        
        if os.path.isfile(file_path):
            try:
                url_list = self.load_tiktok_links(file_path)
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
                print(f"File loaded successfully: {file_path}")
            except Exception as e:
                print(f"Error opening file: {e}")
        else:
            print("No file selected")
    
    def select_directory(self):
        print("=" * 80)
        directory_path = filedialog.askdirectory(
            title="Select Folder"
        )
        
        if os.path.isdir(directory_path):
            print(f"Selected directory: {directory_path}")
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
        # Disable the 'Run" button while it is running to not create multiple running threads
        self.run_button.config(state=tk.DISABLED)
        self.run_button.config(text="Running...", background="black")

        # Create the thread and Start it
        thread = threading.Thread(target=self.background_run)
        thread.daemon = True # Thread will close when main program exits
        thread.start()
    
    def background_run(self):
        # This will hurt many people to look at, but I know no other way...
        global global_url_list
        global global_save_directory
        global global_start
        self.queue.put("=" * 80)
        self.queue.put(f"\nDownloading TikToks to {global_save_directory}\n")

        # assigning to other vars so I do not accidentally change the global
        url_list = global_url_list 
        save_directory = global_save_directory
        
        global_start = time.time()
        video_info_list_of_dicts = self.request_content(target_url_list=url_list)
        self.save(video_info_list=video_info_list_of_dicts, save_directory=save_directory)
        self.queue.put("DONE")

    def save_video(self, video_url: str, save_directory: str, author_username: str, video_id: str):
        save_path = os.path.join(save_directory, f"{author_username}_{video_id}.mp4")

        response = requests.get(video_url, stream=True)
        response.raise_for_status()

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=(8192)): # 8 KB chunks
                if chunk:
                    f.write(chunk)
            f.close()


    def save_photos(self, save_directory: str, sound_url: str, image_url_list: list[str]):
        # Save the slideshow audio to the subdirectory
        try:
            response = requests.get(sound_url, stream=True)

            if response.status_code == 200:
                with open(os.path.join(save_directory, f"sound.mp4"), 'wb') as file:
                    for chunk in response.iter_content(chunk_size=(8192)): # 8 KB chunks
                        if chunk:
                            file.write(chunk)
                    file.close()
        except Exception as e:
            print(f"An Error Occurred While Downloading Slideshow Audio: {e}")
        
        # Save the slideshow photos to the subdirectory
        for index, image_url in enumerate(image_url_list):
            try:
                response = requests.get(image_url, stream=True)

                if response.status_code == 200:
                    with open(os.path.join(save_directory, f"{index}.jpg"), 'wb') as image_file:
                        image_file.write(response.content)
            except Exception as e:
                print(f"An Error Occurred While Downloading Slideshow Images: {e}")
 

    def save(self, video_info_list: list, save_directory: str):
            # Loop through the list of dict objects
            # Each dict contains the information of one video, so download it in chunks of 8 MB to disk
        num_tiktoks = len(video_info_list)
        tiktok_count = 0
        total_byte_size = 0
        for tiktok_info in tqdm(video_info_list, desc="Downloading Videos to Disk "):
            tiktok_count += 1
            self.queue.put(f"\nSaving TikTok {tiktok_count} out of {num_tiktoks} to disk.")

            HD_video_or_sound_url = tiktok_info['HD_video_or_sound_url']
            author_username = tiktok_info['author_username']
            tiktok_id = tiktok_info['tiktok_id']
            is_slideshow_tiktok = tiktok_info["image_url_list"]
            video_byte_size = tiktok_info['HD_size']
            total_byte_size += video_byte_size

            if not is_slideshow_tiktok:
                self.save_video(save_directory=save_directory, video_url=HD_video_or_sound_url ,author_username=author_username, video_id=tiktok_id)
            else:
                # Save directory needs to be altered if it is a slide show, will create a subdir of the slideshow containing .jpg and .mp4 audio
                photo_slideshow_save_path = os.path.join(save_directory, f"{author_username}_{tiktok_id}")
                if not os.path.isdir(photo_slideshow_save_path):
                    os.mkdir(photo_slideshow_save_path)
                
                self.save_photos(save_directory=photo_slideshow_save_path, sound_url=HD_video_or_sound_url, image_url_list=is_slideshow_tiktok)

            

        size = total_byte_size
        if size < 1024: # size less than 1 KB?
            size_str = f"{size} bytes"
        elif size < 1024*1024: # size less than 1 MB?
            size_str = f"{size/1024:.1f} KB"
        elif size < 1024*1024*1024: # size less than 1 GB?
            size_str = f"{size/(1024*1024):.1f} MB"
        else:
            size_str = f"{size/(1024*1024*1024):.1f} GB"
        self.queue.put("\n")
        self.queue.put(f"-->Download to Disk complete. Total Bytes written to Disk: {size_str}")
        self.queue.put("=" * 50)



    def request_content(self, target_url_list: list) -> dict:
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
            self.queue.put(f"\nMaking Request for video {vid_count} out of {num_vids}...")
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
                self.queue.put(f"Failed try {fail_count}, retrying... Website Message:\n\t{json_dict['msg']}")
            
            if failed_response:
                self.queue.put(f'Failed to download video: {target_url}')
                return
        
            # else, video json data successfully grabbed:
            HD_video_or_sound_url = json_dict['data']['hdplay'] # video url is relative path url, for that session. took a while to realize when trying to replicate using postman but it would not work
            HD_size_mb = json_dict['data']['hd_size']
            author_username = json_dict['data']['author']['nickname']
            tiktok_id = json_dict['data']['id']

            if "images" in json_dict['data']:
                image_url_list = json_dict['data']['images']
            else:
                image_url_list = False


            video_to_download = {
                "HD_video_or_sound_url": HD_video_or_sound_url,
                "HD_size": HD_size_mb,
                "author_username":  author_username,
                "tiktok_id": tiktok_id,
                "image_url_list": image_url_list
            }

            video_info_list.append(video_to_download)
        
        session.close()
        self.queue.put("\n")
        self.queue.put(">>Videos Grabbed, Closing HTTP Session and Beginning Write to Disk<<")
        self.queue.put("-" * 50)
        return video_info_list

    def load_tiktok_links(self, filepath: str) -> list:
        self.queue.put("\n")
        with open(filepath, "r") as file:
            url_list = file.readlines()
            file.close()
        
        for index, url in enumerate(url_list):
            fixed_url = url.replace('\n', '')
            url_list[index] = fixed_url
        
        return url_list



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
    
    # Restore standard output when application closes lol
    sys.stdout = sys.__stdout__