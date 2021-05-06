workflow "on check suite creation, run flake8 and post results" {
    on = "pull_request"
    resolves = "run flake8"
}

action "run flake8" {
    uses = "mkvithal/2019_code_academy@master"
    secrets = ["GITHUB_TOKEN"]
}
