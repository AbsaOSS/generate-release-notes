const { Octokit } = require("@octokit/rest");
const core = require('@actions/core');

// Fetch the latest release
async function fetchLatestRelease(octokit, owner, repo) {
    try {
        return await octokit.rest.repos.getLatestRelease({
            owner,
            repo
        });
    } catch (error) {
        throw new Error(`Error fetching latest release: ${error.message}`);
    }
}

async function getReleaseNotesFromComments(octokit, issueNumber, issueTitle, issueAuthor, issueAssignees, repoOwner, repoName) {
    console.log(`Fetching related PRs for issue #${issueNumber}`);
    const relatedPRs = await octokit.rest.issues.listEventsForTimeline({
        owner: repoOwner,
        repo: repoName,
        issue_number: issueNumber
    });

    const prLinks = relatedPRs.data
        .filter(event => event.event === 'cross-referenced' && event.source && event.source.issue.pull_request)
        .map(event => `[#${event.source.issue.number}](${event.source.issue.html_url})`)
        .join(', ');

    console.log(`Found ${prLinks.length} related PRs for issue #${issueNumber}`);
    console.log(`Related PRs for issue #${issueNumber}: ${prLinks}`);

    let commitAuthors = new Set();
    for (const event of relatedPRs.data) {
        if (event.event === 'cross-referenced' && event.source && event.source.issue.pull_request) {
            const prNumber = event.source.issue.number;
            const commits = await octokit.rest.pulls.listCommits({
                owner: repoOwner,
                repo: repoName,
                pull_number: prNumber
            });

            for (const commit of commits.data) {
                commitAuthors.add('@' + commit.author.login);

                const coAuthorMatches = commit.commit.message.match(/Co-authored-by: (.+ <.+>)/gm);
                if (coAuthorMatches) {
                    for (const coAuthorLine of coAuthorMatches) {
                        const emailRegex = /<([^>]+)>/;
                        const nameRegex = /Co-authored-by: (.+) </;
                        const emailMatch = emailRegex.exec(coAuthorLine);
                        const nameMatch = nameRegex.exec(coAuthorLine);
                        if (emailMatch && nameMatch) {
                            const email = emailMatch[1];
                            const name = nameMatch[1].trim();
                            console.log(`Searching for GitHub user with email: ${email}`);
                            const searchResult = await octokit.rest.search.users({
                                q: `${email} in:email`
                            });
                            const user = searchResult.data.items[0];
                            if (user && user.login) {
                                commitAuthors.add('@' + user.login);
                            } else {
                                console.log(`No public GitHub account found for email: ${email}`);
                                commitAuthors.add(name);
                            }
                        }
                    }
                }
            }
        }
    }

    let contributors = new Set([
        ...issueAssignees.map(assignee => '@' + assignee.login),
        ...commitAuthors
    ]);

    console.log(`Fetching release notes from comments for issue #${issueNumber}`);
    const comments = await octokit.rest.issues.listComments({
        owner: repoOwner,
        repo: repoName,
        issue_number: issueNumber
    });

    for (const comment of comments.data) {
        if (comment.body.toLowerCase().startsWith('release notes')) {
            const noteContent = comment.body.replace(/^release notes\s*/i, '').trim();
            console.log(`Found release notes in comments for issue #${issueNumber}`);
            const contributorsList = Array.from(contributors).join(', ');
            return `#${issueNumber} ${issueTitle} implemented by ${contributorsList} in ${prLinks}\n${noteContent.replace(/^\s*[\r\n]/gm, '').replace(/^/gm, '  ')}\n`;
        }
    }

    console.log(`No specific release notes found in comments for issue #${issueNumber}`);
    const contributorsList = Array.from(contributors).join(', ');
    return `x#${issueNumber} ${issueTitle} implemented by ${contributorsList} in ${prLinks}\n`;
}

async function isPrLinkedToIssue(octokit, prNumber, repoOwner, repoName) {
    const pr = await octokit.rest.pulls.get({
        owner: repoOwner,
        repo: repoName,
        pull_number: prNumber
    });
    return /#\d+/.test(pr.data.body);
}

// Function to parse chapters JSON and create a map
function parseChaptersJson(chaptersJson) {
    try {
        const chaptersArray = JSON.parse(chaptersJson);
        const titlesToLabelsMap = new Map();
        chaptersArray.forEach(chapter => {
            if (titlesToLabelsMap.has(chapter.title)) {
                titlesToLabelsMap.get(chapter.title).push(chapter.label);
            } else {
                titlesToLabelsMap.set(chapter.title, [chapter.label]);
            }
        });
        return titlesToLabelsMap;
    } catch (error) {
        throw new Error(`Error parsing chapters JSON: ${error.message}`);
    }
}

