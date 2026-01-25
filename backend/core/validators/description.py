"""
ⒸAngelaMos | 2026
Description validation and audit logic.
Sanity checks AI-generated descriptions for hallucinations and gibberish.
"""

from dataclasses import dataclass
from typing import ClassVar

import config


@dataclass
class AuditResult:
    """
    Result of a description audit.
    """
    score: int
    issues: list[str]
    passed: bool


class DescriptionAuditor:
    """
    Audits AI-generated descriptions for quality and sanity.
    Returns confidence score 0-100 and list of issues found.
    """

    BAD_TOKEN_PATTERNS: ClassVar[list[str]] = [
        "<|",
        "|>",
    ]

    @classmethod
    def audit(cls, description: str) -> AuditResult:
        """
        Audit a description and return score + issues.
        Score is 0-100, higher is better.
        """
        score = 100
        issues: list[str] = []

        if not description or not description.strip():
            return AuditResult(
                score = 0,
                issues = ["Empty description"],
                passed = False
            )

        text = description.strip()

        score, issues = cls._check_bad_tokens(text, score, issues)
        score, issues = cls._check_length(text, score, issues)
        score, issues = cls._check_word_diversity(text, score, issues)
        score, issues = cls._check_consecutive_repeats(text, score, issues)
        score, issues = cls._check_gibberish_ratio(text, score, issues)

        final_score = max(0, score)
        passed = final_score >= config.DESCRIPTION_AUDIT_PASS_THRESHOLD

        return AuditResult(
            score = final_score,
            issues = issues,
            passed = passed
        )

    @classmethod
    def _check_bad_tokens(cls,
                          text: str,
                          score: int,
                          issues: list[str]) -> tuple[int,
                                                      list[str]]:
        """
        Check for model control tokens that shouldn't appear in output.
        """
        for pattern in cls.BAD_TOKEN_PATTERNS:
            count = text.count(pattern)
            if count > 0:
                score -= config.AUDIT_PENALTY_BAD_TOKEN
                issues.append(f"Contains bad token '{pattern}' ({count}x)")
        return score, issues

    @classmethod
    def _check_length(cls,
                      text: str,
                      score: int,
                      issues: list[str]) -> tuple[int,
                                                  list[str]]:
        """
        Check description length is within acceptable bounds.
        """
        if len(text) < config.DESCRIPTION_MIN_LENGTH:
            score -= config.AUDIT_PENALTY_TOO_SHORT
            issues.append(
                f"Too short: {len(text)} chars (min {config.DESCRIPTION_MIN_LENGTH})"
            )
        elif len(text) > config.DESCRIPTION_MAX_LENGTH:
            score -= config.AUDIT_PENALTY_TOO_LONG
            issues.append(
                f"Too long: {len(text)} chars (max {config.DESCRIPTION_MAX_LENGTH})"
            )
        return score, issues

    @classmethod
    def _check_word_diversity(
        cls,
        text: str,
        score: int,
        issues: list[str]
    ) -> tuple[int,
               list[str]]:
        """
        Check that description has sufficient word variety.
        Low diversity suggests repetitive hallucination.
        """
        words = text.lower().split()
        if len(words) == 0:
            return score, issues

        unique_words = set(words)
        diversity = len(unique_words) / len(words)

        if diversity < config.DESCRIPTION_MIN_WORD_DIVERSITY:
            score -= config.AUDIT_PENALTY_LOW_DIVERSITY
            issues.append(
                f"Low word diversity: {diversity:.1%} "
                f"(min {config.DESCRIPTION_MIN_WORD_DIVERSITY:.0%})"
            )
        return score, issues

    @classmethod
    def _check_consecutive_repeats(
        cls,
        text: str,
        score: int,
        issues: list[str]
    ) -> tuple[int,
               list[str]]:
        """
        Check for same word repeated multiple times in a row.
        Strong indicator of hallucination/looping.
        """
        words = text.lower().split()
        max_repeats = config.DESCRIPTION_MAX_CONSECUTIVE_REPEATS

        if len(words) < max_repeats + 1:
            return score, issues

        for i in range(len(words) - max_repeats):
            window = words[i : i + max_repeats + 1]
            if len(set(window)) == 1:
                score -= config.AUDIT_PENALTY_CONSECUTIVE_REPEATS
                issues.append(
                    f"Word repeated {max_repeats + 1}x consecutively: '{window[0]}'"
                )
                break

        return score, issues

    @classmethod
    def _check_gibberish_ratio(
        cls,
        text: str,
        score: int,
        issues: list[str]
    ) -> tuple[int,
               list[str]]:
        """
        Check ratio of non-alphabetic characters.
        High ratio suggests corrupted output.
        """
        if len(text) == 0:
            return score, issues

        non_alpha = sum(
            1 for c in text if not c.isalpha() and not c.isspace()
        )
        gibberish_ratio = non_alpha / len(text)

        if gibberish_ratio > config.DESCRIPTION_MAX_GIBBERISH_RATIO:
            score -= config.AUDIT_PENALTY_HIGH_GIBBERISH
            issues.append(f"High gibberish ratio: {gibberish_ratio:.1%}")

        return score, issues

    @classmethod
    def is_acceptable(cls, description: str) -> bool:
        """
        Quick check if description passes minimum threshold.
        """
        result = cls.audit(description)
        return result.passed
