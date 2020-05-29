from multiprocessing import Pool
import requests  # api interaction
import json  # api payloads
import time
import os
import datetime
import shutil  # image downloader

# internal imports
import bot_config


class Person:
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
    except:
        return ""


def get_refresh_token(otp_code, phone_number):
    data = {'otp_code': otp_code, 'phone_number': phone_number}
    req = requests.post(bot_config.CODE_VALIDATE_URL, headers=bot_config.HEADERS, data=json.dumps(data))
    response = req.json()
    try:
        return response.get("data")["refresh_token"]  # if response.get("data")["validated"] else False
    except:
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

    print("[INFO] Your new Tinder token is: {}".format(ret_token))
    try:
        with open(bot_config.TOKEN_FILE_NAME, 'w') as ostream:
            ostream.write(
                "{}\nDELETE THIS FILE IN ORDER TO FORCE NEW KEY RETRIEVAL\nDO NOT MODIFY THIS FILE".format(ret_token))
        print("[INFO] Your token has been stored for future use.")
    except Exception as e:
        print("[ERROR] Unable to save token. |=> {}".format(e))
    return ret_token


def valid_request(request_obj):
    return request_obj.json()["status"] == 200


def dump_json(json_obj):
    print(json.dumps(json_obj, sort_keys=True, indent=4))


def get_persons():
    req = requests.get(bot_config.GET_USERS_URL, headers=INTERNAL_HEADERS)
    dict = {}
    if valid_request(req):
        for person in req.json()["results"]:
            uid = person["_id"]
            if uid in dict: continue  # name, age, profile_images, instagram_images
            name = person["name"]

            age = datetime.datetime.now().year - int(
                person["birth_date"].split('-')[0]) - 1 if "birth_date" in person and len(
                person["birth_date"]) > 4 else 99
            distance = int(person["distance_mi"]) if "distance_mi" in person and person["distance_mi"] >= 0 else -1
            bio = person["bio"] if "bio" in person else ""

            profile_images = []
            for photo in person["photos"]:
                profile_images.append(photo["url"])

            instagram_images = []
            try:
                if "instagram" in person and "photos" in person["instagram"]:
                    for photo in person["instagram"]["photos"]:
                        if "image" in photo:  # sometimes the nodes dont contain pictures for some reason
                            instagram_images.append(photo["image"])
            except:
                print("[ERROR] Unable to dump Instagram json data. Dumping JSON batch.")
                dump_json(person)

            dict[uid] = Person(name, age, distance, bio, profile_images, instagram_images)
    else:
        print("[ERROR] Invalid response code when fetching new batch of persons.")
    return dict


def swipe(uid, right):
    try:
        req = requests.get('{}/{}'.format(bot_config.LIKE_USER_URL if right else bot_config.DISLIKE_USER_URL, uid),
                           headers=INTERNAL_HEADERS)
        if req.json()["status"] != 200:
            print("[ERROR]\t\tSwipe rejected, consider getting a new key if this happens again.")
    except Exception as e:
        print("[ERROR]\t\tSwipe failed due to unknown error. {}".format(e))


def write_image_file(instagram, url, age, uid, index, total):
    r = requests.get(url, stream=True)
    if r.status_code == 200:  # success
        r.raw.decode_content = True
        file_extension = url.split('?')[0].split('.')[-1] if instagram else url.split('.')[-1]
        path = 'output/image_output/{}'.format(age)
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except:
                print("[WARN] Thread collision when checking if path exists.")  # not a big deal, happens occasionally
        try:
            filename = "{}/{}_{}_{}.{}".format(path, uid, "IG" if instagram else "PP", index, file_extension)
            with open(filename, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        except:
            print("[WARN] Unable to write file to disk, skipping file.")
    else:
        print("[WARN]\t\tFailed to download {} picture {}/{} from uid {}.".format(
            "Instagram" if instagram else "profile",
            index + 1, total, uid))


def start_bot(token_input):
    print("[INFO] Starting bot..")
    INTERNAL_HEADERS['x-auth-token'] = token_input
    now = datetime.datetime.now()
    ostream = open("output/data_{}-{}-{}__{}-{}.txt".format(now.day, now.month, now.year, now.minute, now.second), 'a+', encoding='utf-16')
    swipes = 0
    with Pool(bot_config.POOL_WORKERS) as pool:
        while True:
            persons = get_persons()
            if len(persons) <= 0:
                print("[INFO] No more matches returned, ending script.")
                break

            print("[INFO] =====> Fetched new batch of {} profiles.".format(len(persons)))

            for uid, person in persons.items():
                time.sleep(bot_config.DELAY_INTERVAL_SECONDS)

                right = bot_config.SWIPE_MAX_AGE >= person.age >= bot_config.SWIPE_MIN_AGE and bot_config.SWIPE_MAX_DISTANCE >= person.distance >= bot_config.SWIPE_MIN_DISTANCE and len(
                    person.profile_images) >= bot_config.SWIPE_MIN_IMAGES

                swipes += 1
                print("[INFO] ({}) Swiping {} on {}".format(swipes, 'right' if right else 'left', uid))

                swipe(uid, right)

                if person.age <= bot_config.IMAGE_AGE_MAX:
                    print("[INFO]\t\tDownloading {} profile pictures and {} Instagram pictures.".format(
                        len(person.profile_images), len(person.instagram_images)))
                    try:
                        workers = []
                        if bot_config.IMAGE_PROFILE:
                            index = 0
                            for url in person.profile_images:
                                workers.append(pool.apply_async(write_image_file, (
                                    False, url, person.age, uid, index, len(person.profile_images),)))
                                index += 1

                        if bot_config.IMAGE_INSTAGRAM:
                            index = 0
                            for url in person.instagram_images:
                                workers.append(pool.apply_async(write_image_file, (
                                    True, url, person.age, uid, index, len(person.instagram_images),)))
                                index += 1

                        if len(workers) > 0:
                            [res.get(bot_config.WORKER_TIMEOUT_SECONDS) for res in workers]  # doesnt return anything
                    except:
                        print("[WARN] Timeout occurred when trying to download an image.")
                else:
                    print("[INFO]\t\tSkipping pictures on person age {}".format(person.age))

                ostream.write('{};{};{};{};{};{};{};{}\n'.format(uid, person.name, person.age, person.distance, right,
                                                                 person.profile_images, person.instagram_images,
                                                                 repr(person.bio)))


INTERNAL_HEADERS = bot_config.HEADERS.copy()  # these headers are used for non-auth actions

if __name__ == '__main__':  # required because we spin up a bunch of workers
    token = get_token_if_exist()
    if len(token) < bot_config.MIN_TOKEN_LENGTH:
        token = generate_new_token()
    else:
        print("[INFO] Existing auth key detected. Delete auth file if access errors occur frequently.")

    if token is not '':
        start_bot(token)
