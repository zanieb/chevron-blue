#!/usr/bin/python3

import collections
import io
import json
import os
import unittest

import chevron_blue

SPECS_PATH = os.path.join("spec", "specs")
if os.path.exists(SPECS_PATH):
    SPECS = [path for path in os.listdir(SPECS_PATH) if path.endswith(".json")]
else:
    SPECS = []

STACHE = chevron_blue.render


def _test_case_from_path(json_path):
    json_path = "%s.json" % json_path

    class MustacheTestCase(unittest.TestCase):
        """A simple yaml based test case"""

        def _test_from_object(obj):
            """Generate a unit test from a test object"""

            def test_case(self):
                result = STACHE(
                    obj["template"], obj["data"], partials_dict=obj.get("partials", {})
                )

                assert result == obj["expected"], obj["desc"]

            test_case.__doc__ = "suite: {0}    desc: {1}".format(spec, obj["desc"])
            return test_case

        with io.open(json_path, "r", encoding="utf-8") as f:
            yaml = json.load(f)

        # Generates a unit test for each test object
        for i, test in enumerate(yaml["tests"]):
            vars()[
                "test_" + test["name"].lower().replace(" ", "_").replace("-", "_")
            ] = _test_from_object(test)

        def __repr__(self) -> str:
            return f"<GeneratedMustacheTestCase json_path={json_path}>"

    # Return the built class
    return MustacheTestCase


# Create TestCase for each json file
for spec in SPECS:
    # Ignore optional tests
    if spec[0] != "~":
        spec = spec.split(".")[0]
        globals()[spec] = _test_case_from_path(os.path.join(SPECS_PATH, spec))


