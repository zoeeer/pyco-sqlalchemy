"""
Tips:
- use `charset=UTF8MB4 collate utf8_general_ci`
  (https://stackoverflow.com/questions/766809/whats-the-difference-between-utf8-general-ci-and-utf8-unicode-ci)
- use `ext.TrimColumn instead Columns.Text`

# todo: support simple SQLALchemy-ORM
# todo: support django-ORM


## SQLite has three built-in collating functions: BINARY, NOCASE, and RTRIM.

    BINARY - Compares string data using memcmp(), regardless of text encoding.
    NOCASE - It is almost same as binary, except the 26 upper case characters of ASCII
             are folded to their lower case equivalents before the comparison is performed.
    RTRIM - The same as binary, except that trailing space characters, are ignored.

"""

# mysql>=8.0 support utf8mb4
UTF8 = "utf8_general_ci"
UTF8MB4 = "utf8mb4_general_ci"
_UTF8MB4 = "utf8mb4_unicode_ci"

# sqlite3 could not support UTF8MB4 or UTF8
BINARY = "BINARY"
NOCASE = "NOCASE"
RTRIM = "RTRIM"
