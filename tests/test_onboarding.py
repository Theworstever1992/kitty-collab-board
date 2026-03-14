import pytest
from agents.onboarding import pick_default_avatar

def test_pick_default_avatar():
    assert pick_default_avatar("test") in ["tabby", "tuxedo", "calico"]
    assert pick_default_avatar("jules") in ["tabby", "tuxedo", "calico"]