class ExpandedCoverage(unittest.TestCase):
    def test_unclosed_sections(self):
        test1 = {"template": "{{# section }} oops {{/ wrong_section }}"}

        test2 = {"template": "{{# section }} end of file"}

        self.assertRaises(chevron_blue.ChevronError, chevron_blue.render, **test1)
        self.assertRaises(chevron_blue.ChevronError, chevron_blue.render, **test2)
        # check SyntaxError still catches ChevronError:
        self.assertRaises(SyntaxError, chevron_blue.render, **test1)

    def test_bad_set_delimiter_tag(self):
        args = {"template": "{{= bad!}}"}

        self.assertRaises(SyntaxError, chevron_blue.render, **args)

    def test_unicode_basic(self):
        args = {"template": "(╯°□°）╯︵ ┻━┻"}

        result = chevron_blue.render(**args)
        expected = "(╯°□°）╯︵ ┻━┻"

        self.assertEqual(result, expected)

    def test_unicode_variable(self):
        args = {
            "template": "{{ table_flip }}",
            "data": {"table_flip": "(╯°□°）╯︵ ┻━┻"},
        }

        result = chevron_blue.render(**args)
        expected = "(╯°□°）╯︵ ┻━┻"

        self.assertEqual(result, expected)

    def test_unicode_partial(self):
        args = {
            "template": "{{> table_flip }}",
            "partials_dict": {"table_flip": "(╯°□°）╯︵ ┻━┻"},
        }

        result = chevron_blue.render(**args)
        expected = "(╯°□°）╯︵ ┻━┻"

        self.assertEqual(result, expected)

    def test_missing_key_partial(self):
        args = {
            "template": "before, {{> with_missing_key }}, after",
            "partials_dict": {
                "with_missing_key": "{{#missing_key}}bloop{{/missing_key}}",
            },
        }

        result = chevron_blue.render(**args)
        expected = "before, , after"

        self.assertEqual(result, expected)

    def test_listed_data(self):
        args = {"template": "{{# . }}({{ . }}){{/ . }}", "data": [1, 2, 3, 4, 5]}

        result = chevron_blue.render(**args)
        expected = "(1)(2)(3)(4)(5)"

        self.assertEqual(result, expected)

    def test_main(self):
        result = chevron_blue.main(
            "tests/test.mustache", "tests/data.json", partials_path="tests"
        )

        with io.open("tests/test.rendered", "r", encoding="utf-8") as f:
            expected = f.read()

        self.assertEqual(result, expected)

    def test_recursion(self):
        args = {
            "template": "{{# 1.2 }}{{# data }}{{.}}{{/ data }}{{/ 1.2 }}",
            "data": {"1": {"2": [{"data": ["1", "2", "3"]}]}},
        }

        result = chevron_blue.render(**args)
        expected = "123"

        self.assertEqual(result, expected)

    def test_unicode_inside_list(self):
        args = {"template": "{{#list}}{{.}}{{/list}}", "data": {"list": ["☠"]}}

        result = chevron_blue.render(**args)
        expected = "☠"

        self.assertEqual(result, expected)

    def test_falsy(self):
        args = {
            "template": "{{null}}{{false}}{{list}}{{dict}}{{zero}}",
            "data": {"null": None, "false": False, "list": [], "dict": {}, "zero": 0},
        }

        result = chevron_blue.render(**args)
        expected = "False0"

        self.assertEqual(result, expected)

    def test_complex(self):
        class Complex:
            def __init__(self):
                self.attr = 42

        args = {
            "template": "{{comp.attr}} {{int.attr}}",
            "data": {"comp": Complex(), "int": 1},
        }

        result = chevron_blue.render(**args)
        expected = "42 "

        self.assertEqual(result, expected)

    # https://github.com/noahmorrison/chevron/issues/17
    def test_inverted_coercion(self):
        args = {
            "template": "{{#object}}{{^child}}{{.}}{{/child}}{{/object}}",
            "data": {"object": ["foo", "bar", {"child": True}, "baz"]},
        }

        result = chevron_blue.render(**args)
        expected = "foobarbaz"

        self.assertEqual(result, expected)

    def test_closing_tag_only(self):
        args = {"template": "{{ foo } bar", "data": {"foo": "xx"}}

        self.assertRaises(chevron_blue.ChevronError, chevron_blue.render, **args)

    def test_current_line_rest(self):
        args = {
            "template": "first line\nsecond line\n {{ foo } bar",
            "data": {"foo": "xx"},
        }

        # self.assertRaisesRegex does not exist in python2.6
        for _ in range(10):
            try:
                chevron_blue.render(**args)
            except chevron_blue.ChevronError as error:
                self.assertEqual(error.msg, "unclosed tag at line 3")

    def test_no_opening_tag(self):
        args = {
            "template": "oops, no opening tag {{/ closing_tag }}",
            "data": {"foo": "xx"},
        }

        try:
            chevron_blue.render(**args)
        except chevron_blue.ChevronError as error:
            self.assertEqual(
                error.msg,
                'Trying to close tag "closing_tag"\n'
                "Looks like it was not opened.\n"
                "line 2",
            )

    # https://github.com/noahmorrison/chevron/issues/17
    def test_callable_1(self):
        args_passed = {}

        def first(content, render):
            args_passed["content"] = content
            args_passed["render"] = render

            return "not implemented"

        args = {
            "template": "{{{postcode}}} {{#first}} {{{city}}} || {{{town}}} "
            "|| {{{village}}} || {{{state}}} {{/first}}",
            "data": {
                "postcode": "1234",
                "city": "Mustache City",
                "state": "Nowhere",
                "first": first,
            },
        }

        result = chevron_blue.render(**args)
        expected = "1234 not implemented"
        template_content = (
            " {{& city }} || {{& town }} || {{& village }} || {{& state }} "
        )

        self.assertEqual(result, expected)
        self.assertEqual(args_passed["content"], template_content)

    def test_callable_2(self):
        def first(content, render):
            result = render(content)
            result = [x.strip() for x in result.split(" || ") if x.strip()]
            return result[0]

        args = {
            "template": "{{{postcode}}} {{#first}} {{{city}}} || {{{town}}} "
            "|| {{{village}}} || {{{state}}} {{/first}}",
            "data": {
                "postcode": "1234",
                "town": "Mustache Town",
                "state": "Nowhere",
                "first": first,
            },
        }

        result = chevron_blue.render(**args)
        expected = "1234 Mustache Town"

        self.assertEqual(result, expected)

    def test_callable_3(self):
        """Test generating some data within the function"""

        def first(content, render):
            result = render(content, {"city": "Injected City"})
            result = [x.strip() for x in result.split(" || ") if x.strip()]
            return result[0]

        args = {
            "template": "{{{postcode}}} {{#first}} {{{city}}} || {{{town}}} "
            "|| {{{village}}} || {{{state}}} {{/first}}",
            "data": {
                "postcode": "1234",
                "town": "Mustache Town",
                "state": "Nowhere",
                "first": first,
            },
        }

        result = chevron_blue.render(**args)
        expected = "1234 Injected City"

        self.assertEqual(result, expected)

    def test_callable_4(self):
        """Test render of partial inside lambda"""

        def function(content, render):
            return render(content)

        args = {
            "template": "{{#function}}{{>partial}}{{!comment}}{{/function}}",
            "partials_dict": {
                "partial": "partial content",
            },
            "data": {
                "function": function,
            },
        }

        result = chevron_blue.render(**args)
        expected = "partial content"

        self.assertEqual(result, expected)

    # https://github.com/noahmorrison/chevron/issues/35
    def test_custom_falsy(self):
        class CustomData(dict):
            class LowercaseBool:
                _CHEVRON_return_scope_when_falsy = True

                def __init__(self, value):
                    self.value = value

                def __bool__(self):
                    return self.value

                __nonzero__ = __bool__

                def __str__(self):
                    if self.value:
                        return "true"
                    return "false"

            def __getitem__(self, key):
                item = dict.__getitem__(self, key)
                if isinstance(item, dict):
                    return CustomData(item)
                if isinstance(item, bool):
                    return self.LowercaseBool(item)
                return item

        args = {
            "data": CustomData(
                {
                    "truthy": True,
                    "falsy": False,
                }
            ),
            "template": "{{ truthy }} {{ falsy }}",
        }

        result = chevron_blue.render(**args)
        expected = "true false"

        self.assertEqual(result, expected)

    # https://github.com/noahmorrison/chevron/issues/39
    def test_nest_loops_with_same_key(self):
        args = {
            "template": "A{{#x}}B{{#x}}{{.}}{{/x}}C{{/x}}D",
            "data": {"x": ["z", "x"]},
        }

        result = chevron_blue.render(**args)
        expected = "ABzxCBzxCD"

        self.assertEqual(result, expected)

    # https://github.com/noahmorrison/chevron/issues/49
    def test_partial_indentation(self):
        args = {
            "template": "\t{{> count }}",
            "partials_dict": {"count": "\tone\n\ttwo"},
        }

        result = chevron_blue.render(**args)
        expected = "\t\tone\n\t\ttwo"

        self.assertEqual(result, expected)

    # https://github.com/noahmorrison/chevron/issues/52
    def test_indexed(self):
        args = {
            "template": "count {{count.0}}, {{count.1}}, {{count.100}}, {{nope.0}}",
            "data": {
                "count": [5, 4, 3, 2, 1],
            },
        }

        result = chevron_blue.render(**args)
        expected = "count 5, 4, , "

        self.assertEqual(result, expected)

    def test_iterator_scope_indentation(self):
        args = {
            "data": {
                "thing": ["foo", "bar", "baz"],
            },
            "template": "{{> count }}",
            "partials_dict": {
                "count": "    {{> iter_scope }}",
                "iter_scope": "foobar\n{{#thing}}\n {{.}}\n{{/thing}}",
            },
        }

        result = chevron_blue.render(**args)
        expected = "    foobar\n     foo\n     bar\n     baz\n"

        self.assertEqual(result, expected)

    # https://github.com/noahmorrison/chevron/pull/73
    def test_namedtuple_data(self):
        NT = collections.namedtuple("NT", ["foo", "bar"])
        args = {"template": "{{foo}} {{bar}}", "data": NT("hello", "world")}

        result = chevron_blue.render(**args)
        expected = "hello world"

        self.assertEqual(result, expected)

    def test_get_key_not_in_dunder_dict_returns_attribute(self):
        class C:
            foo = "bar"

        instance = C()
        self.assertTrue("foo" not in instance.__dict__)

        args = {"template": "{{foo}}", "data": instance}
        result = chevron_blue.render(**args)
        expected = "bar"

        self.assertEqual(result, expected)

    def test_disabled_partials(self):
        os.chdir("tests")
        resultNone = chevron_blue.main("test.mustache", "data.json", partials_path=None)

        resultEmpty = chevron_blue.main("test.mustache", "data.json", partials_path="")

        with io.open("test-partials-disabled.rendered", "r", encoding="utf-8") as f:
            expected = f.read()

        self.assertEqual(resultNone, expected)
        self.assertEqual(resultEmpty, expected)
        os.chdir("..")

    # https://github.com/noahmorrison/chevron/pull/94
    def test_keep(self):
        args = {
            "template": "{{ first }} {{ second }} {{ third }}",
            "data": {
                "first": "1st",
                "third": "3rd",
            },
        }

        result = chevron_blue.render(**args)
        expected = "1st  3rd"
        self.assertEqual(result, expected)

        args["keep"] = True

        result = chevron_blue.render(**args)
        expected = "1st {{ second }} 3rd"
        self.assertEqual(result, expected)

        args["template"] = "{{first}} {{second}} {{third}}"
        result = chevron_blue.render(**args)
        expected = "1st {{ second }} 3rd"
        self.assertEqual(result, expected)

        args["template"] = "{{   first    }} {{    second    }} {{    third   }}"
        result = chevron_blue.render(**args)
        expected = "1st {{ second }} 3rd"
        self.assertEqual(result, expected)

    # https://github.com/noahmorrison/chevron/pull/94
    def test_keep_from_partials(self):
        args = {
            "template": "{{ first }} {{> with_missing_key }} {{ third }}",
            "data": {
                "first": "1st",
                "third": "3rd",
            },
            "partials_dict": {
                "with_missing_key": "{{missing_key}}",
            },
        }

        result = chevron_blue.render(**args)
        expected = "1st  3rd"
        self.assertEqual(result, expected)

        args["keep"] = True

        result = chevron_blue.render(**args)
        expected = "1st {{ missing_key }} 3rd"
        self.assertEqual(result, expected)

    # https://github.com/noahmorrison/chevron/pull/94
    def test_no_escape(self):
        args = {
            "template": "{{ html_escaped }}",
            "data": {
                "html_escaped": '< > & "',
            },
            "no_escape": True,
        }

        result = chevron_blue.render(**args)
        expected = '< > & "'
        self.assertEqual(result, expected)

        args = {
            "template": "{{#a}}{{ html_escaped }}{{/a}}",
            "data": {
                "a": {
                    "html_escaped": '< > & "',
                }
            },
            "no_escape": True,
        }

        result = chevron_blue.render(**args)
        expected = '< > & "'
        self.assertEqual(result, expected)


