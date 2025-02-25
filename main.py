import os, requests, json, time
from tqdm import tqdm


def save(video_info_list: list):
        # Loop through the list of dict objects
        # Each dict contains the information of one video, so download it in chunks of 8 MB to disk
    total_byte_size = 0
    for video_info in tqdm(video_info_list, desc="Downloading Videos to Disk "):
        url = video_info['HD_video_url']
        author_username = video_info['author_username']
        video_byte_size = video_info['HD_size']
        total_byte_size += video_byte_size
        save_path = os.path.join("Downloaded-Videos", f"{author_username}.mp4")

        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    # print(f'Chunking.... {video_byte_size-8192} bytes left')
                    # video_byte_size -= 8192
            f.close()
    
    print(f"-->Download to Disk complete. Total Bytes written to Disk: {total_byte_size}")
                
def request_content(target_url_list: list) -> dict:
    tiktok_download_website = "https://www.tikwm.com/api/"
    session = requests.Session()
    session.headers.update({
        'Cookie': 'current_language=en'
    })
    video_info_list = [] # This will become a list of dictionary objects, each dict is info of one tiktok (incl. download link)

        # Loop through list of TikTok URL's
        # Make a request (using same HTTP session for speed and efficiency)
        # Download JSON, create dict of HD-Video-URL, HD-Video-Byte-Size, Author-Username (for file naming)
    for target_url in tqdm(target_url_list, desc="Initiated Session, making Session requests "):
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
    print("-->Videos Grabbed, Closing Session")
    return video_info_list

def load_tiktok_links(collection_name: str) -> list:
    with open(os.path.join('Text-Files', f'{collection_name}.txt'), "r") as file:
        url_list = file.readlines()
        file.close()
    
    for index, url in enumerate(url_list):
        fixed_url = url.replace('\n', '')
        url_list[index] = fixed_url
    
    return url_list

def structured_run():
    print('\n')
    start = time.time()
    url_list = load_tiktok_links('Edits')
    video_info_list_of_dicts = request_content(target_url_list=url_list)
    save(video_info_list=video_info_list_of_dicts)
    end = time.time()
    print(f'-->Runtime: {round( (end-start), 2 )} seconds\n')



if __name__ == '__main__':
    structured_run()