async function run() {
    const repoFullName = core.getInput('repo');
    const [repoOwner, repoName] = repoFullName.split('/');
    const tagName = core.getInput('tag_name');
    const chaptersJson = core.getInput('chapters');
    const titlesToLabelsMap = parseChaptersJson(chaptersJson);

    const githubToken = process.env.GITHUB_TOKEN;

    // Validate environment variables and arguments
    if (!githubToken || !repoOwner || !repoName || !tagName) {
        console.error("Missing required inputs or environment variables.");
        process.exit(1);
    }

    const octokit = new Octokit({ auth: githubToken });

    try {
        const latestRelease = await fetchLatestRelease(octokit, repoOwner, repoName);
        console.log('Latest Release Date:', latestRelease.data.created_at);
        console.log('Latest Release Tag Name:', latestRelease.data.tag_name);

        // Fetch closed issues since the latest release
        const closedIssuesResponse = await octokit.rest.issues.listForRepo({
            owner: repoOwner,
            repo: repoName,
            state: 'closed',
            since: new Date(latestRelease.data.created_at)
        });

        // Filter out pull requests and reverse the order of issues
        const closedIssuesOnlyIssues = closedIssuesResponse.data.filter(issue => !issue.pull_request).reverse();
        console.log(`Found ${closedIssuesOnlyIssues.length} closed issues (only Issues) since last release`);

        // Reverse the order of issues (from oldest to newest)
        const closedIssues = closedIssuesOnlyIssues.reverse();

        // Initialize variables for each chapter
        const chapterContents = new Map(Array.from(titlesToLabelsMap.keys()).map(label => [label, '']));
        let issuesWithoutReleaseNotes = '';
        let prsWithoutLinkedIssue = '';

        // Categorize issues and PRs
        for (const issue of closedIssues) {
            const releaseNotes = await getReleaseNotesFromComments(octokit, issue.number, issue.title, issue.user.login, issue.assignees, repoOwner, repoName);

            let foundReleaseNotes = false;
            titlesToLabelsMap.forEach((labels, title) => {
                if (labels.some(label => issue.labels.map(l => l.name).includes(label))) {
                    chapterContents.set(title, chapterContents.get(title) + releaseNotes + "\n\n");
                    foundReleaseNotes = true;
                }
            });

            // Check for issues without release notes
            if (!foundReleaseNotes || releaseNotes.startsWith('x#')) {
                issuesWithoutReleaseNotes += releaseNotes.replace(/^x#/, '#') + "\n\n";
            }
        }

        // Fetch pull requests since the latest release
        const prsSinceLastRelease = await octokit.rest.pulls.list({
            owner: repoOwner,
            repo: repoName,
            state: 'closed',
            sort: 'updated',
            direction: 'desc',
            since: new Date(latestRelease.data.created_at)
        });

        // Check PRs for linked issues
        for (const pr of prsSinceLastRelease.data) {
            if (!await isPrLinkedToIssue(octokit, pr.number, repoOwner, repoName)) {
                prsWithoutLinkedIssue += `#${pr.number} ${pr.title}\n`;
            }
        }

        // Generate Full Changelog URL
        const changelogUrl = `https://github.com/${repoOwner}/${repoName}/commits/${latestRelease.data.tag_name}`;
        console.log('Changelog URL:', changelogUrl);

        // Prepare Release Notes using chapterContents
        let releaseNotes = '';
        titlesToLabelsMap.forEach((_, title) => {
            const content = chapterContents.get(title);
            releaseNotes += `### ${title}\n` + (content && content.trim() !== '' ? content : "No entries detected.") + "\n\n";
        });

        releaseNotes += "### Issues without Release Notes\n" + (issuesWithoutReleaseNotes || "All issues have release notes.") + "\n\n";
        releaseNotes += "### PRs without Linked Issue\n" + (prsWithoutLinkedIssue || "All PRs are linked to issues.") + "\n\n";
        releaseNotes += "#### Full Changelog : \n" + changelogUrl;

        console.log('Release Notes:', releaseNotes);

        // Set outputs (only needed if this script is part of a GitHub Action)
        core.setOutput('releaseNotes', releaseNotes);

    } catch (error) {
        if (error.status === 404) {
            console.error('Repository not found. Please check the owner and repository name.');
        } else if (error.status === 401) {
            console.error('Authentication failed. Please check your GitHub token.');
        } else {
            console.error('Error fetching data:', error.message);
        }
        process.exit(1);
    }
}

run();
