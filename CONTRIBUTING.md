<img width="1400" height="784" alt="header" src="https://github.com/user-attachments/assets/23f8ae06-1d81-4616-bfa5-e4ac4b2cd384" />

# Contributing to Shownamer (*Image unrelated)

Thank you for considering contributing to **Shownamer**. Bug fixes, useful enhancements, documentation improvements, and suggestions are welcome. The goal is to keep Shownamer simple, useful, and consistent with its philosophy.

## Getting Started

1. Fork the repository.
2. Create a new branch using the branch naming convention described below.
3. Make your changes.
4. Properly test your changes.
5. Commit your changes using Conventional Commits.
6. Push your branch and open a Pull Request.

> [!TIP]
> If you are unsure whether an idea fits the project, open an issue first and discuss it before implementing it.

<br />

### `A.1` Branch Names

Branch names should follow the same conventional style used for commits.

Use a valid Conventional Commit type as the branch prefix:

```text
feat/new-feature
fix/issue-description
docs/update-readme
test/add-cli-tests
refactor/simplify-parser
chore/update-dependencies
```

Keep branch names brief and descriptive.

### `A.2` Commit Messages

Shownamer uses Conventional Commits. Commits that do not follow this format will not be accepted.

#### Format

```
<type>(optional scope): <brief summary>
```

The summary should be brief, clear, meaningful, and written in lowercase.
An optional commit body can be added for extra context. Use a bullet list of short points describing the change:
```
<type>(optional scope): <brief summary>

- change one with description or info
- change two or info or fun point

CLOSES #X
```

#### Common Types

- `feat`: a new feature
- `fix`: a bug fix
- `docs`: documentation changes
- `refactor`: code changes that do not add features or fix bugs
- `test`: adding or modifying tests
- `chore`: maintenance, dependencies, and other project tasks
- `init`: adding new files

#### Examples

```
feat: add optional year field
fix: handle titles with zero correctly
docs: update installation instructions
test: add format validation tests
refactor: simplify filename parser
init(docs): add contributing guide
```
```
fix: handle titles with zero correctly

- zero was being stripped before parsing
- added test case for zero-prefixed titles

CLOSES #14
```

#### Avoid

```
wip: working on something
update: fixed stuff
feat: new feature added
```

Commit messages should describe the actual change rather than using vague descriptions.

<br />

## `B.1` Issues and Enhancement Requests

Issues and enhancement requests do not need to follow a formal writing style. Write them naturally and explain the problem or idea in your own words.

Keep the title brief, simple, and descriptive. Someone should be able to understand what the issue is about just by reading the title.

For example:

- format specifier rejects colon
- support anime filenames with brackets
- title embedding fails for mp4 files
- add support for another episode format

Please do not overthink the wording. You are a human communicating an idea to other humans, and natural language is enough.

The use of AI to write or format simple issue reports is discouraged. There is no need to use AI for something as simple as explaining a bug or suggesting an idea.

<br />

## `C.1` Code and Project Guidelines

- Keep the implementation simple.
- Follow the existing project structure and conventions.
- Use brief, lowercase comments when comments are necessary.
- Avoid unnecessary abstractions and complexity.
- Keep changes focused on the issue or feature being addressed.
- Do not modify unrelated parts of the project.
- Follow the Unix philosophy in spirit: prefer simple tools and solutions that do one thing well.
- Prefer the least complex implementation that solves the problem properly.
- Complex, niche, or unnecessary enhancements may not be accepted.
- A feature being technically possible does not necessarily mean it belongs in Shownamer.

> [!IMPORTANT]
> Shownamer aims to remain lightweight and straightforward rather than becoming a collection of every possible media-management feature.
> This section is paramount, kindly read section `C.1` before attempting anything.

## `C.2` Testing

Properly test your changes before pushing them.

Bug fixes and new features should be tested against the relevant existing functionality. If a change introduces new behavior, add or update tests where appropriate.

There are test scripts added to the repository, kindly use them. Proper instructions are provided within the file (see: `tests/` folder).

Before opening a Pull Request:

- Make sure the relevant tests pass.
- Test the actual CLI behavior when applicable.
- Test edge cases introduced by your changes.
- Make sure existing functionality has not been broken.
- Do not rely solely on a successful build or a single happy-path test.

## `C.3` Project Assets and Documentation

Do not modify or replace existing project assets unless the change specifically concerns that asset.

This includes:

- Header images
- Screenshots
- Other images in docs/assets
- Badges
- Pre-set documentation
- Existing project information
- README presentation and formatting

Do not change these simply as part of an unrelated feature or bug fix.

If documentation needs to be changed because of your contribution, update only the relevant documentation (text only).

## `C.4` Pull Requests

When opening a Pull Request:

- Explain what the change does.
- Explain why the change is needed.

Reference related issues when applicable:

```
Fixes #9
```

- Keep the Pull Request focused.
- Include appropriate tests.
- Avoid unrelated changes.
- Follow the branch and commit conventions described above.

Pull Requests may be adjusted during review to keep the implementation simple and consistent with the project's philosophy.

<br />

## `D.1` Suggestions and Issues

Suggestions are welcome, but not every suggestion will necessarily become part of Shownamer.

Before proposing a large or complex enhancement, consider whether the problem can be solved with a simpler approach. Features should provide genuine value without adding unnecessary complexity or moving the project away from its core purpose.

If you are unsure whether an idea belongs in the project, open an issue and discuss it first.

<br />
<br />

> [!NOTE]
> Keep it simple. Explain the problem, suggest a solution if you have one, and let me figure out the rest.<br />
> And make sure to read section [C](https://github.com/theamallalgi/shownamer/blob/main/CONTRIBUTING.md#c1-code-and-project-guidelines) before any changes.
