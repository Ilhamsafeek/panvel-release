import json
import base64

credentials = {
    "type": "service_account",
    "project_id": "panvel-481009",
    "private_key_id": "d6d03a9f08f4a0f39a8b39f01b86d67774f9df0e",
    "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDmbdoMiXXOd0rC
jwNAN70DyTeNaqldttWdw9kiliVy0LQAjSHDyciLW8DwUsg3ALfhZNBeqlcDxGfx
1rRPI0Ej30nTV/e24JqbVrbyg7l4XIk2Im6t3q/2p11U80v4m8s8SSHftMomeRIt
8v7SF/BUJpeLfPkccQmL/jnobGjOsG2Hz+miVPCJVW6/XETCMLiT8I/Xv9xuCmjF
LOOGjbcSNs5wUD0oqxOgEyo0H7/QQ7KxpmL6twbdAwdVh21V5+oZsK2myrzMk6os
RDQELzwoBjmwJQKUZrI9AdT1GijNJzKuuszRi8JQf/BqwwbhVGAL40KriWWa0Wr
iPOeQIFrAgMBAAECggEAOfhl9GR6okQppzPCbhv3reWn16h/TmfKawPT8xsR9cYi
msbmuTJhBQpCylMRMqE4IXiy4TX6aSS2v8UznHsyjptEn+pQFA6CZtUUdoOEHA8v
p9JWxOAypZtqZA5HTRaotRRy9KwvdSldVPj+eY1zNUB2PK3mn+yiKbl+CQaJAYIv
1pAiY80YP2rT/DZ0EOIUJ6cJrr7zgpB5Lg6AKJS7A1BcmgStojvLvDDVbD8Ggwfq
qbT16X0TNKakFz9RXTtVLKA71ailG2SYJQrWE9RsXNdTv66zRUBqjwyzFQSJYPQC
7q3kz5WVZawu9HzqlIEpFfoJmlBvJpd3xbsO12knvQKBgQD/lW4xYFxs410sIBCp
/dSeClfwvPI953yfACTZJhkOxfGLhewHzqd2O/+DvothovYzp52n1nS48LIBJJze
scmHLRs+nyvKllewkohYY3jpvKDVal9Xqrd1iAa4lScuuDnBXzLvlbcRKr6VIAp8
d1bqfgl9vkeNHDYFR5NcLTDy1wKBgQDmze7GVXcM0hab7rNvvJoSLDLkR8xRmuL5
CHo+009cPRhN9QPoeq8QQGEavzODxkZlvnJ5qFy4bS0/FVt9j4rf2razY4Bwe+CL
T4vosOwarH1dJUJzTc6Syeg8X1Z/AcpoOw0UaYunithmr1Ls66XddA1c63c1v8RJ
nj4EB5QnjQKBgQCmOgnxEzsJltaCXFh6NxyRrSiE6l6i5Guo/e75TE3/zb3LgM6C
RWWlAGCuzr7YQaTe86UWA+TmY6ViGO3t6LOptyyBDgTtPdrKfIMw+YEqhAQWyZg4
7E9loZK9ekSBnk/x9HisWjM2dxZ85tnrGbLt0AtcPOVMYYzA4kx1Ju8vAQKBgG90
wvnEC9mFGqXyf3RV/5EHBwx2H5TI1xKrpVzxbkF8v1/mEh0SIbgXXs0ryBS6iwRX
E7DsPNpS3qa4CZZ42vd/BvtZ8YxgRe8AWu/jgCDhayiv9Yb46+i22A9PetWaZ8Qt
wAM7dNVTl2z+/Wyr300x3cIhc0/ha0ihwhDwF/uBAoGAEF5zdMV5Yfkaq3ylQI3D
3HQgZyn23Wmk+6Ttt2M6NKWfbCHHn7uUUH/zcPZ04JFTpXgtqahgat2xHFYv8vpo
XoU4spVmkkm5r6JzrT85N1n3EpniGCdic1JK2RAJ4oPq9CjOpkvyPT7yrtMTRBqS
mtlpSLpUV3l8Tl1vSllnnhA=
-----END PRIVATE KEY-----""",
    "client_email": "ga4-server-events@panvel-481009.iam.gserviceaccount.com",
    "client_id": "104475052408760082817",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/ga4-server-events%40panvel-481009.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

# Convert to JSON string
json_str = json.dumps(credentials)

# Encode to base64
encoded = base64.b64encode(json_str.encode()).decode()

print("Copy this to your .env file as GA4_CREDENTIALS_BASE64:")
print(encoded)