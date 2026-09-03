from unittest import TestCase
from unittest.mock import patch
from database.init_db import init_db


class TestInitDB(TestCase):
    @patch("database.init_db.AppSQLModel")
    @patch("database.init_db.engine")
    def test_init_db(self, mock_engine, mock_app_sqlmodel):
        init_db()
        mock_app_sqlmodel.metadata.create_all.assert_called_once_with(bind=mock_engine)
