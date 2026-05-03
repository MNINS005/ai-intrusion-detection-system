"""
NSL-KDD Dataset constants — column names, feature lists, label maps
"""

# NSL-KDD has 41 features + label + difficulty_level (42 cols in the raw file)
NSL_KDD_COLUMNS = [
    "duration", "protocol_type", "service", "flag", "src_bytes",
    "dst_bytes", "land", "wrong_fragment", "urgent", "hot",
    "num_failed_logins", "logged_in", "num_compromised", "root_shell",
    "su_attempted", "num_root", "num_file_creations", "num_shells",
    "num_access_files", "num_outbound_cmds", "is_host_login",
    "is_guest_login", "count", "srv_count", "serror_rate",
    "srv_serror_rate", "rerror_rate", "srv_rerror_rate", "same_srv_rate",
    "diff_srv_rate", "srv_diff_host_rate", "dst_host_count",
    "dst_host_srv_count", "dst_host_same_srv_rate", "dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate", "dst_host_srv_diff_host_rate",
    "dst_host_serror_rate", "dst_host_srv_serror_rate",
    "dst_host_rerror_rate", "dst_host_srv_rerror_rate",
    "label", "difficulty_level"
]

CATEGORICAL_FEATURES = ["protocol_type", "service", "flag"]

NUMERICAL_FEATURES = [
    "duration", "src_bytes", "dst_bytes", "land", "wrong_fragment",
    "urgent", "hot", "num_failed_logins", "logged_in", "num_compromised",
    "root_shell", "su_attempted", "num_root", "num_file_creations",
    "num_shells", "num_access_files", "num_outbound_cmds", "is_host_login",
    "is_guest_login", "count", "srv_count", "serror_rate",
    "srv_serror_rate", "rerror_rate", "srv_rerror_rate", "same_srv_rate",
    "diff_srv_rate", "srv_diff_host_rate", "dst_host_count",
    "dst_host_srv_count", "dst_host_same_srv_rate", "dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate", "dst_host_srv_diff_host_rate",
    "dst_host_serror_rate", "dst_host_srv_serror_rate",
    "dst_host_rerror_rate", "dst_host_srv_rerror_rate"
]

TARGET_COLUMN = "label"
DROP_COLUMNS  = ["difficulty_level"]

# ── Label maps ────────────────────────────────────────────────────────────────

# Binary: 0 = normal, 1 = attack
BINARY_LABEL_MAP = {"normal": 0}   # anything not in this → 1

# Multiclass: 5 classes
MULTICLASS_LABEL_MAP = {
    "normal": 0,
    # DoS
    "back": 1, "land": 1, "neptune": 1, "pod": 1, "smurf": 1,
    "teardrop": 1, "apache2": 1, "udpstorm": 1, "processtable": 1, "mailbomb": 1,
    # Probe
    "satan": 2, "ipsweep": 2, "nmap": 2, "portsweep": 2, "mscan": 2, "saint": 2,
    # R2L
    "guess_passwd": 3, "ftp_write": 3, "imap": 3, "phf": 3, "multihop": 3,
    "warezmaster": 3, "warezclient": 3, "spy": 3, "xlock": 3, "xsnoop": 3,
    "snmpguess": 3, "snmpgetattack": 3, "httptunnel": 3, "sendmail": 3, "named": 3,
    # U2R
    "buffer_overflow": 4, "loadmodule": 4, "rootkit": 4, "perl": 4,
    "sqlattack": 4, "xterm": 4, "ps": 4,
}

CLASS_NAMES = {0: "Normal", 1: "DoS", 2: "Probe", 3: "R2L", 4: "U2R"}

# ── Artifact paths (overridden by config.yaml, kept here as fallback) ─────────
ARTIFACTS_DIR          = "artifacts"
RAW_DATA_DIR           = "artifacts/raw"
PROCESSED_DATA_DIR     = "artifacts/processed"
TRANSFORMED_DATA_DIR   = "artifacts/transformed"
MODEL_DIR              = "artifacts/models"
REPORTS_DIR            = "artifacts/reports"
PLOTS_DIR              = "artifacts/plots"