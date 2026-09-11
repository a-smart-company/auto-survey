"""Data models used in the application."""

from pydantic import BaseModel, Field


class Paper(BaseModel):
    """A research paper.

    Attributes:
        title:
            The title of the paper. Must be non-empty.
        authors:
            The authors of the paper. Must be a non-empty list.
        year:
            The year the paper was published. Must be between 1900 and the current year.
            Can be -1 if the year is unknown.
        venue:
            The venue where the paper was published, e.g., conference or journal name.
            Can be an empty string if the venue is unknown.
        url:
            The URL of the paper, preferably a DOI link. Must be a valid URL if
            provided. Can be an empty string if the URL is unknown.
        summary:
            The summary of the paper. Can be an empty string if it is unavailable.
    """

    title: str
    authors: list["Author"]
    year: int
    venue: str
    url: str
    summary: str

    def get_citation(self, in_parens: bool) -> str:
        """Get the citation for the paper in APA style.

        Args:
            in_parens:
                Whether the citation is in parentheses or not. If True, the citation
                should be of the form "(Author, Year)". If False, the citation should be
                of the form "Author (Year)".

        Returns:
            The citation.
        """
        if not self.authors:
            author_str = "Unknown Author"
        elif len(self.authors) == 1:
            author = self.authors[0]
            author_str = f"{author.last_name}"
        elif len(self.authors) == 2:
            author1 = self.authors[0]
            author2 = self.authors[1]
            author_str = f"{author1.last_name} and {author2.last_name}"
        else:
            author1 = self.authors[0]
            author_str = f"{author1.last_name} et al."

        year_str = str(self.year) if self.year != -1 else "n.d."
        if in_parens:
            return f"({author_str}, {year_str})"
        else:
            return f"{author_str} ({year_str})"

    def references_entry(self) -> str:
        """Format the paper as an APA style reference entry.

        Returns:
            The reference entry.
        """
        entry = ""

        authors_str = " and ".join(str(author) for author in self.authors)
        entry += authors_str if authors_str else "Unknown Author"

        year_str = str(self.year) if self.year != -1 else "n.d."
        entry += f" ({year_str})."

        if self.title:
            entry += f" {self.title.title()}."

        if self.venue:
            entry += f" _{self.venue.title()}_."

        return entry.strip()

    def __eq__(self, other: object) -> bool:
        """Check if two Paper instances are equal based on their attributes.

        Args:
            other:
                The other Paper instance to compare with.

        Returns:
            True if the instances are equal, False otherwise.
        """
        if not isinstance(other, Paper):
            return False
        return (
            self.title == other.title
            and self.authors == other.authors
            and self.year == other.year
            and self.venue == other.venue
            and self.url == other.url
            and self.summary == other.summary
        )

    def __hash__(self) -> int:
        """Hash of the paper.

        Returns:
            The hash.
        """
        return hash(
            self.title
            + ",".join(author.first_name + author.last_name for author in self.authors)
            + str(self.year)
            + self.venue
            + self.url
            + self.summary
        )

    def __str__(self) -> str:
        """String representation of the paper.

        Returns:
            The string representation.
        """
        authors_str = ", ".join(
            f"{author.first_name} {author.last_name}".strip() for author in self.authors
        )
        year_str = str(self.year) if self.year != -1 else "Unknown Year"
        venue_str = self.venue if self.venue else "Unknown Venue"
        return f"""
            ## {self.title}

            **Authors:** {authors_str}
            **Year:** {year_str}
            **Venue:** {venue_str}
            **URL:** {self.url if self.url else "Unknown URL"}
            **Summary:** {self.summary if self.summary else "No summary available."}
        """.strip()


class Author(BaseModel):
    """An author of a research paper.

    Attributes:
        first_name:
            The author's first name. Can be an empty string if the first name is
            unknown.
        last_name:
            The author's last name. Can be an empty string if the last name is unknown.
    """

    first_name: str
    last_name: str

    def __str__(self) -> str:
        """String representation of the author.

        Returns:
            The string representation.
        """
        string = ""
        if self.last_name:
            string += self.last_name
        if self.first_name:
            if string:
                string += ", "
            string += self.first_name
        return string if string else "Unknown Author"

    def __eq__(self, other: object) -> bool:
        """Check if two Author instances are equal based on their attributes.

        Args:
            other:
                The other Author instance to compare with.

        Returns:
            True if the instances are equal, False otherwise.
        """
        if not isinstance(other, Author):
            return False
        return self.first_name == other.first_name and self.last_name == other.last_name


class Queries(BaseModel):
    """A list of queries to search for papers.

    Attributes:
        queries:
            A list of queries. Must be non-empty.
    """

    queries: list[str]

    def __post_init__(self) -> None:
        """Post-initialisation to make sure that the queries are correctly formatted."""
        # Remove empty queries and strip whitespace
        self.queries = [query.strip() for query in self.queries if query.strip()]

        # Split queries with "OR" statements into separate queries
        indices_with_or_statement = [
            i for i, query in enumerate(self.queries) if " OR " in query.lower()
        ]
        for i in indices_with_or_statement:
            or_query = self.queries.pop(i)
            subqueries = [subquery.strip() for subquery in or_query.split(" OR ")]
            self.queries.extend(subqueries)

        # Remove "AND" statements from queries
        self.queries = [query.replace(" AND ", " ") for query in self.queries]

        # Remove duplicate queries
        self.queries = list(set(self.queries))


class IsRelevant(BaseModel):
    """A response indicating whether a paper is relevant to a given topic.

    Attributes:
        is_relevant:
            True if the paper is relevant, False otherwise.
    """

    is_relevant: bool


class Summary(BaseModel):
    """A summary of a research paper.

    Attributes:
        summary:
            The summary text. Must be non-empty.
    """

    summary: str


class LiteLLMConfig(BaseModel):
    """Configuration for LiteLLM.

    Attributes:
        model:
            The model ID to use.
        api_base (optional):
            The API base URL for the model, if a custom inference server is used. Can be
            None if not needed. Defaults to None.
        api_key (optional):
            The environment variable name that contains the API key for the model. Can
            be None if not needed. Defaults to None.
        temperature (optional):
            The sampling temperature for the model. Defaults to 1.0.
        num_retries (optional):
            Number of retry attempts for transient connection errors. Defaults to 3.
        timeout_seconds (optional):
            Timeout in seconds for each API request. Defaults to 30.
    """

    model: str
    api_base: str | None = None
    api_key: str | None = None
    temperature: float = Field(default=1.0, ge=0.0, le=2.0)
    num_retries: int = Field(default=3, ge=0)
    timeout_seconds: int = Field(default=30, ge=1)
