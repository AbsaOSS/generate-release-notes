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
        console.error(`Error fetching latest release for ${owner}/${repo}: ${error.status} - ${error.message}`);
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
    console.log(`Found ${pullRequestEvents.length} related PRs for issue #${issueNumber}`);
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
    if (combined.length === 0) {
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

    for (const comment of comments.data) {
        if (comment.body.toLowerCase().startsWith('release notes')) {
            const noteContent = comment.body.replace(/^release notes\s*/i, '').trim();
            console.log(`Found release notes in comments for issue #${issueNumber}`);
            const contributorsList = Array.from(contributors).join(', ');

            console.log(`Related PRs (string) for issue #${issueNumber}: ${relatedPRLinksString}`);
            console.log(`Related PRs (Set) for issue #${issueNumber}: ${relatedPRs}`);
            if (relatedPRs.length === 0) {
                return `- #${issueNumber} _${issueTitle}_ implemented by ${contributorsList}\n${noteContent.replace(/^\s*[\r\n]/gm, '').replace(/^/gm, '  ')}\n`;
            } else {
                return `- #${issueNumber} _${issueTitle}_ implemented by ${contributorsList} in ${relatedPRLinksString}\n${noteContent.replace(/^\s*[\r\n]/gm, '').replace(/^/gm, '  ')}\n`;
            }
        }
    }

    console.log(`No specific release notes found in comments for issue #${issueNumber}`);
    const contributorsList = Array.from(contributors).join(', ');
    if (relatedPRs.length === 0) {
        return `- x#${issueNumber} _${issueTitle}_ implemented by ${contributorsList}\n`;
    } else {
        return `- x#${issueNumber} _${issueTitle}_ implemented by ${contributorsList} in ${relatedPRLinksString}\n`;
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
    const pr = await octokit.rest.pulls.get({
        owner: repoOwner,
        repo: repoName,
        pull_number: prNumber
    });
    return /#\d+/.test(pr.data.body);
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
        throw new Error(`Error parsing chapters JSON: ${error.message}`);
    }
}

/**
 * Fetches a list of closed issues since the latest release.
 * @param {Octokit} octokit - The Octokit instance.
 * @param {string} repoOwner - The owner of the repository.
 * @param {string} repoName - The name of the repository.
 * @param {Object} latestRelease - The latest release object.
 * @returns {Promise<Array>} An array of closed issues since the latest release.
 */
async function fetchClosedIssues(octokit, repoOwner, repoName, latestRelease) {
    let closedIssues;
    if (latestRelease && latestRelease.created_at) {
        console.log(`Fetching closed issues since ${latestRelease.created_at}`);
        closedIssues = await octokit.rest.issues.listForRepo({
            owner: repoOwner,
            repo: repoName,
            state: 'closed',
            since: new Date(latestRelease.created_at)
        });
    } else {
        console.log("No latest release found. Fetching all closed issues from repository creation.");

        const repoDetails = await octokit.rest.repos.get({
            owner: repoOwner,
            repo: repoName
        });

        console.log(`Fetching closed issues since repository created ${repoDetails.data.created_at}`);
        closedIssues = await octokit.rest.issues.listForRepo({
            owner: repoOwner,
            repo: repoName,
            state: 'closed',
            since: new Date(repoDetails.data.created_at)
        });
    }

    return closedIssues.data.filter(issue => !issue.pull_request).reverse();
}

/**
 * Fetches a list of closed pull requests since the latest release.
 * @param {Octokit} octokit - The Octokit instance.
 * @param {string} repoOwner - The owner of the repository.
 * @param {string} repoName - The name of the repository.
 * @param {Object} latestRelease - The latest release object.
 * @returns {Promise<Array>} An array of closed pull requests since the latest release.
 */
async function fetchPullRequests(octokit, repoOwner, repoName, latestRelease) {
    console.log(`Fetching closed pull requests for ${repoOwner}/${repoName}`);

    if (latestRelease) {
        console.log(`Since latest release date: ${latestRelease.created_at}`);
        return await octokit.rest.pulls.list({
            owner: repoOwner,
            repo: repoName,
            state: 'closed',
            sort: 'updated',
            direction: 'desc',
            since: new Date(latestRelease.created_at)
        });

    } else {
        console.log("No latest release found. Fetching all closed pull requests.");
        return await octokit.rest.pulls.list({
            owner: repoOwner,
            repo: repoName,
            state: 'closed',
            sort: 'updated',
            direction: 'desc'
        });
    }
}

