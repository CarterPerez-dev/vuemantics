"""
ⒸAngelaMos | 2026
Description validation and audit logic.
Sanity checks AI-generated descriptions for hallucinations and gibberish.
"""

import re
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

        score, issues = cls._check_complete_garbage(text, score, issues)
        score, issues = cls._check_bad_tokens(text, score, issues)
        score, issues = cls._check_length(text, score, issues)
        score, issues = cls._check_word_diversity(text, score, issues)
        score, issues = cls._check_consecutive_repeats(text, score, issues)
        score, issues = cls._check_gibberish_ratio(text, score, issues)
        score, issues = cls._check_sentence_structure(text, score, issues)
        score, issues = cls._check_common_words(text, score, issues)

        final_score = max(0, score)
        passed = final_score >= config.DESCRIPTION_AUDIT_PASS_THRESHOLD

        return AuditResult(
            score = final_score,
            issues = issues,
            passed = passed
        )

    @classmethod
    def _check_complete_garbage(cls,
                                text: str,
                                score: int,
                                issues: list[str]) -> tuple[int,
                                                            list[str]]:
        """
        Check if description is complete garbage (mostly random special chars).
        This catches catastrophic AI failures that produce gibberish.
        """
        if len(text) == 0:
            return score, issues

        # Check alpha ratio
        alphabetic = sum(1 for c in text if c.isalpha())
        alpha_ratio = alphabetic / len(text)

        if alpha_ratio < 0.3:
            score -= 70
            issues.append(
                f"Complete garbage: only {alpha_ratio:.1%} alphabetic characters"
            )
            return score, issues

        # Check for random character sequences (e.g., "4#2>*)=-C4>8B")
        # Real text doesn't mix letters, numbers, and special chars randomly
        tokens = re.findall(r'[^\s]+', text)
        garbage_tokens = 0

        for token in tokens[:100]:  # Check first 100 tokens
            # Count different character types
            letters = sum(1 for c in token if c.isalpha())
            digits = sum(1 for c in token if c.isdigit())
            special = sum(1 for c in token if not c.isalnum())

            # If token has all three types and is short, it's likely garbage
            if len(token) <= 15 and letters > 0 and digits > 0 and special > 2:
                garbage_tokens += 1

        garbage_ratio = garbage_tokens / len(tokens) if tokens else 0

        if garbage_ratio > 0.3:
            score -= 80
            issues.append(
                f"Random character soup detected: {garbage_ratio:.0%} of tokens are garbage"
            )
        elif garbage_ratio > 0.1:
            score -= 50
            issues.append(
                f"Many random character sequences: {garbage_ratio:.0%} of tokens"
            )

        return score, issues

    @classmethod
    def _check_sentence_structure(cls,
                                   text: str,
                                   score: int,
                                   issues: list[str]) -> tuple[int,
                                                               list[str]]:
        """
        Check for basic sentence structure (capitalization, punctuation).
        Real descriptions should have proper sentences.
        """
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) == 0:
            score -= 30
            issues.append("No sentence structure (missing punctuation)")
            return score, issues

        capitalized = sum(1 for s in sentences if s and s[0].isupper())
        capital_ratio = capitalized / len(sentences)

        if capital_ratio < 0.5 and len(sentences) > 1:
            score -= 15
            issues.append(
                f"Poor capitalization: only {capital_ratio:.0%} of sentences capitalized"
            )

        return score, issues

    @classmethod
    def _check_common_words(cls,
                           text: str,
                           score: int,
                           issues: list[str]) -> tuple[int,
                                                       list[str]]:
        """
        Check if description contains common English words.
        Real descriptions should have words like 'the', 'a', 'and', 'is', etc.
        """
        common_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were',
            'this', 'that', 'these', 'those', 'it', 'its', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'can', 'as', 'not'
        }

        # Extract only alphabetic "words" (filter out garbage like "4#2>*")
        words = [w for w in text.lower().split() if any(c.isalpha() for c in w)]

        if len(words) < 5:
            return score, issues

        # Filter to only real words (mostly alphabetic)
        real_words = [
            w for w in words
            if sum(1 for c in w if c.isalpha()) / len(w) > 0.7
        ]

        if len(real_words) < len(words) * 0.5:
            score -= 50
            issues.append(
                f"Most tokens are not real words ({len(real_words)}/{len(words)})"
            )

        common_found = sum(1 for w in real_words if w in common_words)
        common_ratio = common_found / len(real_words) if real_words else 0

        if common_ratio < 0.02:
            score -= 60
            issues.append(
                f"Almost no common English words ({common_ratio:.1%} of words)"
            )
        elif common_ratio < 0.05:
            score -= 45
            issues.append(
                f"Very few common English words ({common_ratio:.1%} of words)"
            )
        elif common_ratio < 0.15:
            score -= 20
            issues.append(
                f"Few common English words ({common_ratio:.0%} of words)"
            )

        return score, issues

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

        if gibberish_ratio > 0.5:
            score -= 60
            issues.append(f"Extreme gibberish ratio: {gibberish_ratio:.1%}")
        elif gibberish_ratio > config.DESCRIPTION_MAX_GIBBERISH_RATIO:
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
