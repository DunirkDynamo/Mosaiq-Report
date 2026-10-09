import pyodbc


MOSAIQ_DB = {
    'DRIVER': 'SQL Server',
    'SERVER': 'OHICPRPTSQL01',
    'DATABASE': 'MOSAIQ',
    'Trusted_Connection': 'yes',
}


class MosaiqConnection:
    def __init__(self):
        self.cnxn = None

    def connect(self):
        self.cnxn = pyodbc.connect(
            'DRIVER={{{}}};SERVER={};DATABASE={};Trusted_Connection={}{}'.format(
                MOSAIQ_DB['DRIVER'],
                MOSAIQ_DB['SERVER'],
                MOSAIQ_DB['DATABASE'],
                MOSAIQ_DB['Trusted_Connection'],
                ';UID={};PWD={}'.format(
                    MOSAIQ_DB['USERNAME'],
                    MOSAIQ_DB['PASSWORD']
                ) if 'USERNAME' in MOSAIQ_DB else ''
            )
        )

    def close(self):
        if self.cnxn is not None:
            self.cnxn.close()
            self.cnxn = None
