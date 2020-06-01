LOG_PROFILE_DATA = True

# data is stored in the below order with index 0 being the profile uid
LOG_PROFILE_NAME = True
LOG_PROFILE_AGE = True
LOG_PROFILE_DISTANCE = True
LOG_PROFILE_SWIPE = True  # this will be false if AUTO_SWIPE is false
LOG_PROFILE_BIO = True
LOG_PROFILE_IMAGE_URLS = True
LOG_PROFILE_INSTAGRAM_URLS = True

PROFILE_DATA_SEPARATOR = ';'  # this character will be removed from all bios

# if true the bot will swipe according to the below criteria
AUTO_SWIPE = True

# swipe settings
SWIPE_MIN_AGE = 18
SWIPE_MAX_AGE = 25
# set to -1 to include users that have a hidden location
SWIPE_MIN_DISTANCE = 0
SWIPE_MAX_DISTANCE = 25
# minimum profile pictures (not instagram) needed in order to swipe right
SWIPE_MIN_IMAGES = 3

# highest age to download images 
DOWNLOAD_IMAGE_AGE_MAX = 28
# if instagram images should be downloaded
DOWNLOAD_IMAGE_INSTAGRAM = True
# if profile images should be downloaded
DOWNLOAD_IMAGE_PROFILE = True

# below settings are not meant to be configured
API_REQUEST_DELAY_SECONDS = 0.5  # forced throttle between API requests
WORKER_TIMEOUT_SECONDS = 30
EMPTY_RESPONSE_ATTEMPTS = 3  # if no persons returned after this many attempts, the bot will terminate
POOL_WORKERS = 39  # one worker for each image
MAX_POSSIBLE_PROFILE_IMAGES = 39

# WARNING if file name is changed, git will not ignore it and can publish your token (not good)
TOKEN_FILE_NAME = "X-AUTH-KEY"
MIN_TOKEN_LENGTH = 30  # TODO determine if token length is static else the correct min value

CODE_REQUEST_URL = "https://api.gotinder.com/v2/auth/sms/send?auth_type=sms"
CODE_VALIDATE_URL = "https://api.gotinder.com/v2/auth/sms/validate?auth_type=sms"
TOKEN_URL = "https://api.gotinder.com/v2/auth/login/sms"

GET_USERS_URL = "https://api.gotinder.com/user/recs"
LIKE_USER_URL = "https://api.gotinder.com/like"  # add /userid to the end
DISLIKE_USER_URL = "https://api.gotinder.com/pass"  # add /userid to the end

IMAGE_OUTPUT_PATH = "output/image_output"
DATA_OUTPUT_PATH = "output"
DATA_OUTPUT_ENCODING = "utf-16"  # 16 required to handle emojis and non-alphabetic languages

HEADERS = {  # headers used for api calls -> must append auth token after retrieval
    'user-agent': 'Tinder/11.4.0 (iPhone; iOS 12.4.1; Scale/2.00)',
    'content-type': 'application/json'
}
