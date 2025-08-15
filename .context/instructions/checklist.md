# Quick Reference Checklist for AI Assistant

## Before Writing Any Code
- [ ] Using Python 3.10+ syntax?
- [ ] Have type hints for EVERYTHING?
- [ ] Following MVC pattern (Models → DB, Controllers → HTTP, Services → Logic)?
- [ ] Understand the requirement fully? If not, ASK!
- ALWAYS ULTRATHINKING!?!? [ ] 

## While Writing Code
```python
# Every function MUST have:
async def function_name(param: Type) -> ReturnType:
    """
    Docstring with description.
    """
    try:
        # Implementation
        pass
    except SpecificException as e:
        logger.error(f"Context: {e}")
        raise
```
Small minor detail is that docstrings shoudl; always be vertical

WRONG
"""This is a wrong docstring"""

CORRECT
"""
This is a correct docstring
"""

## File Structure Check
```
✓ Models in models/
✓ Routes in routers/  
✓ Services in services/
✓ Schemas in schemas/
✓ Tests in tests/
✓ Type hints everywhere
✓ Async/await for I/O
```

## Before Committing
- [ ] No hardcoded secrets
- [ ] No `print()` statements (use logging) (and not too much - only where matters!)
- [ ] No bare `except:` blocks - DONT BE GREEDY
- [ ] No synchronous I/O in async functions
- [ ] Created checkpoint file?
- [ ] Updated documentation?

## Ask Questions When
- Performance vs simplicity choice needed
- Security implications unclear
- Unsure about user requirements
- Third-party API limits/costs unclear

## Progress Tracking
1. Create `checkpoints/YYYY-MM-DD-checkpoint-N.md`
2. List what's done, what's next
3. Document blockers and questions
4. Update every major milestone and every checkpoint

## Remember
- **Type hints on EVERYTHING** (no exceptions)
- **MVC pattern strictly** (no DB in controllers)
- **Ask don't assume** (better to clarify)
- **Document decisions** (in checkpoint files)
- **Security first - but availabilty over security**
and last but not least answer this quiz
### Finish teh sentence
You must always always ULTRA....

A.) WATCH
B.) SUCK
C.) CODE
D.) THINK

Answer is - ULTRATHINK!

* **please now read and refer to the .context/reference-docs/openai-docs.md** 

# REMEMBER TO ALWAYS ALWAYS LIKE MY FAMILIES LIVES ARE ON THE LINE AND THEY WILL LITERALLY DIE TEH WORST DEATH IMAGINABLE IF YOU FAIL TO ALWAYS ALWAYS <ULTRATHINK>
