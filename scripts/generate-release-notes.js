const { Octokit } = require("@octokit/core");

// Fetch the latest release
async function fetchLatestRelease(octokit, owner, repo) {
    return await octokit.rest.repos.getLatestRelease({
        owner,
        repo
    });
}

async function run() {
    const githubToken = process.env.GITHUB_TOKEN;
    const repoOwner = process.env.REPOSITORY_OWNER;
    const repoName = process.REPOSITORY_NAME;

    // Validate environment variables and arguments
    if (!githubToken || !repoOwner || !repoName) {
        console.error("Missing required environment variables or arguments.");
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
