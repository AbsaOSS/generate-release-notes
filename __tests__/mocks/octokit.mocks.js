const mockEmptyData = () => ({
    rest: {
        repos: {
            getLatestRelease: jest.fn(() => {
                throw {
                    status: 404,
                    message: "Not Found"
                };
            }),
        },
        issues: {
            listForRepo: jest.fn().mockResolvedValue({
                data: [],
            }),
            listEventsForTimeline: jest.fn().mockResolvedValue({
                data: [],
            }),
            listComments: jest.fn().mockResolvedValue({
                data: [],
            }),
        },
        pulls: {
            list: jest.fn().mockResolvedValue({
                data: [],
            }),
            listCommits: jest.fn().mockResolvedValue({
                data: [],
            }),
            listReviewComments: jest.fn().mockResolvedValue({
                data: [],
            }),
            get: jest.fn().mockResolvedValue({
                data: [],
            }),
        },
    }
});

const mockFullPerfectData = () => ({
    rest: {
        repos: {
            getLatestRelease: jest.fn(({owner, repo}) => {
                if (repo === "repo-no-rls") {
                    throw {
                        status: 404,
                        message: "Not Found"
                    };
                } else if (repo === "repo-2nd-rls") {
                    return Promise.resolve({
                        data: {
                            tag_name: 'v0.1.0',
                            published_at: '2023-12-15T09:58:30.000Z',
                            created_at: '2023-12-15T06:56:30.000Z',
                        }
                    });
                } else {
                    return Promise.resolve({
                        data: {
                            tag_name: 'v0.1.0',
                            published_at: '2022-12-12T09:58:30.000Z',
                            created_at: '2022-12-12T06:56:30.000Z',
                        }
                    });
                }
            }),
        },
        issues: {
            listForRepo: jest.fn().mockResolvedValue({
                data: [
                    {
                        number: 1,
                        title: 'Issue title 1',
                        state: 'closed',
                        labels: [{ name: 'bug' }],
                        assignees: [
                            {
                                login: "janeDoe",
                            },
                        ],
                        "closed_at": "2023-12-12T11:58:30.000Z",
                        "created_at": "2023-12-12T09:58:30.000Z",
                        "updated_at": "2023-12-12T10:58:30.000Z",
                    },
                    {
                        number: 2,
                        title: 'Issue title 2',
                        state: 'open',
                        labels: [{ name: 'enhancement' }],
                        assignees: [
                            {
                                login: "johnDoe",
                            },
                        ],
                        "closed_at": null,
                        "created_at": "2023-12-12T11:58:30.000Z",
                        "updated_at": "2023-12-12T12:58:30.000Z",
                    },
                    {
                        number: 3,
                        title: 'Issue title 3 - no release note comment|typo label',
                        state: 'closed',
                        labels: [{ name: 'enhacement' }],
                        assignees: [
                            {
                                login: "janeDoe",
                            },
                        ],
                        "closed_at": "2023-12-12T15:58:30.000Z",
                        "created_at": "2023-12-12T13:58:30.000Z",
                        "updated_at": "2023-12-12T14:58:30.000Z",
                    },
                    {
                        number: 4,
                        title: 'Issue title 4 - assigned|one PR',
                        state: 'closed',
                        labels: [{ name: 'feature' }],
                        assignees: [
                            {
                                login: "johnDoe",
                            },
                        ],
                        "closed_at": "2023-12-12T16:58:30.000Z",
                        "created_at": "2023-12-12T14:58:30.000Z",
                        "updated_at": "2023-12-12T15:58:30.000Z",
                    },
                    {
                        number: 5,
                        title: 'Issue title 5 - not assigned|three PRs',
                        state: 'closed',
                        labels: [{ name: 'feature' }, { name: 'user-custom-label' }],
                        assignees: [],
                        "closed_at": "2023-12-12T18:58:30.000Z",
                        "created_at": "2023-12-12T16:58:30.000Z",
                        "updated_at": "2023-12-12T17:58:30.000Z",
                    },
                    {
                        number: 6,
                        title: 'Issue title 6 - not assigned|no PR',
                        state: 'closed',
                        labels: [{ name: 'feature' }],
                        assignees: [],
                        "closed_at": "2023-12-12T20:58:30.000Z",
                        "created_at": "2023-12-12T18:58:30.000Z",
                        "updated_at": "2023-12-12T19:58:30.000Z",
                    },
                    {
                        number: 7,
                        title: 'Issue title 7 - with co-author|public mail',
                        state: 'closed',
                        labels: [{ name: 'breaking-change' }],
                        assignees: [
                            {
                                login: "janeDoe",
                            },
                        ],
                        "closed_at": "2023-12-12T22:58:30.000Z",
                        "created_at": "2023-12-12T20:58:30.000Z",
                        "updated_at": "2023-12-12T21:58:30.000Z",
                    },
                    {
                        number: 8,
                        title: 'Issue title 8 - with co-author|private mail',
                        state: 'closed',
                        labels: [{ name: 'breaking-change' }],
                        assignees: [
                            {
                                login: "johnDoe",
                            },
                        ],
                        "closed_at": "2023-12-13T07:58:30.000Z",
                        "created_at": "2023-12-13T05:58:30.000Z",
                        "updated_at": "2023-12-13T06:58:30.000Z",
                    },
                    {
                        number: 9,
                        title: 'Issue title 9 - no user defined label',
                        state: 'closed',
                        labels: [{ name: 'no-user-defined' }],
                        assignees: [
                            {
                                login: "janeDoe",
                            },
                        ],
                        "closed_at": "2023-12-13T09:58:30.000Z",
                        "created_at": "2023-12-13T07:58:30.000Z",
                        "updated_at": "2023-12-13T08:58:30.000Z",
                    },
                    {
                        number: 10,
                        title: 'Issue title 10 - skip label',
                        state: 'closed',
                        labels: [{ name: 'skip-release-notes' }],
                        assignees: [
                            {
                                login: "janeDoe",
                            },
                        ],
                        "closed_at": "2023-12-13T11:58:30.000Z",
                        "created_at": "2023-12-13T09:58:30.000Z",
                        "updated_at": "2023-12-13T10:58:30.000Z",
                    },
                ],
            }),
            listEventsForTimeline: jest.fn(({owner, repo, issue_number}) => {
                if (issue_number === 1) {
                    return Promise.resolve({
                        data: [
                            {
                                id: 1,
                                event: 'cross-referenced',
                                labels: [],
                                source: {
                                    issue: {
                                        pull_request: "link-to-pr-1",
                                        number: 1,
                                        html_url: "link-to-pr-1",
                                    },
                                },
                            },
                        ],
                    });
                } else if (issue_number === 2) {
                    return Promise.resolve({
                        data: [
                            {
                                id: 2,
                                event: 'cross-referenced',
                                labels: [],
                                source: {
                                    issue: {
                                        pull_request: "link-to-pr-2",
                                        number: 2,
                                        html_url: "link-to-pr-2",
                                    },
                                },
                            },
                        ],
                    });
                } else if (issue_number === 3) {
                    return Promise.resolve({
                        data: [
                            {
                                id: 3,
                                event: 'cross-referenced',
                                labels: [],
                                source: {
                                    issue: {
                                        pull_request: "link-to-pr-3",
                                        number: 3,
                                        html_url: "link-to-pr-3",
                                    },
                                },
                            },
                        ],
                    });
                } else if (issue_number === 4) {
                    return Promise.resolve({
                        data: [
                            {
                                id: 4,
                                event: 'cross-referenced',
                                labels: [],
                                source: {
                                    issue: {
                                        pull_request: "link-to-pr-4",
                                        number: 4,
                                        html_url: "link-to-pr-4",
                                    },
                                },
                            },
                        ],
                    });
                } else if (issue_number === 5) {
                    return Promise.resolve({
                        data: [
                            {
                                id: 5,
                                event: 'cross-referenced',
                                labels: [],
                                source: {
                                    issue: {
                                        pull_request: "link-to-pr-5",
                                        number: 5,
                                        html_url: "link-to-pr-5",
                                    },
                                },
                            },
                            {
                                id: 15,
                                event: 'cross-referenced',
                                labels: [],
                                source: {
                                    issue: {
                                        pull_request: "link-to-pr-15",
                                        number: 15,
                                        html_url: "link-to-pr-15",
                                    },
                                },
                            },
                            {
                                id: 16,
                                event: 'cross-referenced',
                                labels: [],
                                source: {
                                    issue: {
                                        pull_request: "link-to-pr-16",
                                        number: 16,
                                        html_url: "link-to-pr-16",
                                    },
                                },
                            },
                        ],
                    });
                } else if (issue_number === 6) {
                    return Promise.resolve({
                        data: [],
                    });
                } else if (issue_number === 7) {
                    return Promise.resolve({
                        data: [
                            {
                                id: 7,
                                event: 'cross-referenced',
                                labels: [],
                                source: {
                                    issue: {
                                        pull_request: "link-to-pr-7",
                                        number: 7,
                                        html_url: "link-to-pr-7",
                                    },
                                },
                            },
                        ],
                    });
                } else if (issue_number === 8) {
                    return Promise.resolve({
                        data: [
                            {
                                id: 8,
                                event: 'cross-referenced',
                                labels: [],
                                source: {
                                    issue: {
                                        pull_request: "link-to-pr-8",
                                        number: 8,
                                        html_url: "link-to-pr-8",
                                    },
                                },
                            },
                        ],
                    });
                } else if (issue_number === 9) {
                    return Promise.resolve({
                        data: [
                            {
                                id: 9,
                                event: 'cross-referenced',
                                labels: [],
                                source: {
                                    issue: {
                                        pull_request: "link-to-pr-9",
                                        number: 9,
                                        html_url: "link-to-pr-9",
                                    },
                                },
                            },
                        ],
                    });
                } else if (issue_number === 100) {
                    return Promise.resolve({
                        data: [
                            {
                                id: 1,
                                event: 'labeled',
                                labels: [
                                    {
                                        name: 'todo',
                                    }
                                ],
                                source: {
                                    issue: {
                                        pull_request: "link-to-issue-X"
                                    },
                                },
                            },
                            {
                                id: 2,
                                event: 'cross-referenced',
                                labels: [
                                    {
                                        name: 'todo',
                                    }
                                ],
                                source: {
                                    issue: {
                                        pull_request: "link-to-issue-Y"
                                    },
                                },
                            },
                        ],
                    });
                } else {
                    // default universal return value
                    return Promise.resolve({
                        data: [],
                    });
                }
            }),
            listComments: jest.fn(({owner, repo, issue_number}) => {
                if (issue_number === 1) {
                    return Promise.resolve({
                        data: [
                            {
                                id: 101,
                                user: {login: 'user 1'},
                                body: 'This is the first comment in Issue 1',
                                created_at: '2023-01-01T10:00:00Z',
                                updated_at: '2023-01-01T10:00:00Z'
                            },
                            {
                                id: 102,
                                user: {login: 'user2'},
                                body: 'Release notes:\n- note about change in Issue 1',
                                created_at: '2023-01-02T11:00:00Z',
                                updated_at: '2023-01-02T11:00:00Z'
                            },
                            {
                                id: 103,
                                user: {login: 'user2'},
                                body: 'Release notes:\nnote about change in Issue 1 (no bullet point at start of line)',
                                created_at: '2023-01-02T12:00:00Z',
                                updated_at: '2023-01-02T12:01:00Z'
                            },
                        ]
                    });
                } else if (issue_number === 2) {
                    return Promise.resolve({
                        data: [
                            {
                                id: 201,
                                user: {login: 'user 1'},
                                body: 'This is the first comment in Issue 2.',
                                created_at: '2023-01-01T10:00:00Z',
                                updated_at: '2023-01-01T10:00:00Z'
                            },
                            {
                                id: 202,
                                user: {login: 'user2'},
                                body: 'Release notes:\n- note about change in Issue 2',
                                created_at: '2023-01-02T11:00:00Z',
                                updated_at: '2023-01-02T11:00:00Z'
                            },
                        ]
                    });
                } else if (issue_number === 4) {
                    return Promise.resolve({
                        data: [
                            {
                                id: 401,
                                user: {login: 'user 1'},
                                body: 'This is the first comment in Issue 4.',
                                created_at: '2023-01-01T10:00:00Z',
                                updated_at: '2023-01-01T10:00:00Z'
                            },
                            {
                                id: 402,
                                user: {login: 'user2'},
                                body: 'Release notes:\n- note about change in Issue 4',
                                created_at: '2023-01-02T11:00:00Z',
                                updated_at: '2023-01-02T11:00:00Z'
                            },
                        ]
                    });
                } else if (issue_number === 5) {
                    return Promise.resolve({
                        data: [
                            {
                                id: 501,
                                user: {login: 'user 1'},
                                body: 'This is the first comment in Issue 5.',
                                created_at: '2023-01-01T10:00:00Z',
                                updated_at: '2023-01-01T10:00:00Z'
                            },
                            {
                                id: 502,
                                user: {login: 'user2'},
                                body: 'Release notes:\n- note about change in Issue 5',
                                created_at: '2023-01-02T11:00:00Z',
                                updated_at: '2023-01-02T11:00:00Z'
                            },
                        ]
                    });
                } else if (issue_number === 6) {
                    return Promise.resolve({
                        data: [
                            {
                                id: 601,
                                user: {login: 'user 1'},
                                body: 'This is the first comment in Issue 6.',
                                created_at: '2023-01-01T10:00:00Z',
                                updated_at: '2023-01-01T10:00:00Z'
                            },
                            {
                                id: 602,
                                user: {login: 'user2'},
                                body: 'Release notes:\n- note about change in Issue 6',
                                created_at: '2023-01-02T11:00:00Z',
                                updated_at: '2023-01-02T11:00:00Z'
                            },
                        ]
                    });
                } else if (issue_number === 7) {
                    return Promise.resolve({
                        data: [
                            {
                                id: 701,
                                user: {login: 'user 1'},
                                body: 'This is the first comment in Issue 7.',
                                created_at: '2023-01-01T10:00:00Z',
                                updated_at: '2023-01-01T10:00:00Z'
                            },
                            {
                                id: 702,
                                user: {login: 'user2'},
                                body: 'Release notes:\n- note about change in Issue 7',
                                created_at: '2023-01-02T11:00:00Z',
                                updated_at: '2023-01-02T11:00:00Z'
                            },
                        ]
                    });
                } else if (issue_number === 8) {
                    return Promise.resolve({
                        data: [
                            {
                                id: 801,
                                user: {login: 'user 1'},
                                body: 'This is the first comment in Issue 8.',
                                created_at: '2023-01-01T10:00:00Z',
                                updated_at: '2023-01-01T10:00:00Z'
                            },
                            {
                                id: 802,
                                user: {login: 'user2'},
                                body: 'Release notes:\n- note about change in Issue 8',
                                created_at: '2023-01-02T11:00:00Z',
                                updated_at: '2023-01-02T11:00:00Z'
                            },
                        ]
                    });
                } else if (issue_number === 9) {
                    return Promise.resolve({
                        data: [
                            {
                                id: 801,
                                user: {login: 'user 1'},
                                body: 'This is the first comment in Issue 9.',
                                created_at: '2023-01-01T10:00:00Z',
                                updated_at: '2023-01-01T10:00:00Z'
                            },
                            {
                                id: 802,
                                user: {login: 'user2'},
                                body: 'Release notes\n- note about change in Issue 9',
                                created_at: '2023-01-02T11:00:00Z',
                                updated_at: '2023-01-02T11:00:00Z'
                            },
                        ]
                    });
                } else {
                    return Promise.resolve({
                        data: [],
                    });
                }
            }),
            get: jest.fn(({owner, repo, issue_number}) => {
                console.log(`Called 'get' with issue_number: ${issue_number}`);

                if (issue_number === 2) {
                    return Promise.resolve({
                        data: {
                            state: 'open',
                        },
                    });
                } else {
                    return Promise.resolve({
                        data: {},
                    });
                }
            }),
        },
        pulls: {
            // ready only for process with existing previous release
            list: jest.fn(({owner, repo, state, sort, direction, since}) => {
                return Promise.resolve({
                    data: [
                        {
                            number: 1001,
                            title: 'Pull Request 1',
                            state: 'merged',
                            labels: [{ name: 'user-custom-label' }],
                            created_at: '2023-12-12T15:56:30.000Z',
                            merged_at: '2023-12-12T15:58:30.000Z',
                            assignees: [
                                {
                                    login: "janeDoe",
                                },
                            ],
                        },
                        {
                            number: 1002,
                            title: 'Pull Request 2 - no linked issue - closed',
                            state: 'closed',
                            labels: [],
                            created_at: '2023-12-12T15:57:30.000Z',
                            closed_at: '2023-12-12T15:58:30.000Z',
                            assignees: [
                                {
                                    login: "janeDoe",
                                },
                            ],
                        },
                        {
                            number: 1003,
                            title: 'Pull Request 3 - linked to open issue',
                            state: 'merged',
                            labels: [],
                            created_at: '2023-12-12T15:58:30.000Z',
                            merged_at: '2023-12-12T15:59:30.000Z',
                            assignees: [
                                {
                                    login: "janeDoe",
                                },
                            ],
                        },
                        {
                            number: 1004,
                            title: 'Pull Request 4 - no linked issue - merged',
                            state: 'merged',
                            labels: [],
                            created_at: '2023-12-12T15:59:30.000Z',
                            merged_at: '2023-12-12T16:59:30.000Z',
                            assignees: [
                                {
                                    login: "janeDoe",
                                },
                            ],
                        },
                        {
                            number: 1005,
                            title: 'Pull Request 5',
                            state: 'open',
                            labels: [],
                            created_at: '2023-12-12T15:59:35.000Z',
                            assignees: [
                                {
                                    login: "janeDoe",
                                },
                            ],
                        },
                        {
                            number: 1006,
                            title: 'Pull Request 6 - skip label',
                            state: 'merged',
                            labels: [{ name: 'skip-release-notes' }],
                            created_at: '2023-12-12T15:59:37.000Z',
                            merged_at: '2023-12-12T17:59:37.000Z',
                            assignees: [
                                {
                                    login: "janeDoe",
                                },
                            ],
                        },
                    ],
                });
            }),
            listCommits: jest.fn(({owner, repo, pull_number}) => {
                if (pull_number === 7) {
                    return Promise.resolve({
                        data: [
                            {
                                commit: {
                                    author: {
                                        name: 'Jane Doe',
                                        email: 'jane.doe@example.com',
                                    },
                                    message: 'Initial commit\n\nCo-authored-by: John Doe <john.doe@example.com>'
                                },
                                author: {
                                    login: 'janeDoe',
                                },
                                url: 'https://api.github.com/repos/owner/repo/commits/abc123'
                            },
                        ]
                    });
                } else if (pull_number === 8) {
                    return Promise.resolve({
                        data: [
                            {
                                commit: {
                                    author: {
                                        name: 'John Doe',
                                        email: 'john.doe@example.com',
                                    },
                                    message: 'Initial commit\n\nCo-authored-by: Jane Doe <jane.doe@example.com>'
                                },
                                author: {
                                    login: 'johnDoe',
                                },
                                url: 'https://api.github.com/repos/owner/repo/commits/abc124'
                            },
                        ]
                    });
                } else {
                    return Promise.resolve({
                        data: [],
                    });
                }
            }),
            listReviewComments: jest.fn(({owner, repo, pull_number}) => {
                if (pull_number === 1001) {
                    return Promise.resolve({
                        data: [
                            {
                                body: 'This is first PR comment.',
                            },
                            {
                                body: 'Release notes\nThis is second PR comment ad RLS note',
                            },
                            {
                                body: 'Release notes\nThis is third PR comment ad RLS note',
                            },
                        ],
                    });
                } else {
                    return Promise.resolve({
                        data: [],
                    });
                }
            }),
            get: jest.fn(({owner, repo, pull_number}) => {
                if (pull_number === 1003) {
                    return Promise.resolve({
                        data: {
                            body: 'This is a detailed description of the pull request.\n\nCloses #2',
                        },
                    });
                } else {
                    return Promise.resolve({
                        data: [],
                    });
                }
            }),
        },
        search: {
            users: jest.fn(({q}) => {
                if (q === "john.doe@example.com in:email") {
                    return Promise.resolve({
                        data: {
                            total_count: 1,
                            items: [
                                {
                                    id: 1,
                                    login: "johnDoe"
                                }
                            ]
                        }
                    });
                } else if (q === "jane.doe@example.com in:email") {
                    return Promise.resolve({
                        data: {
                            total_count: 1,
                            items: [
                                {
                                    id: 2
                                }
                            ]
                        },
                    })
                } else {
                    return Promise.resolve({
                        data: [],
                    })
                }
            }),
        },
    }
});
const mockPerfectDataWithoutIssues = () => ({
    rest: {
        repos: {
            getLatestRelease: jest.fn(({owner, repo}) => {
                if (repo === "repo-no-rls") {
                    throw {
                        status: 404,
                        message: "Not Found"
                    };
                } else if (repo === "repo-2nd-rls") {
                    return Promise.resolve({
                        data: {
                            tag_name: 'v0.1.0',
                            published_at: '2023-12-15T09:58:30.000Z',
                            created_at: '2023-12-15T06:56:30.000Z',
                        }
                    });
                } else {
                    return Promise.resolve({
                        data: {
                            tag_name: 'v0.1.0',
                            published_at: '2022-12-12T09:58:30.000Z',
                            created_at: '2022-12-12T06:56:30.000Z',
                        }
                    });
                }
            }),
        },
        issues: {
            listForRepo: jest.fn().mockResolvedValue({
                data: []
            }),
            listEventsForTimeline: jest.fn(({owner, repo, issue_number}) => {
                return Promise.resolve({
                    data: [],
                });
            }),
            listComments: jest.fn(({owner, repo, issue_number}) => {
                return Promise.resolve({
                    data: [],
                });
            }),
            get: jest.fn(({owner, repo, issue_number}) => {
                return Promise.resolve({
                    data: {},
                });
            }),
        },
        pulls: {
            // ready only for process with existing previous release
            list: jest.fn(({owner, repo, state, sort, direction, since}) => {
                return Promise.resolve({
                    data: [
                        {
                            number: 1001,
                            title: 'Pull Request 1',
                            state: 'merged',
                            labels: [{ name: 'user-custom-label' }],
                            created_at: '2023-12-12T15:56:30.000Z',
                            merged_at: '2023-12-12T15:58:30.000Z',
                        },
                        {
                            number: 1002,
                            title: 'Pull Request 2 - no linked issue - closed',
                            state: 'closed',
                            labels: [],
                            created_at: '2023-12-12T15:57:30.000Z',
                            closed_at: '2023-12-12T15:58:30.000Z',
                        },
                        {
                            number: 1003,
                            title: 'Pull Request 3 - linked to open issue',
                            state: 'merged',
                            labels: [],
                            created_at: '2023-12-12T15:58:30.000Z',
                            merged_at: '2023-12-12T15:59:30.000Z',
                        },
                        {
                            number: 1004,
                            title: 'Pull Request 4 - no linked issue - merged',
                            state: 'merged',
                            labels: [],
                            created_at: '2023-12-12T15:59:30.000Z',
                            merged_at: '2023-12-12T16:59:30.000Z',
                        },
                        {
                            number: 1005,
                            title: 'Pull Request 5',
                            state: 'open',
                            labels: [],
                            created_at: '2023-12-12T15:59:35.000Z',
                        },
                        {
                            number: 1006,
                            title: 'Pull Request 6 - skip label',
                            state: 'merged',
                            labels: [{ name: 'skip-release-notes' }],
                            created_at: '2023-12-12T15:59:37.000Z',
                            merged_at: '2023-12-12T17:59:37.000Z',
                        },
                    ],
                });
            }),
            listCommits: jest.fn(({owner, repo, pull_number}) => {
                if (pull_number === 7) {
                    return Promise.resolve({
                        data: [
                            {
                                commit: {
                                    author: {
                                        name: 'Jane Doe',
                                        email: 'jane.doe@example.com',
                                    },
                                    message: 'Initial commit\n\nCo-authored-by: John Doe <john.doe@example.com>'
                                },
                                author: {
                                    login: 'janeDoe',
                                },
                                url: 'https://api.github.com/repos/owner/repo/commits/abc123'
                            },
                        ]
                    });
                } else if (pull_number === 8) {
                    return Promise.resolve({
                        data: [
                            {
                                commit: {
                                    author: {
                                        name: 'John Doe',
                                        email: 'john.doe@example.com',
                                    },
                                    message: 'Initial commit\n\nCo-authored-by: Jane Doe <jane.doe@example.com>'
                                },
                                author: {
                                    login: 'johnDoe',
                                },
                                url: 'https://api.github.com/repos/owner/repo/commits/abc124'
                            },
                        ]
                    });
                } else {
                    return Promise.resolve({
                        data: [],
                    });
                }
            }),
            listReviewComments: jest.fn(({owner, repo, pull_number}) => {
                return Promise.resolve({
                    data: [],
                });
            }),
            get: jest.fn(({owner, repo, pull_number}) => {
                if (pull_number === 1003) {
                    return Promise.resolve({
                        data: {
                            body: 'This is a detailed description of the pull request.\n\nCloses #2',
                        },
                    });
                } else {
                    return Promise.resolve({
                        data: [],
                    });
                }
            }),
        },
        search: {
            users: jest.fn(({q}) => {
                if (q === "john.doe@example.com in:email") {
                    return Promise.resolve({
                        data: {
                            total_count: 1,
                            items: [
                                {
                                    id: 1,
                                    login: "johnDoe"
                                }
                            ]
                        }
                    });
                } else if (q === "jane.doe@example.com in:email") {
                    return Promise.resolve({
                        data: {
                            total_count: 1,
                            items: [
                                {
                                    id: 2
                                }
                            ]
                        },
                    })
                } else {
                    return Promise.resolve({
                        data: [],
                    })
                }
            }),
        },
    }
});

module.exports = {
    mockEmptyData,
    mockFullPerfectData,
    mockPerfectDataWithoutIssues,
};