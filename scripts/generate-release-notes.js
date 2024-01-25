const { Octokit } = require("@octokit/rest");
const core = require('@actions/core');
const github = require('@actions/github');

/**
 * Fetches the latest release information for a given repository.
 * @param {Octokit} octokit - The Octokit instance.
 * @param {string} owner - The owner of the repository.
 * @param {string} repo - The name of the repository.
 * @returns {Promise<Object>} The latest release data.
 */
async function fetchLatestRelease(octokit, owner, repo) {
    console.log(`Starting to fetch the latest release for ${owner}/${repo}`);

    try {
        const release = await octokit.rest.repos.getLatestRelease({owner, repo});
        return release.data;
    } catch (error) {
        console.warn(`Fetching latest release for ${owner}/${repo}: ${error.status} - ${error.message}`);
        return null;
    }
}

/**
 * Retrieves related pull requests for a specific issue.
 * @param {Octokit} octokit - The Octokit instance.
 * @param {number} issueNumber - The issue number.
 * @param {string} repoOwner - The owner of the repository.
 * @param {string} repoName - The name of the repository.
 * @returns {Promise<Array>} An array of related pull requests.
 */
async function getRelatedPRsForIssue(octokit, issueNumber, repoOwner, repoName) {
    console.log(`Fetching related PRs for issue #${issueNumber}`);
    const relatedPRs = await octokit.rest.issues.listEventsForTimeline({owner: repoOwner, repo: repoName, issue_number: issueNumber});

    // Filter events to get only those that are linked pull requests
    const pullRequestEvents = relatedPRs.data.filter(event => event.event === 'cross-referenced' && event.source && event.source.issue.pull_request);
    if (pullRequestEvents) {
        console.log(`Found ${pullRequestEvents.length} related PRs for issue #${issueNumber}`);
    } else {
        console.log(`Found 0 related PRs for issue #${issueNumber}`);
    }
    return pullRequestEvents;
}

/**
 * Fetches contributors for an issue.
 * @param {Array} issueAssignees - List of assignees for the issue.
 * @param {Array} commitAuthors - List of authors of commits.
 * @returns {Set<string>} A set of contributors' usernames.
 */
async function getIssueContributors(issueAssignees, commitAuthors) {
    // Map the issueAssignees to the required format
    const assignees = issueAssignees.map(assignee => '@' + assignee.login);

    // Combine the assignees and commit authors
    const combined = [...assignees, ...commitAuthors];

    // Check if the combined array is empty
    if (combined && combined.length === 0) {
        return new Set(["\"Missing Assignee or Contributor\""]);
    }

    // If not empty, return the Set of combined values
    return new Set(combined);
}

/**
 * Retrieves authors of commits from pull requests related to an issue.
 * @param {Octokit} octokit - The Octokit instance.
 * @param {string} repoOwner - The owner of the repository.
 * @param {string} repoName - The name of the repository.
 * @param {Array} relatedPRs - Related pull requests.
 * @returns {Set<string>} A set of commit authors' usernames.
 */
