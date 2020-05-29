LOG_PROFILE_DATA = True

# swipe settings
SWIPE_MIN_AGE = 18
SWIPE_MAX_AGE = 25
# set to -1 to include users that have a hidden location
SWIPE_MIN_DISTANCE = 0
SWIPE_MAX_DISTANCE = 25
# minimum profile pictures needed in order to swipe right
SWIPE_MIN_IMAGES = 3

# highest age to download images 
IMAGE_AGE_MAX = 28
# if instagram images should be downloaded
IMAGE_INSTAGRAM = True
# if profile images should be downloaded
IMAGE_PROFILE = True

# below settings are not meant to be configured
DELAY_INTERVAL_SECONDS = 0.25
WORKER_TIMEOUT_SECONDS = 30
POOL_WORKERS = 32

TOKEN_FILE_NAME = "X-AUTH-KEY"
MIN_TOKEN_LENGTH = 30

CODE_REQUEST_URL = "https://api.gotinder.com/v2/auth/sms/send?auth_type=sms"
CODE_VALIDATE_URL = "https://api.gotinder.com/v2/auth/sms/validate?auth_type=sms"
TOKEN_URL = "https://api.gotinder.com/v2/auth/login/sms"

GET_USERS_URL = "https://api.gotinder.com/user/recs"
LIKE_USER_URL = "https://api.gotinder.com/like"  # add /userid to the end
DISLIKE_USER_URL = "https://api.gotinder.com/pass"  # add /userid to the end

HEADERS = {  # headers used for api calls -> must append auth token after retrieval
    'user-agent': 'Tinder/11.4.0 (iPhone; iOS 12.4.1; Scale/2.00)',
    'content-type': 'application/json'
}
