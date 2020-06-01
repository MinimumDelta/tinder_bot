from multiprocessing import Pool
import requests  # api interaction
import json  # api payloads
import time
import os
import datetime
import shutil  # image downloader

# internal imports
import bot_config


class Profile:
    def __init__(self, name, age, distance, bio, profile_images, instagram_images):
        self.name = name
        self.age = age
        self.distance = distance
        self.bio = bio
        self.profile_images = profile_images
        self.instagram_images = instagram_images


def send_otp_code(phone_number):
    data = {'phone_number': phone_number}
    req = requests.post(bot_config.CODE_REQUEST_URL, headers=bot_config.HEADERS, data=json.dumps(data))
    response = req.json()
    try:
        return response.get("data")['sms_sent']
    except Exception:
        return ""


def get_refresh_token(otp_code, phone_number):
    data = {'otp_code': otp_code, 'phone_number': phone_number}
    req = requests.post(bot_config.CODE_VALIDATE_URL, headers=bot_config.HEADERS, data=json.dumps(data))
    response = req.json()
    try:
        return response.get("data")["refresh_token"]
    except Exception:
        return ""


def get_api_token(input_refresh_token):
    data = {'refresh_token': input_refresh_token}
    req = requests.post(bot_config.TOKEN_URL, headers=bot_config.HEADERS, data=json.dumps(data))
    response = req.json()
    return response.get("data")["api_token"]


def get_token_if_exist():
    if not os.path.isfile(bot_config.TOKEN_FILE_NAME): return ''  # no file
    with open(bot_config.TOKEN_FILE_NAME, 'r') as istream:
        for line in istream:
            if ' ' not in line.strip() and len(line) > bot_config.MIN_TOKEN_LENGTH:
                return line.strip()
    return ''  # no key found


def generate_new_token():
    phone_number = input(
        "[INPUT] Please enter your phone number under the international format (country code + number): ")
    if send_otp_code(phone_number) is "":
        print("[ERROR] Input rejected.")
        return ''
    otp_code = input("[INPUT] Please enter the code you've received by sms: ")
    ret_refresh_token = get_refresh_token(otp_code, phone_number)
    if ret_refresh_token is '':
        print("[ERROR] Code rejected.")
        return ''

    ret_token = get_api_token(ret_refresh_token)

    print(f"[INFO] Your new Tinder token is: {ret_token}")
    try:
        with open(bot_config.TOKEN_FILE_NAME, 'w') as ostream:
            ostream.write(f"{ret_token}\n"
                          f"DELETE THIS FILE IN ORDER TO FORCE NEW KEY RETRIEVAL\n"
                          f"DO NOT MODIFY THIS FILE")
        print("[INFO] Your token has been stored for future use.")
    except Exception as e:
        print(f"[ERROR] Unable to save token. |=> {e}")
    return ret_token


def is_valid_response_status(request_obj):
    return request_obj.json()["status"] == 200


def print_formatted_json(json_obj):
    print(json.dumps(json_obj, sort_keys=True, indent=4))


def get_persons():
    req = requests.get(bot_config.GET_USERS_URL, headers=INTERNAL_HEADERS)
    persons_dict = {}
    if is_valid_response_status(req):
        for entry in req.json()["results"]:
            uid = entry["_id"]
            if uid in persons_dict: continue  # name, age, profile_images, instagram_images
            name = entry["name"]

            age = datetime.datetime.now().year - int(
                entry["birth_date"].split('-')[0]) - 1 if "birth_date" in entry and len(
                entry["birth_date"]) > 4 else 99
            distance = int(entry["distance_mi"]) if "distance_mi" in entry and entry["distance_mi"] >= 0 else -1
            bio = entry["bio"] if "bio" in entry else ""

            profile_images = []
            for photo in entry["photos"]:
                profile_images.append(photo["url"])

            instagram_images = []
            try:
                if "instagram" in entry and "photos" in entry["instagram"]:
                    for photo in entry["instagram"]["photos"]:
                        if "image" in photo:  # sometimes the nodes dont contain pictures for some reason
                            instagram_images.append(photo["image"])
            except Exception as e:
                print(f"[ERROR] Unable to fetch Instagram data from profile. Dumping JSON data. |=> {e}")
                print_formatted_json(entry)

            persons_dict[uid] = Profile(name, age, distance, bio, profile_images, instagram_images)
    else:
        print("[ERROR] Invalid response code when fetching new batch of profiles. "
              "Consider generating a new auth token if this error persists.")
    return persons_dict


def swipe(uid, right):
    try:
        url = bot_config.LIKE_USER_URL if right else bot_config.DISLIKE_USER_URL
        req = requests.get('{}/{}'.format(url, uid), headers=INTERNAL_HEADERS)
        if not is_valid_response_status(req):
            print("[ERROR]\t\tSwipe rejected, consider generating a new auth token if this happens again.")
    except Exception as e:
        print(f"[ERROR]\t\tSwipe failed due to unhandled error. |=> {e}")


