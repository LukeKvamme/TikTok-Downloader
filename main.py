import json, time, sys, os, requests, queue, threading, time, random
import tkinter as tk
from tkinter import scrolledtext, filedialog
from io import StringIO
from tqdm import tqdm
import urllib
import urllib3
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

global_url_list = []
global_video_info_list_of_dicts = []
global_save_directory = os.getcwd() # idk what to default this to... Downloads/TikTok folder ?
global_start = 0
global_end = 0
global_total_byte_size = 0
global_already_processed_list = []

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

        # Start checking the queue, now just calling self.queue.put() will place the text to print in the terminal in the queue
        self.check_queue()

    def check_queue(self):
        try:
            while True:
                message = self.queue.get_nowait()

                # print the final runtime
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
        # Schedule to check queue again in 100 ms
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
                # IDK HOW ELSE TO CHANGE 😭😭 I tried making it a class var, but could not get it to work
                # I can only blame my own incompetence and lack of knowledge
                global global_url_list
                url_list = self.load_tiktok_links(file_path)
                global_url_list = url_list

                # Clear terminal and show file content... maybe use? Kind of nice to see everything, can scroll anyways
                # self.terminal.delete(1.0, tk.END)
                print(f"Opened file: {os.path.basename(file_path)}")
                print("-" * 50)
                print(*url_list, sep="\n")
                print("-" * 50)
                print(f"File loaded successfully: {file_path}")
                print(f"TikTok URL's loaded from file: {len(url_list)}")
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

            already_processed_list = []
            
            # Display directory contents
            try:

                files = os.listdir(directory_path)
                print(f"Directory contains {len(files)} items:")

                for i, item in enumerate(files, 1):

                    item_path = os.path.join(directory_path, item)

                    if os.path.isdir(item_path):
                        print(f"{i}. 📁 {item} (Directory)")

                    else:
                        if '.mp4' in os.path.basename(item_path):
                            already_processed_list.append(os.path.basename(item_path))

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
                
                #
                # Remove TikTok URL's that are already present in the folder (don't need to re-download)
                #
                global global_url_list
                url_list = global_url_list
                already_downloaded_ids = []
                for already_processed_tiktok in already_processed_list:
                    str_no_mp4 = already_processed_tiktok.split('.mp4')[0]
                    str_just_id = str_no_mp4.split('_')[-1]
                    already_downloaded_ids.append(str_just_id)
                
                replaced_url_list = []
                for url in url_list:
                    already_processed = False

                    for bad_id in already_downloaded_ids:
                        if bad_id in url:
                            already_processed = True
                    
                    if not already_processed:
                        replaced_url_list.append(url)
                
                global_url_list = replaced_url_list

                # Store the directory path for possible later use
                self.current_directory = directory_path
                return directory_path
            except Exception as e:
                print(f"Error reading directory: {e}")

        else:
            print("No Folder/Directory selected")
    
    def is_valid_url(self, url: str):
        '''
        Checks if the TikTok URL is valid (it has not been deleted / taken down / privated)
        '''

        try:
            result = urllib.parse.urlparse(url)
            is_valid = result.scheme in ('http', 'https') and result.netloc
            return is_valid
        except Exception:
            return False


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
        tiktok_counter = 0
        tiktok_count_total = len(url_list)
        
        # create a re-usable session, then pass it through the request + save functions
        # 'with' makes it automatically close out of the session at the end
        # > has a sleep function to be nice internet citizens and to help evade rate limiters
        with requests.Session() as session:

            # configure the session to allow for Retry capabilities
            retry_saving_incase_failure = Retry(
                total=3,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET", "POST"],
                backoff_factor=1 # backoff factor is for delay in retry --> (backoff_factor) * (2 ^ (retries_already - 1) )
            )

            adapter = HTTPAdapter(max_retries=retry_saving_incase_failure)
            session.mount("https://", adapter)
            session.mount("http://", adapter)

            for target_url in url_list:
                if tiktok_counter != 0 and tiktok_counter % 5 == 0:
                    self.queue.put("Sleeping to evade rate limit detection")
                    time.sleep(5 + random.uniform(0,3))

                    # if URL is invalid, skip it and continue
                if not self.is_valid_url(target_url):
                    continue
                else:
                    tiktok_info_dict = self.request_content(session=session, target_url=target_url)

                    if tiktok_info_dict:
                        self.save(session=session, tiktok_info_dict=tiktok_info_dict, save_directory=save_directory)
                        self.queue.put(f"--> Successfully Saved to Disk...\n")
                    else:
                        self.queue.put(f'\n\tSkipping to next URL...\n')

                tiktok_counter += 1
                self.queue.put(f"----- TikToks Downloaded: {tiktok_counter} out of {tiktok_count_total}: {(tiktok_counter/tiktok_count_total)*100:.1f}% completed -----")
            
        self.queue.put("DONE")

        # Print out the total Download size
        global global_total_byte_size
        size = global_total_byte_size

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


    def save_video(self, session, video_url: str, save_directory: str, author_username: str, unique_tiktok_id: str):
        save_path = os.path.join(save_directory, f"{author_username}_{unique_tiktok_id}.mp4")
        temp_path = f"{save_path}.temp"
        downloaded_size = 0
        resume_download = False # track if need to resume the download (chunking errors can happen from losing connection mid-download)

        try:
            # check if a temp file exists --> means we got a chunking error from lost connection, will try to resume if so
            if os.path.exists(temp_path):
                downloaded_size = os.path.getsize(temp_path)
                resume_download = True
                self.queue.put(f"Attempting to resume download from byte {downloaded_size}")
            
            # setting headers for resuming, but not using session.headers.udpate({}) because that would change the persistent headers btwn reqs
            headers = {}
            if resume_download:
                headers['Range'] = f'bytes={downloaded_size}-'
            
            session.headers.update({
                'Cookie': 'current_language=en'
            })
            
            response = session.get(
                video_url,
                stream=True,
                headers=headers,
                timeout=(10, 30) # increasing the timeout value to 10 for connection
            )

            # idk if this server accepts 'range' requests, but will check anyways
            if resume_download and response.status_code != 206:
                # if status code is not 206, then status code is not partial accept --> need to start over
                downloaded_size = 0
                resume_download = False
            
            # mode == 'ab' if it can resume (append mode), 'wb' if it has to restart (write bytes mode, normal writing mode)
            if resume_download:
                mode = 'ab'
            else:
                mode = 'wb'

            # open the file in append / write mode, then process the response in chunks
            with open(temp_path, mode) as file:
                for chunk in response.iter_content(chunk_size=(8192)):
                    if chunk: # filtering out keep-alive chunks
                        file.write(chunk)
            
            # if this is reached, then we successfully wrote all the chunks and the HTTPAdapter retry does not reach here since it would
            # have already restarted by now, so we can return True and fix the temp pathing
            os.replace(temp_path, save_path)
            return True
        
        # handle exceptions that may occur during this process
        except requests.exceptions.ChunkedEncodingError as e:
            # This is the main baddie, we return False to indicate failure --> But the temp_path file is kept so the next attempt will retry
            print(f"Encountered an incomplete read error (unique ID: {unique_tiktok_id}): {e}")
            return False
        
        except Exception as e:
            # If this happens, then something truly catastrophic occurred so we will delete the temp_path, return False, and give up
            print(f"An Error Occurred While Downloading TikTok Video (unique ID: {unique_tiktok_id}): {e}")

            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False

    def save_photos(self, session, save_directory: str, sound_url: str, image_url_list: list[str], unique_tiktok_id: str):
        # Save the slideshow audio to the subdirectory
        try:
            response = session.get(
                sound_url,
                stream=True,
                timeout=(5, 30) # 5 secs to connect, 30 secs to read
            )
            response.raise_for_status()
            
            if response.status_code == 200:
                with open(os.path.join(save_directory, f"sound.mp4"), 'wb') as file:
                    for chunk in response.iter_content(chunk_size=(8192)): # 8 KB chunks
                        if chunk:
                            file.write(chunk)
                    file.close()
            response.close()
        except Exception as e:
            print(f"An Error Occurred While Downloading Slideshow Audio: {e}")
        
        # Save the slideshow photos to the subdirectory
        for index, image_url in enumerate(image_url_list):
            try:
                response = session.get(image_url, stream=True)

                if response.status_code == 200:
                    with open(os.path.join(save_directory, f"{index}.jpg"), 'wb') as image_file:
                        image_file.write(response.content)
            except Exception as e:
                print(f"An Error Occurred While Downloading Slideshow Images (unique ID: {unique_tiktok_id}): {e}")
        
    def save(self, session, tiktok_info_dict: dict, save_directory: str):
            # Loop through the list of dict objects
            # Each dict contains the information of one video, so download it in chunks to disk

        HD_video_or_sound_url = tiktok_info_dict['HD_video_or_sound_url']
        author_username = tiktok_info_dict['author_username']
        tiktok_id = tiktok_info_dict['tiktok_id'] # every tiktok has a unique tiktok id
        is_slideshow_tiktok = tiktok_info_dict["image_url_list"]
        tiktok_byte_size = tiktok_info_dict['HD_size']
    

        if not is_slideshow_tiktok:
            self.queue.put(f"\nSaving TikTok Video to disk.")
            self.queue.put(f"This may take a bit depending on if the session has to retry during chunking or file size.")
            self.save_video(
                session=session,
                save_directory=save_directory,
                video_url=HD_video_or_sound_url,
                author_username=author_username,
                unique_tiktok_id=tiktok_id
            )
        else:
            # Save directory needs to be altered if it is a slide show, will create a subdir of the slideshow containing .jpg and .mp4 audio
            photo_slideshow_save_path = os.path.join(save_directory, f"{author_username}_{tiktok_id}")
            if not os.path.isdir(photo_slideshow_save_path):
                os.mkdir(photo_slideshow_save_path)
            
            self.queue.put(f"\nSaving TikTok Picture Slideshow to disk as its own subdirectory.")
            self.queue.put(f"The Audio will be its own .mp4 file within the subdirectory with the images...")
            self.queue.put(f"If there is no audio file, then the audio has been removed / deleted on TikTok itself.")
            self.save_photos(
                session=session,
                save_directory=photo_slideshow_save_path,
                sound_url=HD_video_or_sound_url,
                image_url_list=is_slideshow_tiktok,
                unique_tiktok_id=tiktok_id
            )
    
        global global_total_byte_size
        global_total_byte_size += tiktok_byte_size

    def request_content(self, session, target_url: list) -> dict:
        self.queue.put(f"\nMaking Request for TikTok.\nTarget URL:\t{target_url}")
        
        tiktok_download_website = "https://www.tikwm.com/api/"
        payload = {
            'url': target_url,
            'hd': '1'
        }
    
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
            elif json_dict['code'] == -1:
                failed_response = True
                break
            
            fail_count += 1
            self.queue.put(f"Failed try {fail_count}, retrying... Website Message:\n\t{json_dict['msg']}")
        
        if failed_response:
            if json_dict['msg'] == "Url parsing is failed! Please check url.":
                self.queue.put(f"\n\tINVALID TIKTOK URL:\t{target_url}\n\tIt has either been deleted, taken down, or privated.")
            else:
                self.queue.put(f'Failed to download TikTok for unknown reason: {target_url}')
            return False
    
        # else, video json data successfully grabbed:
        HD_video_or_sound_url = json_dict['data']['hdplay'] # video url is relative path url, for that session. took a while to realize when trying to replicate using postman but it would not work
        HD_size_mb = json_dict['data']['hd_size']
        author_username = json_dict['data']['author']['unique_id']
        tiktok_id = json_dict['data']['id']

            # I have later discovered that the TikTok URL itself does in fact contain 'video' or 'photo' to denote
            # the type.... bruh
        if "images" in json_dict['data']:
            image_url_list = json_dict['data']['images']
        else:
            image_url_list = False

        if author_username[0] == ".":
            author_username = author_username[1:]

        tiktok_to_download = {
            "HD_video_or_sound_url": HD_video_or_sound_url,
            "HD_size": HD_size_mb,
            "author_username":  author_username,
            "tiktok_id": tiktok_id,
            "image_url_list": image_url_list
        }

        return tiktok_to_download

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
    
    # Add a menu (top of screen on Mac, not sure where this is on Windows ngl) for additional file operations
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