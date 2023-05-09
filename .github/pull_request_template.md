
## Purpose

Describe the purpose of this PR and the motivation if relevant to understanding. Include links to related issues, bugs or features.

Remove the sections below which do not apply.

## Code changes:

- Provide a list of relevant code changes and the side effects they have on other code.

## Requirements changes:

- Provide a list of any changes made to requirements, e.g. changes to files requirements*.txt, constraints.txt, setup.py, pyproject.toml, pre-commit-config.yaml and a reason if not included in the Purpose section (e.g. incompatibility, updates, etc)

## Infrastructure changes:

- Provide a list of changes that impact the infrastructure around running the code -- that is, changes to Makefiles, docker files, git submodules, or .jenkins (testing infrastructure changes). If Jenkins plans are also being manually changed, indicate that as well.

## Checklist
Before submitting this PR, please make sure:

- [ ] You have followed the coding standards guidelines established at [Code Review Checklist](https://meteoswiss.atlassian.net/wiki/spaces/UA/pages/20157433/Factory).
- [ ] Docstrings and type hints are added to new and updated routines, as appropriate
- [ ] All relevant documentation has been updated or added (e.g. README)
- [ ] Unit tests are added or updated for non-operator code
- [ ] New operators are properly tested

Additionally, if the PR updates the version of the package

- [ ] The new version is properly set
- [ ] A Tag will be created after the bump

## Review
For the review process follow the guidelines at [Checklist](https://meteoswiss.atlassian.net/wiki/spaces/UA/pages/20156488/Code+Review)