class Teston_missing_key(unittest.TestCase):
    def test_on_missing_key_ignore(self):
        args = {
            "template": "{{missing}}",
            "data": {},
            "on_missing_key": "ignore",
        }

        result = chevron_blue.render(**args)
        expected = ""
        self.assertEqual(result, expected)

    def test_on_missing_key_warn(self):
        args = {
            "template": "{{missing}}",
            "data": {},
            "on_missing_key": "warn",
        }

        with self.assertWarns(UserWarning, msg="Could not find key 'missing'"):
            chevron_blue.render(**args)

    def test_on_missing_key_error(self):
        args = {
            "template": "{{missing}}",
            "data": {},
            "on_missing_key": "error",
        }

        with self.assertRaises(KeyError) as context:
            chevron_blue.render(**args)
            self.assertEqual(str(context.exception), "Could not find key 'missing'")

    def test_on_missing_key_warn_false(self):
        args = {
            "template": "{{missing}}",
            "data": {},
            "warn": False,
        }

        result = chevron_blue.render(**args)
        expected = ""
        self.assertEqual(result, expected)

    def test_on_missing_key_warn_true(self):
        args = {
            "template": "{{missing}}",
            "data": {},
            "warn": True,
        }

        with self.assertWarns(UserWarning, msg="Could not find key 'missing'"):
            chevron_blue.render(**args)

    def test_on_missing_key_and_warn(self):
        args = {
            "template": "{{missing}}",
            "data": {},
            "warn": True,
            "on_missing_key": "ignore",
        }

        with self.assertRaises(ValueError) as context:
            chevron_blue.render(**args)
            self.assertEqual(
                str(context.exception),
                "The `warn` argument cannot be used with `on_missing_key`.",
            )


# Run unit tests from command line
if __name__ == "__main__":
    unittest.main()
