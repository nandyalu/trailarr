class TestConfig:

    def test_monitor_interval_string_input(self):
        """Test that monitor_interval can accept string input (API use case)"""
        app_settings.monitor_interval = "120"  # String input like from API
        assert app_settings.monitor_interval == 120
        
    def test_monitor_interval_string_below_minimum(self):
        """Test that monitor_interval enforces minimum value with string input"""
        app_settings.monitor_interval = "5"  # Below minimum of 10
        assert app_settings.monitor_interval == 10
        
    def test_monitor_interval_invalid_string(self):
        """Test that monitor_interval handles invalid string input"""
        original_value = app_settings.monitor_interval
        app_settings.monitor_interval = "invalid"  # Invalid string
        assert app_settings.monitor_interval == 60  # Should use default
