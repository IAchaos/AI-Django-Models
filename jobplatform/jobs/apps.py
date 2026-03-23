from django.apps import AppConfig


class JobsConfig(AppConfig):
    name = 'jobs'

    def ready(self):
        """
        The key thing the diagrams show  signals.py and models.py never import each other directly.
        They are completely decoupled. Django is the middleman that connects them at runtime through
        the signal system. That is the whole point , the Application model does not know that a signal
        receiver exists. It just saves, and Django broadcasts the event to whoever is listening.
        """
        import jobs.signals
