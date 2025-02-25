import os, requests, json


def save(video_info: dict):
    url = video_info['HD_video_url']
    author_username = video_info['author_username']
    video_byte_size = video_info['HD_size']
    save_path = os.path.join("Downloaded-Videos", f"{author_username}.mp4")

    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(save_path, 'wb') as f:
        print(f'Dumping video: {author_username}.mp4 -- File Size: {video_byte_size} bytes')
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
        f.close()
                
def request(target_url: str) -> dict:
    tiktok_download_website = "https://www.tikwm.com/api/"

    payload = {'url': target_url,
    'hd': '1'}
  
    headers = {
    'Cookie': 'current_language=en'
    }

    failed_response = True
    fail_count = 0
    while failed_response and fail_count < 10:
        response = requests.request("POST", tiktok_download_website, headers=headers, data=payload)
        response.raise_for_status()
        json_dict = json.loads(response.text)

        if json_dict['msg'] == 'success':
            failed_response = False
            break
        
        fail_count += 1
        print(f'Failed try {fail_count}, retrying...')
    
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
    
    return video_to_download

def load_tiktok_links(collection_name: str) -> list:
    with open(os.path.join('Text-Files', f'{collection_name}.txt'), "r") as file:
        url_list = file.readlines()
        file.close()
    
    for index, url in enumerate(url_list):
        fixed_url = url.replace('\n', '')
        url_list[index] = fixed_url
    
    return url_list

def structured_run():
    url_list = load_tiktok_links('Edits')
    for url in url_list:
        video_info_dictionary = request(target_url=url)
        save(video_info=video_info_dictionary)
    print('Download Complete')


if __name__ == '__main__':
    structured_run()