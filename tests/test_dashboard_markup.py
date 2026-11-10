from collections import Counter
from html.parser import HTMLParser
from pathlib import Path


class DashboardMarkupAudit(HTMLParser):
    """Collect basic semantic and accessible-name metadata from the dashboard."""

    VOID_ELEMENTS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.label_for = set()
        self.controls = []
        self.buttons = []
        self.label_depth = 0
        self.button_stack = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        element_id = attributes.get("id")
        if element_id:
            self.ids.append(element_id)

        if tag == "label":
            if attributes.get("for"):
                self.label_for.add(attributes["for"])
            self.label_depth += 1

        if tag in {"input", "select", "textarea"}:
            self.controls.append({
                "tag": tag,
                "id": element_id,
                "type": attributes.get("type", "text").lower(),
                "inside_label": self.label_depth > 0,
                "aria_label": attributes.get("aria-label"),
                "aria_labelledby": attributes.get("aria-labelledby"),
            })

        if tag == "button":
            self.button_stack.append({
                "text": [],
                "aria_label": attributes.get("aria-label"),
                "aria_labelledby": attributes.get("aria-labelledby"),
                "title": attributes.get("title"),
            })

    def handle_data(self, data):
        if self.button_stack and data.strip():
            self.button_stack[-1]["text"].append(data.strip())

    def handle_endtag(self, tag):
        if tag == "label" and self.label_depth:
            self.label_depth -= 1
        elif tag == "button" and self.button_stack:
            self.buttons.append(self.button_stack.pop())


def _dashboard_markup():
    path = Path(__file__).resolve().parents[1] / "static" / "index.html"
    parser = DashboardMarkupAudit()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def test_dashboard_html_has_unique_ids():
    parser = _dashboard_markup()
    duplicates = sorted(
        element_id
        for element_id, count in Counter(parser.ids).items()
        if count > 1
    )
    assert not duplicates, f"Duplicate HTML IDs: {duplicates}"


def test_dashboard_form_controls_have_accessible_labels():
    parser = _dashboard_markup()
    unlabeled = [
        control
        for control in parser.controls
        if control["type"] != "hidden"
        and not (
            control["inside_label"]
            or control["aria_label"]
            or control["aria_labelledby"]
            or (control["id"] and control["id"] in parser.label_for)
        )
    ]
    assert not unlabeled, f"Form controls without accessible labels: {unlabeled}"


def test_dashboard_buttons_have_accessible_names():
    parser = _dashboard_markup()
    unnamed = [
        button
        for button in parser.buttons
        if not (
            "".join(button["text"]).strip()
            or button["aria_label"]
            or button["aria_labelledby"]
            or button["title"]
        )
    ]
    assert not unnamed, f"Buttons without accessible names: {unnamed}"
