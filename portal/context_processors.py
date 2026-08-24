"""Template context processors."""
def site_context(request):
    return {
        'SITE_NAME': 'Ayurveda Skill Portal',
        'SITE_TAGLINE': 'Skill Mapping & Internship Portal - SIH 2026',
    }