async function run() {
    const repoOwner = github.context.repo.owner;
    const repoName = github.context.repo.repo;
    const tagName = core.getInput('tag-name');
    const chaptersJson = core.getInput('chapters');
    const warnings = core.getInput('warnings').toLowerCase() === 'true';
    const githubToken = process.env.GITHUB_TOKEN;

    // Validate environment variables and arguments
    if (!githubToken || !repoOwner || !repoName) {
        console.error("Missing required inputs or environment variables.");
        process.exit(1);
    }

    const octokit = new Octokit({ auth: githubToken });

    try {
        const latestRelease = await fetchLatestRelease(octokit, repoOwner, repoName);

        // Fetch closed issues since the latest release
        const closedIssuesOnlyIssues = await fetchClosedIssues(octokit, repoOwner, repoName, latestRelease);
        console.log(`Found ${closedIssuesOnlyIssues.length} closed issues (only Issues) since last release`);

        // Initialize variables for each chapter
        const titlesToLabelsMap = parseChaptersJson(chaptersJson);
        const chapterContents = new Map(Array.from(titlesToLabelsMap.keys()).map(label => [label, '']));
        let issuesWithoutReleaseNotes = '', issuesWithoutUserLabels = '', issuesWithoutPR = '', prsWithoutLinkedIssue = '';

        // Categorize issues and PRs
        for (const issue of closedIssuesOnlyIssues) {
            let relatedPRs = await getRelatedPRsForIssue(octokit, issue.number, repoOwner, repoName);
            let prLinks = relatedPRs
                .map(event => `[#${event.source.issue.number}](${event.source.issue.html_url})`)
                .join(', ');
            console.log(`Related PRs for issue #${issue.number}: ${prLinks}`);

            const releaseNotesRaw = await getReleaseNotesFromComments(octokit, issue.number, issue.title, issue.assignees, repoOwner, repoName, relatedPRs, prLinks);
            const releaseNotes = releaseNotesRaw.replace(/^- x#/, '- #');

            // Check for issues without release notes
            if (warnings && releaseNotesRaw.startsWith('- x#')) {
                issuesWithoutReleaseNotes += releaseNotes;
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
                issuesWithoutUserLabels += releaseNotes;
            }

            // Check for issues without PR
            if (!relatedPRs.length && warnings) {
                issuesWithoutPR += releaseNotes;
            }
        }

        // Check PRs for linked issues
        if (warnings) {
            // Fetch pull requests since the latest release
            const prsSinceLastRelease = await fetchPullRequests(octokit, repoOwner, repoName, latestRelease);
            console.log(`Found ${prsSinceLastRelease.data.length} closed PRs since last release`);

            for (const pr of prsSinceLastRelease.data) {
                if (!await isPrLinkedToIssue(octokit, pr.number, repoOwner, repoName)) {
                    prsWithoutLinkedIssue += `#${pr.number} _${pr.title}_\n`;
                }
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
            releaseNotes += `### ${title}\n` + (content && content.trim() !== '' ? content : "No entries detected.") + "\n\n";
        });

        if (warnings) {
            releaseNotes += "### Issues without Pull Request ⚠️\n" + (issuesWithoutPR || "All issues linked to a Pull Request.") + "\n\n";
            releaseNotes += "### Issues without User Defined Labels ⚠️\n" + (issuesWithoutUserLabels || "All issues contain at least one of user defined labels.") + "\n\n";
            releaseNotes += "### Issues without Release Notes ⚠️\n" + (issuesWithoutReleaseNotes || "All issues have release notes.") + "\n\n";
            releaseNotes += "### PRs without Linked Issue ⚠️\n" + (prsWithoutLinkedIssue || "All PRs are linked to issues.") + "\n\n";
        }
        releaseNotes += "#### Full Changelog\n" + changelogUrl;

        console.log('Release Notes:', releaseNotes);

        // Set outputs (only needed if this script is part of a GitHub Action)
        core.setOutput('releaseNotes', releaseNotes);
        console.log('GitHub Action completed successfully');
    } catch (error) {
        if (error.status === 404) {
            console.error('Repository not found. Please check the owner and repository name.');
        } else if (error.status === 401) {
            console.error('Authentication failed. Please check your GitHub token.');
        } else {
            console.error(`Error fetching data: ${error.status} - ${error.message}`);
        }
        process.exit(1);
    }
}

run();
