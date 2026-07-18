"""Email analyzer configuration settings."""


# File validation settings
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB
ALLOWED_FILE_EXTENSIONS = ['.eml', '.msg', '.txt']
ALLOWED_MIME_TYPES = ['message/rfc822', 'text/plain']

# Security analysis settings
MAX_EMAIL_AGE_DAYS = 30
MAX_RELAY_SERVERS = 5

# Suspicious patterns for subject analysis
SUSPICIOUS_SUBJECT_PATTERNS = [
    "urgent", "password", "account", "verify", "bank", "update", "security",
    "login", "suspend", "unusual activity", "confirm your", "verify your",
    "reset", "credit card", "payment", "invoice", "statement", "tax"
]

# Suspicious file extensions for attachments
SUSPICIOUS_ATTACHMENT_EXTENSIONS = [
    'exe', 'bat', 'cmd', 'scr', 'js', 'vbs', 'hta', 'msi', 
    'ps1', 'psd1', 'psm1', 'jar', 'reg', 'dll', 'com'
]

# Suspicious mailer patterns
SUSPICIOUS_MAILER_PATTERNS = ['php', 'script', 'bulk', 'mass']

# Hash algorithms supported
SUPPORTED_HASH_ALGORITHMS = ['md5', 'sha1', 'sha256']

# URL extraction patterns
URL_PATTERN = r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$_@.&+-]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)'
EMAIL_PATTERN = r'[\w\.-]+@[\w\.-]+'

# HTML security patterns
HTML_REDIRECTION_PATTERN = r'href=["\']https?://(?!www\.|mail\.)(.*?)["\'].*?>.*?(?:click|https?://www\.)'
IP_ADDRESS_URL_PATTERN = r'href=["\']https?://[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}'
ENCODED_URL_PATTERN = r'href=["\'](?:https?:\/\/)?(?:%[0-9A-Fa-f]{2})+'

# Data URI schemes to check
MALICIOUS_DATA_URI_SCHEMES = ['data:text/html', 'data:application/javascript']
