from unittest import TestCase
from unittest.mock import patch
from core.base.database.utils.init_db import init_db


class TestInitDB(TestCase):
    @patch("core.base.database.utils.init_db.AppSQLModel")
    @patch("core.base.database.utils.init_db.engine")
    def test_init_db(self, mock_engine, mock_app_sqlmodel):
        init_db()
        mock_app_sqlmodel.metadata.create_all.assert_called_once_with(bind=mock_engine)
