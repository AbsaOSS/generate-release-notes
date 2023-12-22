const { Octokit } = require("@octokit/core");
const core = require('@actions/core');

// Fetch the latest release
async function fetchLatestRelease(octokit, owner, repo) {
    try {
        const response = await octokit.rest.repos.getLatestRelease({
            owner,
            repo
        });
        return response;
    } catch (error) {
        throw new Error(`Error fetching latest release: ${error.message}`);
    }
}

async function run() {
    const repoOwner = core.getInput('repo_owner');
    const repoName = core.getInput('repo_name');
    const tagName = core.getInput('tag_name');
    const chapters = core.getInput('chapters');

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
