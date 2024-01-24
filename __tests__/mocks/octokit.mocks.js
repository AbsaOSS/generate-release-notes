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
            get: jest.fn().mockResolvedValue({
                data: [],
            }),
        },
    }
});

const mockFullPerfectData = () => ({
    rest: {
        repos: {
            getLatestRelease: jest.fn().mockResolvedValue({ data: {
                    tag_name: 'v1.0.0',
                    published_at: '2023-12-12T09:58:30.000Z',
                    created_at: '2023-12-12T09:56:30.000Z',
                } }),
        },
        issues: {
            listForRepo: jest.fn().mockResolvedValue({
                data: [
                    {
                        number: 1,
                        title: 'Issue 1',
                        state: 'closed',
                        labels: [{ name: 'bug' }],
                        assignees: [],
                    },
                    {
                        number: 2,
                        title: 'Issue 2',
                        state: 'open',
                        labels: [{ name: 'enhancement' }],
                        assignees: [
                            {
                                login: "someone"
                            },
                        ],
                    },
                ],
            }),
            listEventsForTimeline: jest.fn().mockResolvedValue({
                data: [
                    {
                        id: 1,
                        event: 'labeled',
                        label: { name: 'bug' },
                        source: {
                            issue: {
                                pull_request: "link"
                            },
                        },
                    },
                    {
                        id: 2,
                        event: 'cross-referenced',
                        source: {
                            issue: {
                                pull_request: "link"
                            },
                        },
                    },
                ],
            }),
            listComments: jest.fn().mockResolvedValue({
                data: [
                    {
                        id: 101,
                        user: { login: 'user1' },
                        body: 'This is the first comment.',
                        created_at: '2023-01-01T10:00:00Z',
                        updated_at: '2023-01-01T10:00:00Z'
                    },
                    {
                        id: 102,
                        user: { login: 'user2' },
                        body: 'Release notes:\\n- note about change',
                        created_at: '2023-01-02T11:00:00Z',
                        updated_at: '2023-01-02T11:00:00Z'
                    },
                ],
            }),
        },
        pulls: {
            list: jest.fn().mockResolvedValue({
                data: [
                    {
                        id: 1,
                        title: 'Pull Request 1',
                        state: 'closed',
                        labels: [{ name: 'bug' }],
                    },
                    {
                        id: 2,
                        title: 'Pull Request 2',
                        state: 'open',
                        labels: [{ name: 'enhancement' }],
                    },
                ],
            }),
            listCommits: jest.fn().mockResolvedValue({
                data: [
                    {
                        commit: {
                            author: {
                                name: 'John Doe',
                                email: 'john.doe@example.com',
                            },
                            message: 'Initial commit'
                        },
                        author: {
                            login: 'johnDoe',
                        },
                        url: 'https://api.github.com/repos/owner/repo/commits/abc123'
                    },
                    {
                        commit: {
                            author: {
                                name: 'Jane Smith',
                                email: 'jane.smith@example.com',
                            },
                            message: 'Add new feature'
                        },
                        author: {
                            login: 'johnDoe',
                        },
                        url: 'https://api.github.com/repos/owner/repo/commits/def456'
                    },
                ],
            }),
            get: jest.fn().mockResolvedValue({
                data: [
                    {
                        body: 'This is a detailed description of the pull request.',
                    },
                ],
            }),
        },
    }
});

module.exports = {
    mockEmptyData,
    mockFullPerfectData,
};