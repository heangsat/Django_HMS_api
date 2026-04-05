import pymysql

pymysql.version_info = (2, 2, 8, "final", 0)  # Add this line
pymysql.install_as_MySQLdb()