async function getPRCommitAuthors(octokit, repoOwner, repoName, relatedPRs) {
    let commitAuthors = new Set();
    for (const event of relatedPRs) {
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

    return commitAuthors;
}

/**
 * Fetches comments for a specific issue.
 * @param {Octokit} octokit - The Octokit instance.
 * @param {number} issueNumber - The issue number.
 * @param {string} repoOwner - The owner of the repository.
 * @param {string} repoName - The name of the repository.
 * @returns {Promise<Array>} An array of issue comments.
 */
async function getIssueComments(octokit, issueNumber, repoOwner, repoName) {
    return await octokit.rest.issues.listComments({owner: repoOwner, repo: repoName, issue_number: issueNumber});
}

/**
 * Generates release notes from issue comments.
 * @param {Octokit} octokit - The Octokit instance.
 * @param {number} issueNumber - The issue number.
 * @param {string} issueTitle - The title of the issue.
 * @param {Array} issueAssignees - List of assignees for the issue.
 * @param {string} repoOwner - The owner of the repository.
 * @param {string} repoName - The name of the repository.
 * @param {Array} relatedPRs - Related pull requests.
 * @param {string} relatedPRLinksString - String of related PR links.
 * @returns {Promise<string>} The formatted release note for the issue.
 */
async function getReleaseNotesFromComments(octokit, issueNumber, issueTitle, issueAssignees, repoOwner, repoName, relatedPRs, relatedPRLinksString) {
    console.log(`Fetching release notes from comments for issue #${issueNumber}`);
    const comments = await getIssueComments(octokit, issueNumber, repoOwner, repoName);
    let commitAuthors = await getPRCommitAuthors(octokit, repoOwner, repoName, relatedPRs);
    let contributors = await getIssueContributors(issueAssignees, commitAuthors);

    let releaseNotes = [];
    for (const comment of comments.data) {
        if (comment.body.toLowerCase().startsWith('release notes')) {
            const noteContent = comment.body.replace(/^release notes:?.*(\r\n|\n|\r)?/i, '').trim();
            console.log(`Found release notes in comments for issue #${issueNumber}`);
            releaseNotes.push(noteContent.replace(/^\s*[\r\n]/gm, '').replace(/^/gm, '  '));
        }
    }

    if (releaseNotes.length === 0) {
        console.log(`No specific release notes found in comments for issue #${issueNumber}`);
        const contributorsList = Array.from(contributors).join(', ');
        if (relatedPRs.length === 0) {
            return `- x#${issueNumber} _${issueTitle}_ implemented by ${contributorsList}\n`;
        } else {
            return `- x#${issueNumber} _${issueTitle}_ implemented by ${contributorsList} in ${relatedPRLinksString}\n`;
        }
    } else {
        const contributorsList = Array.from(contributors).join(', ');
        const notes = releaseNotes.join('\n');
        if (relatedPRs.length === 0) {
            return `- #${issueNumber} _${issueTitle}_ implemented by ${contributorsList}\n${notes}\n`;
        } else {
            return `- #${issueNumber} _${issueTitle}_ implemented by ${contributorsList} in ${relatedPRLinksString}\n${notes}\n`;
        }
    }
}

/**
 * Checks if a pull request is linked to an issue.
 * @param {Octokit} octokit - The Octokit instance.
 * @param {number} prNumber - The pull request number.
 * @param {string} repoOwner - The owner of the repository.
 * @param {string} repoName - The name of the repository.
 * @returns {Promise<boolean>} True if the pull request is linked to an issue, false otherwise.
 */
async function isPrLinkedToIssue(octokit, prNumber, repoOwner, repoName) {
    // Get the pull request details
    const pr = await octokit.rest.pulls.get({
        owner: repoOwner,
        repo: repoName,
        pull_number: prNumber
    });

    // Regex pattern to find references to issues
    const regexPattern = /([Cc]los(e|es|ed)|[Ff]ix(es|ed)?|[Rr]esolv(e|es|ed))\s*#\s*([0-9]+)/g;

    // Test if the PR body contains any issue references
    return regexPattern.test(pr.data.body);
}


/**
 * Checks if a pull request is linked to any open issues.
 * @param {Octokit} octokit - The Octokit instance.
 * @param {number} prNumber - The pull request number.
 * @param {string} repoOwner - The owner of the repository.
 * @param {string} repoName - The name of the repository.
 * @returns {Promise<boolean>} True if the pull request is linked to any open issue, false otherwise.
 */
async function isPrLinkedToOpenIssue(octokit, prNumber, repoOwner, repoName) {
    // Get the pull request details
    const pr = await octokit.rest.pulls.get({
        owner: repoOwner,
        repo: repoName,
        pull_number: prNumber
    });

    // Regex pattern to find references to issues
    const regexPattern = /([Cc]los(e|es|ed)|[Ff]ix(es|ed)?|[Rr]esolv(e|es|ed))\s*#\s*([0-9]+)/g;

    // Extract all issue numbers from the PR body
    const issueMatches = pr.data.body.match(regexPattern);
    if (!issueMatches) {
        return false; // No issue references found in PR body
    }

    // Check each linked issue
    for (const match of issueMatches) {
        const issueNumber = +match.match(/#([0-9]+)/)[1];

        // Get the issue details
        const issue = await octokit.rest.issues.get({
            owner: repoOwner,
            repo: repoName,
            issue_number: issueNumber
        });

        // If any of the issues is open, return true
        if (issue.data.state === 'open') {
            return true;
        }
    }

    // If none of the issues are open, return false
    return false;
}


/**
 * Parses the JSON string of chapters into a map.
 * @param {string} chaptersJson - The JSON string of chapters.
 * @returns {Map<string, string[]>} A map where each key is a chapter title and the value is an array of corresponding labels.
 */
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
        core.setFailed(`Error parsing chapters JSON: ${error.message}`)
    }
}

/**
 * Fetches a list of closed issues since the latest release.
 * @param {Octokit} octokit - The Octokit instance.
 * @param {string} repoOwner - The owner of the repository.
 * @param {string} repoName - The name of the repository.
 * @param {Object} latestRelease - The latest release object.
 * @param {boolean} usePublishedAt - Flag to use created-at or published-at time point.
 * @param {string} skipLabel - The label to skip issues.
 * @returns {Promise<Array>} An array of closed issues since the latest release.
 */
