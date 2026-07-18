"""Static library of parameterized dork templates.

Each template's `pattern` has a single `{target}` placeholder, substituted with
the user-supplied domain/username/email before being sent to a search engine.
`target_types` restricts which templates apply to which target type, so the
frontend only offers relevant dorks (e.g. `site:linkedin.com/in/{target}` only
makes sense for a username).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class DorkTemplate:
    key: str
    pattern: str
    target_types: tuple[str, ...]
    description: str


DORK_TEMPLATES: list[DorkTemplate] = [
    DorkTemplate(
        key="site_search",
        pattern="site:{target}",
        target_types=("domain",),
        description="All indexed pages on the domain",
    ),
    DorkTemplate(
        key="subdomains",
        pattern="site:*.{target} -site:www.{target}",
        target_types=("domain",),
        description="Indexed subdomains",
    ),
    DorkTemplate(
        key="login_pages",
        pattern="site:{target} inurl:login OR inurl:admin OR inurl:signin",
        target_types=("domain",),
        description="Exposed login/admin pages",
    ),
    DorkTemplate(
        key="filetype_pdf",
        pattern="site:{target} filetype:pdf",
        target_types=("domain",),
        description="PDF documents",
    ),
    DorkTemplate(
        key="filetype_xlsx",
        pattern="site:{target} filetype:xlsx OR filetype:csv",
        target_types=("domain",),
        description="Spreadsheets",
    ),
    DorkTemplate(
        key="filetype_config",
        pattern="site:{target} filetype:env OR filetype:log OR filetype:conf",
        target_types=("domain",),
        description="Exposed config/log files",
    ),
    DorkTemplate(
        key="exposed_credentials",
        pattern="site:{target} intext:password OR intext:api_key OR intext:secret",
        target_types=("domain",),
        description="Pages mentioning credentials/secrets",
    ),
    DorkTemplate(
        key="pastebin_mentions",
        pattern="site:pastebin.com \"{target}\"",
        target_types=("domain", "username", "email"),
        description="Pastebin mentions",
    ),
    DorkTemplate(
        key="github_mentions",
        pattern="site:github.com \"{target}\"",
        target_types=("domain", "username", "email"),
        description="GitHub mentions (code, issues, gists)",
    ),
    DorkTemplate(
        key="linkedin_profile",
        pattern="site:linkedin.com/in \"{target}\"",
        target_types=("username",),
        description="LinkedIn profile mentions",
    ),
    DorkTemplate(
        key="social_mentions",
        pattern="\"{target}\" site:twitter.com OR site:reddit.com OR site:facebook.com",
        target_types=("username", "email"),
        description="Social media mentions",
    ),
    DorkTemplate(
        key="generic_mentions",
        pattern="\"{target}\"",
        target_types=("domain", "username", "email"),
        description="Any indexed mention",
    ),
]


def get_templates_for_target_type(target_type: str) -> list[DorkTemplate]:
    return [t for t in DORK_TEMPLATES if target_type in t.target_types]


def get_template_by_key(key: str) -> DorkTemplate | None:
    return next((t for t in DORK_TEMPLATES if t.key == key), None)
