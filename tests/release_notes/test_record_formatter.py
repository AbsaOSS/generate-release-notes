from release_notes_generator.record.record_formatter import RecordFormatter


def test_format_record_with_issue(record_with_issue_closed_one_pull):
    formatter = RecordFormatter()
    formatted = formatter.format(record_with_issue_closed_one_pull)
    expected_output = "- #122 _Fix the bug_ implemented by developers in [#123](http://example.com/pull/123)\n  - release notes 1\n  - release notes 2"

    assert expected_output == formatted


# TODO - following tests could be used when topic will be implemented
# def test_format_record_without_issue(record_without_issue):
#     formatter = RecordFormatter()
#     formatted = formatter.format(record_without_issue)
#     expected_output = "- #1 _Pull Request Title_ implemented by developers in [#1](http://example.com/pull/1), [#2](http://example.com/pull/2)\n  - release notes 1\n  - release notes 2"
#     assert formatted == expected_output
#
#
# def test_format_pulls():
#     formatter = RecordFormatter()
#     pulls = [PullRequest(number=1, url="http://example.com/pull/1"), PullRequest(number=2, url="http://example.com/pull/2")]
#     formatted_pulls = formatter._format_pulls(pulls)
#     expected_output = "[#1](http://example.com/pull/1), [#2](http://example.com/pull/2)"
#     assert formatted_pulls == expected_output
#
#
# def test_format_developers(record_with_issue):
#     formatter = RecordFormatter()
#     developers = formatter._format_developers(record_with_issue)
#     assert developers == "developers"
#
#
# def test_format_release_note_rows(record_with_issue):
#     formatter = RecordFormatter()
#     release_note_rows = formatter._format_release_note_rows(record_with_issue)
#     expected_output = "  - release notes 1\n  - release notes 2"
#     assert release_note_rows == expected_output