def write_image_file(instagram, url, age, uid, index, total):
    r = requests.get(url, stream=True)
    if r.status_code == 200:  # success
        r.raw.decode_content = True
        file_extension = url.split('?')[0].split('.')[-1] if instagram else url.split('.')[-1]
        path = f'{bot_config.IMAGE_OUTPUT_PATH}/{age}'
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except Exception as e:
                print(
                    f"[WARN] Thread collision when checking if path exists. |=> {e}")  # not a big deal, happens occasionally
        try:
            filename = "{}/{}_{}_{}.{}".format(path, uid, "IG" if instagram else "PP", index, file_extension)
            with open(filename, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        except Exception as e:
            print(f"[WARN] Unable to write file to disk, skipping file. |=> {e}")
    else:
        print("[WARN]\t\tFailed to download {} picture {}/{} from uid {}.".format(
            "Instagram" if instagram else "profile",
            index + 1, total, uid))


def start_bot(token_input):
    print(f"[INFO] Starting bot with {bot_config.POOL_WORKERS} workers..")
    INTERNAL_HEADERS['x-auth-token'] = token_input
    now = datetime.datetime.now()
    filename = f"{bot_config.DATA_OUTPUT_PATH}/data_{now.day}-{now.month}-{now.year}__{now.hour}-{now.minute}-{now.second}.txt"
    ostream = open(filename, 'a+',
                   encoding=bot_config.DATA_OUTPUT_ENCODING)
    ostream.write(''.format())  # TODO print bot config settings
    swipes = 0
    fails = 0
    with Pool(min(bot_config.POOL_WORKERS, bot_config.MAX_POSSIBLE_PROFILE_IMAGES)) as pool:
        while True:
            persons = get_persons()
            if len(persons) <= 0:
                if fails < bot_config.EMPTY_RESPONSE_ATTEMPTS:
                    print("[INFO] No matches returned, trying again in two seconds...")
                    fails += 1
                    time.sleep(2)  # seconds
                    continue
                else:
                    print("[ERROR] No matches returned, ending script. Consider generating a new token or changing "
                          "swipe location.")
                    break
            else:
                fails = 0

            print(f"[INFO] =====> Fetched new batch of {len(persons)} profiles.")

            for uid, profile in persons.items():
                time.sleep(bot_config.API_REQUEST_DELAY_SECONDS)

                if bot_config.AUTO_SWIPE:
                    right = (bot_config.SWIPE_MAX_AGE >= profile.age >= bot_config.SWIPE_MIN_AGE
                             and bot_config.SWIPE_MAX_DISTANCE >= profile.distance >= bot_config.SWIPE_MIN_DISTANCE
                             and len(profile.profile_images) >= bot_config.SWIPE_MIN_IMAGES)
                    swipes += 1
                    print("[INFO] ({}) Swiping {} on {}".format(swipes, 'right' if right else 'left', uid))
                    swipe(uid, right)

                if bot_config.DOWNLOAD_IMAGE_PROFILE and bot_config.DOWNLOAD_IMAGE_INSTAGRAM:
                    if profile.age <= bot_config.DOWNLOAD_IMAGE_AGE_MAX:
                        # TODO make language reflect which ones are really being downloaded (based on config)
                        print(f"[INFO]\t\tDownloading {len(profile.profile_images)} profile "
                              f"pictures and {len(profile.instagram_images)} Instagram pictures.")
                        try:
                            workers = []
                            if bot_config.DOWNLOAD_IMAGE_PROFILE:
                                index = 0
                                for url in profile.profile_images:
                                    workers.append(pool.apply_async(write_image_file, (
                                        False, url, profile.age, uid, index, len(profile.profile_images),)))
                                    index += 1

                            if bot_config.DOWNLOAD_IMAGE_INSTAGRAM:
                                index = 0
                                for url in profile.instagram_images:
                                    workers.append(pool.apply_async(write_image_file, (
                                        True, url, profile.age, uid, index, len(profile.instagram_images),)))
                                    index += 1

                            [res.get(bot_config.WORKER_TIMEOUT_SECONDS) for res in workers]
                        except Exception as e:
                            print(f"[WARN] Timeout occurred when trying to download an image. |=> {e}")
                    else:
                        print(f"[INFO]\t\tSkipping pictures on profile with age {profile.age}")

                if bot_config.LOG_PROFILE_DATA:
                    print(f"[INFO] Writing log data..")
                    sepr = bot_config.PROFILE_DATA_SEPARATOR
                    log_string = f"{uid}{sepr}"
                    if bot_config.LOG_PROFILE_NAME:
                        log_string += f"{profile.name}{sepr}"
                    if bot_config.LOG_PROFILE_AGE:
                        log_string += f"{profile.age}{sepr}"
                    if bot_config.LOG_PROFILE_DISTANCE:
                        log_string += f"{profile.distance}{sepr}"
                    if bot_config.LOG_PROFILE_SWIPE and bot_config.AUTO_SWIPE:
                        log_string += f"{right}{sepr}"
                    if bot_config.LOG_PROFILE_BIO:
                        log_string += f"{repr(profile.bio.replace(sepr, ''))}{sepr}"
                    if bot_config.LOG_PROFILE_IMAGE_URLS:
                        log_string += f"{profile.profile_images}{sepr}"
                    if bot_config.LOG_PROFILE_INSTAGRAM_URLS:
                        log_string += f"{profile.instagram_images}{sepr}"

                    ostream.write(f"{log_string}\n")


if __name__ == '__main__':  # required because we spin up a bunch of workers
    # these headers are used for non-auth request actions (swiping, requesting new profiles, etc)
    INTERNAL_HEADERS = bot_config.HEADERS.copy()
    token = get_token_if_exist()
    if len(token) < bot_config.MIN_TOKEN_LENGTH:
        token = generate_new_token()
    else:
        print("[INFO] Existing auth key detected. Delete and regenerate "
              "auth file if access-related errors occur frequently.")

    if token is not '':
        start_bot(token)
