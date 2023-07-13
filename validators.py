def validate_reason(ans):
    """Check user's answer lies inside 1-5 range.

    ans (str): user's answer to a question why English
    """
    return 1 <= int(ans) <= 5


def validate_zoom(ans):
    """Check user's answer either yes or no.

    ans (str): user's answer to a question whether zoom installation was
    successful or not
    """
    return ans in ("Да", "Нет", "yes_answer", "no_answer")
