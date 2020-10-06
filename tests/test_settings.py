from example_app.settings import Settings


def test_setting_defaults(app_settings, aws_region):
    # see also tests.conftest.app_env fixture;
    # it uses monkeypatch to modify env-vars and the
    # tests.conftest.app_settings inherits those env-vars
    # - it might also get values from .env if they match
    #   default env-var-name patterns for setting fields
    # - see also example_app/settings/*.yaml
    settings = app_settings
    assert isinstance(settings, Settings)

    assert settings.cognito_region == aws_region
    assert settings.cognito_client_id == "testing-client"
    assert settings.cognito_pool_id == "testing-pool-id"

    # # to debug settings, use the `assert False` with a pytest command like:
    # # 'pytest -s --pdb tests/test_settings.py'
    # assert False
