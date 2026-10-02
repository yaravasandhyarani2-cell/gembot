"""Clipboard image attachment behavior for the terminal prompt."""

import agent


def test_clipboard_image_is_only_attached_on_explicit_paste(monkeypatch):
    clipboard_reads = []

    def clipboard_image():
        clipboard_reads.append(True)
        return {"type": "image", "data": "image-bytes"}

    monkeypatch.setattr(agent, "get_clipboard_image", clipboard_image)

    prompt, images = agent.parse_multimodal_input("write Fibonacci code")
    assert prompt == "write Fibonacci code"
    assert images == []
    assert clipboard_reads == []

    prompt, images = agent.parse_multimodal_input("/paste")
    assert "clipboard" in prompt.lower()
    assert images == ["image-bytes"]
    assert clipboard_reads == [True]

    prompt, images = agent.parse_multimodal_input("/paste fix the issues in this screenshot")
    assert prompt == "fix the issues in this screenshot"
    assert images == ["image-bytes"]
    assert clipboard_reads == [True, True]


def test_ctrl_v_key_binding_queues_clipboard_image(monkeypatch):
    pending_images = []
    monkeypatch.setattr(
        agent,
        "get_clipboard_image",
        lambda: {"type": "image", "data": "pasted-image"},
    )

    class FakeApp:
        def __init__(self):
            self.invalidated = False

        def invalidate(self):
            self.invalidated = True

    class FakeEvent:
        def __init__(self):
            self.app = FakeApp()

    bindings = agent.make_terminal_key_bindings(pending_images)
    ctrl_v = next(binding for binding in bindings.bindings if binding.keys[0].value == "c-v")
    event = FakeEvent()
    ctrl_v.handler(event)

    assert pending_images == ["pasted-image"]
    assert event.app.invalidated
