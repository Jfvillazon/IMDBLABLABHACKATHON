from sample_repo.shop.config import load_config


def test_explicit_environment_override(monkeypatch):
    monkeypatch.setenv("REPOMEDIC_DEMO_KEY", "local-test-override")
    assert load_config()["api_key"] == "local-test-override"


def test_configuration_reads_are_independent(monkeypatch):
    monkeypatch.setenv("REPOMEDIC_DEMO_KEY", "first-local-value")
    first = load_config()
    monkeypatch.setenv("REPOMEDIC_DEMO_KEY", "second-local-value")
    assert load_config()["api_key"] == "second-local-value"
    assert first["api_key"] == "first-local-value"
