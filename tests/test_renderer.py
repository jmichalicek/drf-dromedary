import importlib

import pytest
from rest_framework.renderers import JSONRenderer
from rest_framework.utils import encoders, json

from drf_dromedary import render
from tests.render import AddsFooRenderer


@pytest.fixture
def reload_render(request):
    """
    Exists to provide a finalizer which reloads the render library to allow for
    changing settings which affect the CamelCaseJSONRenderer class' parent class.

    This fixture should be listed before the settings fixture.
    """
    from drf_dromedary import render

    def reload():
        importlib.reload(render)

    request.addfinalizer(reload)


def test_renderer_default_parent_class():
    assert issubclass(render.CamelCaseJSONRenderer, JSONRenderer)
    input = {
        "a_key": "foo",
        "a_bigger_key": "Bar",
        "key_and_val_4_int": 1,
        "key_and_val_4a_float": 2.345,
        "dict_key": {"inner_key": "val"},
    }

    renderer = render.CamelCaseJSONRenderer()
    output = renderer.render(input)
    expected = json.dumps(
        {
            "aKey": "foo",
            "aBiggerKey": "Bar",
            "keyAndVal4Int": 1,
            "keyAndVal4aFloat": 2.345,
            "dictKey": {"innerKey": "val"},
        },
        cls=encoders.JSONEncoder,
        indent=0,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).replace("\n", "")
    assert output == bytes(expected, "utf-8")


def test_renderer_custom_parent_class(reload_render, settings):
    settings.JSON_CAMEL_CASE = {
        "RENDERER_CLASS": "tests.render.AddsFooRenderer",
    }

    importlib.reload(render)
    assert issubclass(render.CamelCaseJSONRenderer, AddsFooRenderer)

    input = {
        "a_key": "foo",
        "a_bigger_key": "Bar",
        "key_and_val_4_int": 1,
        "key_and_val_4a_float": 2.345,
        "dict_key": {"inner_key": "val"},
    }

    renderer = render.CamelCaseJSONRenderer()
    output = renderer.render(input)
    # The results here may not be what you first expect. We camelize and then call super().render()
    # so our parent class' modifications happen after camelization, resulting in a snake case prefix.
    expected = json.dumps(
        {
            "foo_aKey": "foo",
            "foo_aBiggerKey": "Bar",
            "foo_keyAndVal4Int": 1,
            "foo_keyAndVal4aFloat": 2.345,
            "foo_dictKey": {"innerKey": "val"},
        },
        cls=encoders.JSONEncoder,
        indent=0,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).replace("\n", "")
    assert output == bytes(expected, "utf-8")