async function fetchClosedIssues(octokit, repoOwner, repoName, latestRelease, usePublishedAt, skipLabel) {
    let since;
    if (latestRelease) {
        if (usePublishedAt) {
            since = new Date(latestRelease.published_at)
            console.log(`Fetching closed issues since ${since.toISOString()} - published-at.`);
        } else {
            since = new Date(latestRelease.created_at)
            console.log(`Fetching closed issues since ${since.toISOString()} - created-at.`);
        }
    } else {
        const firstClosedIssue = await octokit.rest.issues.listForRepo({
            owner: repoOwner,
            repo: repoName,
            state: 'closed',
            per_page: 1,
            sort: 'created',
            direction: 'asc'
        });

        if (firstClosedIssue && firstClosedIssue.data.length > 0) {
            since = new Date(firstClosedIssue.data[0].created_at);
            console.log(`Fetching closed issues since the first closed issue on ${since.toISOString()}`);
        } else {
            console.log("No closed issues found.");
            return [];
        }
    }

    const closedIssues = await octokit.rest.issues.listForRepo({
        owner: repoOwner,
        repo: repoName,
        state: 'closed',
        since: since
    });

    return closedIssues.data
        .filter(issue => !issue.pull_request) // Filter out pull requests
        .filter(issue => !issue.labels.some(label => label.name === skipLabel)) // Filter out issues with skip label
        .reverse();
}

/**
 * Fetches a list of closed pull requests since the latest release.
 * @param {Octokit} octokit - The Octokit instance.
 * @param {string} repoOwner - The owner of the repository.
 * @param {string} repoName - The name of the repository.
 * @param {Object} latestRelease - The latest release object.
 * @param {boolean} usePublishedAt - Flag to use created-at or published-at time point.
 * @param {string} skipLabel - The label to skip issues.
 * @param {string} prState - The state of the pull request.
 * @returns {Promise<Array>} An array of closed pull requests since the latest release.
 */
async function fetchPullRequests(octokit, repoOwner, repoName, latestRelease, usePublishedAt, skipLabel,  prState = 'merged') {
    console.log(`Fetching ${prState} pull requests for ${repoOwner}/${repoName}`);

    let pullRequests;
    let since;
    let response;

    if (latestRelease) {
        if (usePublishedAt) {
            console.log(`Since latest release date: ${latestRelease.published_at} - published-at.`);
            since = new Date(latestRelease.published_at);
        } else {
            console.log(`Since latest release date: ${latestRelease.created_at} - created-at.`);
            since = new Date(latestRelease.created_at);
        }

        response = await octokit.rest.pulls.list({
            owner: repoOwner,
            repo: repoName,
            state: 'all',
            sort: 'updated',
            direction: 'desc',
            since: since
        });
    } else {
        console.log('No latest release found. Fetching all pull requests of repository.');
        response = await octokit.rest.pulls.list({
            owner: repoOwner,
            repo: repoName,
            state: 'all',
            sort: 'updated',
            direction: 'desc'
        });
    }

    pullRequests = response.data;

    // Filter based on prState
    if (prState === 'merged') {
        pullRequests = pullRequests.filter(pr => pr.merged_at);
    } else if (prState === 'closed') {
        pullRequests = pullRequests.filter(pr => !pr.merged_at && pr.state === 'closed');
    }

    // Filter out pull requests with the specified skipLabel
    console.log(`Filtering out pull requests with label: ${skipLabel}`)
    pullRequests = pullRequests.filter(pr => !pr.labels.some(label => label.name === skipLabel));

    return pullRequests;
}

