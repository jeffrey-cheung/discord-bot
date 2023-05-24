import os

# Reddit Credentials
os.environ['CLIENT_ID'] = "[REDACTED]"
os.environ['CLIENT_SECRET'] = "[REDACTED]"
os.environ['USER_AGENT_PLAY_BY_PLAY'] = "[REDACTED]"
os.environ['USER_AGENT_SHADOW_BALL'] = "[REDACTED]"

# play_by_play Credentials (Test)
os.environ['MLR_SEARCH_TEST'] = "[REDACTED]"
os.environ['MLR_WEBHOOK_TEST'] = "[REDACTED]"
os.environ['MILR_SEARCH_TEST'] = "[REDACTED]"
os.environ['MILR_WEBHOOK_TEST'] = "[REDACTED]"

# play_by_play Credentials (Prod)
os.environ['MLR_SEARCH'] = ""
os.environ['MLR_WEBHOOK'] = ""
os.environ['MILR_SEARCH'] = ""
os.environ['MILR_WEBHOOK'] = ""

# Discord Bot Credentials
os.environ['TOKEN_LUDABOT'] = "[REDACTED]"
os.environ['TOKEN_SHADOWBALL'] = "[REDACTED]"
