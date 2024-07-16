from release_notes_generator.model.chapter import Chapter


# __init__

def test_initialization(service_chapters):
    assert service_chapters.sort_ascending is True
    assert service_chapters.print_empty_chapters is True
    assert service_chapters.user_defined_labels == ['bug', 'enhancement']
    assert isinstance(service_chapters.chapters[service_chapters.CLOSED_ISSUES_WITHOUT_PULL_REQUESTS], Chapter)


# populate

def test_populate_closed_issue(service_chapters, record_with_issue_closed_no_pull):
    service_chapters.populate({1: record_with_issue_closed_no_pull})

    assert 1 == len(service_chapters.chapters[service_chapters.CLOSED_ISSUES_WITHOUT_PULL_REQUESTS].rows)
    assert 1 == len(service_chapters.chapters[service_chapters.CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS].rows)


def test_populate_merged_pr(service_chapters, record_with_no_issue_one_pull_merged):
    service_chapters.populate({2: record_with_no_issue_one_pull_merged})

    assert 1 == len(service_chapters.chapters[service_chapters.MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS].rows)


def test_populate_closed_pr(service_chapters, record_with_no_issue_one_pull_closed):
    service_chapters.populate({2: record_with_no_issue_one_pull_closed})

    assert 1 == len(service_chapters.chapters[service_chapters.CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS].rows)


def test_populate_not_closed_issue(service_chapters, record_with_issue_open_one_pull_closed):
    service_chapters.populate({1: record_with_issue_open_one_pull_closed})
    print(service_chapters.to_string())

    assert 1 == len(service_chapters.chapters[service_chapters.MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES].rows)


def test_populate_not_closed_issue_without_pull(service_chapters, record_with_issue_open_no_pull):
    service_chapters.populate({1: record_with_issue_open_no_pull})
    print(service_chapters.to_string())

    assert 0 == len(service_chapters.chapters[service_chapters.CLOSED_ISSUES_WITHOUT_PULL_REQUESTS].rows)
    assert 0 == len(service_chapters.chapters[service_chapters.CLOSED_ISSUES_WITHOUT_USER_DEFINED_LABELS].rows)
    assert 0 == len(service_chapters.chapters[service_chapters.MERGED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS].rows)
    assert 0 == len(service_chapters.chapters[service_chapters.CLOSED_PRS_WITHOUT_ISSUE_AND_USER_DEFINED_LABELS].rows)
    assert 0 == len(service_chapters.chapters[service_chapters.MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES].rows)
    assert 0 == len(service_chapters.chapters[service_chapters.OTHERS_NO_TOPIC].rows)


def test_populate_no_issue_with_pull(service_chapters, record_with_no_issue_one_pull_merged_with_issue_mentioned):
    service_chapters.populate({1: record_with_no_issue_one_pull_merged_with_issue_mentioned})
    print(service_chapters.to_string())

    assert 1 == len(service_chapters.chapters[service_chapters.MERGED_PRS_LINKED_TO_NOT_CLOSED_ISSUES].rows)