async function run() {
    console.log('Starting GitHub Action');
    const githubToken = process.env.GITHUB_TOKEN;
    const tagName = core.getInput('tag-name');
    const githubRepository = process.env.GITHUB_REPOSITORY;

    // Validate GitHub token
    if (!githubToken) {
        core.setFailed("GitHub token is missing.");
        return;
    }

    // Validate GitHub repository environment variable
    if (!githubRepository) {
        core.setFailed("GITHUB_REPOSITORY environment variable is missing.");
        return;
    }

    // Extract owner and repo from GITHUB_REPOSITORY
    const [owner, repo] = githubRepository.split('/');
    if (!owner || !repo) {
        core.setFailed("GITHUB_REPOSITORY environment variable is not in the correct format 'owner/repo'.");
        return;
    }

    // Validate tag name
    if (!tagName) {
        core.setFailed("Tag name is missing.");
        return;
    }

    const repoOwner = github.context.repo.owner;
    const repoName = github.context.repo.repo;
    const chaptersJson = core.getInput('chapters') || "[]";
    const warnings = core.getInput('warnings') ? core.getInput('warnings').toLowerCase() === 'true' : true;
    const skipLabel = core.getInput('skip-release-notes-label') || 'skip-release-notes';
    const usePublishedAt = core.getInput('published-at') ? core.getInput('published-at').toLowerCase() === 'true' : false;
    const printEmptyChapters = core.getInput('print-empty-chapters') ? core.getInput('print-empty-chapters').toLowerCase() === 'true' : true;

    const octokit = new Octokit({ auth: githubToken });

    try {
        const latestRelease = await fetchLatestRelease(octokit, repoOwner, repoName);

        // Fetch closed issues since the latest release
        const closedIssuesOnlyIssues = await fetchClosedIssues(octokit, repoOwner, repoName, latestRelease, usePublishedAt, skipLabel);
        if (closedIssuesOnlyIssues) {
            console.log(`Found ${closedIssuesOnlyIssues.length} closed issues (only Issues) since last release`);
        } else {
            console.log(`Found 0 closed issues (only Issues) since last release`);
        }

        // Initialize variables for each chapter
        const titlesToLabelsMap = parseChaptersJson(chaptersJson);
        const chapterContents = new Map(Array.from(titlesToLabelsMap.keys()).map(label => [label, '']));
        let closedIssuesWithoutReleaseNotes = '', closedIssuesWithoutUserLabels = '', closedIssuesWithoutPR = '', mergedPRsWithoutLinkedIssue = '';
        let mergedPRsLinkedToOpenIssue = '', closedPRsLinkedToIssue = '';

        // Categorize issues and PRs
        for (const issue of closedIssuesOnlyIssues) {
            let relatedPRs = await getRelatedPRsForIssue(octokit, issue.number, repoOwner, repoName);
            console.log(`Related PRs for issue #${issue.number}: ${relatedPRs.map(event => event.id).join(', ')}`);
            let prLinks = relatedPRs
                .map(event => `[#${event.source.issue.number}](${event.source.issue.html_url})`)
                .join(', ');
            console.log(`Related PRs for issue #${issue.number}: ${prLinks}`);

            const releaseNotesRaw = await getReleaseNotesFromComments(octokit, issue.number, issue.title, issue.assignees, repoOwner, repoName, relatedPRs, prLinks);
            const releaseNotes = releaseNotesRaw.replace(/^- x#/, '- #');

            // Check for issues without release notes
            if (warnings && releaseNotesRaw.startsWith('- x#')) {
                closedIssuesWithoutReleaseNotes += releaseNotes;
            }

            let foundUserLabels = false;
            titlesToLabelsMap.forEach((labels, title) => {
                if (labels.some(label => issue.labels.map(l => l.name).includes(label))) {
                    chapterContents.set(title, chapterContents.get(title) + releaseNotes);
                    foundUserLabels = true;
                }
            });

            // Check for issues without user defined labels
            if (!foundUserLabels && warnings) {
                closedIssuesWithoutUserLabels += releaseNotes;
            }

            // Check for issues without PR
            if (!relatedPRs.length && warnings) {
                closedIssuesWithoutPR += releaseNotes;
            }
        }

        // Check PRs for linked issues
        if (warnings) {
            // Fetch merged pull requests since the latest release
            const mergedPRsSinceLastRelease = await fetchPullRequests(octokit, repoOwner, repoName, latestRelease, usePublishedAt, skipLabel);
            if (mergedPRsSinceLastRelease) {
                console.log(`Found ${mergedPRsSinceLastRelease.length} merged PRs since last release`);
                const sortedMergedPRs = mergedPRsSinceLastRelease.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));

                for (const pr of sortedMergedPRs) {
                    if (!await isPrLinkedToIssue(octokit, pr.number, repoOwner, repoName)) {
                        mergedPRsWithoutLinkedIssue += `#${pr.number} _${pr.title}_\n`;
                    } else {
                        if (await isPrLinkedToOpenIssue(octokit, pr.number, repoOwner, repoName)) {
                            mergedPRsLinkedToOpenIssue += `#${pr.number} _${pr.title}_\n`;
                        }
                    }
                }
            } else {
                console.log(`Found 0 merged PRs since last release`);
            }

            // Fetch closed pull requests since the latest release
            const closedPRsSinceLastRelease = await fetchPullRequests(octokit, repoOwner, repoName, latestRelease, usePublishedAt, skipLabel, 'closed');
            if (closedPRsSinceLastRelease) {
                console.log(`Found ${closedPRsSinceLastRelease.length} closed PRs since last release`);
                const sortedClosedPRs = closedPRsSinceLastRelease.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));

                for (const pr of sortedClosedPRs) {
                    if (!await isPrLinkedToIssue(octokit, pr.number, repoOwner, repoName)) {
                        closedPRsLinkedToIssue += `#${pr.number} _${pr.title}_\n`;
                    }
                }
            } else {
                console.log(`Found 0 closed PRs since last release`);
            }
        }

        let changelogUrl;
        if (latestRelease) {
            // If there is a latest release, create a URL pointing to commits since the latest release
            changelogUrl = `https://github.com/${repoOwner}/${repoName}/compare/${latestRelease.tag_name}...${tagName}`;
            console.log('Changelog URL (since latest release):', changelogUrl);
        } else {
            // If there is no latest release, create a URL pointing to all commits
            changelogUrl = `https://github.com/${repoOwner}/${repoName}/commits/${tagName}`;
            console.log('Changelog URL (all commits):', changelogUrl);
        }

        // Prepare Release Notes using chapterContents
        let releaseNotes = '';
        titlesToLabelsMap.forEach((_, title) => {
            const content = chapterContents.get(title);
            if (printEmptyChapters || (content && content.trim() !== '')) {
                releaseNotes += `### ${title}\n` + (content && content.trim() !== '' ? content : "No entries detected.") + "\n\n";
            }
        });

        if (warnings) {
            if (printEmptyChapters) {
                releaseNotes += "### Closed Issues without Pull Request ⚠️\n" + (closedIssuesWithoutPR || "All closed issues linked to a Pull Request.") + "\n\n";
                releaseNotes += "### Closed Issues without User Defined Labels ⚠️\n" + (closedIssuesWithoutUserLabels || "All closed issues contain at least one of user defined labels.") + "\n\n";
                releaseNotes += "### Closed Issues without Release Notes ⚠️\n" + (closedIssuesWithoutReleaseNotes || "All closed issues have release notes.") + "\n\n";
                releaseNotes += "### Merged PRs without Linked Issue ⚠️\n" + (mergedPRsWithoutLinkedIssue || "All merged PRs are linked to issues.") + "\n\n";
                releaseNotes += "### Merged PRs Linked to Open Issue ⚠️\n" + (mergedPRsLinkedToOpenIssue || "All merged PRs are linked to Closed issues.") + "\n\n";
                releaseNotes += "### Closed PRs without Linked Issue ⚠️\n" + (closedPRsLinkedToIssue || "All closed PRs are linked to issues.") + "\n\n";
            } else {
                releaseNotes += closedIssuesWithoutPR ? "### Closed Issues without Pull Request ⚠️\n" + closedIssuesWithoutPR + "\n\n" : "";
                releaseNotes += closedIssuesWithoutUserLabels ? "### Closed Issues without User Defined Labels ⚠️\n" + closedIssuesWithoutUserLabels + "\n\n" : "";
                releaseNotes += closedIssuesWithoutReleaseNotes ? "### Closed Issues without Release Notes ⚠️\n" + closedIssuesWithoutReleaseNotes + "\n\n" : "";
                releaseNotes += mergedPRsWithoutLinkedIssue ? "### Merged PRs without Linked Issue ⚠️\n" + mergedPRsWithoutLinkedIssue + "\n\n" : "";
                releaseNotes += mergedPRsLinkedToOpenIssue ? "### Merged PRs Linked to Open Issue ⚠️\n" + mergedPRsLinkedToOpenIssue + "\n\n" : "";
                releaseNotes += closedPRsLinkedToIssue ? "### Closed PRs without Linked Issue ⚠️\n" + closedPRsLinkedToIssue + "\n\n" : "";
            }
        }
        releaseNotes += "#### Full Changelog\n" + changelogUrl;

        console.log('Release Notes:', releaseNotes);

        // Set outputs (only needed if this script is part of a GitHub Action)
        core.setOutput('releaseNotes', releaseNotes);
        console.log('GitHub Action completed successfully');
    } catch (error) {
        if (error.status === 404) {
            console.error('Repository not found. Please check the owner and repository name.');
            core.setFailed(error.message)
        } else if (error.status === 401) {
            console.error('Authentication failed. Please check your GitHub token.');
            core.setFailed(error.message)
        } else {
            console.error(`Error fetching data: ${error.status} - ${error.message}`);
            core.setFailed(`Error fetching data: ${error.status} - ${error.message}`);
        }
    }
}

module.exports.run = run;

if (require.main === module) {
    run();
}
